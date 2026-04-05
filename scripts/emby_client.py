import copy
import logging

from network.http_session import create_session

logger = logging.getLogger(__name__)


class EmbyClient:
    def __init__(self, server_url, api_key):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.session = create_session({'X-Emby-Token': self.api_key})

    def get_session(self):
        return self.session

    def get_user_info(self, user_id):
        try:
            response = self.session.get(
                f"{self.server_url}/emby/Users/{user_id}",
                timeout=3
            )
            return response.json()
        except Exception as e:
            logger.warning('获取用户信息失败: user_id=%s, error=%s', user_id, e)
            return {}

    def get_user_policy(self, user_id):
        try:
            response = self.session.get(
                f"{self.server_url}/emby/Users/{user_id}/Policy",
                timeout=5
            )
            if response.status_code != 200:
                logger.warning('获取用户策略失败: user_id=%s, status_code=%s', user_id, response.status_code)
                return {}
            return response.json() or {}
        except Exception as e:
            logger.warning('获取用户策略失败: user_id=%s, error=%s', user_id, e)
            return {}

    def set_user_policy(self, user_id, policy):
        try:
            clean_policy = copy.deepcopy(policy or {})
            for key in ('Id', 'UserId', 'Name'):
                clean_policy.pop(key, None)

            response = self.session.post(
                f"{self.server_url}/emby/Users/{user_id}/Policy",
                json=clean_policy,
                timeout=8,
            )
            if response.status_code not in (200, 204):
                logger.error('设置用户策略失败: user_id=%s, status_code=%s', user_id, response.status_code)
            return response.status_code in (200, 204)
        except Exception as e:
            logger.error('设置用户策略失败: user_id=%s, error=%s', user_id, e)
            return False

    def update_user_policy_fields(self, user_id, updates):
        try:
            current_policy = self.get_user_policy(user_id)
            if not current_policy:
                logger.error('更新用户策略字段失败: user_id=%s, reason=no_current_policy', user_id)
                return False
            merged_policy = copy.deepcopy(current_policy)
            merged_policy.update(updates or {})
            return self.set_user_policy(user_id, merged_policy)
        except Exception as e:
            logger.error('更新用户策略字段失败: user_id=%s, error=%s', user_id, e)
            return False

    def set_user_disabled(self, user_id, disabled):
        return self.update_user_policy_fields(user_id, {'IsDisabled': bool(disabled)})

    def set_user_password(self, user_id, password):
        try:
            payload = {
                'CurrentPw': '',
                'CurrentPassword': '',
                'NewPw': password,
                'NewPassword': password,
                'ResetPassword': False,
            }
            response = self.session.post(
                f"{self.server_url}/emby/Users/{user_id}/Password",
                json=payload,
                timeout=8,
            )
            if response.status_code not in (200, 204):
                logger.error('设置用户密码失败: user_id=%s, status_code=%s', user_id, response.status_code)
            return response.status_code in (200, 204)
        except Exception as e:
            logger.error('设置用户密码失败: user_id=%s, error=%s', user_id, e)
            return False

    def create_user(self, username, password):
        username = (username or '').strip()
        if not username:
            return None, '用户名不能为空'

        try:
            response = self.session.post(
                f"{self.server_url}/emby/Users/New",
                params={'Name': username},
                timeout=8,
            )
            if response.status_code not in (200, 201, 204):
                logger.error('创建用户失败: username=%s, status_code=%s', username, response.status_code)
                return None, f'创建用户失败: HTTP {response.status_code}'

            user_data = response.json() if response.text else {}
            user_id = user_data.get('Id')

            if not user_id:
                user = self.get_user_by_name(username)
                user_id = user.get('Id') if user else None

            if not user_id:
                logger.error('创建用户成功但未获取到用户ID: username=%s', username)
                return None, '创建用户成功但未获取到用户ID'

            if not self.set_user_password(user_id, password):
                logger.error('用户已创建但设置密码失败: username=%s, user_id=%s', username, user_id)
                return None, '用户已创建，但设置密码失败'

            logger.info('创建用户成功: username=%s, user_id=%s', username, user_id)
            return user_id, ''
        except Exception as e:
            logger.exception('创建用户异常: username=%s, error=%s', username, e)
            return None, f'创建用户异常: {str(e)}'

    def get_user_by_name(self, username):
        target = (username or '').strip().lower()
        if not target:
            return None
        for user in self.get_users():
            if str(user.get('Name') or '').strip().lower() == target:
                return user
        return None

    def get_active_sessions(self):
        try:
            response = self.session.get(
                f"{self.server_url}/emby/Sessions",
                timeout=5
            )
            return {s['Id']: s for s in response.json() if s.get('NowPlayingItem')}
        except Exception as e:
            logger.warning('获取活动会话失败: error=%s', e)
            return {}

    @staticmethod
    def parse_media_info(item):
        if not item:
            return "未知内容"
        if item.get('SeriesName'):
            return f"{item['SeriesName']} S{item['ParentIndexNumber']}E{item['IndexNumber']}"
        return item.get('Name', '未知内容')

    def get_users(self):
        try:
            response = self.session.get(
                f"{self.server_url}/emby/Users",
                timeout=5
            )
            return response.json()
        except Exception as e:
            logger.warning('获取用户列表失败: error=%s', e)
            return []

    def delete_user(self, user_id):
        try:
            response = self.session.delete(
                f"{self.server_url}/emby/Users/{user_id}",
                timeout=8,
            )
            if response.status_code not in (200, 204):
                logger.error('删除用户失败: user_id=%s, status_code=%s', user_id, response.status_code)
            return response.status_code in (200, 204)
        except Exception as e:
            logger.error('删除用户失败: user_id=%s, error=%s', user_id, e)
            return False

    def get_server_info(self):
        try:
            response = self.session.get(
                f"{self.server_url}/emby/System/Info",
                timeout=5
            )
            return response.json()
        except Exception as e:
            logger.warning('获取服务器信息失败: error=%s', e)
            return {}

    def get_library_views(self):
        try:
            response = self.session.get(
                f"{self.server_url}/emby/Views",
                timeout=10
            )
            return response.json().get('Items') or []
        except Exception as e:
            logger.warning('获取媒体库视图失败: error=%s', e)
            return []

    def get_library_items(self, parent_id=None, include_item_types=None, recursive=True, fields=None):
        try:
            params = {
                'Recursive': str(recursive).lower()
            }
            if parent_id:
                params['ParentId'] = parent_id
            if include_item_types:
                params['IncludeItemTypes'] = include_item_types
            if fields:
                params['Fields'] = fields

            response = self.session.get(
                f"{self.server_url}/emby/Items",
                params=params,
                timeout=30
            )
            return response.json().get('Items') or []
        except Exception as e:
            logger.warning(
                '获取媒体库项目失败: parent_id=%s, include_item_types=%s, recursive=%s, fields=%s, error=%s',
                parent_id,
                include_item_types,
                recursive,
                fields,
                e,
            )
            return []

    def get_movies(self, fields=None):
        fields = fields or 'ProviderIds,ProductionYear,Status'
        return self.get_library_items(include_item_types='Movie', fields=fields)

    def get_series_list(self, fields=None):
        fields = fields or 'ProviderIds,ProductionYear,Status,RecursiveItemCount'
        return self.get_library_items(include_item_types='Series', fields=fields)

    def get_series_seasons(self, series_id, fields=None):
        try:
            fields = fields or 'EpisodeCount,PremiereDate'
            response = self.session.get(
                f"{self.server_url}/emby/Shows/{series_id}/Seasons",
                params={'Fields': fields},
                timeout=15
            )
            return response.json().get('Items') or []
        except Exception as e:
            logger.warning('获取季列表失败: series_id=%s, fields=%s, error=%s', series_id, fields, e)
            return []

    def get_season_episodes(self, series_id, season_id, fields=None):
        try:
            fields = fields or 'PremiereDate,SortOrder'
            response = self.session.get(
                f"{self.server_url}/emby/Shows/{series_id}/Episodes",
                params={
                    'seasonId': season_id,
                    'Fields': fields
                },
                timeout=15
            )
            return response.json().get('Items') or []
        except Exception as e:
            logger.warning('获取剧集列表失败: series_id=%s, season_id=%s, fields=%s, error=%s', series_id, season_id, fields, e)
            return []

    def get_all_series_episodes(self, series_id, fields=None):
        try:
            fields = fields or 'PremiereDate,SortOrder'
            response = self.session.get(
                f"{self.server_url}/emby/Shows/{series_id}/Episodes",
                params={
                    'Fields': fields
                },
                timeout=30
            )
            return response.json().get('Items') or []
        except Exception as e:
            logger.warning('获取全部剧集失败: series_id=%s, fields=%s, error=%s', series_id, fields, e)
            return []
