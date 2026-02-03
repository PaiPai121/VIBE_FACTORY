from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class BaseProvider(ABC):
    """
    基础提供者类，所有其他 Provider 必须继承此类
    遵循模块化驱动原则，严禁硬编码
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化提供者
        :param api_key: API密钥，如果未提供则从环境变量读取
        """
        self.api_key = api_key or self._get_api_key()
        
    @abstractmethod
    def _get_api_key(self) -> str:
        """
        获取API密钥的抽象方法，子类必须实现
        通过环境变量获取，遵循环境变量感知原则
        """
        pass
    
    @abstractmethod
    async def generate_response(self, prompt: str) -> Dict[str, Any]:
        """
        生成响应的抽象方法，子类必须实现
        :param prompt: 输入提示
        :return: 包含响应内容的字典
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否正确
        :return: 配置是否有效
        """
        pass