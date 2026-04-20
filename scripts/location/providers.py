from __future__ import annotations

import json
import logging
import time
from typing import Any

from .result import build_location_record

logger = logging.getLogger(__name__)


class IP138Provider:
    name = 'ip138'

    def __init__(self, runner):
        self.runner = runner

    def lookup(self, ip_address: str) -> dict[str, Any]:
        output = self.runner.run(['qoo-ip138', f'--ip={ip_address}'])

        location = ''
        isp = ''
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            for key in ('归属地', '归属地理位置', 'location', 'Location'):
                if key in line and (':' in line or '：' in line):
                    sep = '：' if '：' in line else ':'
                    location = line.rsplit(sep, 1)[1].strip()

            for key in ('运营商', 'isp', 'ISP'):
                if key in line and (':' in line or '：' in line):
                    sep = '：' if '：' in line else ':'
                    isp = line.rsplit(sep, 1)[1].strip()

        return build_location_record(
            provider=self.name,
            ip=ip_address,
            location=location,
            isp=isp,
        )


class HIOFDProvider:
    name = '自建库'

    def __init__(self, runner, retries: int = 3, retry_delay_sec: float = 1.0):
        self.runner = runner
        self.retries = retries
        self.retry_delay_sec = retry_delay_sec

    def lookup(self, ip_address: str) -> dict[str, Any]:
        last_err: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                output = self.runner.run(['ip-hiofd', '--ip', ip_address, '--json'])
                data = json.loads(output)

                result_ip = str(data.get('result_ip') or '').strip()
                if result_ip and result_ip != ip_address:
                    raise RuntimeError(f'自建库 返回 IP 不一致: query={ip_address}, result={result_ip}')

                latitude = self._to_float(data.get('latitude'))
                longitude = self._to_float(data.get('longitude'))

                return build_location_record(
                    provider=self.name,
                    ip=ip_address,
                    location=str(data.get('location') or '').strip(),
                    district=str(data.get('district') or '').strip(),
                    street=str(data.get('street') or '').strip(),
                    isp=str(data.get('isp') or '').strip(),
                    latitude=latitude,
                    longitude=longitude,
                )
            except Exception as e:
                last_err = e
                if attempt < self.retries:
                    logger.warning('📍 自建库 查询重试(%s/%s) %s: %s', attempt, self.retries, ip_address, e)
                    time.sleep(self.retry_delay_sec)

        raise RuntimeError(f'自建库 多次查询失败({self.retries}次): {last_err}')

    @staticmethod
    def _to_float(value):
        if value in (None, ''):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
