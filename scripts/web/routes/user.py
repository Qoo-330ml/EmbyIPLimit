from flask import jsonify, request
from flask_login import current_user, login_required
import logging

from web.helpers import send_wish_comment_email, to_int

logger = logging.getLogger(__name__)


def register_user_routes(server):
    @server.app.get('/api/user/profile')
    @login_required
    def user_profile():
        if getattr(current_user, 'is_temp_admin', False):
            return jsonify({'error': '临时管理员无用户档案'}), 400

        try:
            user_id = current_user.user_id
            username = current_user.username

            user_info = server.emby_client.get_user_info(user_id) or {}
            groups_map = server.get_user_groups_map()
            user_groups = groups_map.get(user_id, [])
            expiry_info = server.db_manager.get_user_expiry(user_id) or {}

            return jsonify({
                'user_id': user_id,
                'username': username,
                'groups': user_groups,
                'expiry_date': expiry_info.get('expiry_date') or '',
                'never_expire': bool(expiry_info.get('never_expire')),
                'is_disabled': bool((user_info.get('Policy') or {}).get('IsDisabled')),
                'email': expiry_info.get('email') or '',
            })
        except Exception as exc:
            logger.exception('获取用户档案失败: %s', exc)
            return jsonify({'error': '获取用户档案失败'}), 500

    @server.app.post('/api/user/change-password')
    @login_required
    def user_change_password():
        if getattr(current_user, 'is_temp_admin', False):
            return jsonify({'error': '临时管理员请通过配置修改密码'}), 400

        data = request.get_json(silent=True) or {}
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')

        if not new_password:
            return jsonify({'error': '新密码不能为空'}), 400
        if len(new_password) < 4:
            return jsonify({'error': '新密码长度不能少于4位'}), 400

        try:
            user_id = current_user.user_id
            username = current_user.username

            if not server.emby_client.authenticate_user(username, current_password):
                return jsonify({'error': '当前密码错误'}), 401

            ok = server.emby_client.set_user_password(user_id, new_password)
            if not ok:
                return jsonify({'error': '修改密码失败'}), 500

            return jsonify({'success': True, 'message': '密码修改成功'})
        except Exception as exc:
            logger.exception('修改密码失败: %s', exc)
            return jsonify({'error': '修改密码失败'}), 500

    @server.app.post('/api/user/update-email')
    @login_required
    def user_update_email():
        if getattr(current_user, 'is_temp_admin', False):
            return jsonify({'error': '临时管理员请通过配置修改邮箱'}), 400

        data = request.get_json(silent=True) or {}
        email = data.get('email', '').strip()

        if not email:
            return jsonify({'error': '邮箱不能为空'}), 400

        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'error': '邮箱格式不正确'}), 400

        try:
            user_id = current_user.user_id
            server.db_manager.set_user_email(user_id, email)
            return jsonify({'success': True, 'message': '邮箱更新成功'})
        except Exception as exc:
            logger.exception('更新邮箱失败: %s', exc)
            return jsonify({'error': '更新邮箱失败'}), 500

    @server.app.get('/api/user/playback-history')
    @login_required
    def user_playback_history():
        if getattr(current_user, 'is_temp_admin', False):
            return jsonify({'error': '临时管理员无播放记录'}), 400

        try:
            user_id = current_user.user_id
            limit = min(int(request.args.get('limit', 20)), 100)

            records = server.db_manager.get_user_playback_records(user_id, limit=limit)
            if not records:
                records = server.db_manager.get_playback_records_by_username(
                    current_user.username, limit=limit
                )

            return jsonify({'records': server.serialize_playback_records(records)})
        except Exception as exc:
            logger.exception('获取播放记录失败: %s', exc)
            return jsonify({'error': '获取播放记录失败'}), 500

    @server.app.get('/api/user/wishes')
    @login_required
    def user_wishes():
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503

        if getattr(current_user, 'is_temp_admin', False):
            return jsonify({'error': '临时管理员无求片记录'}), 400

        user_id = current_user.user_id
        page = to_int(request.args.get('page', 1), 1)
        page_size = to_int(request.args.get('page_size', 25), 25)

        try:
            user_requests = server.wish_store.list_user_requests(user_id, page=page, page_size=page_size)
            return jsonify(user_requests)
        except Exception as exc:
            logger.exception('获取求片列表失败: %s', exc)
            return jsonify({'error': '获取求片列表失败'}), 500

    @server.app.get('/api/user/wishes/all')
    @login_required
    def user_all_wishes():
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503

        if getattr(current_user, 'is_temp_admin', False):
            return jsonify({'error': '临时管理员无权查看'}), 400

        page = to_int(request.args.get('page', 1), 1)
        page_size = to_int(request.args.get('page_size', 25), 25)

        try:
            result = server.wish_store.list_all_requests_for_user(page=page, page_size=page_size)
            return jsonify(result)
        except Exception as exc:
            logger.exception('获取求片列表失败: %s', exc)
            return jsonify({'error': '获取求片列表失败'}), 500

    @server.app.get('/api/user/wishes/<int:request_id>/comments')
    @login_required
    def user_wish_comments(request_id):
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503

        if getattr(current_user, 'is_temp_admin', False):
            return jsonify({'error': '临时管理员无权查看评论'}), 400

        page = to_int(request.args.get('page', 1), 1)
        page_size = to_int(request.args.get('page_size', 50), 50)

        try:
            result = server.wish_store.list_comments(request_id, page=page, page_size=page_size)
            return jsonify(result)
        except Exception as exc:
            logger.exception('获取评论失败: %s', exc)
            return jsonify({'error': '获取评论失败'}), 500

    @server.app.post('/api/user/wishes/<int:request_id>/comments')
    @login_required
    def user_wish_add_comment(request_id):
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503

        if getattr(current_user, 'is_temp_admin', False):
            return jsonify({'error': '临时管理员无权评论'}), 400

        data = request.get_json(silent=True) or {}
        content = (data.get('content') or '').strip()
        if not content:
            return jsonify({'error': '评论内容不能为空'}), 400

        user_id = current_user.user_id
        username = current_user.username
        reply_to_id = data.get('reply_to_id') or None

        try:
            comment = server.wish_store.add_comment(request_id, user_id, username, content, reply_to_id=reply_to_id)
            if not comment:
                return jsonify({'error': '添加评论失败'}), 500
            if reply_to_id:
                try:
                    reply_user = server.wish_store.get_comment_user_info(reply_to_id)
                    if reply_user and str(reply_user['user_id']) != str(user_id):
                        replied_user_email = server.db_manager.get_user_email(reply_user['user_id'])
                        if replied_user_email:
                            wish_info = server.wish_store.get_wish_user_info(request_id)
                            if wish_info:
                                server.email_notifier.send_comment_notification(
                                    replied_user_email, wish_info['title'], wish_info['media_type'], content, username
                                )
                except Exception:
                    pass
            return jsonify({'success': True, 'comment': comment}), 201
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        except Exception as exc:
            logger.exception('添加评论失败: %s', exc)
            return jsonify({'error': '添加评论失败'}), 500

    @server.app.delete('/api/user/wishes/comments/<int:comment_id>')
    @login_required
    def user_wish_delete_comment(comment_id):
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503

        if getattr(current_user, 'is_temp_admin', False):
            return jsonify({'error': '临时管理员无权操作'}), 400

        user_id = current_user.user_id
        try:
            deleted = server.wish_store.delete_comment(comment_id, user_id=user_id)
            if not deleted:
                return jsonify({'error': '评论不存在或无权删除'}), 404
            return jsonify({'success': True})
        except Exception as exc:
            logger.exception('删除评论失败: %s', exc)
            return jsonify({'error': '删除评论失败'}), 500
