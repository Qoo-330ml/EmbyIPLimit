import logging

import yaml
from flask import jsonify, request

from config_loader import load_config, save_config
from email_notifier import EmailNotifier
from logger import get_logs
from network.http_session import update_proxy_config
from web.helpers import admin_required
from web.runtime import create_location_service

logger = logging.getLogger(__name__)


def register_admin_system_routes(server):
    @server.app.get('/api/admin/logs')
    @admin_required
    def admin_logs():
        try:
            return jsonify({'logs': get_logs()})
        except Exception as exc:
            logger.exception('获取日志失败: %s', exc)
            return jsonify({'error': '获取日志失败'}), 500

    @server.app.get('/api/admin/config')
    @admin_required
    def admin_get_config():
        try:
            return jsonify({'config': load_config()})
        except Exception as exc:
            logger.exception('获取配置失败: %s', exc)
            return jsonify({'error': '获取配置失败'}), 500

    @server.app.put('/api/admin/config')
    @admin_required
    def admin_save_config():
        data = request.get_json(silent=True) or {}
        new_config = data.get('config')
        if not isinstance(new_config, dict):
            return jsonify({'error': '配置格式错误'}), 400

        try:
            if new_config.get('webhook', {}).get('body') and isinstance(new_config['webhook']['body'], str):
                new_config['webhook']['body'] = yaml.safe_load(new_config['webhook']['body']) or {}

            if 'web' not in new_config:
                new_config['web'] = {}

            old_emby_url = server.config.get('emby', {}).get('server_url')
            old_emby_api_key = server.config.get('emby', {}).get('api_key')
            old_use_geocache = server.config.get('ip_location', {}).get('use_geocache', False)

            new_emby_url = new_config.get('emby', {}).get('server_url')
            new_emby_api_key = new_config.get('emby', {}).get('api_key')
            new_use_geocache = new_config.get('ip_location', {}).get('use_geocache', False)

            if save_config(new_config):
                server.config = load_config()

                update_proxy_config(server.config.get('proxy', {}))

                if old_emby_url != new_emby_url or old_emby_api_key != new_emby_api_key:
                    server.emby_client.update_config(new_emby_url, new_emby_api_key)

                if old_use_geocache != new_use_geocache:
                    try:
                        server.location_service = create_location_service(server.config, server.db_manager, server.emby_client)
                        if server.monitor:
                            server.monitor.location_service = server.location_service
                            server.monitor.alert_service.get_location = server.monitor._get_location
                    except Exception as e:
                        logger.warning('LocationService 重载失败: %s', e)

                if server.tmdb_client:
                    server.tmdb_client.update_config(server.config.get('tmdb', {}))

                if server.shadow_syncer:
                    server.shadow_syncer.update_config(server.config)

                if server.monitor:
                    server.monitor.update_runtime_config(server.config)

                server.email_notifier = EmailNotifier(server.config)

                return jsonify({'success': True})
            return jsonify({'error': '保存配置失败'}), 500
        except yaml.YAMLError:
            return jsonify({'error': 'Webhook Body YAML 格式错误'}), 400
        except Exception as exc:
            logger.exception('保存配置时发生错误: %s', exc)
            return jsonify({'error': '保存配置时发生错误'}), 500

    @server.app.post('/api/admin/webhook/test')
    @admin_required
    def admin_test_webhook():
        if not server.monitor:
            return jsonify({'error': '监控器未初始化'}), 503
        try:
            ok = server.monitor.test_webhook()
            if ok:
                return jsonify({'success': True})
            return jsonify({'error': 'Webhook 测试发送失败，请检查 URL、超时、Body 与接收端响应'}), 500
        except Exception as exc:
            logger.exception('Webhook 测试失败: %s', exc)
            return jsonify({'error': 'Webhook 测试失败'}), 500

    @server.app.post('/api/admin/email/test')
    @admin_required
    def admin_test_email():
        try:
            email_config = server.config.get('email', {})
            if not email_config.get('enabled'):
                return jsonify({'error': '邮件通知未启用'}), 400
            if not email_config.get('sender_email') or not email_config.get('sender_password'):
                return jsonify({'error': '发件人邮箱或密码未配置'}), 400
            notifier = server.email_notifier
            ok, msg = notifier.test_connection()
            if ok:
                return jsonify({'success': True, 'message': '邮件服务连接测试成功'})
            return jsonify({'error': msg}), 500
        except Exception as exc:
            logger.exception('邮件测试失败: %s', exc)
            return jsonify({'error': '邮件测试失败'}), 500
