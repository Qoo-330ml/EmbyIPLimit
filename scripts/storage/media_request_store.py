from __future__ import annotations

import sqlite3


class WishStore:
    ALLOWED_STATUSES = {'pending', 'approved', 'rejected'}
    SELECT_FIELDS = '''
        id, tmdb_id, media_type, season_number, title, original_title, release_date, year,
        overview, poster_path, poster_url, backdrop_path, backdrop_url,
        status, created_at, updated_at
    '''

    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS media_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tmdb_id INTEGER NOT NULL,
                    media_type TEXT NOT NULL,
                    season_number INTEGER DEFAULT 0,
                    title TEXT NOT NULL,
                    original_title TEXT,
                    release_date TEXT,
                    year TEXT,
                    overview TEXT,
                    poster_path TEXT,
                    poster_url TEXT,
                    backdrop_path TEXT,
                    backdrop_url TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )

            self._ensure_column(conn, 'media_requests', 'season_number', "INTEGER DEFAULT 0")
            if self._has_legacy_unique_constraint(conn):
                self._rebuild_media_requests_table(conn)
            self._ensure_unique_index(conn)
            conn.execute("UPDATE media_requests SET status = 'approved' WHERE status = 'fulfilled'")
            conn.commit()

    def add_request(self, item):
        tmdb_id = int(item.get('tmdb_id'))
        media_type = (item.get('media_type') or '').strip()
        if media_type not in {'movie', 'tv'}:
            raise ValueError('媒体类型错误')

        season_number = self._normalize_season_number(item.get('season_number')) if media_type == 'tv' else 0

        payload = {
            'tmdb_id': tmdb_id,
            'media_type': media_type,
            'season_number': season_number,
            'title': (item.get('title') or '').strip(),
            'original_title': (item.get('original_title') or '').strip(),
            'release_date': (item.get('release_date') or '').strip(),
            'year': (item.get('year') or '').strip(),
            'overview': (item.get('overview') or '').strip(),
            'poster_path': (item.get('poster_path') or '').strip(),
            'poster_url': (item.get('poster_url') or '').strip(),
            'backdrop_path': (item.get('backdrop_path') or '').strip(),
            'backdrop_url': (item.get('backdrop_url') or '').strip(),
        }
        if not payload['title']:
            raise ValueError('标题不能为空')

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            existing = conn.execute(
                f'''
                SELECT {self.SELECT_FIELDS}
                FROM media_requests
                WHERE tmdb_id = ? AND media_type = ? AND season_number = ?
                ''',
                (payload['tmdb_id'], payload['media_type'], payload['season_number']),
            ).fetchone()
            if existing:
                existing_record = self._normalize_record(dict(existing))
                if existing_record.get('status') != 'rejected':
                    conn.execute(
                        '''
                        UPDATE media_requests
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        ''',
                        (existing_record['id'],),
                    )
                    conn.commit()
                    existing_record = self.get_request(existing_record['id']) or existing_record
                    existing_record['created'] = False
                    return existing_record

                conn.execute(
                    '''
                    UPDATE media_requests
                    SET title = ?,
                        original_title = ?,
                        release_date = ?,
                        year = ?,
                        overview = ?,
                        poster_path = ?,
                        poster_url = ?,
                        backdrop_path = ?,
                        backdrop_url = ?,
                        season_number = ?,
                        status = 'pending',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''',
                    (
                        payload['title'],
                        payload['original_title'],
                        payload['release_date'],
                        payload['year'],
                        payload['overview'],
                        payload['poster_path'],
                        payload['poster_url'],
                        payload['backdrop_path'],
                        payload['backdrop_url'],
                        payload['season_number'],
                        existing_record['id'],
                    ),
                )
                conn.commit()

                record = self.get_request(existing_record['id'])
                if not record:
                    raise RuntimeError('恢复求片记录失败')
                record['created'] = True
                return record

            cursor = conn.execute(
                '''
                INSERT INTO media_requests (
                    tmdb_id, media_type, season_number, title, original_title, release_date, year,
                    overview, poster_path, poster_url, backdrop_path, backdrop_url,
                    status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                ''',
                (
                    payload['tmdb_id'],
                    payload['media_type'],
                    payload['season_number'],
                    payload['title'],
                    payload['original_title'],
                    payload['release_date'],
                    payload['year'],
                    payload['overview'],
                    payload['poster_path'],
                    payload['poster_url'],
                    payload['backdrop_path'],
                    payload['backdrop_url'],
                ),
            )
            request_id = int(cursor.lastrowid)
            conn.commit()

        record = self.get_request(request_id)
        if not record:
            raise RuntimeError('保存求片记录失败')
        record['created'] = True
        return record

    def get_request(self, request_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                f'''
                SELECT {self.SELECT_FIELDS}
                FROM media_requests
                WHERE id = ?
                ''',
                (request_id,),
            ).fetchone()
            if not row:
                return None
            return self._normalize_record(dict(row))

    def list_requests(self, status=''):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status and status in self.ALLOWED_STATUSES:
                rows = conn.execute(
                    f'''
                    SELECT {self.SELECT_FIELDS}
                    FROM media_requests
                    WHERE status = ?
                    ORDER BY updated_at DESC, created_at DESC
                    ''',
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    f'''
                    SELECT {self.SELECT_FIELDS}
                    FROM media_requests
                    ORDER BY updated_at DESC, created_at DESC
                    '''
                ).fetchall()
            return [self._normalize_record(dict(row)) for row in rows]

    def list_public_requests(self, page=1, page_size=25):
        try:
            page = max(int(page or 1), 1)
        except Exception:
            page = 1
        try:
            page_size = max(min(int(page_size or 25), 50), 1)
        except Exception:
            page_size = 25

        offset = (page - 1) * page_size
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            total_row = conn.execute(
                '''
                SELECT COUNT(1)
                FROM media_requests
                WHERE status != 'rejected'
                '''
            ).fetchone()
            total_results = int(total_row[0] or 0) if total_row else 0
            rows = conn.execute(
                f'''
                SELECT {self.SELECT_FIELDS}
                FROM media_requests
                WHERE status != 'rejected'
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ? OFFSET ?
                ''',
                (page_size, offset),
            ).fetchall()

        total_pages = ((total_results - 1) // page_size) + 1 if total_results else 1
        requests = []
        for row in rows:
            record = self._normalize_record(dict(row))
            record['requested'] = True
            record['request_status'] = record.get('status')
            requests.append(record)

        return {
            'requests': requests,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'total_results': total_results,
        }

    def get_request_map(self, items, include_rejected=False):
        mapping = {}
        if not items:
            return mapping

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            for item in items:
                try:
                    tmdb_id = int(item.get('tmdb_id'))
                except Exception:
                    continue
                media_type = (item.get('media_type') or '').strip()
                if media_type not in {'movie', 'tv'}:
                    continue
                season_number = self._normalize_season_number(item.get('season_number')) if media_type == 'tv' else 0

                if include_rejected:
                    row = conn.execute(
                        f'''
                        SELECT {self.SELECT_FIELDS}
                        FROM media_requests
                        WHERE tmdb_id = ? AND media_type = ? AND season_number = ?
                        ''',
                        (tmdb_id, media_type, season_number),
                    ).fetchone()
                else:
                    row = conn.execute(
                        f'''
                        SELECT {self.SELECT_FIELDS}
                        FROM media_requests
                        WHERE tmdb_id = ? AND media_type = ? AND season_number = ? AND status != 'rejected'
                        ''',
                        (tmdb_id, media_type, season_number),
                    ).fetchone()

                if row:
                    mapping[self._make_lookup_key(media_type, tmdb_id, season_number)] = self._normalize_record(dict(row))
        return mapping

    def update_request_status(self, request_id, status):
        status = (status or '').strip()
        if status not in self.ALLOWED_STATUSES:
            raise ValueError('状态错误')
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                '''
                UPDATE media_requests
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (status, request_id),
            )
            conn.commit()
            if cursor.rowcount <= 0:
                return None
        return self.get_request(request_id)

    def delete_request(self, request_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('DELETE FROM media_requests WHERE id = ?', (request_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _normalize_record(self, record):
        normalized = dict(record)
        normalized['season_number'] = self._normalize_season_number(normalized.get('season_number')) if normalized.get('media_type') == 'tv' else 0
        normalized['lookup_key'] = self._make_lookup_key(
            normalized.get('media_type'),
            normalized.get('tmdb_id'),
            normalized.get('season_number'),
        )
        normalized['is_season_request'] = bool(normalized.get('media_type') == 'tv' and normalized.get('season_number', 0) > 0)
        return normalized

    def _make_lookup_key(self, media_type, tmdb_id, season_number=0):
        media_type = (media_type or '').strip()
        season_number = self._normalize_season_number(season_number) if media_type == 'tv' else 0
        return f'{media_type}:{tmdb_id}:{season_number}'

    def _normalize_season_number(self, season_number):
        try:
            return max(int(season_number or 0), 0)
        except Exception:
            return 0

    def _ensure_column(self, conn, table_name, column_name, definition):
        columns = {row[1] for row in conn.execute(f'PRAGMA table_info({table_name})').fetchall()}
        if column_name not in columns:
            conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}')

    def _has_legacy_unique_constraint(self, conn):
        indexes = conn.execute("PRAGMA index_list('media_requests')").fetchall()
        for index in indexes:
            name = index[1]
            unique = int(index[2])
            origin = index[3] if len(index) > 3 else ''
            if not unique:
                continue
            index_info = conn.execute(f"PRAGMA index_info('{name}')").fetchall()
            columns = [row[2] for row in index_info]
            if columns == ['tmdb_id', 'media_type'] and origin in {'u', 'pk'}:
                return True
        return False

    def _rebuild_media_requests_table(self, conn):
        conn.execute('DROP INDEX IF EXISTS idx_media_requests_unique_lookup')
        conn.execute('DROP TABLE IF EXISTS media_request_submissions')
        conn.execute('ALTER TABLE media_requests RENAME TO media_requests_legacy')
        conn.execute(
            '''
            CREATE TABLE media_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tmdb_id INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                season_number INTEGER DEFAULT 0,
                title TEXT NOT NULL,
                original_title TEXT,
                release_date TEXT,
                year TEXT,
                overview TEXT,
                poster_path TEXT,
                poster_url TEXT,
                backdrop_path TEXT,
                backdrop_url TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(media_requests_legacy)").fetchall()}
        has_status = 'status' in columns
        has_created_at = 'created_at' in columns
        has_updated_at = 'updated_at' in columns
        conn.execute(
            f'''
            INSERT INTO media_requests (
                id, tmdb_id, media_type, season_number, title, original_title, release_date, year,
                overview, poster_path, poster_url, backdrop_path, backdrop_url,
                status, created_at, updated_at
            )
            SELECT
                id,
                tmdb_id,
                media_type,
                COALESCE(season_number, 0),
                title,
                original_title,
                release_date,
                year,
                overview,
                poster_path,
                poster_url,
                backdrop_path,
                backdrop_url,
                {"status" if has_status else "'pending'"},
                {"created_at" if has_created_at else "CURRENT_TIMESTAMP"},
                {"updated_at" if has_updated_at else "CURRENT_TIMESTAMP"}
            FROM media_requests_legacy
            '''
        )
        conn.execute('DROP TABLE media_requests_legacy')

    def _ensure_unique_index(self, conn):
        conn.execute(
            '''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_media_requests_unique_lookup
            ON media_requests (tmdb_id, media_type, season_number)
            '''
        )
