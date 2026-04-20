import logging

from datetime import datetime, timedelta

from flask import jsonify, request

from web.helpers import admin_required, send_webhook_if_enabled

logger = logging.getLogger(__name__)


def register_admin_user_routes(server):
    @server.app.get('/api/admin/users')
    @admin_required
    def admin_users():
        try:
            users = server.get_all_users_with_expiry()
            stats = {
                'total': len(users),
                'disabled': sum(1 for user in users if user.get('is_disabled')),
                'expired': sum(1 for user in users if user.get('is_expired')),
                'never_expire': sum(1 for user in users if user.get('never_expire')),
            }
            return jsonify({'users': users, 'stats': stats})
        except Exception as exc:
            logger.exception('获取用户列表失败: %s', exc)
            return jsonify({'error': '获取用户列表失败'}), 500

    @server.app.post('/api/admin/users/create')
    @admin_required
    def admin_create_user():
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip() or username
        template_user_id = (data.get('template_user_id') or '').strip()
        group_ids = data.get('group_ids') or []

        if not username:
            return jsonify({'error': '请输入用户名'}), 400

        try:
            user_id, error = server.emby_client.create_user(username, password)
            if error:
                return jsonify({'error': error}), 500

            if template_user_id:
                policy = server.emby_client.get_user_policy(template_user_id)
                if policy and not server.emby_client.set_user_policy(user_id, policy):
                    return jsonify({'error': '用户已创建，但复制模板权限失败'}), 500

            for group_id in group_ids:
                try:
                    server.db_manager.add_user_to_group(group_id, user_id)
                except Exception:
                    pass

            return jsonify({'success': True, 'user_id': user_id}), 201
        except Exception as exc:
            logger.exception('创建用户失败: %s', exc)
            return jsonify({'error': '创建用户失败'}), 500

    @server.app.delete('/api/admin/users/<user_id>')
    @admin_required
    def admin_delete_user(user_id):
        try:
            ok = server.emby_client.delete_user(user_id)
            if not ok:
                return jsonify({'error': '删除用户失败'}), 500
            try:
                server.db_manager.clear_user_expiry(user_id)
            except Exception:
                pass
            return jsonify({'success': True})
        except Exception as exc:
            logger.exception('删除用户失败: %s', exc)
            return jsonify({'error': '删除用户失败'}), 500

    @server.app.post('/api/admin/users/toggle')
    @admin_required
    def admin_toggle_user():
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id')
        action = data.get('action')
        request_username = (data.get('username') or '').strip()
        if not user_id or action not in {'ban', 'unban'}:
            return jsonify({'error': '参数错误'}), 400

        try:
            user_info = server.emby_client.get_user_info(user_id) if server.emby_client else {}
            resolved_username = (user_info.get('Name') or request_username or user_id).strip()

            success = (
                server.security_client.disable_user(user_id, username=resolved_username)
                if action == 'ban'
                else server.security_client.enable_user(user_id, username=resolved_username)
            )
            if not success:
                return jsonify({'error': f'用户{"封禁" if action == "ban" else "解封"}失败'}), 500

            send_webhook_if_enabled(
                server,
                'user_banned_manual' if action == 'ban' else 'user_unbanned_manual',
                {
                    'username': resolved_username,
                },
            )

            return jsonify({'success': True})
        except Exception as exc:
            logger.exception('切换用户状态失败: %s', exc)
            return jsonify({'error': '操作失败'}), 500

    @server.app.post('/api/admin/users/expiry')
    @admin_required
    def admin_set_user_expiry():
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id')
        expiry_date = (data.get('expiry_date') or '').strip()
        never_expire = bool(data.get('never_expire', False))

        if not user_id:
            return jsonify({'error': '参数错误'}), 400

        try:
            if never_expire:
                server.db_manager.set_user_never_expire(user_id, True)
                return jsonify({'success': True, 'message': '用户已设置为永不过期'})

            if expiry_date:
                datetime.strptime(expiry_date, '%Y-%m-%d')
                server.db_manager.set_user_expiry(user_id, expiry_date, False)
                return jsonify({'success': True, 'message': f'用户到期时间已设置为 {expiry_date}'})

            server.db_manager.clear_user_expiry(user_id)
            return jsonify({'success': True, 'message': '用户到期时间已清除'})
        except ValueError:
            return jsonify({'error': '日期格式错误，应为 YYYY-MM-DD'}), 400
        except Exception as exc:
            logger.exception('设置到期时间失败: %s', exc)
            return jsonify({'error': '设置到期时间失败'}), 500

    @server.app.post('/api/admin/users/batch_expiry')
    @admin_required
    def admin_batch_expiry():
        data = request.get_json(silent=True) or {}
        user_ids = data.get('user_ids') or []
        days = data.get('days')
        target_date = (data.get('target_date') or '').strip()

        if not user_ids:
            return jsonify({'error': '请选择用户'}), 400

        try:
            success_count = 0
            fail_count = 0
            for user_id in user_ids:
                try:
                    if target_date:
                        datetime.strptime(target_date, '%Y-%m-%d')
                        server.db_manager.set_user_expiry(user_id, target_date, False)
                    else:
                        days_int = int(days)
                        current_expiry = server.db_manager.get_user_expiry(user_id)
                        if current_expiry and current_expiry.get('expiry_date'):
                            current_date = datetime.strptime(current_expiry['expiry_date'], '%Y-%m-%d')
                        else:
                            current_date = datetime.now()
                        new_date = current_date + timedelta(days=days_int)
                        server.db_manager.set_user_expiry(user_id, new_date.strftime('%Y-%m-%d'), False)
                    success_count += 1
                except Exception:
                    fail_count += 1

            return jsonify({'success': True, 'success_count': success_count, 'fail_count': fail_count})
        except Exception as exc:
            logger.exception('批量设置到期时间失败: %s', exc)
            return jsonify({'error': '批量设置到期时间失败'}), 500

    @server.app.post('/api/admin/users/batch_clear_expiry')
    @admin_required
    def admin_batch_clear_expiry():
        data = request.get_json(silent=True) or {}
        user_ids = data.get('user_ids') or []
        if not user_ids:
            return jsonify({'error': '请选择用户'}), 400

        success_count = 0
        fail_count = 0
        for user_id in user_ids:
            try:
                server.db_manager.clear_user_expiry(user_id)
                success_count += 1
            except Exception:
                fail_count += 1

        return jsonify({'success': True, 'success_count': success_count, 'fail_count': fail_count})

    @server.app.post('/api/admin/users/batch_never_expire')
    @admin_required
    def admin_batch_never_expire():
        data = request.get_json(silent=True) or {}
        user_ids = data.get('user_ids') or []
        cancel = bool(data.get('cancel', False))
        if not user_ids:
            return jsonify({'error': '请选择用户'}), 400

        success_count = 0
        fail_count = 0
        for user_id in user_ids:
            try:
                server.db_manager.set_user_never_expire(user_id, not cancel)
                success_count += 1
            except Exception:
                fail_count += 1

        return jsonify({'success': True, 'success_count': success_count, 'fail_count': fail_count})

    @server.app.post('/api/admin/users/batch_toggle')
    @admin_required
    def admin_batch_toggle():
        data = request.get_json(silent=True) or {}
        user_ids = data.get('user_ids') or []
        action = data.get('action')
        if not user_ids or action not in {'ban', 'unban'}:
            return jsonify({'error': '参数错误'}), 400

        success_count = 0
        fail_count = 0
        for user_id in user_ids:
            ok = server.security_client.disable_user(user_id) if action == 'ban' else server.security_client.enable_user(user_id)
            if ok:
                success_count += 1
            else:
                fail_count += 1

        return jsonify({'success': True, 'success_count': success_count, 'fail_count': fail_count})

    @server.app.post('/api/admin/users/alert_threshold')
    @admin_required
    def admin_set_user_alert_threshold():
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id')
        threshold = data.get('alert_threshold')

        if not user_id:
            return jsonify({'error': '参数错误'}), 400

        try:
            if threshold is None or threshold == '':
                server.db_manager.clear_user_alert_threshold(user_id)
                return jsonify({'success': True, 'message': '已清除用户告警阈值，将使用全局默认值'})
            threshold = int(threshold)
            if threshold < 1:
                return jsonify({'error': '告警阈值必须大于0'}), 400
            server.db_manager.set_user_alert_threshold(user_id, threshold)
            return jsonify({'success': True, 'message': f'用户告警阈值已设置为 {threshold}'})
        except (ValueError, TypeError):
            return jsonify({'error': '告警阈值必须为正整数'}), 400
        except Exception as exc:
            logger.exception('设置告警阈值失败: %s', exc)
            return jsonify({'error': '设置告警阈值失败'}), 500

    @server.app.post('/api/admin/users/batch_alert_threshold')
    @admin_required
    def admin_batch_alert_threshold():
        data = request.get_json(silent=True) or {}
        user_ids = data.get('user_ids') or []
        threshold = data.get('alert_threshold')

        if not user_ids:
            return jsonify({'error': '请选择用户'}), 400

        success_count = 0
        fail_count = 0
        for user_id in user_ids:
            try:
                if threshold is None or threshold == '':
                    server.db_manager.clear_user_alert_threshold(user_id)
                else:
                    t = int(threshold)
                    if t < 1:
                        fail_count += 1
                        continue
                    server.db_manager.set_user_alert_threshold(user_id, t)
                success_count += 1
            except Exception:
                fail_count += 1

        return jsonify({'success': True, 'success_count': success_count, 'fail_count': fail_count})
