"""
网络连接诊断工具
用于帮助用户诊断和解决AI服务连接问题
"""
import socket
import ssl
import asyncio
import aiohttp
from urllib.parse import urlparse


def check_internet_connectivity():
    """检查基本互联网连接"""
    try:
        # 尝试连接到多个公共DNS服务器
        hosts_to_try = [
            ("8.8.8.8", 53),      # Google DNS
            ("1.1.1.1", 53),      # Cloudflare DNS
            ("www.baidu.com", 80), # Baidu
            ("www.google.com", 80) # Google
        ]

        for host, port in hosts_to_try:
            try:
                socket.create_connection((host, port), timeout=5)
                return True
            except OSError:
                continue  # 尝试下一个主机

        return False
    except Exception:
        return False


def check_host_connectivity(hostname, port=443):
    """检查特定主机的连接性"""
    try:
        socket.create_connection((hostname, port), timeout=10)
        return True
    except OSError:
        return False


def check_ssl_connection(hostname, port=443):
    """检查SSL连接"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                return True
    except Exception:
        return False


async def check_api_connectivity(url, api_key=None):
    """检查API端点连通性"""
    try:
        headers = {"User-Agent": "Vibe-Nexus-Diagnostic/1.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as response:
                return response.status
    except Exception as e:
        return str(e)


def diagnose_network_issues():
    """执行完整的网络诊断"""
    print(">>> 开始网络连接诊断...")

    # 检查基本互联网连接
    print("\n1. 检查基本互联网连接...")
    internet_ok = check_internet_connectivity()
    if internet_ok:
        print("   [PASS] 基本互联网连接正常")
    else:
        print("   [FAIL] 基本互联网连接异常")
        return False

    # 检查Google服务连接
    print("\n2. 检查Google Gemini服务连接...")
    google_ok = check_host_connectivity("generativelanguage.googleapis.com", 443)
    if google_ok:
        print("   [PASS] Google Gemini服务连接正常")
    else:
        print("   [FAIL] 无法连接到Google Gemini服务")
        print("   提示: 可能需要配置代理或网络环境无法访问Google服务")

    # 检查Zhipu服务连接
    print("\n3. 检查Zhipu AI服务连接...")
    zhipu_ok = check_host_connectivity("open.bigmodel.cn", 443)
    if zhipu_ok:
        print("   [PASS] Zhipu AI服务连接正常")
    else:
        print("   [FAIL] 无法连接到Zhipu AI服务")
        print("   提示: 可能需要检查网络设置或服务可用性")

    # 检查SSL连接
    print("\n4. 检查SSL连接安全性...")
    google_ssl_ok = check_ssl_connection("generativelanguage.googleapis.com", 443)
    zhipu_ssl_ok = check_ssl_connection("open.bigmodel.cn", 443)

    if google_ssl_ok:
        print("   [PASS] Google Gemini SSL连接安全")
    else:
        print("   [WARN] Google Gemini SSL连接存在问题")

    if zhipu_ssl_ok:
        print("   [PASS] Zhipu AI SSL连接安全")
    else:
        print("   [WARN] Zhipu AI SSL连接存在问题")

    print("\n>>> 诊断结果总结:")
    print(f"   基本互联网连接: {'[PASS] 正常' if internet_ok else '[FAIL] 异常'}")
    print(f"   Google服务连接: {'[PASS] 正常' if google_ok else '[FAIL] 异常'}")
    print(f"   Zhipu服务连接: {'[PASS] 正常' if zhipu_ok else '[FAIL] 异常'}")
    print(f"   Google SSL安全: {'[PASS] 安全' if google_ssl_ok else '[WARN] 不安全'}")
    print(f"   Zhipu SSL安全: {'[PASS] 安全' if zhipu_ssl_ok else '[WARN] 不安全'}")

    if not google_ok and not zhipu_ok:
        print("\n[WARN] 建议采取以下措施:")
        print("   1. 检查防火墙设置，确保允许出站HTTPS连接")
        print("   2. 如果在企业网络中，可能需要配置代理")
        print("   3. 检查网络策略是否阻止了AI服务的访问")
        print("   4. 尝试使用VPN或其他网络环境")

    return google_ok or zhipu_ok  # 至少一个服务可用


if __name__ == "__main__":
    diagnose_network_issues()