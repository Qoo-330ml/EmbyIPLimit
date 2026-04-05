from __future__ import annotations

import logging
from datetime import datetime

from .ip_utils import get_ipv6_prefix, is_ipv4, is_ipv6, is_same_network

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self, emby_client, security_client, db_manager, get_location, send_webhook, whitelist_resolver, ipv6_prefix_length):
        self.emby = emby_client
        self.security = security_client
        self.db = db_manager
        self.get_location = get_location
        self.send_webhook = send_webhook
        self.whitelist_resolver = whitelist_resolver
        self.ipv6_prefix_length = ipv6_prefix_length

    def check_login_abnormality(self, active_sessions, alerts_enabled, alert_threshold, auto_disable, user_id, new_ip):
        if not alerts_enabled:
            return

        existing_networks = set()
        for sess in active_sessions.values():
            if sess['user_id'] == user_id:
                existing_ip = sess['ip']
                if not is_same_network(existing_ip, new_ip, self.ipv6_prefix_length):
                    network = get_ipv6_prefix(existing_ip, self.ipv6_prefix_length) if is_ipv6(existing_ip) else existing_ip
                    existing_networks.add(network)

        if len(existing_networks) >= (alert_threshold - 1):
            self.trigger_alert(active_sessions, user_id, new_ip, len(existing_networks) + 1, auto_disable=auto_disable)

    def trigger_alert(self, active_sessions, user_id, trigger_ip, session_count, auto_disable=True):
        try:
            user_info = self.emby.get_user_info(user_id)
            username = user_info.get('Name', '未知用户').strip()

            if self.whitelist_resolver(username):
                logger.info('⚪ 白名单用户 [%s] 受保护，跳过禁用', username)
                return

            location = self.get_location(trigger_ip)
            ip_type = 'IPv6' if is_ipv6(trigger_ip) else 'IPv4' if is_ipv4(trigger_ip) else '未知'

            device = '未知设备'
            client = '未知客户端'
            for sess in active_sessions.values():
                if sess['user_id'] == user_id and sess['ip'] == trigger_ip:
                    device = sess.get('device', '未知设备')
                    client = sess.get('client', '未知客户端')
                    break

            alert_msg = f"""
            🚨 安全告警 🚨
            时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            用户名: {username}
            可疑IP: {trigger_ip} ({ip_type}) ({location})
            并发会话数: {session_count}
            """
            logger.info('=' * 60)
            logger.info(alert_msg.strip())
            logger.info('=' * 60)

            if auto_disable and self.security.disable_user(user_id, username):
                self.log_security_action(user_id, trigger_ip, session_count, username)
                self.send_webhook(
                    {
                        'username': username,
                        'user_id': user_id,
                        'ip_address': trigger_ip,
                        'ip_type': ip_type,
                        'location': location,
                        'session_count': session_count,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'reason': f'检测到{session_count}个并发会话',
                        'device': device,
                        'client': client,
                    }
                )
        except Exception as e:
            logger.error('❌ 告警处理失败: %s', e)

    def log_security_action(self, user_id, ip, count, username):
        log_data = {
            'timestamp': datetime.now(),
            'user_id': user_id,
            'username': username,
            'trigger_ip': ip,
            'active_sessions': count,
            'action': 'DISABLE'
        }
        try:
            self.db.log_security_event(log_data)
        except Exception as e:
            logger.error('❌ 安全日志记录失败: %s', e)

    def check_expired_users(self, whitelist, active_webhook_sender=None):
        try:
            expired_users = self.db.get_all_expired_users()

            for user_id in expired_users:
                try:
                    user_info = self.emby.get_user_info(user_id)
                    if not user_info:
                        continue

                    username = user_info.get('Name', '未知用户').strip()

                    if username.lower() in whitelist:
                        logger.info('⚪ 白名单用户 [%s] 到期但受保护，跳过禁用', username)
                        continue

                    is_disabled = user_info.get('Policy', {}).get('IsDisabled', False)
                    if is_disabled:
                        continue

                    if self.security.disable_user(user_id, username):
                        logger.info('🔒 用户 [%s] 账号已到期，自动封禁', username)
                        log_data = {
                            'timestamp': datetime.now(),
                            'user_id': user_id,
                            'username': username,
                            'trigger_ip': 'system',
                            'active_sessions': 0,
                            'action': 'DISABLE_EXPIRED'
                        }
                        self.db.log_security_event(log_data)

                        if active_webhook_sender:
                            active_webhook_sender(
                                {
                                    'username': username,
                                    'user_id': user_id,
                                    'ip_address': 'system',
                                    'ip_type': 'N/A',
                                    'location': '系统自动',
                                    'session_count': 0,
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'reason': '账号已到期',
                                    'device': 'N/A',
                                    'client': 'N/A'
                                }
                            )
                except Exception as e:
                    logger.error('❌ 处理到期用户 %s 失败: %s', user_id, e)
        except Exception as e:
            logger.error('❌ 检查到期用户失败: %s', e)
