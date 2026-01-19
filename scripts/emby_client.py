import requests

class EmbyClient:
    def __init__(self, server_url, api_key):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({'X-Emby-Token': self.api_key})
    
    def get_user_info(self, user_id):
        try:
            response = self.session.get(
                f"{self.server_url}/emby/Users/{user_id}",
                timeout=3
            )
            return response.json()
        except Exception as e:
            print(f"获取用户信息失败: {str(e)}")
            return {}
    
    def get_active_sessions(self):
        try:
            response = self.session.get(
                f"{self.server_url}/emby/Sessions",
                timeout=5
            )
            return {s['Id']: s for s in response.json() if s.get('NowPlayingItem')}
        except Exception as e:
            print(f"获取会话失败: {str(e)}")
            return {}
    
    @staticmethod
    def parse_media_info(item):
        if not item:
            return "未知内容"
        if item.get('SeriesName'):
            return f"{item['SeriesName']} S{item['ParentIndexNumber']}E{item['IndexNumber']}"
        return item.get('Name', '未知内容')
    
    def get_users(self):
        """获取所有用户列表"""
        try:
            response = self.session.get(
                f"{self.server_url}/emby/Users",
                timeout=5
            )
            return response.json()
        except Exception as e:
            print(f"获取用户列表失败: {str(e)}")
            return []