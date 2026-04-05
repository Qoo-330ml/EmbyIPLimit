import yaml
from flask import jsonify, request
from flask_login import login_required

from config_loader import load_config, save_config
from logger import get_logs
from network.http_session import update_proxy_config


def register_admin_system_routes(server):
    @server.app.get('/api/admin/logs')
    @login_required
    def admin_logs():
        return jsonify({'logs': get_logs()})

    @server.app.get('/api/admin/config')
    @login_required
    def admin_get_config():
        return jsonify({'config': load_config()})

    @server.app.put('/api/admin/config')
    @login_required
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

            old_use_geocache = server.config.get('ip_location', {}).get('use_geocache', False)
            new_use_geocache = new_config.get('ip_location', {}).get('use_geocache', False)

            if save_config(new_config):
                server.config = load_config()
                update_proxy_config(server.config.get('proxy', {}))
                if old_use_geocache != new_use_geocache:
                    server.location_service.update_config(new_use_geocache)
                if server.tmdb_client:
                    server.tmdb_client.update_config(server.config.get('tmdb', {}))
                if server.monitor:
                    server.monitor.update_runtime_config(server.config)
                return jsonify({'success': True})
            return jsonify({'error': '保存配置失败'}), 500
        except yaml.YAMLError as exc:
            return jsonify({'error': f'Webhook Body YAML 格式错误: {exc}'}), 400
        except Exception as exc:
            return jsonify({'error': f'保存配置时发生错误: {exc}'}), 500

    @server.app.post('/api/admin/webhook/test')
    @login_required
    def admin_test_webhook():
        if not server.monitor:
            return jsonify({'error': '监控器未初始化'}), 503
        ok = server.monitor.test_webhook()
        if ok:
            return jsonify({'success': True})
        return jsonify({'error': 'Webhook 测试发送失败，请检查 URL、超时、Body 与接收端响应'}), 500
