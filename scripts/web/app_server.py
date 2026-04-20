from __future__ import annotations

import logging
import os
import secrets
import string
import sys
import threading
from datetime import datetime

from flask import Flask, jsonify
from flask_login import LoginManager, UserMixin

from config_loader import get_base_dir, save_config
from email_notifier import EmailNotifier
from web.routes import (
    register_admin_group_routes,
    register_admin_shadow_routes,
    register_admin_system_routes,
    register_admin_user_routes,
    register_admin_wish_routes,
    register_auth_routes,
    register_frontend_routes,
    register_public_routes,
    register_user_routes,
)

logger = logging.getLogger(__name__)


def _generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class AdminUser(UserMixin):
    id = 'admin'
    is_admin = True
    is_admin_emby = False
    is_temp_admin = True


class EmbyUser(UserMixin):
    is_admin = False
    is_temp_admin = False

    def __init__(self, user_id, username, groups=None, expiry_date=None, never_expire=False, is_admin_emby=False):
        self.id = f'emby:{user_id}'
        self.user_id = user_id
        self.username = username
        self.groups = groups or []
        self.expiry_date = expiry_date
        self.never_expire = never_expire
        self.is_admin_emby = is_admin_emby


class WebServer:
    def __init__(
        self,
        config,
        db_manager,
        emby_client,
        wish_store,
        shadow_library=None,
        shadow_syncer=None,
        security_client=None,
        location_service=None,
        monitor=None,
        tmdb_client=None,
    ):
        self.config = config
        self.db_manager = db_manager
        self.emby_client = emby_client
        self.wish_store = wish_store
        self.shadow_library = shadow_library
        self.shadow_syncer = shadow_syncer
        self.security_client = security_client
        self.location_service = location_service
        self.monitor = monitor
        self.tmdb_client = tmdb_client
        self.email_notifier = EmailNotifier(config)
        self.logger = logging.getLogger('embyq.web')

        self.temp_admin_username = 'admin'
        self.temp_admin_password = None

        self.login_manager = LoginManager()
        self.location_service = location_service

        base_dir = get_base_dir()
        self.frontend_dist = os.path.join(base_dir, 'frontend', 'dist')
        self.frontend_assets = os.path.join(self.frontend_dist, 'assets')
        self.project_root = base_dir

        self.app = self.create_app()

        self._register_auth_handlers()
        self._register_routes()

        self.running = False
        self.server_thread = None

        self._init_temp_admin()

    def _register_auth_handlers(self):
        @self.login_manager.user_loader
        def load_user(user_id):
            if user_id == 'admin':
                if self.config.get('web', {}).get('admin_disabled', False):
                    return None
                return AdminUser()
            if user_id and user_id.startswith('emby:'):
                from flask import session as flask_session
                emby_data = flask_session.get('emby_user_data')
                if emby_data and emby_data.get('user_id') == user_id[5:]:
                    return EmbyUser(
                        user_id=emby_data['user_id'],
                        username=emby_data.get('username', ''),
                        groups=emby_data.get('groups', []),
                        expiry_date=emby_data.get('expiry_date'),
                        never_expire=emby_data.get('never_expire', False),
                        is_admin_emby=emby_data.get('is_admin_emby', False),
                    )
            return None

    def create_app(self):
        base_dir = get_base_dir()
        self.frontend_dist = os.path.join(base_dir, 'frontend', 'dist')
        app = Flask(
            __name__,
            template_folder=self.frontend_dist,
        )
        app.static_folder = None

        web_config = self.config.setdefault('web', {})
        secret_key = web_config.get('secret_key')
        if not secret_key:
            secret_key = secrets.token_hex(32)
            web_config['secret_key'] = secret_key
            save_config(self.config)
        app.secret_key = secret_key

        self.login_manager.init_app(app)

        logging.getLogger('werkzeug').setLevel(logging.WARNING)

        return app

    def _register_routes(self):
        register_auth_routes(self)
        register_public_routes(self)
        register_frontend_routes(self)
        register_admin_user_routes(self)
        register_admin_group_routes(self)
        register_admin_wish_routes(self)
        register_admin_shadow_routes(self)
        register_admin_system_routes(self)
        register_user_routes(self)

    def create_admin_user(self):
        return AdminUser()

    def _init_temp_admin(self):
        web_config = self.config.setdefault('web', {})
        if web_config.get('admin_disabled', False):
            return

        need_save = False

        if not web_config.get('admin_username'):
            web_config['admin_username'] = 'admin'
            need_save = True

        password = web_config.get('admin_password') or None
        if not password or password == 'admin123':
            password = _generate_random_password()
            web_config['admin_password'] = password
            need_save = True

        self.temp_admin_username = web_config['admin_username']
        self.temp_admin_password = web_config.get('admin_password')

        if need_save:
            save_config(self.config)
            sys.stdout.flush()

            logger.info('=' * 50)
            logger.info('🔑 临时管理员账号已自动创建')
            logger.info('   用户名: %s', self.temp_admin_username)
            logger.info('   密码: %s', self.temp_admin_password)
            logger.info('   请尽快登录并配置 Emby 连接')
            logger.info('   首次有 Emby 管理员登录后将自动禁用此账号')
            logger.info('=' * 50)

            sys.stdout.write('\n' + '#' * 50 + '\n')
            sys.stdout.write('# 🔑 临时管理员账号已自动创建\n')
            sys.stdout.write('# 用户名: %s\n' % self.temp_admin_username)
            sys.stdout.write('# 密码: %s\n' % self.temp_admin_password)
            sys.stdout.write('# 请尽快登录并配置 Emby 连接\n')
            sys.stdout.write('# 首次有 Emby 管理员登录后将自动禁用此账号\n')
            sys.stdout.write('#' * 50 + '\n\n')
            sys.stdout.flush()

    def disable_temp_admin(self):
        web_config = self.config.setdefault('web', {})
        web_config['admin_disabled'] = True
        save_config(self.config)
        logger.info('🔑 临时管理员账号已自动禁用 (由 Emby 管理员接管)')

    def is_guest_request_enabled(self):
        return bool(self.config.get('guest_request', {}).get('enabled', False))

    def is_temp_admin_enabled(self):
        return not self.config.get('web', {}).get('admin_disabled', False)

    def frontend_index_exists(self):
        return os.path.exists(os.path.join(self.frontend_dist, 'index.html'))

    def start(self, host='0.0.0.0', port=5001):
        if self.running:
            return
        self.running = True

        web_cfg = self.config.get('web', {})
        host = web_cfg.get('host', host)
        port = web_cfg.get('port', port)

        from werkzeug.serving import run_simple

        server_thread = threading.Thread(
            target=lambda: run_simple(
                host,
                port,
                self.app,
                use_reloader=False,
                threaded=True,
            ),
            daemon=True,
        )
        server_thread.start()
        self.server_thread = server_thread

        import time
        time.sleep(0.5)

        base_url = f'http://localhost:{port}'
        logger.info('Web服务器已启动: url=%s', base_url)

        if self.shadow_syncer:
            time.sleep(0.3)

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.shadow_syncer:
            self.shadow_syncer.stop()

    def get_user_groups_map(self):
        if not self.db_manager:
            return {}
        return self.db_manager.get_user_groups_map()

    def get_user_expiry(self, user_id):
        if not self.db_manager:
            return {}
        return self.db_manager.get_user_expiry(user_id)

    def get_all_users_with_expiry(self):
        users = self.emby_client.get_users() if self.emby_client else []
        default_threshold = self.config.get('notifications', {}).get('alert_threshold', 2)
        result = []
        for user in users:
            user_id = user.get('Id', '')
            expiry_info = self.db_manager.get_user_expiry(user_id) if self.db_manager else {}
            groups = self.db_manager.get_user_group_names(user_id) if self.db_manager else []
            is_disabled = bool(user.get('Policy', {}).get('IsDisabled', False))
            user_data = {
                'id': user.get('Id'),
                'name': user.get('Name'),
                'is_disabled': is_disabled,
                'expiry_date': expiry_info.get('expiry_date') if expiry_info else None,
                'never_expire': expiry_info.get('never_expire', False) if expiry_info else False,
                'alert_threshold': expiry_info.get('alert_threshold') if expiry_info else None,
                'effective_alert_threshold': self.db_manager.get_effective_alert_threshold(user_id, default_threshold) if self.db_manager else default_threshold,
                'groups': groups,
            }
            if expiry_info and expiry_info.get('expiry_date'):
                try:
                    expiry_date = datetime.strptime(expiry_info['expiry_date'], '%Y-%m-%d')
                    user_data['is_expired'] = datetime.now() > expiry_date
                except Exception:
                    user_data['is_expired'] = False
            else:
                user_data['is_expired'] = False
            result.append(user_data)
        return result

    def _lookup_location(self, ip_address):
        if not ip_address or not self.location_service:
            return '未知位置'
        try:
            info = self.location_service.lookup(ip_address)
            return info.get('formatted', '未知位置') if info else '未知位置'
        except Exception:
            return '未知位置'

    def get_server_info(self):
        if not self.emby_client:
            return {'server_name': '', 'version': '', 'operating_system': '', 'is_running': False}
        try:
            raw = self.emby_client.get_server_info()
            if not raw or not raw.get('ServerName'):
                return {'server_name': '', 'version': '', 'operating_system': '', 'is_running': False}
            return {
                'server_name': raw.get('ServerName', ''),
                'version': raw.get('Version', ''),
                'operating_system': raw.get('OperatingSystem', ''),
                'is_running': True,
            }
        except Exception as e:
            self.logger.warning('获取 Emby 服务器信息失败: %s', e)
            return {'server_name': '', 'version': '', 'operating_system': '', 'is_running': False}

    def get_landing_posters(self):
        import json
        import os
        from datetime import date as date_cls

        from config_loader import get_data_dir

        source = self.config.get('landing', {}).get('source', 'default')
        today = date_cls.today().isoformat()
        posters_dir = os.path.join(get_data_dir(), 'landing-posters')
        cache_file = os.path.join(posters_dir, 'cache.json')

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                if cached.get('date') == today and cached.get('source') == source and cached.get('posters'):
                    return cached['posters']
            except Exception:
                pass

        if source == 'tmdb' and self.tmdb_client and self.tmdb_client.is_ready():
            posters = self.tmdb_client.get_trending_backdrops(limit=5)
            if posters:
                os.makedirs(posters_dir, exist_ok=True)
                saved_posters = []
                for poster in posters:
                    try:
                        import re
                        from urllib.parse import quote
                        title = poster.get('title', '未知内容')
                        safe_name = re.sub(r'[\\/:*?"<>|]', '_', title)
                        safe_name = safe_name.strip('_.')
                        filename = f'{safe_name} - tmdb.jpg'
                        filepath = os.path.join(posters_dir, filename)
                        if os.path.exists(filepath):
                            saved_posters.append({
                                'url': f'/landing-posters/{quote(filename)}',
                                'title': title,
                            })
                            continue
                        response = self.tmdb_client.session.get(poster['backdrop_url'], timeout=15)
                        if response.status_code == 200:
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            saved_posters.append({
                                'url': f'/landing-posters/{quote(filename)}',
                                'title': title,
                            })
                    except Exception as e:
                        self.logger.warning('下载TMDB海报失败: %s, error=%s', poster.get('backdrop_url'), e)
                if saved_posters:
                    try:
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump({'date': today, 'source': source, 'posters': saved_posters}, f, ensure_ascii=False)
                    except Exception as e:
                        self.logger.warning('保存海报缓存失败: %s', e)
                    return saved_posters

        elif source == 'emby' and self.emby_client and self.emby_client.server_url:
            posters = self.emby_client.get_backdrop_posters(limit=5)
            if posters:
                os.makedirs(posters_dir, exist_ok=True)
                saved_posters = []
                for poster in posters:
                    try:
                        import re
                        from urllib.parse import quote
                        title = poster.get('title', '未知内容')
                        safe_name = re.sub(r'[\\/:*?"<>|]', '_', title)
                        safe_name = safe_name.strip('_.')
                        filename = f'{safe_name} - emby.jpg'
                        filepath = os.path.join(posters_dir, filename)
                        if os.path.exists(filepath):
                            saved_posters.append({
                                'url': f'/landing-posters/{quote(filename)}',
                                'title': title,
                            })
                            continue
                        response = self.emby_client.session.get(poster['url'], timeout=10)
                        if response.status_code == 200:
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            saved_posters.append({
                                'url': f'/landing-posters/{quote(filename)}',
                                'title': title,
                            })
                    except Exception as e:
                        self.logger.warning('下载Emby海报失败: %s, error=%s', poster.get('url'), e)
                if saved_posters:
                    try:
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump({'date': today, 'source': source, 'posters': saved_posters}, f, ensure_ascii=False)
                    except Exception as e:
                        self.logger.warning('保存海报缓存失败: %s', e)
                    return saved_posters

        return []

    def start_landing_posters_scheduler(self):
        import os
        import threading
        from datetime import date as date_cls, time as time_cls, datetime, timedelta

        from config_loader import get_data_dir

        def _run():
            while True:
                source = self.config.get('landing', {}).get('source', 'default')
                if source == 'default':
                    now = datetime.now()
                    target = now.replace(hour=2, minute=0, second=0, microsecond=0)
                    if now >= target:
                        target += timedelta(days=1)
                    wait_secs = (target - now).total_seconds()
                    threading.Event().wait(wait_secs)
                    continue
                source_label = 'TMDB' if source == 'tmdb' else 'Emby'
                now = datetime.now()
                target = now.replace(hour=2, minute=0, second=0, microsecond=0)
                if now >= target:
                    target += timedelta(days=1)
                wait_secs = (target - now).total_seconds()
                self.logger.info('%s海报定时任务将在 %s 执行（等待 %.0f 秒）', source_label, target.strftime('%Y-%m-%d %H:%M:%S'), wait_secs)
                threading.Event().wait(wait_secs)
                self.logger.info('开始定时拉取%s落地页海报...', source_label)
                self.get_landing_posters()

        t = threading.Thread(target=_run, daemon=True, name='landing-posters-scheduler')
        t.start()

    def get_all_active_sessions(self):
        if not self.emby_client:
            return []
        sessions_dict = self.emby_client.get_active_sessions()
        sessions = []
        for session_id, session in sessions_dict.items():
            user_id = session.get('UserId', '')
            user_name = session.get('UserName', '')
            ip_address = session.get('RemoteEndPoint', '')
            sessions.append({
                'session_id': session_id,
                'user_id': user_id,
                'username': user_name,
                'device_name': session.get('DeviceName', ''),
                'client_type': session.get('Client', ''),
                'ip_address': ip_address,
                'media_name': self.emby_client.parse_media_info(session.get('NowPlayingItem')),
                'location': self._lookup_location(ip_address),
            })
        return sessions

    def get_user_active_sessions(self, user_id):
        if not self.emby_client:
            return []
        sessions_dict = self.emby_client.get_active_sessions()
        sessions = []
        for session_id, session in sessions_dict.items():
            if session.get('UserId') == user_id:
                sessions.append({
                    'session_id': session_id,
                    'device_name': session.get('DeviceName', ''),
                    'client_type': session.get('Client', ''),
                    'ip_address': session.get('RemoteEndPoint', ''),
                    'media_name': self.emby_client.parse_media_info(session.get('NowPlayingItem')),
                })
        return sessions

    def get_user_id_by_username(self, username):
        if not self.emby_client:
            return None
        user = self.emby_client.get_user_by_name(username)
        return user.get('Id') if user else None

    def get_user_playback_records(self, user_id=None):
        if not self.db_manager or not user_id:
            return []
        return self.db_manager.get_user_playback_records(user_id)

    def get_user_ban_info(self, user_id=None):
        if not self.db_manager or not user_id:
            return None
        return self.db_manager.get_user_ban_info(user_id)

    def serialize_ban_info(self, ban_info):
        if not ban_info:
            return {}
        return {
            'timestamp': ban_info[0] if len(ban_info) > 0 else None,
            'trigger_ip': ban_info[1] if len(ban_info) > 1 else None,
            'active_sessions': ban_info[2] if len(ban_info) > 2 else 0,
            'action': ban_info[3] if len(ban_info) > 3 else None,
        }

    def serialize_playback_records(self, records):
        result = []
        for r in records:
            if hasattr(r, 'session_id'):
                result.append({
                    'session_id': r.session_id,
                    'ip_address': r.ip_address,
                    'location': r.location,
                    'device_name': r.device_name,
                    'client_type': r.client_type,
                    'media_name': r.media_name,
                    'start_time': (
                        r.start_time.strftime('%Y-%m-%dT%H:%M:%S')
                        if r.start_time else None
                    ),
                    'end_time': (
                        r.end_time.strftime('%Y-%m-%dT%H:%M:%S')
                        if r.end_time else None
                    ),
                    'duration': int(r.duration) if r.duration else None,
                })
            elif isinstance(r, (list, tuple)) and len(r) >= 9:
                result.append({
                    'session_id': r[0],
                    'ip_address': r[1],
                    'device_name': r[2],
                    'client_type': r[3],
                    'media_name': r[4],
                    'start_time': r[5],
                    'end_time': r[6],
                    'duration': int(r[7]) if r[7] else None,
                    'location': r[8],
                })
        return result
