import sqlite3


class UserManagementRepositoryMixin:
    def set_user_expiry(self, user_id, expiry_date, never_expire=False):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO user_expiry (user_id, expiry_date, never_expire, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    expiry_date = excluded.expiry_date,
                    never_expire = excluded.never_expire,
                    updated_at = CURRENT_TIMESTAMP
                ''',
                (user_id, expiry_date, 1 if never_expire else 0),
            )
            conn.commit()

    def set_user_never_expire(self, user_id, never_expire=True):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO user_expiry (user_id, never_expire, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    never_expire = excluded.never_expire,
                    updated_at = CURRENT_TIMESTAMP
                ''',
                (user_id, 1 if never_expire else 0),
            )
            conn.commit()

    def get_user_expiry(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT expiry_date, never_expire FROM user_expiry WHERE user_id = ?',
                (user_id,),
            )
            result = cursor.fetchone()
            if result:
                return {'expiry_date': result[0], 'never_expire': bool(result[1])}
            return None

    def is_user_never_expire(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT never_expire FROM user_expiry WHERE user_id = ?',
                (user_id,),
            )
            result = cursor.fetchone()
            return bool(result[0]) if result else False

    def get_all_expired_users(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT user_id FROM user_expiry
                WHERE expiry_date IS NOT NULL
                  AND expiry_date < DATE('now')
                  AND (never_expire IS NULL OR never_expire = 0)
                '''
            )
            return [row[0] for row in cursor.fetchall()]

    def clear_user_expiry(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM user_expiry WHERE user_id = ?', (user_id,))
            conn.commit()

    def create_user_group(self, group_id, name):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO user_groups (group_id, name, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ''',
                (group_id, name),
            )
            conn.commit()

    def delete_user_group(self, group_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM user_group_members WHERE group_id = ?', (group_id,))
            conn.execute('DELETE FROM user_groups WHERE group_id = ?', (group_id,))
            conn.commit()

    def get_all_user_groups(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT group_id, name FROM user_groups ORDER BY created_at')
            groups = []
            for group_id, name in cursor.fetchall():
                member_cursor = conn.execute(
                    'SELECT user_id FROM user_group_members WHERE group_id = ?',
                    (group_id,),
                )
                members = [m[0] for m in member_cursor.fetchall()]
                groups.append({'id': group_id, 'name': name, 'members': members})
            return groups

    def add_user_to_group(self, group_id, user_id):
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    '''
                    INSERT INTO user_group_members (group_id, user_id)
                    VALUES (?, ?)
                    ''',
                    (group_id, user_id),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_user_from_group(self, group_id, user_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'DELETE FROM user_group_members WHERE group_id = ? AND user_id = ?',
                (group_id, user_id),
            )
            conn.commit()

    def get_group_members(self, group_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT user_id FROM user_group_members WHERE group_id = ?',
                (group_id,),
            )
            return [row[0] for row in cursor.fetchall()]
