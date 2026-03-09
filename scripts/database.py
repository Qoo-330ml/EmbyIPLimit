import os
import sqlite3
from datetime import datetime

def get_data_dir():
    """获取data目录路径"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

class DatabaseManager:
    def __init__(self, db_name=None):
        data_dir = get_data_dir()
        os.makedirs(data_dir, exist_ok=True)
        
        # 从配置获取数据库名称
        self.db_path = os.path.join(data_dir, db_name) if db_name else os.path.join(data_dir, 'emby_playback.db')
        self.init_db()
    
    def init_db(self):
        """初始化数据库结构"""
        with sqlite3.connect(self.db_path) as conn:
            # 播放历史表
            conn.execute('''
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
            ''')
            
            # 安全日志表（带自动迁移）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    user_id TEXT,
                    username TEXT,
                    trigger_ip TEXT,
                    active_sessions INTEGER,
                    action TEXT
                )
            ''')
            
            # 检查旧表结构
            try:
                cursor = conn.execute("PRAGMA table_info(security_log)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'username' not in columns:
                    conn.execute('ALTER TABLE security_log ADD COLUMN username TEXT')
            except sqlite3.OperationalError:
                pass
            
            # 用户到期时间表（支持永不过期）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_expiry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    expiry_date DATE,
                    never_expire INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 迁移：检查并添加 never_expire 列（兼容旧数据库）
            try:
                conn.execute('SELECT never_expire FROM user_expiry LIMIT 1')
            except sqlite3.OperationalError:
                # 列不存在，需要添加
                conn.execute('ALTER TABLE user_expiry ADD COLUMN never_expire INTEGER DEFAULT 0')
                conn.commit()

            # 用户组表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 用户组成员表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_group_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(group_id, user_id)
                )
            ''')

            conn.commit()

    def record_session_start(self, session_data):
        """记录播放开始"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO playback_history (
                    session_id, user_id, username, ip_address,
                    device_name, client_type, media_name, 
                    start_time, location
                ) VALUES (?,?,?,?,?,?,?,?,?)
            ''', (
                session_data['session_id'],
                session_data['user_id'],
                session_data['username'],
                session_data['ip'],
                session_data['device'],
                session_data['client'],
                session_data['media'],
                session_data['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                session_data.get('location', '未知位置')
            ))
            conn.commit()
    
    def get_user_playback_records(self, user_id, limit=10):
        """获取用户最近的播放记录（只返回已结束的会话）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT session_id, ip_address, device_name, client_type, media_name,
                       start_time, end_time, duration, location
                FROM playback_history
                WHERE user_id = ? AND end_time IS NOT NULL
                ORDER BY start_time DESC
                LIMIT ?
            ''', (user_id, limit))
            return cursor.fetchall()
    
    def get_user_ban_info(self, user_id):
        """获取用户封禁信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT timestamp, trigger_ip, active_sessions, action
                FROM security_log
                WHERE user_id = ? AND action = 'DISABLE'
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (user_id,))
            return cursor.fetchone()
    
    def get_playback_records_by_username(self, username, limit=10):
        """通过用户名获取最近的播放记录（只返回已结束的会话）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT session_id, ip_address, device_name, client_type, media_name,
                       start_time, end_time, duration, location
                FROM playback_history
                WHERE username = ? AND end_time IS NOT NULL
                ORDER BY start_time DESC
                LIMIT ?
            ''', (username, limit))
            return cursor.fetchall()
    
    def get_ban_info_by_username(self, username):
        """通过用户名获取封禁信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT timestamp, trigger_ip, active_sessions, action
                FROM security_log
                WHERE username = ? AND action = 'DISABLE'
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (username,))
            return cursor.fetchone()

    def record_session_end(self, session_id, end_time, duration):
        """记录播放结束"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE playback_history 
                SET end_time = ?, duration = ?
                WHERE session_id = ?
            ''', (
                end_time.strftime('%Y-%m-%d %H:%M:%S'),
                duration,
                session_id
            ))
            conn.commit()

    def log_security_event(self, log_data):
        """记录安全日志"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO security_log 
                (timestamp, user_id, username, trigger_ip, active_sessions, action)
                VALUES (?,?,?,?,?,?)
            ''', (
                log_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                log_data['user_id'],
                log_data['username'],
                log_data['trigger_ip'],
                log_data['active_sessions'],
                log_data['action']
            ))
            conn.commit()

    def set_user_expiry(self, user_id, expiry_date, never_expire=False):
        """设置用户到期时间，支持永不过期"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO user_expiry (user_id, expiry_date, never_expire, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                expiry_date = excluded.expiry_date,
                never_expire = excluded.never_expire,
                updated_at = CURRENT_TIMESTAMP
            ''', (user_id, expiry_date, 1 if never_expire else 0))
            conn.commit()

    def set_user_never_expire(self, user_id, never_expire=True):
        """设置用户永不过期状态"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO user_expiry (user_id, never_expire, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                never_expire = excluded.never_expire,
                updated_at = CURRENT_TIMESTAMP
            ''', (user_id, 1 if never_expire else 0))
            conn.commit()

    def get_user_expiry(self, user_id):
        """获取用户到期时间"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT expiry_date, never_expire FROM user_expiry WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            if result:
                return {'expiry_date': result[0], 'never_expire': bool(result[1])}
            return None

    def is_user_never_expire(self, user_id):
        """检查用户是否永不过期"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT never_expire FROM user_expiry WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            return bool(result[0]) if result else False

    def get_all_expired_users(self):
        """获取所有已到期但未禁用的用户（排除永不过期的）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT user_id FROM user_expiry 
                WHERE expiry_date IS NOT NULL 
                AND expiry_date < DATE('now')
                AND (never_expire IS NULL OR never_expire = 0)
            ''')
            return [row[0] for row in cursor.fetchall()]

    def clear_user_expiry(self, user_id):
        """清除用户到期时间"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                DELETE FROM user_expiry WHERE user_id = ?
            ''', (user_id,))
            conn.commit()

    # ==================== 用户组管理方法 ====================

    def create_user_group(self, group_id, name):
        """创建用户组"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO user_groups (group_id, name, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (group_id, name))
            conn.commit()

    def delete_user_group(self, group_id):
        """删除用户组"""
        with sqlite3.connect(self.db_path) as conn:
            # 先删除组成员
            conn.execute('DELETE FROM user_group_members WHERE group_id = ?', (group_id,))
            # 再删除组
            conn.execute('DELETE FROM user_groups WHERE group_id = ?', (group_id,))
            conn.commit()

    def get_all_user_groups(self):
        """获取所有用户组及其成员"""
        with sqlite3.connect(self.db_path) as conn:
            # 获取所有组
            cursor = conn.execute('''
                SELECT group_id, name FROM user_groups ORDER BY created_at
            ''')
            groups = []
            for row in cursor.fetchall():
                group_id, name = row
                # 获取该组的成员
                member_cursor = conn.execute('''
                    SELECT user_id FROM user_group_members WHERE group_id = ?
                ''', (group_id,))
                members = [m[0] for m in member_cursor.fetchall()]
                groups.append({
                    'id': group_id,
                    'name': name,
                    'members': members
                })
            return groups

    def add_user_to_group(self, group_id, user_id):
        """添加用户到组"""
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    INSERT INTO user_group_members (group_id, user_id)
                    VALUES (?, ?)
                ''', (group_id, user_id))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # 用户已在组中
                return False

    def remove_user_from_group(self, group_id, user_id):
        """从组中移除用户"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                DELETE FROM user_group_members WHERE group_id = ? AND user_id = ?
            ''', (group_id, user_id))
            conn.commit()

    def get_group_members(self, group_id):
        """获取组的成员列表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT user_id FROM user_group_members WHERE group_id = ?
            ''', (group_id,))
            return [row[0] for row in cursor.fetchall()]