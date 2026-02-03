import logging
import os
from datetime import datetime

def setup_logging():
    """
    设置日志配置
    """
    # 创建logs目录
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 配置日志格式
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 文件处理器 - 记录所有日志
    file_handler = logging.FileHandler(
        f"logs/vibe_nexus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    # 控制台处理器 - 只显示错误及以上级别
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.ERROR)
    logger.addHandler(console_handler)
    
    return logger


def log_error(error_msg, context=""):
    """
    记录错误日志
    """
    logger = logging.getLogger(__name__)
    if context:
        logger.error(f"[CONTEXT: {context}] {error_msg}")
    else:
        logger.error(error_msg)


def log_info(info_msg, context=""):
    """
    记录信息日志
    """
    logger = logging.getLogger(__name__)
    if context:
        logger.info(f"[CONTEXT: {context}] {info_msg}")
    else:
        logger.info(info_msg)