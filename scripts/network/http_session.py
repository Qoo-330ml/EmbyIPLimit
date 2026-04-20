from __future__ import annotations

import requests


class ProxySession:
    _instance = None
    _session = None
    _proxy_config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._session = requests.Session()
        return cls._instance

    def update_proxy(self, config):
        enabled = config.get('enabled', False)
        url = (config.get('url') or '').strip()

        self._proxy_config = {}

        if not enabled or not url:
            self._session.proxies.clear()
            return

        if url.startswith(('socks5://', 'socks5h://', 'https://', 'http://')):
            proxy_url = url
        else:
            proxy_url = 'http://' + url

        self._proxy_config['http'] = proxy_url
        self._proxy_config['https'] = proxy_url
        self._session.proxies.clear()
        self._session.proxies.update(self._proxy_config)

    def get_session(self):
        return self._session

    def is_enabled(self):
        return bool(self._proxy_config)


def get_session():
    return ProxySession().get_session()


def bind_shared_proxy_config(session):
    session = session or requests.Session()
    session.proxies = get_session().proxies
    return session


def create_session(default_headers=None):
    session = bind_shared_proxy_config(requests.Session())
    if default_headers:
        session.headers.update(default_headers)
    return session


def update_proxy_config(config):
    ProxySession().update_proxy(config)


def apply_proxy_config(session):
    return bind_shared_proxy_config(session)


def is_proxy_enabled():
    return ProxySession().is_enabled()
