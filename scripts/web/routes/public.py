import logging

from flask import jsonify, request

from web.helpers import get_emby_external_url, send_webhook_if_enabled, to_int

logger = logging.getLogger(__name__)


def register_public_routes(server):
    @server.app.get('/api/public/landing-posters')
    def public_landing_posters():
        try:
            posters = server.get_landing_posters()
            return jsonify(posters)
        except Exception as exc:
            logger.exception('获取落地页轮播图失败: %s', exc)
            return jsonify([])

    @server.app.get('/api/public/server-info')
    def public_server_info():
        try:
            return jsonify(server.get_server_info())
        except Exception as exc:
            logger.exception('获取服务器信息失败: %s', exc)
            return jsonify({'error': '获取服务器信息失败'}), 500

    @server.app.get('/api/public/active-sessions')
    def public_active_sessions():
        try:
            sessions = server.get_all_active_sessions()
            groups_map = server.get_user_groups_map()
            for session in sessions:
                user_id = session.get('user_id')
                session['groups'] = groups_map.get(user_id, []) if user_id else []
            return jsonify({'sessions': sessions})
        except Exception as exc:
            logger.exception('获取活跃会话失败: %s', exc)
            return jsonify({'error': '获取活跃会话失败'}), 500

    @server.app.get('/api/public/search')
    def public_search():
        username = (request.args.get('username') or '').strip()
        if not username:
            return jsonify({'error': '请输入用户名'}), 400

        try:
            server.logger.info('公开搜索用户: username=%s', username)
            user_id = server.get_user_id_by_username(username)
            if not user_id:
                server.logger.warning('公开搜索未找到用户: username=%s', username)
                return jsonify({'error': f'未找到用户名为 {username} 的用户'}), 404

            playback_records = server.serialize_playback_records(
                server.get_user_playback_records(user_id=user_id)
            )
            ban_info = server.serialize_ban_info(server.get_user_ban_info(user_id=user_id))
            user_info = server.emby_client.get_user_info(user_id) or {}
            active_sessions = server.get_user_active_sessions(user_id)
            user_groups = server.get_user_groups_map().get(user_id, [])

            return jsonify(
                {
                    'user_id': user_id,
                    'username': username,
                    'user_info': user_info,
                    'user_groups': user_groups,
                    'playback_records': playback_records,
                    'ban_info': ban_info,
                    'active_sessions': active_sessions,
                }
            )
        except Exception as exc:
            logger.exception('公开搜索用户失败: username=%s, error=%s', username, exc)
            return jsonify({'error': '搜索用户失败'}), 500

    @server.app.get('/api/public/tmdb/search')
    def public_tmdb_search():
        if not server.is_guest_request_enabled():
            return jsonify({'error': '求片功能未启用'}), 403
        if not server.tmdb_client:
            return jsonify({'error': 'TMDB 客户端未初始化'}), 503

        query = (request.args.get('q') or '').strip()
        if not query:
            return jsonify({'error': '请输入搜索关键词'}), 400

        page = to_int(request.args.get('page', 1), 1)
        server.logger.info('公开 TMDB 搜索: query=%s, page=%s', query, page)
        try:
            search_payload = server.tmdb_client.search_multi(query, page=page)
            results = search_payload.get('results') or []
            if server.wish_store and results:
                request_map = server.wish_store.get_request_map(results)
                for item in results:
                    season_number = 0
                    if item.get('media_type') == 'tv':
                        try:
                            season_number = max(int(item.get('season_number') or 0), 0)
                        except Exception:
                            season_number = 0
                    lookup_key = f"{item.get('media_type')}:{item.get('tmdb_id')}:{season_number}"
                    item['lookup_key'] = lookup_key
                    item['season_number'] = season_number
                    request_record = request_map.get(lookup_key)
                    item['requested'] = bool(request_record)
                    if request_record:
                        item['request_id'] = request_record.get('id')
                        item['request_status'] = request_record.get('status')
            if server.shadow_library and results:
                for item in results:
                    tmdb_id = item.get('tmdb_id')
                    media_type = item.get('media_type')
                    shadow_records = server.shadow_library.check_tmdb(tmdb_id, media_type)
                    if shadow_records:
                        item['in_library'] = True
                        if media_type == 'tv':
                            season_records = server.shadow_library.get_series_seasons_by_tmdb(tmdb_id)
                            item['library_season_count'] = len(season_records)
                            try:
                                tmdb_result = server.tmdb_client.get_tv_seasons(tmdb_id)
                                tmdb_seasons = tmdb_result.get('seasons') or []
                                item['tmdb_season_count'] = len(tmdb_seasons)
                            except Exception:
                                item['tmdb_season_count'] = 0
                    else:
                        item['in_library'] = False
                        if media_type == 'tv':
                            item['library_season_count'] = 0
                            item['tmdb_season_count'] = 0
            return jsonify(search_payload)
        except RuntimeError as exc:
            server.logger.warning('TMDB 搜索运行时失败: query=%s, error=%s', query, exc)
            return jsonify({'error': str(exc)}), 503
        except Exception as exc:
            server.logger.exception('TMDB 搜索失败: query=%s, error=%s', query, exc)
            return jsonify({'error': 'TMDB 搜索失败'}), 500

    @server.app.get('/api/public/tmdb/seasons')
    def public_tmdb_seasons():
        if not server.is_guest_request_enabled():
            return jsonify({'error': '求片功能未启用'}), 403
        if not server.tmdb_client:
            return jsonify({'error': 'TMDB 客户端未初始化'}), 503

        tmdb_id = request.args.get('tmdb_id')
        if not tmdb_id:
            return jsonify({'error': '缺少 tmdb_id 参数'}), 400

        server.logger.info('公开 TMDB 季详情查询: tmdb_id=%s', tmdb_id)

        try:
            tmdb_id_int = int(tmdb_id)
        except ValueError:
            return jsonify({'error': 'tmdb_id 参数错误'}), 400

        try:
            tmdb_result = server.tmdb_client.get_tv_seasons(tmdb_id_int)
            tmdb_seasons = tmdb_result.get('seasons') or []
            shadow_seasons = []
            if server.shadow_library:
                shadow_seasons = server.shadow_library.get_series_seasons_by_tmdb(tmdb_id_int)
            shadow_season_numbers = {s.get('season_number') for s in shadow_seasons}
            request_map = {}
            if server.wish_store and tmdb_seasons:
                request_map = server.wish_store.get_request_map(
                    [
                        {
                            'tmdb_id': tmdb_id_int,
                            'media_type': 'tv',
                            'season_number': season.get('season_number'),
                        }
                        for season in tmdb_seasons
                    ]
                )
            result_seasons = []
            for season in tmdb_seasons:
                sn = season.get('season_number')
                in_library = sn in shadow_season_numbers
                lookup_key = f"tv:{tmdb_id_int}:{max(int(sn or 0), 0)}"
                request_record = request_map.get(lookup_key)
                result_seasons.append(
                    {
                        **season,
                        'lookup_key': lookup_key,
                        'requested': bool(request_record),
                        'request_id': request_record.get('id') if request_record else None,
                        'request_status': request_record.get('status') if request_record else '',
                        'in_library': in_library,
                    }
                )
            return jsonify(
                {
                    'seasons': result_seasons,
                    'library_season_count': len(shadow_seasons),
                }
            )
        except RuntimeError as exc:
            return jsonify({'error': str(exc)}), 503
        except Exception as exc:
            logger.exception('获取季信息失败: tmdb_id=%s, error=%s', tmdb_id, exc)
            return jsonify({'error': '获取季信息失败'}), 500

    @server.app.get('/api/public/wishes')
    def public_list_wishes():
        if not server.is_guest_request_enabled():
            return jsonify({'error': '求片功能未启用'}), 403
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503

        try:
            page = to_int(request.args.get('page', 1), 1)
            page_size = to_int(request.args.get('page_size', 20), 20)
            return jsonify(server.wish_store.list_public_requests(page=page, page_size=page_size))
        except Exception as exc:
            logger.exception('获取已求列表失败: %s', exc)
            return jsonify({'error': '获取已求列表失败'}), 500

    @server.app.post('/api/public/wishes')
    def public_create_wish():
        if not server.is_guest_request_enabled():
            return jsonify({'error': '求片功能未启用'}), 403
        if not server.wish_store:
            return jsonify({'error': '求片存储未初始化'}), 503

        data = request.get_json(silent=True) or {}
        item = data.get('item') if isinstance(data.get('item'), dict) else data
        if not isinstance(item, dict):
            return jsonify({'error': '请求参数错误'}), 400

        try:
            from flask_login import current_user
            if current_user.is_authenticated and not getattr(current_user, 'is_temp_admin', False):
                item['user_id'] = current_user.user_id
        except Exception:
            pass

        server.logger.info(
            '公开提交求片: title=%s, media_type=%s, tmdb_id=%s, season_number=%s, user_id=%s',
            item.get('title'),
            item.get('media_type'),
            item.get('tmdb_id'),
            item.get('season_number'),
            item.get('user_id'),
        )
        try:
            if item.get('media_type') == 'tv':
                try:
                    season_number = max(int(item.get('season_number') or 0), 0)
                except Exception:
                    season_number = 0
                if season_number == 0:
                    tmdb_id = int(item.get('tmdb_id'))
                    tmdb_seasons = (server.tmdb_client.get_tv_seasons(tmdb_id) or {}).get('seasons') or []
                    if len(tmdb_seasons) > 1:
                        return jsonify({'error': '该剧包含多季，请先选择具体季再提交求片'}), 400
            record = server.wish_store.add_request(item)
            message = '已加入想看清单' if record.get('created') else '该内容已在求片清单中'
            status_code = 201 if record.get('created') else 200
            if record.get('created'):
                send_webhook_if_enabled(
                    server,
                    'guest_request_created',
                    {
                        'request_id': record.get('id'),
                        'tmdb_id': record.get('tmdb_id'),
                        'media_type': record.get('media_type'),
                        'season_number': record.get('season_number'),
                        'title': record.get('title'),
                        'original_title': record.get('original_title'),
                        'request_status': record.get('status'),
                        'created_at': record.get('created_at'),
                        'source': 'public_request',
                    },
                )
            server.logger.info(
                '公开提交求片完成: title=%s, media_type=%s, tmdb_id=%s, season_number=%s, created=%s, request_id=%s',
                item.get('title'),
                item.get('media_type'),
                item.get('tmdb_id'),
                item.get('season_number'),
                record.get('created'),
                record.get('id'),
            )
            return jsonify({'success': True, 'request': record, 'message': message}), status_code
        except ValueError as exc:
            server.logger.warning('公开提交求片参数错误: item=%s, error=%s', item, exc)
            return jsonify({'error': str(exc)}), 400
        except Exception as exc:
            server.logger.exception('公开提交求片失败: item=%s, error=%s', item, exc)
            return jsonify({'error': '保存求片失败'}), 500

    @server.app.get('/api/public/invite/<code>')
    def public_get_invite(code):
        try:
            available, message = server.db_manager.is_invite_available(code)
            if not available:
                return jsonify({'error': message}), 404

            invite = server.db_manager.get_invite_by_code(code)
            if not invite:
                return jsonify({'error': '邀请不存在'}), 404

            return jsonify({'invite': invite})
        except Exception as exc:
            logger.exception('获取邀请信息失败: code=%s, error=%s', code, exc)
            return jsonify({'error': '获取邀请信息失败'}), 500

    @server.app.post('/api/public/invite/<code>/register')
    def public_register_invite(code):
        try:
            available, message = server.db_manager.is_invite_available(code)
            if not available:
                return jsonify({'error': message}), 400

            data = request.get_json(silent=True) or {}
            username = (data.get('username') or '').strip()
            password = (data.get('password') or '').strip() or username
            user_email = (data.get('email') or '').strip()
            if not username:
                return jsonify({'error': '请输入用户名'}), 400

            invite = server.db_manager.get_invite_by_code(code)
            if not invite:
                return jsonify({'error': '邀请不存在'}), 404

            user_id, create_error = server.emby_client.create_user(username, password)
            if create_error:
                return jsonify({'error': create_error}), 500

            try:
                if invite.get('group_id'):
                    server.db_manager.add_user_to_group(invite['group_id'], user_id)
                if invite.get('account_expiry_date'):
                    server.db_manager.set_user_expiry(user_id, invite['account_expiry_date'], False)
                target_email = invite.get('target_email')
                email_to_bind = user_email if user_email else (target_email if invite.get('used_count', 0) == 0 else None)
                if email_to_bind:
                    server.db_manager.set_user_email(user_id, email_to_bind)
                server.db_manager.consume_invite(code)
            except Exception as exc:
                logger.exception('注册后续处理失败: user_id=%s, error=%s', user_id, exc)
                return jsonify({'error': '注册成功但后续处理失败，请联系管理员'}), 500

            send_webhook_if_enabled(
                server,
                'invite_registered',
                {
                    'username': username,
                    'user_id': user_id,
                    'invite_code': code,
                    'group_id': invite.get('group_id') or '',
                    'account_expiry_date': invite.get('account_expiry_date') or '',
                    'redirect_url': get_emby_external_url(server.config),
                },
            )

            return jsonify({'success': True, 'redirect_url': get_emby_external_url(server.config)})
        except Exception as exc:
            logger.exception('邀请注册失败: code=%s, error=%s', code, exc)
            return jsonify({'error': '注册失败，请稍后重试'}), 500
