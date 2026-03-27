import os
import secrets
import sqlite3
import string
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any, Union, Generator


def get_data_dir() -> str:
    """获取data目录路径
    
    通过获取当前文件的绝对路径，然后向上两级目录，再添加data目录，得到data目录的路径
    例如：如果当前文件是 scripts/database.py，那么data目录就是 EmbyQ/data/
    """
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


class DatabaseManager:
    """数据库管理器类，用于处理所有与数据库相关的操作"""
    
    # 表名常量
    TABLE_PLAYBACK_HISTORY = 'playback_history'
    TABLE_SECURITY_LOG = 'security_log'
    TABLE_USER_EXPIRY = 'user_expiry'
    TABLE_USER_GROUPS = 'user_groups'
    TABLE_USER_GROUP_MEMBERS = 'user_group_members'
    TABLE_INVITES = 'invites'
    TABLE_IP_LOCATION_CACHE = 'ip_location_cache'
    
    def __init__(self, db_name: Optional[str] = None):
        """初始化数据库管理器
        
        Args:
            db_name: 数据库文件名，如果不指定则使用默认名称 'emby_playback.db'
        """
        # 获取data目录路径
        data_dir = get_data_dir()
        os.makedirs(data_dir, exist_ok=True)

        # 设置数据库路径
        self.db_path = os.path.join(data_dir, db_name) if db_name else os.path.join(data_dir, 'emby_playback.db')
        self._connection_pool: Dict[str, sqlite3.Connection] = {}
        # 初始化数据库结构
        self._init_db()
    
    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """获取数据库连接的上下文管理器
        
        自动处理事务提交和连接关闭
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使用Row工厂，返回字典式结果
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句的辅助方法"""
        with self._get_connection() as conn:
            return conn.execute(query, params)
    
    def _execute_many(self, query: str, params_list: List[tuple]) -> None:
        """批量执行SQL语句"""
        with self._get_connection() as conn:
            conn.executemany(query, params_list)
    
    def _table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return cursor.fetchone() is not None
    
    def _column_exists(self, table_name: str, column_name: str) -> bool:
        """检查表的列是否存在"""
        with self._get_connection() as conn:
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return column_name in columns
    
    def _add_column_if_not_exists(self, table_name: str, column_name: str, column_type: str, default: Any = None) -> None:
        """如果列不存在则添加列"""
        if not self._column_exists(table_name, column_name):
            with self._get_connection() as conn:
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                if default is not None:
                    alter_sql += f" DEFAULT {default}"
                conn.execute(alter_sql)
    
    def _init_db(self) -> None:
        """初始化数据库结构
        
        创建所有必要的数据库表，并处理表结构的自动迁移
        """
        # 创建播放历史表
        self._create_playback_history_table()
        # 创建安全日志表
        self._create_security_log_table()
        # 创建用户到期表
        self._create_user_expiry_table()
        # 创建用户组表
        self._create_user_groups_table()
        # 创建用户组成员表
        self._create_user_group_members_table()
        # 创建邀请表
        self._create_invites_table()
        # 创建IP归属地缓存表
        self._create_ip_location_cache_table()
    
    def _create_playback_history_table(self) -> None:
        """创建播放历史表"""
        self._execute('''
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
        
        # 创建索引以提升查询性能
        self._execute('CREATE INDEX IF NOT EXISTS idx_playback_user_id ON playback_history(user_id)')
        self._execute('CREATE INDEX IF NOT EXISTS idx_playback_username ON playback_history(username)')
        self._execute('CREATE INDEX IF NOT EXISTS idx_playback_start_time ON playback_history(start_time)')
    
    def _create_security_log_table(self) -> None:
        """创建安全日志表"""
        self._execute('''
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
        
        # 创建索引
        self._execute('CREATE INDEX IF NOT EXISTS idx_security_user_id ON security_log(user_id)')
        self._execute('CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_log(timestamp)')
    
    def _create_user_expiry_table(self) -> None:
        """创建用户到期时间表"""
        self._execute('''
            CREATE TABLE IF NOT EXISTS user_expiry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                expiry_date DATE,
                never_expire INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 添加缺失的列（兼容旧数据库）
        self._add_column_if_not_exists('user_expiry', 'never_expire', 'INTEGER', 0)
        
        # 创建索引
        self._execute('CREATE INDEX IF NOT EXISTS idx_expiry_user_id ON user_expiry(user_id)')
    
    def _create_user_groups_table(self) -> None:
        """创建用户组表"""
        self._execute('''
            CREATE TABLE IF NOT EXISTS user_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        self._execute('CREATE INDEX IF NOT EXISTS idx_groups_group_id ON user_groups(group_id)')
    
    def _create_user_group_members_table(self) -> None:
        """创建用户组成员表"""
        self._execute('''
            CREATE TABLE IF NOT EXISTS user_group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(group_id, user_id)
            )
        ''')
        
        # 创建索引
        self._execute('CREATE INDEX IF NOT EXISTS idx_members_group_id ON user_group_members(group_id)')
        self._execute('CREATE INDEX IF NOT EXISTS idx_members_user_id ON user_group_members(user_id)')
    
    def _create_invites_table(self) -> None:
        """创建邀请链接表"""
        self._execute('''
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
        ''')
        
        # 创建索引
        self._execute('CREATE INDEX IF NOT EXISTS idx_invites_code ON invites(code)')
        self._execute('CREATE INDEX IF NOT EXISTS idx_invites_active ON invites(is_active)')
    
    def _create_ip_location_cache_table(self) -> None:
        """创建IP归属地缓存表"""
        self._execute('''
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
        ''')
        
        # 创建索引
        self._execute('CREATE INDEX IF NOT EXISTS idx_ip_cache_address ON ip_location_cache(ip_address)')
    
    def _format_datetime(self, dt: datetime) -> str:
        """格式化datetime对象为字符串"""
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def record_session_start(self, session_data: Dict[str, Any]) -> None:
        """记录会话开始
        
        Args:
            session_data: 会话数据字典，包含以下键：
                - session_id: 会话ID
                - user_id: 用户ID
                - username: 用户名
                - ip: IP地址
                - device: 设备名称
                - client: 客户端类型
                - media: 媒体名称
                - start_time: 开始时间（datetime对象）
                - location: 位置信息（可选）
        """
        self._execute('''
            INSERT INTO playback_history (
                session_id, user_id, username, ip_address,
                device_name, client_type, media_name,
                start_time, location
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_data['session_id'],
            session_data['user_id'],
            session_data['username'],
            session_data['ip'],
            session_data.get('device'),
            session_data.get('client'),
            session_data.get('media'),
            self._format_datetime(session_data['start_time']),
            session_data.get('location', '未知位置')
        ))
    
    def record_session_end(self, session_id: str, end_time: datetime, duration: int) -> None:
        """记录会话结束
        
        Args:
            session_id: 会话ID
            end_time: 结束时间（datetime对象）
            duration: 播放时长（秒）
        """
        self._execute('''
            UPDATE playback_history
            SET end_time = ?, duration = ?
            WHERE session_id = ? AND end_time IS NULL
        ''', (
            self._format_datetime(end_time),
            duration,
            session_id
        ))
    
    def get_user_playback_records(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户的播放记录
        
        Args:
            user_id: 用户ID
            limit: 返回记录的数量限制，默认10条
        
        Returns:
            播放记录列表
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT session_id, ip_address, device_name, client_type, media_name,
                       start_time, end_time, duration, location
                FROM playback_history
                WHERE user_id = ? AND end_time IS NOT NULL
                ORDER BY start_time DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_ban_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户的封禁信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            最近一次的封禁记录，如果不存在则返回None
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT timestamp, trigger_ip, active_sessions, action
                FROM security_log
                WHERE user_id = ? AND action = 'DISABLE'
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_playback_records_by_username(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """通过用户名获取播放记录"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT session_id, ip_address, device_name, client_type, media_name,
                       start_time, end_time, duration, location
                FROM playback_history
                WHERE username = ? AND end_time IS NOT NULL
                ORDER BY start_time DESC
                LIMIT ?
            ''', (username, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_ban_info_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """通过用户名获取封禁信息"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT timestamp, trigger_ip, active_sessions, action
                FROM security_log
                WHERE username = ? AND action = 'DISABLE'
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def log_security_event(self, log_data: Dict[str, Any]) -> None:
        """记录安全事件"""
        self._execute('''
            INSERT INTO security_log
            (timestamp, user_id, username, trigger_ip, active_sessions, action)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self._format_datetime(log_data['timestamp']),
            log_data['user_id'],
            log_data.get('username'),
            log_data['trigger_ip'],
            log_data['active_sessions'],
            log_data['action']
        ))
    
    def set_user_expiry(self, user_id: str, expiry_date: str, never_expire: bool = False) -> None:
        """设置用户的到期时间"""
        self._execute('''
            INSERT INTO user_expiry (user_id, expiry_date, never_expire, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                expiry_date = excluded.expiry_date,
                never_expire = excluded.never_expire,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, expiry_date, 1 if never_expire else 0))
    
    def set_user_never_expire(self, user_id: str, never_expire: bool = True) -> None:
        """设置用户永不过期"""
        self._execute('''
            INSERT INTO user_expiry (user_id, never_expire, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                never_expire = excluded.never_expire,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, 1 if never_expire else 0))
    
    def get_user_expiry(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户的到期信息"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT expiry_date, never_expire FROM user_expiry WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return {'expiry_date': row['expiry_date'], 'never_expire': bool(row['never_expire'])}
            return None
    
    def is_user_never_expire(self, user_id: str) -> bool:
        """检查用户是否永不过期"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT never_expire FROM user_expiry WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            return bool(row['never_expire']) if row else False
    
    def get_all_expired_users(self) -> List[str]:
        """获取所有已过期的用户"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT user_id FROM user_expiry
                WHERE expiry_date IS NOT NULL
                AND expiry_date < DATE('now')
                AND (never_expire IS NULL OR never_expire = 0)
            ''')
            return [row['user_id'] for row in cursor.fetchall()]
    
    def clear_user_expiry(self, user_id: str) -> None:
        """清除用户的到期信息"""
        self._execute('DELETE FROM user_expiry WHERE user_id = ?', (user_id,))
    
    def create_user_group(self, group_id: str, name: str) -> None:
        """创建用户组"""
        self._execute('''
            INSERT INTO user_groups (group_id, name, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (group_id, name))
    
    def delete_user_group(self, group_id: str) -> None:
        """删除用户组"""
        with self._get_connection() as conn:
            conn.execute('DELETE FROM user_group_members WHERE group_id = ?', (group_id,))
            conn.execute('DELETE FROM user_groups WHERE group_id = ?', (group_id,))
    
    def get_all_user_groups(self) -> List[Dict[str, Any]]:
        """获取所有用户组信息"""
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT group_id, name FROM user_groups ORDER BY created_at')
            groups = []
            for row in cursor.fetchall():
                member_cursor = conn.execute(
                    'SELECT user_id FROM user_group_members WHERE group_id = ?',
                    (row['group_id'],)
                )
                members = [m['user_id'] for m in member_cursor.fetchall()]
                groups.append({
                    'id': row['group_id'],
                    'name': row['name'],
                    'members': members,
                })
            return groups
    
    def add_user_to_group(self, group_id: str, user_id: str) -> bool:
        """将用户添加到用户组
        
        Returns:
            如果添加成功则返回True，如果用户已经在组中则返回False
        """
        try:
            self._execute('''
                INSERT INTO user_group_members (group_id, user_id)
                VALUES (?, ?)
            ''', (group_id, user_id))
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_user_from_group(self, group_id: str, user_id: str) -> None:
        """从用户组中移除用户"""
        self._execute('''
            DELETE FROM user_group_members WHERE group_id = ? AND user_id = ?
        ''', (group_id, user_id))
    
    def get_group_members(self, group_id: str) -> List[str]:
        """获取用户组的成员"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT user_id FROM user_group_members WHERE group_id = ?
            ''', (group_id,))
            return [row['user_id'] for row in cursor.fetchall()]
    
    def _generate_invite_code(self, length: int = 8) -> str:
        """生成邀请码"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def create_invite(
        self,
        valid_hours: int,
        max_uses: int,
        group_id: Optional[str] = None,
        account_expiry_date: Optional[str] = None,
        created_by: str = 'admin'
    ) -> Dict[str, Any]:
        """创建邀请链接
        
        Raises:
            RuntimeError: 如果生成邀请码失败
        """
        expires_at = datetime.now() + timedelta(hours=valid_hours)
        code = None
        
        with self._get_connection() as conn:
            # 尝试生成唯一的邀请码
            for _ in range(10):
                candidate = self._generate_invite_code(8)
                exists = conn.execute('SELECT 1 FROM invites WHERE code = ?', (candidate,)).fetchone()
                if not exists:
                    code = candidate
                    break
            
            if not code:
                raise RuntimeError('生成邀请链接失败，请重试')
            
            conn.execute('''
                INSERT INTO invites (
                    code, expires_at, max_uses, used_count, group_id,
                    account_expiry_date, is_active, created_by, updated_at
                ) VALUES (?, ?, ?, 0, ?, ?, 1, ?, CURRENT_TIMESTAMP)
            ''', (
                code,
                self._format_datetime(expires_at),
                max_uses,
                group_id,
                account_expiry_date,
                created_by,
            ))
        
        return self.get_invite_by_code(code)
    
    def get_invite_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """通过邀请码获取邀请信息"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT code, expires_at, max_uses, used_count, group_id,
                       account_expiry_date, is_active, created_by, created_at
                FROM invites
                WHERE code = ?
            ''', (code,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'code': row['code'],
                'expires_at': row['expires_at'],
                'max_uses': row['max_uses'],
                'used_count': row['used_count'],
                'group_id': row['group_id'],
                'account_expiry_date': row['account_expiry_date'],
                'is_active': bool(row['is_active']),
                'created_by': row['created_by'],
                'created_at': row['created_at'],
            }
    
    def consume_invite(self, code: str) -> bool:
        """使用邀请码"""
        self._execute('''
            UPDATE invites
            SET used_count = used_count + 1,
                is_active = CASE WHEN used_count + 1 >= max_uses THEN 0 ELSE is_active END,
                updated_at = CURRENT_TIMESTAMP
            WHERE code = ? AND is_active = 1
        ''', (code,))
        return True
    
    def list_invites(self) -> List[Dict[str, Any]]:
        """列出所有邀请"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT code, expires_at, max_uses, used_count, group_id,
                       account_expiry_date, is_active, created_by, created_at
                FROM invites
                ORDER BY created_at DESC
            ''')
            return [{
                'code': row['code'],
                'expires_at': row['expires_at'],
                'max_uses': row['max_uses'],
                'used_count': row['used_count'],
                'group_id': row['group_id'],
                'account_expiry_date': row['account_expiry_date'],
                'is_active': bool(row['is_active']),
                'created_by': row['created_by'],
                'created_at': row['created_at'],
            } for row in cursor.fetchall()]
    
    def delete_invite(self, code: str) -> None:
        """删除邀请（将其标记为无效）"""
        self._execute(
            'UPDATE invites SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE code = ?',
            (code,)
        )
    
    def is_invite_available(self, code: str) -> Tuple[bool, str]:
        """检查邀请是否可用"""
        invite = self.get_invite_by_code(code)
        if not invite:
            return False, '邀请不存在'
        if not invite['is_active']:
            return False, '邀请已失效'
        if invite['used_count'] >= invite['max_uses']:
            return False, '邀请名额已用完'
        try:
            expires_at = datetime.strptime(invite['expires_at'], '%Y-%m-%d %H:%M:%S')
            if expires_at < datetime.now():
                return False, '邀请已过期'
        except (ValueError, TypeError):
            return False, '邀请时间异常'
        return True, ''
    
    def get_ip_location(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """从数据库查询IP归属地"""
        if not ip_address:
            return None
        
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT provider, ip_address, location, district, street, isp,
                       latitude, longitude, formatted
                FROM ip_location_cache
                WHERE ip_address = ?
            ''', (ip_address,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['ts'] = int(datetime.now().timestamp())
                return result
            return None
    
    def save_ip_location(self, location_info: Dict[str, Any]) -> bool:
        """保存IP归属地到数据库"""
        if not location_info or not location_info.get('ip'):
            return False
        
        self._execute('''
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
        ''', (
            location_info.get('ip'),
            location_info.get('provider'),
            location_info.get('location'),
            location_info.get('district'),
            location_info.get('street'),
            location_info.get('isp'),
            location_info.get('latitude'),
            location_info.get('longitude'),
            location_info.get('formatted')
        ))
        return True
    
    def cleanup_old_ip_locations(self, days: int = 30) -> int:
        """清理指定天数前的IP归属地缓存记录"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM ip_location_cache
                WHERE created_at < datetime('now', '-' || ? || ' days')
            ''', (days,))
            return cursor.rowcount
    
    def get_security_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取安全日志，支持分页
        
        Args:
            limit: 返回记录的数量限制，默认100条
            offset: 偏移量，用于分页
        """
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT id, timestamp, user_id, username, trigger_ip, active_sessions, action
                FROM security_log
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_security_logs_count(self) -> int:
        """获取安全日志总数"""
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM security_log')
            return cursor.fetchone()[0]
    
    def get_playback_records_count(self, user_id: Optional[str] = None) -> int:
        """获取播放记录总数"""
        with self._get_connection() as conn:
            if user_id:
                cursor = conn.execute(
                    'SELECT COUNT(*) FROM playback_history WHERE user_id = ?',
                    (user_id,)
                )
            else:
                cursor = conn.execute('SELECT COUNT(*) FROM playback_history')
            return cursor.fetchone()[0]
