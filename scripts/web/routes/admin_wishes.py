from flask import jsonify, request
from flask_login import login_required


def register_admin_wish_routes(server):
    @server.app.get('/api/admin/wishes')
    @login_required
    def admin_list_wishes():
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503
        status = (request.args.get('status') or '').strip()
        return jsonify({'requests': server.wish_store.list_requests(status=status)})

    @server.app.patch('/api/admin/wishes/<int:request_id>/status')
    @login_required
    def admin_update_wish_status(request_id):
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503
        data = request.get_json(silent=True) or {}
        status = (data.get('status') or '').strip()
        try:
            record = server.wish_store.update_request_status(request_id, status)
            if not record:
                return jsonify({'error': '求片记录不存在'}), 404
            return jsonify({'success': True, 'request': record})
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        except Exception as exc:
            return jsonify({'error': f'更新状态失败: {exc}'}), 500
