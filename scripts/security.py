import logging

logger = logging.getLogger(__name__)


class EmbySecurity:
    def __init__(self, emby_client):
        self.emby_client = emby_client
        self.session = emby_client.get_session()

    def disable_user(self, user_id, username=None):
        display_name = username or user_id
        try:
            logger.warning('准备禁用用户: username=%s, user_id=%s', display_name, user_id)
            ok = self.emby_client.set_user_disabled(user_id, True)
            if ok:
                logger.warning('用户已禁用: username=%s, user_id=%s', display_name, user_id)
                return True
            logger.error('禁用用户失败: username=%s, user_id=%s', display_name, user_id)
            return False
        except Exception as e:
            logger.exception('禁用用户异常: username=%s, user_id=%s, error=%s', display_name, user_id, e)
            return False

    def enable_user(self, user_id, username=None):
        display_name = username or user_id
        try:
            logger.info('准备启用用户: username=%s, user_id=%s', display_name, user_id)
            ok = self.emby_client.set_user_disabled(user_id, False)
            if ok:
                logger.info('用户已启用: username=%s, user_id=%s', display_name, user_id)
                return True
            logger.error('启用用户失败: username=%s, user_id=%s', display_name, user_id)
            return False
        except Exception as e:
            logger.exception('启用用户异常: username=%s, user_id=%s, error=%s', display_name, user_id, e)
            return False
