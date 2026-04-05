from flask import jsonify, request
from flask_login import current_user, login_required, login_user, logout_user


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

        admin_username = server.config.get('web', {}).get('admin_username', 'admin')
        admin_password = server.config.get('web', {}).get('admin_password', 'admin123')

        if username == admin_username and password == admin_password:
            login_user(server.create_admin_user())
            server.logger.info('管理员登录成功: username=%s', admin_username)
            return jsonify({'success': True, 'user': {'username': admin_username}})

        server.logger.warning('管理员登录失败: username=%s', username)
        return jsonify({'error': '用户名或密码错误'}), 401

    @server.app.post('/api/auth/logout')
    @login_required
    def api_logout():
        server.logger.info('管理员退出登录')
        logout_user()
        return jsonify({'success': True})

    @server.app.get('/api/auth/me')
    def api_me():
        if current_user.is_authenticated:
            return jsonify({'authenticated': True, 'user': {'username': 'admin'}})
        return jsonify({'authenticated': False})
