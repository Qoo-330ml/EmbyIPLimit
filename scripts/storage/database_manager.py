import os
import sqlite3

from .invite_repository import InviteRepositoryMixin
from .ip_location_repository import IPLocationRepositoryMixin
from .paths import get_data_dir
from .playback_repository import PlaybackRepositoryMixin
from .user_repository import UserManagementRepositoryMixin


class DatabaseManager(
    PlaybackRepositoryMixin,
    UserManagementRepositoryMixin,
    InviteRepositoryMixin,
    IPLocationRepositoryMixin,
):
    def __init__(self, db_name=None):
        data_dir = get_data_dir()
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, db_name) if db_name else os.path.join(data_dir, 'emby_playback.db')
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS playback_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    device_name TEXT,
                    client_type TEXT,
                    media_name TEXT,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    duration INTEGER,
                    location TEXT
                )
                '''
            )

            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS security_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    user_id TEXT,
                    username TEXT,
                    trigger_ip TEXT,
                    active_sessions INTEGER,
                    action TEXT
                )
                '''
            )

            try:
                cursor = conn.execute('PRAGMA table_info(security_log)')
                columns = [row[1] for row in cursor.fetchall()]
                if 'username' not in columns:
                    conn.execute('ALTER TABLE security_log ADD COLUMN username TEXT')
            except sqlite3.OperationalError:
                pass

            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS user_expiry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    expiry_date DATE,
                    never_expire INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )

            try:
                conn.execute('SELECT never_expire FROM user_expiry LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE user_expiry ADD COLUMN never_expire INTEGER DEFAULT 0')
                conn.commit()

            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS user_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )

            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS user_group_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(group_id, user_id)
                )
                '''
            )

            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS invites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    max_uses INTEGER NOT NULL,
                    used_count INTEGER DEFAULT 0,
                    group_id TEXT,
                    account_expiry_date DATE,
                    is_active INTEGER DEFAULT 1,
                    created_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )

            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS ip_location_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL UNIQUE,
                    provider TEXT NOT NULL,
                    location TEXT,
                    district TEXT,
                    street TEXT,
                    isp TEXT,
                    latitude REAL,
                    longitude REAL,
                    formatted TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )

            conn.commit()
