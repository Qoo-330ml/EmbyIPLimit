from __future__ import annotations

import os
import sys
import time
from typing import Any


class LocationService:
    """IP 归属地查询服务：优先 IP-hiofd，失败回退 ip138。"""

    def __init__(self, timeout_sec: int = 45):
        self.timeout_sec = timeout_sec
        self.cache: dict[str, dict[str, Any]] = {}
        self.ip_hiofd_project_dir = os.environ.get("IP_HIOFD_PROJECT_DIR", "/home/pdz/Fnos/项目/IP-hiofd")

    def _format_location(self, location: str, district: str, street: str, isp: str) -> str:
        parts = []

        if location:
            # 页面默认返回 "中国 · 浙江 · 金华"，统一替换为空格再按 "·" 拼接
            clean = location.replace(" ", "")
            parts.append(clean.replace("·", ""))

        if district:
            parts.append(district.strip())
        if street:
            parts.append(street.strip())

        left = "·".join(parts) if parts else "未知位置"
        return f"{left} | {isp.strip()}" if isp else left

    def _query_hiofd(self, ip_address: str) -> dict[str, Any]:
        # 优先直接 import 已安装包；若未安装，则尝试从本地项目目录导入
        try:
            from ip_hiofd import HiofdIpClient  # type: ignore
        except Exception:
            if self.ip_hiofd_project_dir not in sys.path:
                sys.path.insert(0, self.ip_hiofd_project_dir)
            from ip_hiofd import HiofdIpClient  # type: ignore

        client = HiofdIpClient()
        result = client.lookup(ip_address, timeout_sec=self.timeout_sec)

        location = str(result.location or "").strip()
        district = str(result.district or "").strip()
        street = str(result.street or "").strip()
        isp = str(result.isp or "").strip()

        return {
            "provider": "hiofd",
            "ip": ip_address,
            "location": location,
            "district": district,
            "street": street,
            "isp": isp,
            "formatted": self._format_location(location, district, street, isp),
            "ts": int(time.time()),
        }

    def _query_ip138(self, ip_address: str) -> dict[str, Any]:
        from ip138.ip138 import ip138

        result = ip138(ip_address)
        location = str(result.get("归属地") or "").strip()
        isp = str(result.get("运营商") or "").strip()

        # ip138 没有稳定区/街道字段，这里保持空
        return {
            "provider": "ip138",
            "ip": ip_address,
            "location": location,
            "district": "",
            "street": "",
            "isp": isp,
            "formatted": self._format_location(location, "", "", isp),
            "ts": int(time.time()),
        }

    def lookup(self, ip_address: str) -> dict[str, Any]:
        if not ip_address:
            return {
                "provider": "none",
                "ip": "",
                "location": "",
                "district": "",
                "street": "",
                "isp": "",
                "formatted": "未知位置",
                "ts": int(time.time()),
            }

        if ip_address in self.cache:
            return self.cache[ip_address]

        try:
            info = self._query_hiofd(ip_address)
        except Exception as e:
            print(f"📍 Hiofd 查询失败({ip_address}): {e}，回退 ip138")
            try:
                info = self._query_ip138(ip_address)
            except Exception as e2:
                print(f"📍 ip138 查询也失败({ip_address}): {e2}")
                info = {
                    "provider": "none",
                    "ip": ip_address,
                    "location": "",
                    "district": "",
                    "street": "",
                    "isp": "",
                    "formatted": "解析失败",
                    "ts": int(time.time()),
                }

        self.cache[ip_address] = info
        return info
