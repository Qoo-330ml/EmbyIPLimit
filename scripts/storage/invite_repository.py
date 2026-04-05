import secrets
import sqlite3
import string
from datetime import datetime, timedelta


class InviteRepositoryMixin:
    def _generate_invite_code(self, length=8):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def create_invite(self, valid_hours, max_uses, group_id=None, account_expiry_date=None, created_by='admin'):
        expires_at = datetime.now() + timedelta(hours=int(valid_hours))
        code = None

        with sqlite3.connect(self.db_path) as conn:
            for _ in range(10):
                candidate = self._generate_invite_code(8)
                exists = conn.execute('SELECT 1 FROM invites WHERE code = ?', (candidate,)).fetchone()
                if not exists:
                    code = candidate
                    break

            if not code:
                raise RuntimeError('生成邀请链接失败，请重试')

            conn.execute(
                '''
                INSERT INTO invites (
                    code, expires_at, max_uses, used_count, group_id,
                    account_expiry_date, is_active, created_by, updated_at
                ) VALUES (?, ?, ?, 0, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                ''',
                (
                    code,
                    expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                    int(max_uses),
                    group_id or None,
                    account_expiry_date or None,
                    created_by,
                ),
            )
            conn.commit()

        return self.get_invite_by_code(code)

    def get_invite_by_code(self, code):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT code, expires_at, max_uses, used_count, group_id,
                       account_expiry_date, is_active, created_by, created_at
                FROM invites
                WHERE code = ?
                ''',
                (code,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'code': row[0],
                'expires_at': row[1],
                'max_uses': row[2],
                'used_count': row[3],
                'group_id': row[4],
                'account_expiry_date': row[5],
                'is_active': bool(row[6]),
                'created_by': row[7],
                'created_at': row[8],
            }

    def consume_invite(self, code):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                UPDATE invites
                SET used_count = used_count + 1,
                    is_active = CASE WHEN used_count + 1 >= max_uses THEN 0 ELSE is_active END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE code = ? AND is_active = 1
                ''',
                (code,),
            )
            conn.commit()
            return True

    def list_invites(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                SELECT code, expires_at, max_uses, used_count, group_id,
                       account_expiry_date, is_active, created_by, created_at
                FROM invites
                ORDER BY created_at DESC
                '''
            )
            rows = cursor.fetchall()
            return [
                {
                    'code': row[0],
                    'expires_at': row[1],
                    'max_uses': row[2],
                    'used_count': row[3],
                    'group_id': row[4],
                    'account_expiry_date': row[5],
                    'is_active': bool(row[6]),
                    'created_by': row[7],
                    'created_at': row[8],
                }
                for row in rows
            ]

    def delete_invite(self, code):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE invites SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE code = ?',
                (code,),
            )
            conn.commit()

    def is_invite_available(self, code):
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
        except Exception:
            return False, '邀请时间异常'
        return True, ''
