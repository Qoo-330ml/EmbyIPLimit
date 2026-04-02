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
        self._proxy_config = {}

        if not enabled:
            self._session.proxies.clear()
            return

        http_proxy = config.get('http', '').strip()
        https_proxy = config.get('https', '').strip()
        socks5_proxy = config.get('socks5', '').strip()

        if http_proxy:
            self._proxy_config['http'] = http_proxy
        if https_proxy:
            self._proxy_config['https'] = https_proxy
        if socks5_proxy:
            self._proxy_config['http'] = socks5_proxy
            self._proxy_config['https'] = socks5_proxy

        self._session.proxies.update(self._proxy_config)

    def get_session(self):
        return self._session

    def is_enabled(self):
        return bool(self._proxy_config)


def get_session():
    return ProxySession().get_session()


def update_proxy_config(config):
    ProxySession().update_proxy(config)


def is_proxy_enabled():
    return ProxySession().is_enabled()
