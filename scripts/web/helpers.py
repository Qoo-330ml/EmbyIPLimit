from __future__ import annotations

from functools import wraps

from flask import jsonify
from flask_login import current_user


def to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': '未登录'}), 401
        if not getattr(current_user, 'is_admin', False) and not getattr(current_user, 'is_admin_emby', False):
            return jsonify({'error': '权限不足'}), 403
        return f(*args, **kwargs)
    return decorated


def build_external_url(base_url, path=''):
    base = (base_url or '').rstrip('/')
    suffix = '/' + str(path).lstrip('/') if path else ''
    return f'{base}{suffix}' if base else (suffix or '')


def get_emby_external_url(config):
    return build_external_url(config.get('emby', {}).get('external_url') or '', '')


def get_service_external_url(config):
    return build_external_url(config.get('service', {}).get('external_url') or '', '')


def send_webhook_if_enabled(server, event_type, payload):
    notifier = getattr(getattr(server, 'monitor', None), 'webhook_notifier', None)
    if notifier and notifier.is_enabled():
        notifier.send(event_type, payload)
        return True
    return False


def send_wish_comment_email(server, request_id, comment_content, commenter_name):
    if not server.wish_store:
        return False
    info = server.wish_store.get_wish_user_info(request_id)
    if not info or not info['user_id']:
        return False
    user_email = server.db_manager.get_user_email(info['user_id'])
    if not user_email:
        return False
    return server.email_notifier.send_comment_notification(
        user_email, info['title'], info['media_type'], comment_content, commenter_name
    )


def send_wish_status_email(server, request_id, new_status, admin_name):
    if not server.wish_store:
        return False
    info = server.wish_store.get_wish_user_info(request_id)
    if not info or not info['user_id']:
        return False
    user_email = server.db_manager.get_user_email(info['user_id'])
    if not user_email:
        return False
    return server.email_notifier.send_wish_status_notification(
        user_email, info['title'], info['media_type'], new_status, admin_name
    )
