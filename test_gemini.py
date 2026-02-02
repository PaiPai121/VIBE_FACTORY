#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试 Gemini API 连接
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取 API Key
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key 存在: {bool(api_key)}")
print(f"API Key 长度: {len(api_key) if api_key else 0}")

if not api_key or api_key == "your_gemini_api_key_here":
    print("错误: 请在 .env 文件中设置有效的 GOOGLE_API_KEY")
else:
    print("API Key 配置正确，可以测试 Gemini 连接")
    # 尝试简单的 API 调用
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        print("Gemini API 配置成功")
    except Exception as e:
        print(f"Gemini API 配置失败: {e}")