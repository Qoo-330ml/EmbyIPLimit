import os
import shutil
import yaml

def get_base_dir():
    """获取项目根目录（EmbyIPLimit目录）"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_scripts_dir():
    """获取scripts目录路径"""
    return os.path.dirname(os.path.abspath(__file__))

def get_data_dir():
    """获取data目录路径"""
    return os.path.join(get_base_dir(), 'data')

DEFAULT_CONFIG = {
    'emby': {
        'server_url': 'https://emby.example.com',
        'api_key': 'your_api_key_here'
    },
    'database': {
        'name': 'emby_playback.db'
    },
    'monitor': {
        'check_interval': 10
    },
    'notifications': {
        'enable_alerts': True,
        'alert_threshold': 2
    },
    'security': {
        'auto_disable': True,
        'whitelist': ["admin", "user1", "user2"]
    },
    'webhook': {
        'enabled': False,
        'url': '',
        'timeout': 10,
        'retry_attempts': 3,
        'title': 'Emby用户封禁通知',
        'content_template': '用户 {username} 在 {location} 使用 {ip_address} ({ip_type}) 登录，检测到 {session_count} 个并发会话，已自动封禁。'
    }
}

def load_config():
    """加载配置并管理依赖文件"""
    data_dir = get_data_dir()
    scripts_dir = get_scripts_dir()
    
    # 确保data目录存在
    os.makedirs(data_dir, exist_ok=True)
    
    # 检查default_config.yaml是否存在
    default_config_path = os.path.join(scripts_dir, 'default_config.yaml')
    if not os.path.exists(default_config_path):
        print("❌ default_config.yaml文件不存在")
        exit(1)
    
    # 检查data目录下的config.yaml是否存在
    config_file = os.path.join(data_dir, 'config.yaml')
    if not os.path.exists(config_file):
        # 如果不存在，从default_config.yaml复制
        shutil.copy2(default_config_path, config_file)
        print(f"📄 配置文件已生成于: {config_file}，请填写必要项后重启容器")
    
    # 加载用户配置
    with open(config_file, 'r', encoding='utf-8') as f:
        user_config = yaml.safe_load(f) or {}
    
    # 深度合并配置
    config = DEFAULT_CONFIG.copy()
    for section in user_config:
        if section in config:
            config[section].update(user_config[section])
        else:
            config[section] = user_config[section]
    
    # 验证必要字段
    required_fields = [
        ('emby', 'server_url'),
        ('emby', 'api_key')
    ]
    
    missing = []
    for section, field in required_fields:
        if not config.get(section, {}).get(field):
            missing.append(f"{section}.{field}")
    
    if missing:
        print("❌ 缺失必要配置项：")
        for item in missing: 
            print(f"  - {item}")
        exit(1)
    
    return config

def save_config(config):
    """保存配置到文件"""
    data_dir = get_data_dir()
    config_file = os.path.join(data_dir, 'config.yaml')
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

def get_raw_config():
    """获取原始配置文件内容（用于编辑）"""
    data_dir = get_data_dir()
    config_file = os.path.join(data_dir, 'config.yaml')
    
    if not os.path.exists(config_file):
        return ""
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return ""