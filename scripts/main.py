from config_loader import load_config
from database import DatabaseManager
from emby_client import EmbyClient
from security import EmbySecurity
from monitor import EmbyMonitor
from web_server import WebServer

def main():
    print("start")
    # 加载配置
    config = load_config()
    
    # 初始化核心组件
    db_manager = DatabaseManager(config['database']['name'])
    emby_client = EmbyClient(
        server_url=config['emby']['server_url'],
        api_key=config['emby']['api_key']
    )
    security = EmbySecurity(
        server_url=config['emby']['server_url'],
        api_key=config['emby']['api_key']
    )
    
    # 启动监控服务
    monitor = EmbyMonitor(
        db_manager=db_manager,
        emby_client=emby_client,
        security_client=security,
        config=config
    )
    
    # 初始化并启动Web服务器
    web_server = WebServer(
        db_manager=db_manager,
        emby_client=emby_client,
        security_client=security,
        config=config
    )
    web_server.start()
    
    # 运行监控服务
    monitor.run()

if __name__ == '__main__':
    main()