from __future__ import annotations

import logging
import os
import threading
from datetime import datetime

from flask import Flask, jsonify
from flask_login import LoginManager, UserMixin

from config_loader import get_base_dir
from web.routes import (
    register_admin_group_routes,
    register_admin_shadow_routes,
    register_admin_system_routes,
    register_admin_user_routes,
    register_admin_wish_routes,
    register_auth_routes,
    register_frontend_routes,
    register_public_routes,
)
from web.runtime import create_location_service

logger = logging.getLogger(__name__)


class WebServer:
    def __init__(
        self,
        db_manager,
        emby_client,
        security_client,
        config,
        location_service=None,
        monitor=None,
        tmdb_client=None,
        wish_store=None,
        shadow_library=None,
        shadow_syncer=None,
    ):
        self.db_manager = db_manager
        self.emby_client = emby_client
        self.security_client = security_client
        self.config = config
        self.tmdb_client = tmdb_client
        self.wish_store = wish_store
        self.shadow_library = shadow_library
        self.shadow_syncer = shadow_syncer
        self.logger = logger

        if location_service:
            self.location_service = location_service
        else:
            self.location_service = create_location_service(config, db_manager, self.emby_client)

        self.monitor = monitor

        self.project_root = get_base_dir()
        self.frontend_dist = os.path.join(self.project_root, 'frontend', 'dist')
        self.frontend_assets = os.path.join(self.frontend_dist, 'assets')

        self.app = Flask(__name__, static_folder=None)
        self.app.secret_key = 'embyq_secret_key'

        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = None

        self._register_auth_handlers()
        self._register_routes()

        self.running = False
        self.server_thread = None

    def _register_auth_handlers(self):
        @self.login_manager.user_loader
        def load_user(user_id):
            if user_id == 'admin':
                return AdminUser()
            return None

        @self.login_manager.unauthorized_handler
        def unauthorized():
            return jsonify({'error': '未登录或登录已失效'}), 401

    def _register_routes(self):
        register_auth_routes(self)
        register_public_routes(self)
        register_admin_user_routes(self)
        register_admin_wish_routes(self)
        register_admin_shadow_routes(self)
        register_admin_system_routes(self)
        register_admin_group_routes(self)
        register_frontend_routes(self)

    def create_admin_user(self):
        return AdminUser()

    def frontend_index_exists(self):
        return os.path.exists(os.path.join(self.frontend_dist, 'index.html'))

    def start(self):
        from waitress import serve

        if self.running:
            return

        def run_server():
            serve(self.app, host='0.0.0.0', port=5000)

        self.running = True
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logger.info('Web服务器已启动: url=http://localhost:5000')

    def get_all_active_sessions(self):
        active_sessions = getattr(self.monitor, 'active_sessions', {}) if self.monitor else {}
        sessions = []
        for session in (active_sessions or {}).values():
            sessions.append(
                {
                    'session_id': session.get('session_id'),
                    'user_id': session.get('user_id'),
                    'username': session.get('username') or '未知用户',
                    'ip_address': session.get('ip') or '',
                    'location': session.get('location') or '未知位置',
                    'device': session.get('device') or '未知设备',
                    'client': session.get('client') or '未知客户端',
                    'media': session.get('media') or '未知内容',
                }
            )
        sessions.sort(key=lambda current: (current.get('username') or '', current.get('session_id') or ''))
        return sessions

    def get_user_groups_map(self):
        groups = self.db_manager.get_all_user_groups() or []
        mapping = {}
        for group in groups:
            group_name = (group.get('name') or '').strip()
            if not group_name:
                continue
            for user_id in group.get('members') or []:
                mapping.setdefault(user_id, []).append(group_name)
        return mapping

    def get_user_id_by_username(self, username):
        user = self.emby_client.get_user_by_name(username)
        return user.get('Id') if user else None

    def get_user_playback_records(self, user_id=None, username=''):
        if user_id:
            records = self.db_manager.get_user_playback_records(user_id, limit=10)
            if records:
                return records
        if username:
            return self.db_manager.get_playback_records_by_username(username, limit=10)
        return []

    def serialize_playback_records(self, records):
        payload = []
        for record in records or []:
            payload.append(
                {
                    'session_id': record[0],
                    'ip_address': record[1],
                    'device_name': record[2],
                    'client_type': record[3],
                    'media_name': record[4],
                    'start_time': record[5],
                    'end_time': record[6],
                    'duration': record[7],
                    'location': record[8],
                }
            )
        return payload

    def get_user_ban_info(self, user_id=None, username=''):
        if user_id:
            record = self.db_manager.get_user_ban_info(user_id)
            if record:
                return record
        if username:
            return self.db_manager.get_ban_info_by_username(username)
        return None

    def serialize_ban_info(self, record):
        if not record:
            return None
        action = record[3]
        reason_type = 'expired' if action == 'DISABLE_EXPIRED' else 'concurrent_sessions'
        return {
            'timestamp': record[0],
            'trigger_ip': record[1],
            'active_sessions': record[2],
            'action': action,
            'reason_type': reason_type,
        }

    def get_user_active_sessions(self, user_id):
        return [session for session in self.get_all_active_sessions() if session.get('user_id') == user_id]

    def is_guest_request_enabled(self):
        return bool(self.config.get('guest_request', {}).get('enabled', False))

    def get_all_users_with_expiry(self):
        groups_map = self.get_user_groups_map()
        users = []
        today = datetime.now().date()

        for user in self.emby_client.get_users() or []:
            user_id = user.get('Id')
            expiry_info = self.db_manager.get_user_expiry(user_id) or {}
            expiry_date = expiry_info.get('expiry_date') or ''
            never_expire = bool(expiry_info.get('never_expire'))
            is_expired = False

            if expiry_date and not never_expire:
                try:
                    is_expired = datetime.strptime(expiry_date, '%Y-%m-%d').date() < today
                except ValueError:
                    is_expired = False

            users.append(
                {
                    'id': user_id,
                    'name': user.get('Name') or '',
                    'groups': groups_map.get(user_id, []),
                    'is_disabled': bool((user.get('Policy') or {}).get('IsDisabled')),
                    'expiry_date': expiry_date,
                    'never_expire': never_expire,
                    'is_expired': is_expired,
                }
            )

        users.sort(key=lambda current: (current.get('name') or '').lower())
        return users


class AdminUser(UserMixin):
    id = 'admin'
