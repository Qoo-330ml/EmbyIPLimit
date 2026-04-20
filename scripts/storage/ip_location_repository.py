import sqlite3
from datetime import datetime


class IPLocationRepositoryMixin:
    def get_ip_location(self, ip_address):
        if not ip_address:
            return None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT provider, ip_address, location, district, street, isp,
                       latitude, longitude, formatted
                FROM ip_location_cache
                WHERE ip_address = ?
                ''',
                (ip_address,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    'provider': row[0],
                    'ip': row[1],
                    'location': row[2],
                    'district': row[3],
                    'street': row[4],
                    'isp': row[5],
                    'latitude': row[6],
                    'longitude': row[7],
                    'formatted': row[8],
                    'ts': int(datetime.now().timestamp()),
                }
            return None

    def save_ip_location(self, location_info):
        if not location_info or not location_info.get('ip'):
            return False

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO ip_location_cache (
                    ip_address, provider, location, district, street, isp,
                    latitude, longitude, formatted, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(ip_address) DO UPDATE SET
                    provider = excluded.provider,
                    location = excluded.location,
                    district = excluded.district,
                    street = excluded.street,
                    isp = excluded.isp,
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    formatted = excluded.formatted,
                    updated_at = CURRENT_TIMESTAMP
                ''',
                (
                    location_info.get('ip'),
                    location_info.get('provider'),
                    location_info.get('location'),
                    location_info.get('district'),
                    location_info.get('street'),
                    location_info.get('isp'),
                    location_info.get('latitude'),
                    location_info.get('longitude'),
                    location_info.get('formatted'),
                ),
            )
            conn.commit()
            return True

    def cleanup_old_ip_locations(self, days=30):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                DELETE FROM ip_location_cache
                WHERE created_at < datetime('now', '-' || ? || ' days')
                ''',
                (days,),
            )
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
