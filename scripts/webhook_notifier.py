import logging
import requests

logger = logging.getLogger(__name__)


class WebhookNotifier:
    def __init__(self, config):
        self.config = config or {}
        self.enabled = bool(self.config.get('enabled', False))
        self.url = (self.config.get('url') or '').strip()
        self.timeout = int(self.config.get('timeout', 10) or 10)
        self.body_mode = (self.config.get('body_mode') or 'json').strip().lower()
        self.body_template = self.config.get('body_template') or ''
        self.headers = self.config.get('headers') or {}

    def is_enabled(self):
        return self.enabled and bool(self.url)

    def send(self, event_type, payload):
        if not self.enabled:
            logger.info('Webhook 通知跳过: reason=disabled, event_type=%s', event_type)
            return False
        if not self.url:
            logger.warning('Webhook 通知跳过: reason=missing_url, event_type=%s', event_type)
            return False

        try:
            headers = dict(self.headers)
            if self.body_mode == 'raw' and self.body_template:
                body = self._render_body(event_type, payload)
                headers.setdefault('Content-Type', 'text/plain; charset=utf-8')
                response = requests.post(
                    self.url,
                    data=body.encode('utf-8'),
                    headers=headers,
                    timeout=self.timeout,
                )
            else:
                headers.setdefault('Content-Type', 'application/json')
                response = requests.post(
                    self.url,
                    json={
                        'event_type': event_type,
                        'payload': payload,
                    },
                    headers=headers,
                    timeout=self.timeout,
                )

            if 200 <= response.status_code < 300:
                logger.info('Webhook 通知发送成功: event_type=%s, status_code=%s', event_type, response.status_code)
                return True

            logger.warning(
                'Webhook 通知发送失败: event_type=%s, status_code=%s, response=%s',
                event_type,
                response.status_code,
                (response.text or '')[:300],
            )
            return False
        except Exception as e:
            logger.exception('Webhook 通知异常: event_type=%s, error=%s', event_type, e)
            return False

    def _render_body(self, event_type, payload):
        body = self.body_template or ''
        replacements = {
            '{{event_type}}': str(event_type),
            '{{payload}}': str(payload),
        }
        for key, value in replacements.items():
            body = body.replace(key, value)
        return body

    def notify_user_disabled(self, username, reason, session=None):
        payload = {
            'username': username,
            'reason': reason,
            'session': session or {},
        }
        return self.send('user_disabled', payload)

    def notify_user_recovered(self, username, user_id=''):
        payload = {
            'username': username,
            'user_id': user_id,
        }
        return self.send('user_recovered', payload)

    def update_config(self, config):
        self.__init__(config)
        logger.info('Webhook 配置已更新: enabled=%s, has_url=%s, body_mode=%s', self.enabled, bool(self.url), self.body_mode)
