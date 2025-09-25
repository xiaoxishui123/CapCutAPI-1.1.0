#!/usr/bin/env python3
"""
测试CapCut HTTP MCP Bridge
验证与Dify的兼容性
"""

import requests
import json
import time

def test_health_check():
    """测试健康检查"""
    print("=== 测试健康检查 ===")
    try:
        response = requests.get("http://localhost:8083/health", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_mcp_initialize():
    """测试MCP初始化"""
    print("\n=== 测试MCP初始化 ===")
    try:
        # 模拟Dify发送的初始化请求
        payload = {
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "dify",
                    "version": "1.0.0"
                }
            }
        }
        
        response = requests.post(
            "http://localhost:8083/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 验证响应格式
        required_fields = ["protocolVersion", "capabilities", "serverInfo"]
        has_all_fields = all(field in result for field in required_fields)
        
        print(f"包含所有必需字段: {has_all_fields}")
        return response.status_code == 200 and has_all_fields
        
    except Exception as e:
        print(f"MCP初始化测试失败: {e}")
        return False

def test_mcp_list_tools():
    """测试工具列表"""
    print("\n=== 测试工具列表 ===")
    try:
        payload = {
            "method": "tools/list",
            "params": {}
        }
        
        response = requests.post(
            "http://localhost:8083/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"工具数量: {len(result.get('tools', []))}")
        
        # 显示工具名称
        tools = result.get('tools', [])
        tool_names = [tool.get('name') for tool in tools]
        print(f"工具列表: {tool_names}")
        
        return response.status_code == 200 and len(tools) > 0
        
    except Exception as e:
        print(f"工具列表测试失败: {e}")
        return False

def test_mcp_call_tool():
    """测试工具调用"""
    print("\n=== 测试工具调用 ===")
    try:
        payload = {
            "method": "tools/call",
            "params": {
                "name": "health_check",
                "arguments": {}
            }
        }
        
        response = requests.post(
            "http://localhost:8083/mcp",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 验证响应格式
        has_content = "content" in result
        print(f"包含content字段: {has_content}")
        
        return response.status_code == 200 and has_content
        
    except Exception as e:
        print(f"工具调用测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试CapCut HTTP MCP Bridge...")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(2)
    
    tests = [
        ("健康检查", test_health_check),
        ("MCP初始化", test_mcp_initialize),
        ("工具列表", test_mcp_list_tools),
        ("工具调用", test_mcp_call_tool)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{test_name}: {'✅ 通过' if result else '❌ 失败'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"{test_name}: ❌ 异常 - {e}")
    
    print("\n=== 测试总结 ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！HTTP MCP Bridge与Dify兼容")
    else:
        print("⚠️  部分测试失败，需要进一步调试")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)