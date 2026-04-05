from datetime import datetime

from flask import jsonify, request
from flask_login import login_required

from web.helpers import build_external_url, get_service_external_url


def register_admin_group_routes(server):
    @server.app.get('/api/admin/groups')
    @login_required
    def admin_groups():
        return jsonify({'groups': server.db_manager.get_all_user_groups()})

    @server.app.post('/api/admin/groups')
    @login_required
    def admin_create_group():
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': '请输入用户组名称'}), 400

        group_id = f'group_{datetime.now().strftime("%Y%m%d%H%M%S%f")}'
        try:
            server.db_manager.create_user_group(group_id, name)
            return jsonify({'success': True, 'group': {'id': group_id, 'name': name, 'members': []}})
        except Exception as exc:
            return jsonify({'error': f'创建用户组失败: {exc}'}), 500

    @server.app.delete('/api/admin/groups/<group_id>')
    @login_required
    def admin_delete_group(group_id):
        try:
            server.db_manager.delete_user_group(group_id)
            return jsonify({'success': True})
        except Exception as exc:
            return jsonify({'error': f'删除用户组失败: {exc}'}), 500

    @server.app.post('/api/admin/groups/<group_id>/members')
    @login_required
    def admin_add_group_member(group_id):
        data = request.get_json(silent=True) or {}
        user_id = (data.get('user_id') or '').strip()
        if not user_id:
            return jsonify({'error': '请选择用户'}), 400
        added = server.db_manager.add_user_to_group(group_id, user_id)
        if not added:
            return jsonify({'error': '用户已在该组中'}), 400
        return jsonify({'success': True})

    @server.app.delete('/api/admin/groups/<group_id>/members/<user_id>')
    @login_required
    def admin_remove_group_member(group_id, user_id):
        try:
            server.db_manager.remove_user_from_group(group_id, user_id)
            return jsonify({'success': True})
        except Exception as exc:
            return jsonify({'error': f'移除组成员失败: {exc}'}), 500

    @server.app.get('/api/admin/invites')
    @login_required
    def admin_list_invites():
        invites = server.db_manager.list_invites()
        service_url = get_service_external_url(server.config)
        for invite in invites:
            invite['invite_url'] = build_external_url(service_url, f'invite/{invite["code"]}') or f'/invite/{invite["code"]}'
        return jsonify({'invites': invites})

    @server.app.delete('/api/admin/invites/<code>')
    @login_required
    def admin_delete_invite(code):
        server.db_manager.delete_invite(code)
        return jsonify({'success': True})

    @server.app.post('/api/admin/invites')
    @login_required
    def admin_create_invite():
        data = request.get_json(silent=True) or {}
        valid_hours = int(data.get('valid_hours') or 24)
        max_uses = int(data.get('max_uses') or 1)
        group_id = (data.get('group_id') or '').strip() or None
        account_expiry_date = (data.get('account_expiry_date') or '').strip() or None

        try:
            invite = server.db_manager.create_invite(
                valid_hours=valid_hours,
                max_uses=max_uses,
                group_id=group_id,
                account_expiry_date=account_expiry_date,
                created_by='admin',
            )
            service_url = get_service_external_url(server.config)
            invite_url = build_external_url(service_url, f'invite/{invite["code"]}') or f'/invite/{invite["code"]}'
            invite['invite_url'] = invite_url
            return jsonify({'success': True, 'invite': invite, 'invite_url': invite_url})
        except Exception as exc:
            return jsonify({'error': f'生成邀请链接失败: {exc}'}), 500
