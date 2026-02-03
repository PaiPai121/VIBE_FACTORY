import asyncio
from typing import Dict, Any, Optional
import aiohttp
from providers.base import BaseProvider
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入日志工具
try:
    from utils.logging_utils import log_error
except ImportError:
    # 如果日志工具不可用，则使用基本的日志记录
    import logging
    def log_error(error_msg, context=""):
        logging.error(f"[{context}] {error_msg}")


class ZhipuProvider(BaseProvider):
    """
    Zhipu AI (GLM) 提供者
    继承自 BaseProvider，遵循模块化驱动原则
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        super().__init__(api_key)
        # 优先使用传入的模型参数，否则使用环境变量，最后使用默认值
        self.model = model or os.getenv("ZHIPU_MODEL", "glm-4")
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
    def _get_api_key(self) -> str:
        """
        从环境变量获取 Zhipu API 密钥
        遵循环境变量感知原则，严禁硬编码
        """
        api_key = os.getenv("ZHIPU_API_KEY")
        if not api_key:
            raise ValueError("ZHIPU_API_KEY 环境变量未设置")
        return api_key
        
    async def generate_response(self, prompt: str) -> Dict[str, Any]:
        """
        调用 Zhipu API 生成响应
        遵循鲁棒性原则，处理网络超时和JSON解析失败
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status != 200:
                        # 处理错误情况，提供降级输出
                        error_text = await response.text()
                        # 检查是否是API配额或认证问题
                        if response.status == 429 or "余额不足" in error_text or "quota" in error_text.lower():
                            detailed_error = (
                                f"API服务问题: {error_text}\n"
                                f"可能的原因:\n"
                                f"1. API配额已用尽\n"
                                f"2. API密钥无效或已过期\n"
                                f"3. 账户余额不足\n"
                                f"4. 达到请求频率限制\n"
                                f"建议: 检查API密钥有效性或充值账户"
                            )
                            log_error(detailed_error, "ZhipuProvider.generate_response")
                            return {
                                "success": False,
                                "error": detailed_error,
                                "content": ""
                            }
                        else:
                            return {
                                "success": False,
                                "error": f"API请求失败，状态码: {response.status}, 错误信息: {error_text}",
                                "content": ""
                            }
                    
                    response_json = await response.json()
                    
                    # 尝试提取内容
                    try:
                        content = response_json['choices'][0]['message']['content']
                        return {
                            "success": True,
                            "content": content,
                            "raw_response": response_json
                        }
                    except (KeyError, IndexError) as e:
                        # JSON解析失败，提供降级输出
                        return {
                            "success": False,
                            "error": f"解析响应失败: {str(e)}",
                            "content": "",
                            "raw_response": response_json
                        }
                        
        except asyncio.TimeoutError:
            # 处理网络超时，提供降级输出
            import traceback
            log_error(f"Zhipu API请求超时: {self.api_url}", "ZhipuProvider.generate_response")
            log_error(f"堆栈跟踪: {traceback.format_exc()}", "ZhipuProvider.generate_response")
            return {
                "success": False,
                "error": "请求超时",
                "content": ""
            }
        except aiohttp.ClientConnectorError as e:
            # 处理连接错误
            import traceback
            log_error(f"Zhipu API连接错误: {str(e)} - URL: {self.api_url}", "ZhipuProvider.generate_response")
            log_error(f"堆栈跟踪: {traceback.format_exc()}", "ZhipuProvider.generate_response")

            # 检查是否是常见的网络连接问题
            error_str = str(e)
            if "open.bigmodel.cn" in error_str and ("timeout" in error_str.lower() or "信号灯超时时间已到" in error_str):
                detailed_error = (
                    f"网络连接问题: 无法连接到Zhipu AI服务({self.api_url})\n"
                    f"可能的原因:\n"
                    f"1. 网络防火墙阻止了对Zhipu服务的访问\n"
                    f"2. 当前网络环境无法访问Zhipu服务\n"
                    f"3. 需要配置代理才能访问Zhipu服务\n"
                    f"4. API密钥可能无效或配额已用尽\n"
                    f"建议: 检查网络连接或尝试使用其他AI提供者"
                )
                log_error(detailed_error, "ZhipuProvider.generate_response")
                return {
                    "success": False,
                    "error": detailed_error,
                    "content": ""
                }
            else:
                return {
                    "success": False,
                    "error": f"连接错误: {str(e)}",
                    "content": ""
                }
        except Exception as e:
            # 处理其他异常，提供降级输出
            import traceback
            log_error(f"Zhipu API发生未知错误: {str(e)} - URL: {self.api_url}", "ZhipuProvider.generate_response")
            log_error(f"堆栈跟踪: {traceback.format_exc()}", "ZhipuProvider.generate_response")
            return {
                "success": False,
                "error": f"发生未知错误: {str(e)}",
                "content": ""
            }
    
    def validate_config(self) -> bool:
        """
        验证配置是否正确
        """
        return self.api_key is not None and len(self.api_key) > 0