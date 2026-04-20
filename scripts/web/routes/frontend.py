import os

from flask import jsonify, send_from_directory


def register_frontend_routes(server):
    @server.app.get('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(server.frontend_assets, filename)

    @server.app.get('/logo.svg')
    def serve_logo():
        return send_from_directory(server.frontend_dist, 'logo.svg')

    @server.app.get('/favicon.svg')
    def serve_favicon():
        return send_from_directory(server.frontend_dist, 'favicon.svg')

    @server.app.get('/icons.svg')
    def serve_icons():
        return send_from_directory(server.frontend_dist, 'icons.svg')

    @server.app.get('/emby-upload.jpg')
    def serve_emby_upload():
        return send_from_directory(server.frontend_dist, 'emby-upload.jpg')

    @server.app.get('/VERSION')
    def serve_version():
        return send_from_directory(server.project_root, 'VERSION')

    @server.app.get('/ABOUT.md')
    def serve_about():
        return send_from_directory(server.project_root, 'ABOUT.md')

    @server.app.get('/landing-posters/<path:filename>')
    def serve_landing_posters(filename):
        import os
        from config_loader import get_data_dir
        posters_dir = os.path.join(get_data_dir(), 'landing-posters')
        if os.path.exists(os.path.join(posters_dir, filename)):
            return send_from_directory(posters_dir, filename)
        return jsonify({'error': '图片不存在'}), 404

    @server.app.get('/')
    def serve_home():
        return send_from_directory(server.frontend_dist, 'index.html')

    @server.app.get('/<path:path>')
    def serve_spa(path):
        if path.startswith('api/'):
            return jsonify({'error': '接口不存在'}), 404

        candidate = os.path.join(server.frontend_dist, path)
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return send_from_directory(server.frontend_dist, path)
        return send_from_directory(server.frontend_dist, 'index.html')
