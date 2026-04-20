import logging

from datetime import datetime

from flask import jsonify, request

from web.helpers import admin_required, build_external_url, get_service_external_url

logger = logging.getLogger(__name__)


def register_admin_group_routes(server):
    @server.app.get('/api/admin/groups')
    @admin_required
    def admin_groups():
        try:
            return jsonify({'groups': server.db_manager.get_all_user_groups()})
        except Exception as exc:
            logger.exception('获取用户组列表失败: %s', exc)
            return jsonify({'error': '获取用户组列表失败'}), 500

    @server.app.post('/api/admin/groups')
    @admin_required
    def admin_create_group():
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': '请输入用户组名称'}), 400

        group_id = f'group_{datetime.now().strftime("%Y%m%d%H%M%S%f")}'
        try:
            server.db_manager.create_user_group(group_id, name)
            return jsonify({'success': True, 'group': {'id': group_id, 'name': name, 'members': []}}), 201
        except Exception as exc:
            logger.exception('创建用户组失败: %s', exc)
            return jsonify({'error': '创建用户组失败'}), 500

    @server.app.delete('/api/admin/groups/<group_id>')
    @admin_required
    def admin_delete_group(group_id):
        try:
            server.db_manager.delete_user_group(group_id)
            return jsonify({'success': True})
        except Exception as exc:
            logger.exception('删除用户组失败: %s', exc)
            return jsonify({'error': '删除用户组失败'}), 500

    @server.app.post('/api/admin/groups/<group_id>/members')
    @admin_required
    def admin_add_group_member(group_id):
        data = request.get_json(silent=True) or {}
        user_id = (data.get('user_id') or '').strip()
        if not user_id:
            return jsonify({'error': '请选择用户'}), 400
        try:
            added = server.db_manager.add_user_to_group(group_id, user_id)
            if not added:
                return jsonify({'error': '用户已在该组中'}), 400
            return jsonify({'success': True})
        except Exception as exc:
            logger.exception('添加组成员失败: %s', exc)
            return jsonify({'error': '添加组成员失败'}), 500

    @server.app.delete('/api/admin/groups/<group_id>/members/<user_id>')
    @admin_required
    def admin_remove_group_member(group_id, user_id):
        try:
            server.db_manager.remove_user_from_group(group_id, user_id)
            return jsonify({'success': True})
        except Exception as exc:
            logger.exception('移除组成员失败: %s', exc)
            return jsonify({'error': '移除组成员失败'}), 500

    @server.app.post('/api/admin/groups/<group_id>/alert_threshold')
    @admin_required
    def admin_set_group_alert_threshold(group_id):
        data = request.get_json(silent=True) or {}
        threshold = data.get('alert_threshold')

        try:
            if threshold is None or threshold == '':
                server.db_manager.set_group_alert_threshold(group_id, None)
                return jsonify({'success': True, 'message': '已清除用户组告警阈值，将使用全局默认值'})
            threshold = int(threshold)
            if threshold < 1:
                return jsonify({'error': '告警阈值必须大于0'}), 400
            server.db_manager.set_group_alert_threshold(group_id, threshold)
            return jsonify({'success': True, 'message': f'用户组告警阈值已设置为 {threshold}'})
        except (ValueError, TypeError):
            return jsonify({'error': '告警阈值必须为正整数'}), 400
        except Exception as exc:
            logger.exception('设置用户组告警阈值失败: %s', exc)
            return jsonify({'error': '设置用户组告警阈值失败'}), 500

    @server.app.get('/api/admin/invites')
    @admin_required
    def admin_list_invites():
        try:
            invites = server.db_manager.list_invites()
            service_url = get_service_external_url(server.config)
            for invite in invites:
                invite['invite_url'] = build_external_url(service_url, f'invite/{invite["code"]}') or f'/invite/{invite["code"]}'
            return jsonify({'invites': invites})
        except Exception as exc:
            logger.exception('获取邀请列表失败: %s', exc)
            return jsonify({'error': '获取邀请列表失败'}), 500

    @server.app.delete('/api/admin/invites/<code>')
    @admin_required
    def admin_delete_invite(code):
        try:
            server.db_manager.delete_invite(code)
            return jsonify({'success': True})
        except Exception as exc:
            logger.exception('删除邀请失败: %s', exc)
            return jsonify({'error': '删除邀请失败'}), 500

    @server.app.post('/api/admin/invites')
    @admin_required
    def admin_create_invite():
        data = request.get_json(silent=True) or {}
        try:
            valid_hours = int(data.get('valid_hours') or 24)
            max_uses = int(data.get('max_uses') or 1)
        except (ValueError, TypeError):
            return jsonify({'error': '参数格式错误'}), 400

        if valid_hours < 1 or max_uses < 1:
            return jsonify({'error': '有效时长和使用次数必须大于0'}), 400

        group_id = (data.get('group_id') or '').strip() or None
        account_expiry_date = (data.get('account_expiry_date') or '').strip() or None
        target_email = (data.get('target_email') or '').strip() or None

        try:
            invite = server.db_manager.create_invite(
                valid_hours=valid_hours,
                max_uses=max_uses,
                group_id=group_id,
                account_expiry_date=account_expiry_date,
                created_by='admin',
                target_email=target_email,
            )
            service_url = get_service_external_url(server.config)
            invite_url = build_external_url(service_url, f'invite/{invite["code"]}') or f'/invite/{invite["code"]}'
            invite['invite_url'] = invite_url

            if target_email:
                try:
                    server.email_notifier.send_invite_notification(target_email, invite_url, valid_hours, max_uses)
                except Exception:
                    pass

            return jsonify({'success': True, 'invite': invite, 'invite_url': invite_url}), 201
        except Exception as exc:
            logger.exception('生成邀请链接失败: %s', exc)
            return jsonify({'error': '生成邀请链接失败'}), 500
