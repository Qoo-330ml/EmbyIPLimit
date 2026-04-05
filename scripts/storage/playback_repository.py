import sqlite3


class PlaybackRepositoryMixin:
    def record_session_start(self, session_data):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO playback_history (
                    session_id, user_id, username, ip_address,
                    device_name, client_type, media_name,
                    start_time, location
                ) VALUES (?,?,?,?,?,?,?,?,?)
                ''',
                (
                    session_data['session_id'],
                    session_data['user_id'],
                    session_data['username'],
                    session_data['ip'],
                    session_data['device'],
                    session_data['client'],
                    session_data['media'],
                    session_data['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                    session_data.get('location', '未知位置'),
                ),
            )
            conn.commit()

    def get_user_playback_records(self, user_id, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT session_id, ip_address, device_name, client_type, media_name,
                       start_time, end_time, duration, location
                FROM playback_history
                WHERE user_id = ? AND end_time IS NOT NULL
                ORDER BY start_time DESC
                LIMIT ?
                ''',
                (user_id, limit),
            )
            return cursor.fetchall()

    def get_user_ban_info(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT timestamp, trigger_ip, active_sessions, action
                FROM security_log
                WHERE user_id = ? AND action = 'DISABLE'
                ORDER BY timestamp DESC
                LIMIT 1
                ''',
                (user_id,),
            )
            return cursor.fetchone()

    def get_playback_records_by_username(self, username, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT session_id, ip_address, device_name, client_type, media_name,
                       start_time, end_time, duration, location
                FROM playback_history
                WHERE username = ? AND end_time IS NOT NULL
                ORDER BY start_time DESC
                LIMIT ?
                ''',
                (username, limit),
            )
            return cursor.fetchall()

    def get_ban_info_by_username(self, username):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT timestamp, trigger_ip, active_sessions, action
                FROM security_log
                WHERE username = ? AND action IN ('DISABLE', 'DISABLE_EXPIRED')
                ORDER BY timestamp DESC
                LIMIT 1
                ''',
                (username,),
            )
            return cursor.fetchone()

    def record_session_end(self, session_id, end_time, duration):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                UPDATE playback_history
                SET end_time = ?, duration = ?
                WHERE session_id = ? AND end_time IS NULL
                ''',
                (
                    end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    duration,
                    session_id,
                ),
            )
            conn.commit()

    def log_security_event(self, log_data):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO security_log
                (timestamp, user_id, username, trigger_ip, active_sessions, action)
                VALUES (?,?,?,?,?,?)
                ''',
                (
                    log_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    log_data['user_id'],
                    log_data['username'],
                    log_data['trigger_ip'],
                    log_data['active_sessions'],
                    log_data['action'],
                ),
            )
            conn.commit()

    def get_security_logs(self, limit=100):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT id, timestamp, user_id, username, trigger_ip, active_sessions, action
                FROM security_log
                ORDER BY timestamp ASC
                LIMIT ?
                ''',
                (limit,),
            )
            logs = []
            for row in cursor.fetchall():
                logs.append(
                    {
                        'id': row[0],
                        'timestamp': row[1],
                        'user_id': row[2],
                        'username': row[3],
                        'trigger_ip': row[4],
                        'active_sessions': row[5],
                        'action': row[6],
                    }
                )
            return logs
