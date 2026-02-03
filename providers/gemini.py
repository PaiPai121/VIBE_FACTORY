from typing import Dict, Any, Optional
import asyncio
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


class GeminiProvider(BaseProvider):
    """
    Google Gemini 提供者
    继承自 BaseProvider，遵循模块化驱动原则
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        super().__init__(api_key)
        # 优先使用传入的模型参数，否则使用环境变量，最后使用默认值
        self.model = model or os.getenv("GEMINI_MODEL", os.getenv("GOOGLE_MODEL", "gemini-pro"))
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
    def _get_api_key(self) -> str:
        """
        从环境变量获取 Gemini API 密钥
        遵循环境变量感知原则，严禁硬编码
        """
        # 尝试从多个可能的环境变量名获取API密钥
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 或 GOOGLE_API_KEY 环境变量未设置")
        return api_key
        
    async def generate_response(self, prompt: str) -> Dict[str, Any]:
        """
        调用 Gemini API 生成响应
        遵循鲁棒性原则，处理网络超时和JSON解析失败
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url_with_key = f"{self.api_url}?key={self.api_key}"
                async with session.post(url_with_key, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status != 200:
                        # 处理错误情况，提供降级输出
                        error_text = await response.text()
                        # 检查是否是API配额或认证问题
                        if response.status == 400 and "API key not valid" in error_text:
                            detailed_error = (
                                f"API认证问题: {error_text}\n"
                                f"可能的原因:\n"
                                f"1. API密钥无效或格式错误\n"
                                f"2. API密钥未激活\n"
                                f"3. API密钥权限不足\n"
                                f"建议: 检查API密钥的有效性和权限设置"
                            )
                            log_error(detailed_error, "GeminiProvider.generate_response")
                            return {
                                "success": False,
                                "error": detailed_error,
                                "content": ""
                            }
                        elif response.status == 429:
                            detailed_error = (
                                f"API配额问题: 请求频率过高或配额已用尽\n"
                                f"可能的原因:\n"
                                f"1. 达到请求频率限制\n"
                                f"2. API配额已用尽\n"
                                f"3. 账户超出使用限制\n"
                                f"建议: 等待一段时间后重试或检查API配额"
                            )
                            log_error(detailed_error, "GeminiProvider.generate_response")
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
                        content = response_json['candidates'][0]['content']['parts'][0]['text']
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
            log_error(f"Gemini API请求超时: {self.api_url}", "GeminiProvider.generate_response")
            log_error(f"堆栈跟踪: {traceback.format_exc()}", "GeminiProvider.generate_response")
            return {
                "success": False,
                "error": "请求超时",
                "content": ""
            }
        except aiohttp.ClientConnectorError as e:
            # 处理连接错误
            import traceback
            log_error(f"Gemini API连接错误: {str(e)} - URL: {self.api_url}", "GeminiProvider.generate_response")
            log_error(f"堆栈跟踪: {traceback.format_exc()}", "GeminiProvider.generate_response")

            # 检查是否是常见的网络连接问题
            error_str = str(e)
            if "generativelanguage.googleapis.com" in error_str and ("timeout" in error_str.lower() or "信号灯超时时间已到" in error_str):
                detailed_error = (
                    f"网络连接问题: 无法连接到Google Gemini服务({self.api_url})\n"
                    f"可能的原因:\n"
                    f"1. 网络防火墙阻止了对Google服务的访问\n"
                    f"2. 当前网络环境无法访问Google服务\n"
                    f"3. 需要配置代理才能访问Google服务\n"
                    f"4. API密钥可能无效或配额已用尽\n"
                    f"建议: 检查网络连接或尝试使用其他AI提供者"
                )
                log_error(detailed_error, "GeminiProvider.generate_response")
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
            log_error(f"Gemini API发生未知错误: {str(e)} - URL: {self.api_url}", "GeminiProvider.generate_response")
            log_error(f"堆栈跟踪: {traceback.format_exc()}", "GeminiProvider.generate_response")
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