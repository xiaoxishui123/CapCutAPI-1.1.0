#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCutAPI 服务测试脚本
用于验证部署的API服务是否正常工作
"""

import requests
import json
import sys

# 服务器地址
SERVER_URL = "http://8.148.70.18:9000"

def test_api_endpoint(endpoint, method="GET", data=None):
    """测试API端点"""
    url = f"{SERVER_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ 不支持的HTTP方法: {method}")
            return False
            
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                print(f"✅ {endpoint} - 成功")
                return True
            else:
                print(f"❌ {endpoint} - 失败: {result.get('error', '未知错误')}")
                return False
        else:
            print(f"❌ {endpoint} - HTTP错误: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint} - 连接错误: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ {endpoint} - JSON解析错误: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=== CapCutAPI 服务测试 ===")
    print(f"服务器地址: {SERVER_URL}")
    print()
    
    # 测试的API端点列表
    test_cases = [
        # GET请求测试
        ("/get_intro_animation_types", "GET"),
        ("/get_outro_animation_types", "GET"),
        ("/get_transition_types", "GET"),
        ("/get_mask_types", "GET"),
        ("/get_font_types", "GET"),
        
        # POST请求测试（创建草稿）
        ("/create_draft", "POST", {
            "draft_id": "test_draft_001",
            "width": 1080,
            "height": 1920
        }),
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for endpoint, method, *args in test_cases:
        data = args[0] if args else None
        if test_api_endpoint(endpoint, method, data):
            success_count += 1
    
    print()
    print("=== 测试结果 ===")
    print(f"总测试数: {total_count}")
    print(f"成功数: {success_count}")
    print(f"失败数: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 所有测试通过！服务运行正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查服务配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 