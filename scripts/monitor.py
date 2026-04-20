import logging
import time
from datetime import datetime

from monitoring.alert_service import AlertService
from monitoring.ip_utils import extract_ip_address, get_ipv6_prefix, is_ipv4, is_ipv6, is_same_network
from monitoring.session_tracker import SessionTracker
from web.runtime import build_webhook_notifier, create_location_service

logger = logging.getLogger(__name__)


class EmbyMonitor:
    def __init__(self, db_manager, emby_client, security_client, config, location_service=None):
        self.db = db_manager
        self.emby = emby_client
        self.security = security_client
        self.config = config
        self.active_sessions = {}

        if location_service:
            self.location_service = location_service
        else:
            self.location_service = create_location_service(config, db_manager, self.emby)

        self.whitelist = [name.strip().lower() for name in config['security']['whitelist'] if name.strip()]
        self.auto_disable = config['security']['auto_disable']
        self.alert_threshold = config['notifications']['alert_threshold']
        self.alerts_enabled = config['notifications']['enable_alerts']
        self.ipv6_prefix_length = config['security'].get('ipv6_prefix_length', 64)

        self.webhook_notifier = None
        self.session_tracker = SessionTracker(
            db_manager=self.db,
            emby_client=self.emby,
            location_lookup=self._get_location,
            login_abnormality_checker=lambda user_id, ip: self.alert_service.check_login_abnormality(
                self.active_sessions,
                self.alerts_enabled,
                self._get_effective_threshold(user_id),
                self.auto_disable,
                user_id,
                ip,
            ),
            whitelist_resolver=self._is_whitelist_user,
        )
        self.alert_service = AlertService(
            emby_client=self.emby,
            security_client=self.security,
            db_manager=self.db,
            get_location=self._get_location,
            send_webhook=self._send_webhook_notification,
            whitelist_resolver=self._is_whitelist_user,
            ipv6_prefix_length=self.ipv6_prefix_length,
        )
        self.update_runtime_config(config)

    def update_runtime_config(self, config):
        self.config = config
        self.whitelist = [name.strip().lower() for name in config['security']['whitelist'] if name.strip()]
        self.auto_disable = config['security']['auto_disable']
        self.alert_threshold = config['notifications']['alert_threshold']
        self.alerts_enabled = config['notifications']['enable_alerts']
        self.ipv6_prefix_length = config['security'].get('ipv6_prefix_length', 64)
        self.alert_service.ipv6_prefix_length = self.ipv6_prefix_length

        try:
            self.webhook_notifier = build_webhook_notifier(config, current=self.webhook_notifier)
            if self.webhook_notifier and not self.webhook_notifier.is_enabled():
                logger.info('🔕 Webhook通知未启用')
            elif self.webhook_notifier:
                logger.info('🔔 Webhook通知已启用')
        except Exception as e:
            logger.error('❌ Webhook通知初始化/更新失败: %s', e)
            self.webhook_notifier = None

    def _is_whitelist_user(self, username):
        return (username or '').strip().lower() in self.whitelist

    def _get_effective_threshold(self, user_id):
        try:
            return self.db.get_effective_alert_threshold(user_id, self.alert_threshold)
        except Exception:
            return self.alert_threshold

    def process_sessions(self):
        if not self.emby or not self.emby.server_url:
            return

        try:
            current_sessions = self.emby.get_active_sessions()
            self.session_tracker.update_session_positions(self.active_sessions, current_sessions)
            self.session_tracker.detect_ended_sessions(self.active_sessions, current_sessions)
            self.session_tracker.detect_new_sessions(self.active_sessions, current_sessions)
        except Exception as e:
            logger.error('❌ 会话更新失败: %s', e)

    def _get_location(self, ip_address):
        if not ip_address:
            return '未知位置'

        try:
            info = self.location_service.lookup(ip_address)
            return info.get('formatted', '未知位置')
        except Exception as e:
            logger.error('📍 解析 %s 失败: %s', ip_address, e)
            return '解析失败'

    def _send_webhook_notification(self, user_info: dict):
        if not self.webhook_notifier:
            return

        try:
            success = self.webhook_notifier.send_ban_notification(user_info)
            if success:
                logger.info('🔔 Webhook通知已发送: %s', user_info['username'])
            else:
                logger.warning('⚠️ Webhook通知发送失败: %s', user_info['username'])
        except Exception as e:
            logger.error('❌ Webhook通知异常: %s', e)

    def test_webhook(self):
        if not self.webhook_notifier or not self.webhook_notifier.is_enabled():
            logger.warning('⚠️ Webhook未启用，无法测试')
            return False

        logger.info('🧪 测试Webhook配置...')
        return self.webhook_notifier.test_webhook()

    def _recover_active_sessions(self):
        try:
            unclosed = self.db.get_unclosed_sessions()
            if not unclosed:
                return

            current_sessions = self.emby.get_active_sessions()
            current_session_ids = set(current_sessions.keys())

            recovered = 0
            closed = 0
            for row in unclosed:
                session_id = row[0]
                if session_id in current_session_ids:
                    session = current_sessions[session_id]
                    play_state = session.get('PlayState', {})
                    self.active_sessions[session_id] = {
                        'session_id': session_id,
                        'user_id': row[1],
                        'username': row[2],
                        'ip': row[3],
                        'device': row[4],
                        'client': row[5],
                        'media': row[6],
                        'start_time': datetime.strptime(row[7], '%Y-%m-%d %H:%M:%S') if isinstance(row[7], str) else row[7],
                        'location': row[8],
                        'playback_duration': 0,
                        'last_position_ticks': play_state.get('PositionTicks'),
                        'is_paused': play_state.get('IsPaused', False),
                        'pause_started_at': None,
                        'total_paused_seconds': 0,
                    }
                    recovered += 1
                else:
                    end_time = datetime.now()
                    start_time = datetime.strptime(row[7], '%Y-%m-%d %H:%M:%S') if isinstance(row[7], str) else row[7]
                    duration = max(int((end_time - start_time).total_seconds()), 0)
                    self.db.record_session_end(session_id, end_time, duration)
                    closed += 1

            if recovered or closed:
                logger.info('🔄 会话恢复: 恢复 %d 个活跃会话, 关闭 %d 个过期会话', recovered, closed)
        except Exception as e:
            logger.error('❌ 会话恢复失败: %s', e)

    def _check_expired_users(self):
        self.alert_service.check_expired_users(self.whitelist, self._send_webhook_notification)

    def run(self):
        logger.info('🔍 监控服务启动 | 数据库: %s', self.config['database']['name'])

        self._recover_active_sessions()

        expiry_check_counter = 0
        expiry_check_interval = 60
        ip_cache_cleanup_counter = 0
        ip_cache_cleanup_interval = 7200

        try:
            while True:
                self.process_sessions()

                expiry_check_counter += 1
                if expiry_check_counter >= expiry_check_interval:
                    self._check_expired_users()
                    expiry_check_counter = 0

                ip_cache_cleanup_counter += 1
                if ip_cache_cleanup_counter >= ip_cache_cleanup_interval:
                    try:
                        deleted_count = self.db.cleanup_old_ip_locations(days=30)
                        if deleted_count > 0:
                            logger.info('🧹 已清理 %s 条30天前的IP归属地缓存记录', deleted_count)
                    except Exception as e:
                        logger.error('❌ 清理IP归属地缓存失败: %s', e)
                    ip_cache_cleanup_counter = 0

                time.sleep(self.config['monitor']['check_interval'])
        except KeyboardInterrupt:
            logger.info('\n👋 监控服务停止')
