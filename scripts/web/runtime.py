from __future__ import annotations

from location.service import LocationService
from webhook_notifier import WebhookNotifier


def create_location_service(config, db_manager, emby_client):
    use_geocache = config.get('ip_location', {}).get('use_geocache', False)
    emby_server_info = emby_client.get_server_info()
    return LocationService(
        use_hiofd=use_geocache,
        db_manager=db_manager,
        emby_server_info=emby_server_info,
    )


def build_webhook_notifier(config, current=None):
    webhook_config = config.get('webhook', {})
    if current:
        current.update_config(webhook_config)
        return current
    if webhook_config.get('enabled', False):
        return WebhookNotifier(webhook_config)
    return None
