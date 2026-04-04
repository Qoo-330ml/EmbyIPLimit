import logging

logger = logging.getLogger(__name__)


class EmbySecurity:
    def __init__(self, emby_client):
        self.emby_client = emby_client
        self.session = emby_client.get_session()

    def disable_user(self, user_id, username=None):
        """显示用户名的禁用方法"""
        display_name = username or user_id
        try:
            policy_url = f"{self.emby_client.server_url}/emby/Users/{user_id}/Policy"
            logger.warning('准备禁用用户: username=%s, user_id=%s', display_name, user_id)

            response = self.session.post(
                policy_url,
                json={"IsDisabled": True}
            )

            if response.status_code in (200, 204):
                logger.warning('用户已禁用: username=%s, user_id=%s', display_name, user_id)
                return True

            logger.error('禁用用户失败: username=%s, user_id=%s, status_code=%s', display_name, user_id, response.status_code)
            return False

        except Exception as e:
            logger.exception('禁用用户异常: username=%s, user_id=%s, error=%s', display_name, user_id, e)
            return False

    def enable_user(self, user_id, username=None):
        """启用用户（带用户名显示）"""
        display_name = username or user_id
        try:
            policy_url = f"{self.emby_client.server_url}/emby/Users/{user_id}/Policy"
            logger.info('准备启用用户: username=%s, user_id=%s', display_name, user_id)

            response = self.session.post(
                policy_url,
                json={"IsDisabled": False}
            )

            if response.status_code in (200, 204):
                logger.info('用户已启用: username=%s, user_id=%s', display_name, user_id)
                return True

            logger.error('启用用户失败: username=%s, user_id=%s, status_code=%s', display_name, user_id, response.status_code)
            return False
        except Exception as e:
            logger.exception('启用用户异常: username=%s, user_id=%s, error=%s', display_name, user_id, e)
            return False
