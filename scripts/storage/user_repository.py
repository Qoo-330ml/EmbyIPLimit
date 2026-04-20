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
                'SELECT expiry_date, never_expire, alert_threshold, email FROM user_expiry WHERE user_id = ?',
                (user_id,),
            )
            result = cursor.fetchone()
            if result:
                return {'expiry_date': result[0], 'never_expire': bool(result[1]), 'alert_threshold': result[2], 'email': result[3] or ''}
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
            cursor = conn.execute('SELECT group_id, name, alert_threshold FROM user_groups ORDER BY created_at')
            groups = []
            for group_id, name, alert_threshold in cursor.fetchall():
                member_cursor = conn.execute(
                    'SELECT user_id FROM user_group_members WHERE group_id = ?',
                    (group_id,),
                )
                members = [m[0] for m in member_cursor.fetchall()]
                groups.append({'id': group_id, 'name': name, 'members': members, 'alert_threshold': alert_threshold})
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

    def set_user_alert_threshold(self, user_id, threshold):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO user_expiry (user_id, alert_threshold, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    alert_threshold = excluded.alert_threshold,
                    updated_at = CURRENT_TIMESTAMP
                ''',
                (user_id, threshold),
            )
            conn.commit()

    def get_user_alert_threshold(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT alert_threshold FROM user_expiry WHERE user_id = ?',
                (user_id,),
            )
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else None

    def clear_user_alert_threshold(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE user_expiry SET alert_threshold = NULL, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                (user_id,),
            )
            conn.commit()

    def set_group_alert_threshold(self, group_id, threshold):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                UPDATE user_groups SET alert_threshold = ?, updated_at = CURRENT_TIMESTAMP
                WHERE group_id = ?
                ''',
                (threshold, group_id),
            )
            conn.commit()

    def get_group_alert_threshold(self, group_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT alert_threshold FROM user_groups WHERE group_id = ?',
                (group_id,),
            )
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else None

    def get_user_group_ids(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT group_id FROM user_group_members WHERE user_id = ?',
                (user_id,),
            )
            return [row[0] for row in cursor.fetchall()]

    def get_user_group_names(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT g.name FROM user_group_members m JOIN user_groups g ON m.group_id = g.group_id WHERE m.user_id = ?',
                (user_id,),
            )
            return [row[0] for row in cursor.fetchall()]

    def get_user_groups_map(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT m.user_id, g.name FROM user_group_members m JOIN user_groups g ON m.group_id = g.group_id ORDER BY m.user_id'
            )
            groups_map = {}
            for user_id, group_name in cursor.fetchall():
                if user_id not in groups_map:
                    groups_map[user_id] = []
                groups_map[user_id].append(group_name)
            return groups_map

    def set_user_email(self, user_id, email):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO user_expiry (user_id, email, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    email = excluded.email,
                    updated_at = CURRENT_TIMESTAMP
                ''',
                (user_id, email),
            )
            conn.commit()

    def get_user_email(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT email FROM user_expiry WHERE user_id = ?',
                (user_id,),
            )
            result = cursor.fetchone()
            return result[0] if result and result[0] else ''

    def get_effective_alert_threshold(self, user_id, default_threshold):
        user_threshold = self.get_user_alert_threshold(user_id)
        if user_threshold is not None:
            return user_threshold

        group_ids = self.get_user_group_ids(user_id)
        for group_id in group_ids:
            group_threshold = self.get_group_alert_threshold(group_id)
            if group_threshold is not None:
                return group_threshold

        return default_threshold
