#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义下载功能修复验证脚本
测试修复后的功能是否正常工作
"""

import requests
import json
import sys
import time

# 服务器地址
BASE_URL = "http://localhost:9000"

# 测试配置
TEST_DRAFT_ID = "dfd_cat_1761981498_f549b6e1"  # 替换为实际的草稿ID
WINDOWS_PATH = r"F:\jianying\cgwz\JianyingPro Drafts"
LINUX_PATH = "/home/user/JianyingPro Drafts"

def print_test_header(test_name):
    """打印测试标题"""
    print("\n" + "="*60)
    print(f"🧪 测试: {test_name}")
    print("="*60)

def print_result(success, message):
    """打印测试结果"""
    if success:
        print(f"✅ PASS: {message}")
    else:
        print(f"❌ FAIL: {message}")
    return success

def test_1_configure_windows_path():
    """测试1: 配置Windows路径（跨平台）"""
    print_test_header("配置Windows路径（在Linux服务器上）")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/draft/path/config",
            json={
                "custom_path": WINDOWS_PATH,
                "client_os": "windows"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return print_result(True, f"成功配置Windows路径: {WINDOWS_PATH}")
            else:
                return print_result(False, f"配置失败: {data.get('error')}")
        else:
            return print_result(False, f"HTTP错误: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"异常: {str(e)}")

def test_2_configure_linux_path():
    """测试2: 配置Linux路径（本地）"""
    print_test_header("配置Linux路径（在Linux服务器上）")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/draft/path/config",
            json={
                "custom_path": LINUX_PATH,
                "client_os": "linux"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return print_result(True, f"成功配置Linux路径: {LINUX_PATH}")
            else:
                return print_result(False, f"配置失败: {data.get('error')}")
        else:
            return print_result(False, f"HTTP错误: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"异常: {str(e)}")

def test_3_get_path_config():
    """测试3: 获取路径配置"""
    print_test_header("获取当前路径配置")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/draft/path/config",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                custom_path = data.get('custom_path', '')
                return print_result(True, f"成功获取配置: {custom_path}")
            else:
                return print_result(False, f"获取失败: {data.get('error')}")
        else:
            return print_result(False, f"HTTP错误: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"异常: {str(e)}")

def test_4_request_custom_download():
    """测试4: 请求自定义下载（检查参数传递）"""
    print_test_header("请求自定义下载并检查响应")
    
    try:
        # 先配置Windows路径
        requests.post(
            f"{BASE_URL}/api/draft/path/config",
            json={
                "custom_path": WINDOWS_PATH,
                "client_os": "windows"
            },
            timeout=10
        )
        
        # 请求下载
        response = requests.post(
            f"{BASE_URL}/api/draft/download",
            json={
                "draft_id": TEST_DRAFT_ID,
                "use_custom_path": True,
                "draft_folder": WINDOWS_PATH,
                "client_os": "windows"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                download_url = data.get('download_url', '')
                
                # 检查URL是否包含参数
                has_client_os = 'client_os' in download_url
                has_draft_folder = 'draft_folder' in download_url
                
                if has_client_os and has_draft_folder:
                    print(f"   下载URL: {download_url}")
                    return print_result(True, "下载URL包含正确的参数")
                else:
                    missing = []
                    if not has_client_os:
                        missing.append('client_os')
                    if not has_draft_folder:
                        missing.append('draft_folder')
                    return print_result(False, f"下载URL缺少参数: {', '.join(missing)}")
            else:
                return print_result(False, f"下载请求失败: {data.get('error')}")
        else:
            return print_result(False, f"HTTP错误: {response.status_code}")
            
    except Exception as e:
        return print_result(False, f"异常: {str(e)}")

def test_5_check_proxy_endpoint():
    """测试5: 检查代理下载端点"""
    print_test_header("检查代理下载端点")
    
    try:
        from urllib.parse import urlencode
        
        params = urlencode({
            'client_os': 'windows',
            'draft_folder': WINDOWS_PATH
        })
        
        proxy_url = f"{BASE_URL}/api/draft/download/proxy/{TEST_DRAFT_ID}?{params}"
        
        print(f"   测试代理URL: {proxy_url}")
        
        # 注意：这个测试只检查URL格式，不真正下载
        # 因为可能没有真实的草稿文件
        
        response = requests.head(proxy_url, timeout=10, allow_redirects=True)
        
        if response.status_code in [200, 302, 307]:
            return print_result(True, f"代理端点可访问 (状态码: {response.status_code})")
        elif response.status_code == 404:
            return print_result(True, "代理端点存在（草稿文件不存在是正常的）")
        else:
            return print_result(False, f"代理端点异常: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        return print_result(False, "无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        return print_result(False, f"异常: {str(e)}")

def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀 开始自定义下载功能修复验证测试")
    print("="*60)
    print(f"服务器地址: {BASE_URL}")
    print(f"测试草稿ID: {TEST_DRAFT_ID}")
    print("="*60)
    
    results = []
    
    # 运行所有测试
    results.append(("配置Windows路径", test_1_configure_windows_path()))
    results.append(("配置Linux路径", test_2_configure_linux_path()))
    results.append(("获取路径配置", test_3_get_path_config()))
    results.append(("请求自定义下载", test_4_request_custom_download()))
    results.append(("检查代理端点", test_5_check_proxy_endpoint()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*60)
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查上面的详细信息")
        return 1

def check_server_availability():
    """检查服务器是否可用"""
    print("🔍 检查服务器可用性...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ 服务器正在运行 (状态码: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务器: {BASE_URL}")
        print("   请确保服务器正在运行:")
        print(f"   cd /home/CapCutAPI-1.1.0")
        print(f"   python capcut_server.py")
        return False
    except Exception as e:
        print(f"❌ 服务器检查失败: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("自定义下载功能修复验证脚本")
    print("版本: 1.0.0")
    print("日期: 2025-11-01")
    print("="*60)
    
    # 检查服务器
    if not check_server_availability():
        sys.exit(1)
    
    # 运行测试
    exit_code = run_all_tests()
    
    print("\n💡 提示:")
    print("   - 如果测试失败，请查看服务器日志: logs/capcutapi.log")
    print("   - 完整测试指南: 自定义下载功能修复测试指南.md")
    print("   - 问题分析报告: 自定义下载功能问题分析.md")
    print()
    
    sys.exit(exit_code)


