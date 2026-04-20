import logging

from flask import jsonify, request, session
from flask_login import current_user, login_required, login_user, logout_user

logger = logging.getLogger(__name__)


def register_auth_routes(server):
    @server.app.get('/api/health')
    def health():
        return jsonify(
            {
                'ok': True,
                'frontend_built': server.frontend_index_exists(),
            }
        )

    @server.app.post('/api/auth/login')
    def api_login():
        data = request.get_json(silent=True) or {}
        username = data.get('username', '')
        password = data.get('password', '')

        try:
            if username == server.temp_admin_username and password == server.temp_admin_password:
                if server.config.get('web', {}).get('admin_disabled', False):
                    server.logger.warning('临时管理员已被禁用，登录拒绝: username=%s', server.temp_admin_username)
                    return jsonify({'error': '临时管理员已被禁用，请使用 Emby 管理员账号登录'}), 403
                login_user(server.create_admin_user())
                server.logger.info('临时管理员登录成功: username=%s', server.temp_admin_username)
                return jsonify({
                    'success': True,
                    'user': {
                        'username': server.temp_admin_username,
                        'is_admin': True,
                        'is_temp_admin': True,
                    },
                })

            if not server.emby_client:
                server.logger.warning('登录失败: Emby客户端未初始化')
                return jsonify({'error': '用户名或密码错误'}), 401

            emby_user = server.emby_client.authenticate_user(username, password)
            if not emby_user:
                server.logger.warning('Emby用户登录失败: username=%s', username)
                return jsonify({'error': '用户名或密码错误'}), 401

            user_id = emby_user.get('Id') or emby_user.get('user_id', '')
            display_name = emby_user.get('Name') or username

            user_info = server.emby_client.get_user_info(user_id) or {}
            if user_info.get('Policy', {}).get('IsDisabled'):
                server.logger.warning('Emby用户已禁用: username=%s, user_id=%s', display_name, user_id)
                return jsonify({'error': '账号已被禁用'}), 403

            is_admin_emby = bool(user_info.get('Policy', {}).get('IsAdministrator'))

            groups_map = server.get_user_groups_map()
            user_groups = groups_map.get(user_id, [])
            expiry_info = server.db_manager.get_user_expiry(user_id) or {}
            expiry_date = expiry_info.get('expiry_date') or ''
            never_expire = bool(expiry_info.get('never_expire'))

            session['emby_user_data'] = {
                'user_id': user_id,
                'username': display_name,
                'groups': user_groups,
                'expiry_date': expiry_date,
                'never_expire': never_expire,
                'is_admin_emby': is_admin_emby,
            }

            from web.app_server import EmbyUser
            emby_user_obj = EmbyUser(
                user_id=user_id,
                username=display_name,
                groups=user_groups,
                expiry_date=expiry_date,
                never_expire=never_expire,
                is_admin_emby=is_admin_emby,
            )
            login_user(emby_user_obj)

            if is_admin_emby and server.is_temp_admin_enabled():
                server.disable_temp_admin()

            server.logger.info('Emby用户登录成功: username=%s, user_id=%s, is_admin_emby=%s', display_name, user_id, is_admin_emby)
            return jsonify({
                'success': True,
                'user': {
                    'username': display_name,
                    'user_id': user_id,
                    'is_admin': is_admin_emby,
                    'is_admin_emby': is_admin_emby,
                    'groups': user_groups,
                    'expiry_date': expiry_date,
                    'never_expire': never_expire,
                },
            })
        except Exception as exc:
            logger.exception('登录处理异常: username=%s, error=%s', username, exc)
            return jsonify({'error': '登录服务暂时不可用，请稍后重试'}), 500

    @server.app.post('/api/auth/logout')
    @login_required
    def api_logout():
        session.pop('emby_user_data', None)
        server.logger.info('用户退出登录')
        logout_user()
        return jsonify({'success': True})

    @server.app.get('/api/auth/me')
    def api_me():
        if current_user.is_authenticated:
            if getattr(current_user, 'is_temp_admin', False):
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'username': server.temp_admin_username,
                        'is_admin': True,
                        'is_temp_admin': True,
                    },
                })
            return jsonify({
                'authenticated': True,
                'user': {
                    'username': getattr(current_user, 'username', ''),
                    'user_id': getattr(current_user, 'user_id', ''),
                    'is_admin': getattr(current_user, 'is_admin_emby', False),
                    'is_admin_emby': getattr(current_user, 'is_admin_emby', False),
                    'groups': getattr(current_user, 'groups', []),
                    'expiry_date': getattr(current_user, 'expiry_date', ''),
                    'never_expire': getattr(current_user, 'never_expire', False),
                },
            })
        return jsonify({'authenticated': False})
