from __future__ import annotations


def to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
