#!/usr/bin/env python3
"""
简化的Webhook通知器
仅支持默认通用消息格式
"""

import json
import logging
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

class WebhookNotifier:
    def __init__(self, config):
        """
        初始化Webhook通知器
        
        Args:
            config (dict): Webhook配置
                - enabled: 是否启用
                - url: Webhook地址
                - timeout: 请求超时时间
                - retry_attempts: 重试次数
                - body: 自定义请求体配置字典，包含用户自定义的字段
        """
        self.enabled = config.get('enabled', False)
        self.url = config.get('url', '')
        self.timeout = config.get('timeout', 10)
        self.retry_attempts = config.get('retry_attempts', 3)
        
        # 动态加载body配置
        self.body_config = config.get('body', {})
        
        if self.enabled and not self.url:
            logger.warning("Webhook已启用但未配置URL")
            self.enabled = False

    def send_ban_notification(self, user_info):
        """
        发送用户封禁通知
        
        Args:
            user_info (dict): 用户信息
                - username: 用户名
                - user_id: 用户ID
                - ip_address: IP地址
                - ip_type: IP类型 (IPv4/IPv6)
                - location: 地理位置
                - session_count: 并发会话数
                - reason: 封禁原因
                - device: 设备信息
                - client: 客户端
                - timestamp: 时间戳
        
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled:
            logger.info("Webhook通知未启用")
            return False
            
        if not self.url:
            logger.error("未配置Webhook URL")
            return False
            
        try:
            payload = self._build_payload(user_info)
            return self._send_request(payload)
        except ValueError as e:
            # 配置错误，记录错误但不抛出异常
            logger.error(f"Webhook配置错误: {e}")
            return False
        except Exception as e:
            logger.error(f"构建Webhook通知失败: {e}")
            return False

    def _format_template(self, value, user_info):
        """
        格式化单个值（支持递归格式化嵌套对象）
        
        Args:
            value: 要格式化的值（字符串、字典、列表等）
            user_info (dict): 用户信息
            
        Returns:
            格式化后的值
        """
        if isinstance(value, str):
            # 字符串类型，进行模板格式化
            try:
                return value.format(**user_info)
            except (KeyError, ValueError) as e:
                logger.warning(f"模板格式化失败: {e}")
                return value
        elif isinstance(value, dict):
            # 字典类型，递归处理每个值
            result = {}
            for k, v in value.items():
                result[k] = self._format_template(v, user_info)
            return result
        elif isinstance(value, list):
            # 列表类型，递归处理每个元素
            return [self._format_template(item, user_info) for item in value]
        else:
            # 其他类型，直接返回
            return value

    def _build_payload(self, user_info):
        """
        构建动态Webhook payload，基于用户自定义的body配置
        
        Args:
            user_info (dict): 用户信息
            
        Returns:
            dict: Webhook payload - 基于用户配置的动态格式
            
        Raises:
            ValueError: 当未配置body字段时抛出异常
        """
        payload = {}
        
        # 遍历用户配置的body字段
        for key, value in self.body_config.items():
            payload[key] = self._format_template(value, user_info)
        
        # 如果没有配置body字段，提示用户配置
        if not payload:
            error_msg = (
                "❌ Webhook配置错误：未找到body字段配置\n"
                "请在config.yaml的webhook配置中添加body字段，例如：\n"
                "webhook:\n"
                "  enabled: true\n"
                "  url: \"your-webhook-url\"\n"
                "  body:\n"
                "    title: \"通知标题\"\n"
                "    content: \"通知内容：{username} 在 {location} 登录"
            )
            logger.error(error_msg)
            raise ValueError("Webhook body配置缺失，请查看日志了解配置方法")
        
        logger.debug(f"构建的Payload: {payload}")
        return payload

    def _send_request(self, payload):
        """
        发送HTTP POST请求到Webhook服务
        
        Args:
            payload (dict): 请求负载 - 符合API文档格式
            
        Returns:
            bool: 发送是否成功
        """
        if not self.url:
            return False
            
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    self.url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                logger.info(f"Webhook通知发送成功 (尝试 {attempt + 1})")
                return True
                
            except requests.exceptions.Timeout:
                logger.warning(f"Webhook请求超时 (尝试 {attempt + 1}/{self.retry_attempts})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Webhook请求失败 (尝试 {attempt + 1}/{self.retry_attempts}): {e}")
            except Exception as e:
                logger.error(f"Webhook发送异常 (尝试 {attempt + 1}/{self.retry_attempts}): {e}")
                
        logger.error(f"Webhook通知发送失败，已重试 {self.retry_attempts} 次")
        return False

    def test_webhook(self):
        """
        测试Webhook配置
        
        Returns:
            bool: 测试是否成功
        """
        test_user_info = {
            'username': '测试用户',
            'user_id': 'test_123',
            'ip_address': '192.168.1.100',
            'ip_type': 'IPv4',
            'location': '测试地点',
            'session_count': 1,
            'reason': '测试通知',
            'device': '测试设备',
            'client': '测试客户端',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info("🔔 开始测试Webhook通知...")
        logger.info(f"测试用户: {test_user_info['username']}")
        logger.info(f"IP地址: {test_user_info['ip_address']} ({test_user_info['ip_type']})")
        logger.info(f"位置: {test_user_info['location']}")
        
        success = self.send_ban_notification(test_user_info)
        
        if success:
            logger.info("✅ Webhook通知发送成功！")
        else:
            logger.error("❌ Webhook通知发送失败")
            
        return success