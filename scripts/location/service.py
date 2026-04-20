from __future__ import annotations

import logging
from typing import Any

from geocache_client import GeoCacheClient

from .command_runner import CommandRunner
from .providers import HIOFDProvider, IP138Provider
from .result import build_unknown_location

logger = logging.getLogger(__name__)


class LocationService:
    """IP 归属地查询服务：支持 qoo-ip138 和自建库两种方式切换。"""

    def __init__(self, timeout_sec: int = 45, use_hiofd: bool = False, db_manager=None, emby_server_info: dict = None):
        self.timeout_sec = timeout_sec
        self.use_hiofd = use_hiofd
        self.cache: dict[str, dict[str, Any]] = {}
        self.hiofd_retries = 3
        self.hiofd_retry_delay_sec = 1.0
        self.db_manager = db_manager
        self.emby_server_info = emby_server_info or {}
        self.runner = CommandRunner(timeout_sec=self.timeout_sec)
        self.ip138_provider = IP138Provider(self.runner)
        self.hiofd_provider = HIOFDProvider(self.runner, retries=self.hiofd_retries, retry_delay_sec=self.hiofd_retry_delay_sec)

        self.geocache_client = None
        self.geocache_enabled = self.use_hiofd
        if self.geocache_enabled:
            self.geocache_client = GeoCacheClient(emby_server_info=self.emby_server_info)
            logging.info('🌍 GeoCache 已启用')

    def update_config(self, use_hiofd: bool):
        old_provider = self._current_provider_name()
        new_provider = '自建库' if use_hiofd else 'ip138'
        old_geocache_enabled = self.geocache_enabled
        new_geocache_enabled = use_hiofd

        if old_provider != new_provider:
            logging.info('📍 IP解析方式已切换: %s -> %s', old_provider, new_provider)
            self.use_hiofd = use_hiofd
            self.geocache_enabled = new_geocache_enabled

            if new_geocache_enabled and not old_geocache_enabled:
                self.geocache_client = GeoCacheClient(emby_server_info=self.emby_server_info)
                logging.info('🌍 GeoCache 已启用')
            elif not new_geocache_enabled and old_geocache_enabled:
                self.geocache_client = None
                logging.info('🌍 GeoCache 已禁用')

            self.cache.clear()
            logging.info('📍 已清空IP解析缓存')

    def lookup(self, ip_address: str) -> dict[str, Any]:
        if not ip_address:
            return build_unknown_location('', '未知位置')

        current_provider = self._current_provider_name()

        cached_info = self.cache.get(ip_address)
        if cached_info and cached_info.get('provider') == current_provider:
            return cached_info
        if cached_info:
            logging.info('📍 解析方式已切换，重新查询 %s', ip_address)

        if self.db_manager:
            db_info = self.db_manager.get_ip_location(ip_address)
            if db_info and db_info.get('provider') == current_provider:
                self.cache[ip_address] = db_info
                return db_info
            if db_info:
                logging.info('📍 数据库中IP归属地数据源已切换，重新查询 %s', ip_address)

        try:
            info = self._get_active_provider().lookup(ip_address)
        except Exception as e:
            provider = self._current_provider_name()
            logging.error('📍 %s 查询失败(%s): %s', provider, ip_address, e)
            info = build_unknown_location(ip_address, '解析失败')

        self.cache[ip_address] = info

        if info.get('provider') != 'none' and self.db_manager:
            self.db_manager.save_ip_location(info)

        if info.get('provider') != 'none' and self.geocache_enabled and self.geocache_client:
            self.geocache_client.report_location_info(info)

        return info

    def _get_active_provider(self):
        return self.hiofd_provider if self.use_hiofd else self.ip138_provider

    def _current_provider_name(self):
        return '自建库' if self.use_hiofd else 'ip138'
