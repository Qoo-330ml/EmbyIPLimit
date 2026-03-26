import logging
import os
import sys
from datetime import datetime


def get_data_dir():
    """获取data目录路径"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


class MemoryLogHandler(logging.Handler):
    """内存日志处理器，用于存储最近的日志"""
    def __init__(self, max_lines=1000):
        super().__init__()
        self.max_lines = max_lines
        self.logs = []
    
    def emit(self, record):
        """添加日志条目"""
        try:
            msg = self.format(record)
            self.logs.append(msg)
            # 保持日志数量不超过最大值
            if len(self.logs) > self.max_lines:
                self.logs = self.logs[-self.max_lines:]
        except Exception:
            self.handleError(record)
    
    def get_logs(self):
        """获取所有日志"""
        return self.logs.copy()


# 全局内存日志处理器
memory_handler = None


def setup_logging():
    """配置日志系统"""
    global memory_handler
    
    # 创建 data 目录
    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    
    # 日志文件路径
    log_file = os.path.join(data_dir, 'embyq.log')
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 内存处理器
    memory_handler = MemoryLogHandler(max_lines=1000)
    memory_handler.setLevel(logging.INFO)
    memory_handler.setFormatter(formatter)
    root_logger.addHandler(memory_handler)
    
    return root_logger


def get_logs():
    """获取所有日志"""
    global memory_handler
    if memory_handler:
        return memory_handler.get_logs()
    return []


def info(msg):
    """记录 INFO 级别日志"""
    logging.info(msg)


def warning(msg):
    """记录 WARNING 级别日志"""
    logging.warning(msg)


def error(msg):
    """记录 ERROR 级别日志"""
    logging.error(msg)


def debug(msg):
    """记录 DEBUG 级别日志"""
    logging.debug(msg)
