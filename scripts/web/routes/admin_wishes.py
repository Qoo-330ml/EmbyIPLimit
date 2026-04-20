import logging

from flask import jsonify, request
from flask_login import current_user

from web.helpers import admin_required, send_wish_comment_email, send_wish_status_email

logger = logging.getLogger(__name__)


def register_admin_wish_routes(server):
    @server.app.get('/api/admin/wishes')
    @admin_required
    def admin_list_wishes():
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503
        try:
            status = (request.args.get('status') or '').strip()
            return jsonify({'requests': server.wish_store.list_requests(status=status)})
        except Exception as exc:
            logger.exception('获取求片列表失败: %s', exc)
            return jsonify({'error': '获取求片列表失败'}), 500

    @server.app.patch('/api/admin/wishes/<int:request_id>/status')
    @admin_required
    def admin_update_wish_status(request_id):
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503
        data = request.get_json(silent=True) or {}
        status = (data.get('status') or '').strip()
        try:
            record = server.wish_store.update_request_status(request_id, status)
            if not record:
                return jsonify({'error': '求片记录不存在'}), 404
            admin_name = getattr(current_user, 'username', None) or '管理员'
            try:
                send_wish_status_email(server, request_id, status, admin_name)
            except Exception:
                pass
            return jsonify({'success': True, 'request': record})
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        except Exception as exc:
            logger.exception('更新状态失败: %s', exc)
            return jsonify({'error': '更新状态失败'}), 500

    @server.app.delete('/api/admin/wishes/<int:request_id>')
    @admin_required
    def admin_delete_wish(request_id):
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503
        try:
            deleted = server.wish_store.delete_request(request_id)
            if not deleted:
                return jsonify({'error': '求片记录不存在'}), 404
            return jsonify({'success': True})
        except Exception as exc:
            logger.exception('删除求片失败: %s', exc)
            return jsonify({'error': '删除求片失败'}), 500

    @server.app.get('/api/admin/wishes/<int:request_id>/comments')
    @admin_required
    def admin_wish_comments(request_id):
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503
        try:
            result = server.wish_store.list_comments(request_id)
            return jsonify(result)
        except Exception as exc:
            logger.exception('获取评论失败: %s', exc)
            return jsonify({'error': '获取评论失败'}), 500

    @server.app.post('/api/admin/wishes/<int:request_id>/comments')
    @admin_required
    def admin_wish_add_comment(request_id):
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503
        data = request.get_json(silent=True) or {}
        content = (data.get('content') or '').strip()
        if not content:
            return jsonify({'error': '评论内容不能为空'}), 400
        admin_name = getattr(current_user, 'username', None) or 'admin'
        admin_id = getattr(current_user, 'user_id', None) or 'admin'
        reply_to_id = data.get('reply_to_id') or None
        try:
            comment = server.wish_store.add_comment(request_id, admin_id, admin_name, content, reply_to_id=reply_to_id)
            if not comment:
                return jsonify({'error': '添加评论失败'}), 500
            try:
                send_wish_comment_email(server, request_id, content, admin_name)
            except Exception:
                pass
            return jsonify({'success': True, 'comment': comment}), 201
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        except Exception as exc:
            logger.exception('添加评论失败: %s', exc)
            return jsonify({'error': '添加评论失败'}), 500

    @server.app.delete('/api/admin/wishes/comments/<int:comment_id>')
    @admin_required
    def admin_wish_delete_comment(comment_id):
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503
        try:
            deleted = server.wish_store.delete_comment(comment_id)
            if not deleted:
                return jsonify({'error': '评论不存在'}), 404
            return jsonify({'success': True})
        except Exception as exc:
            logger.exception('删除评论失败: %s', exc)
            return jsonify({'error': '删除评论失败'}), 500
