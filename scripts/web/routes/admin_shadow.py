from flask import jsonify, request
from flask_login import login_required

from web.helpers import send_webhook_if_enabled, to_int


def register_admin_shadow_routes(server):
    @server.app.get('/api/admin/shadow/stats')
    @login_required
    def admin_shadow_stats():
        if not server.shadow_library:
            return jsonify({'error': '影子库未初始化'}), 503
        return jsonify({'stats': server.shadow_library.get_library_stats()})

    @server.app.post('/api/admin/shadow/sync')
    @login_required
    def admin_shadow_sync():
        if not server.shadow_syncer:
            return jsonify({'error': '影子库同步器未初始化'}), 503
        server.logger.warning('管理员触发影子库同步')
        try:
            result = server.shadow_syncer.sync_all()
            server.logger.warning('影子库同步完成: result=%s', result)
            movie_result = (result or {}).get('movies') or {}
            series_result = (result or {}).get('series') or {}
            send_webhook_if_enabled(
                server,
                'shadow_sync_completed',
                {
                    'movies_synced': movie_result.get('synced', 0),
                    'movies_failed': movie_result.get('errors', 0),
                    'series_synced': series_result.get('synced', 0),
                    'series_failed': series_result.get('errors', 0),
                    'result': result,
                },
            )
            return jsonify({'success': True, 'result': result})
        except Exception as exc:
            server.logger.exception('影子库同步失败: error=%s', exc)
            send_webhook_if_enabled(
                server,
                'shadow_sync_failed',
                {
                    'error': str(exc),
                },
            )
            return jsonify({'error': f'同步失败: {exc}'}), 500

    @server.app.get('/api/admin/shadow/movies')
    @login_required
    def admin_shadow_movies():
        if not server.shadow_library:
            return jsonify({'error': '影子库未初始化'}), 503
        page = to_int(request.args.get('page', 1), 1)
        page_size = to_int(request.args.get('page_size', 20), 20)
        return jsonify(server.shadow_library.get_movies(page=page, page_size=page_size))

    @server.app.get('/api/admin/shadow/series')
    @login_required
    def admin_shadow_series():
        if not server.shadow_library:
            return jsonify({'error': '影子库未初始化'}), 503
        page = to_int(request.args.get('page', 1), 1)
        page_size = to_int(request.args.get('page_size', 20), 20)
        return jsonify(server.shadow_library.get_series_list(page=page, page_size=page_size))

    @server.app.get('/api/admin/shadow/series/<emby_id>')
    @login_required
    def admin_shadow_series_detail(emby_id):
        if not server.shadow_library:
            return jsonify({'error': '影子库未初始化'}), 503
        detail = server.shadow_library.get_series_detail(emby_id)
        if not detail:
            return jsonify({'error': '剧集不存在'}), 404
        return jsonify(detail)

    @server.app.get('/api/admin/shadow/search')
    @login_required
    def admin_shadow_search():
        if not server.shadow_library:
            return jsonify({'error': '影子库未初始化'}), 503
        query = (request.args.get('q') or '').strip()
        media_type = (request.args.get('type') or '').strip() or None
        if not query:
            return jsonify({'error': '请输入搜索关键词'}), 400
        results = server.shadow_library.search_library(query, media_type)
        return jsonify({'results': results})
