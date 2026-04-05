from __future__ import annotations

import time
from typing import Any


def format_location(location: str, district: str, street: str, isp: str) -> str:
    parts = []

    if location:
        clean = location.replace(' ', '')
        parts.append(clean.replace('·', ''))

    if district:
        parts.append(district.strip())
    if street:
        parts.append(street.strip())

    left = '·'.join(parts) if parts else '未知位置'
    return f'{left} | {isp.strip()}' if isp else left


def build_location_record(
    provider: str,
    ip: str,
    location: str = '',
    district: str = '',
    street: str = '',
    isp: str = '',
    latitude: float | None = None,
    longitude: float | None = None,
    formatted: str | None = None,
) -> dict[str, Any]:
    return {
        'provider': provider,
        'ip': ip,
        'location': location,
        'district': district,
        'street': street,
        'isp': isp,
        'latitude': latitude,
        'longitude': longitude,
        'formatted': formatted if formatted is not None else format_location(location, district, street, isp),
        'ts': int(time.time()),
    }


def build_unknown_location(ip: str = '', formatted: str = '未知位置') -> dict[str, Any]:
    return build_location_record(
        provider='none',
        ip=ip,
        formatted=formatted,
    )
