#!/usr/bin/env python3
"""
CapCut MCP Bridge 测试脚本
验证修复后的MCP服务是否正确返回InitializeResult格式
"""

import json
import requests
import time
import sys

def test_mcp_bridge():
    """测试MCP Bridge服务"""
    
    base_url = "http://localhost:8082"
    
    print("=== CapCut MCP Bridge 测试 ===")
    print(f"测试服务地址: {base_url}")
    print()
    
    # 1. 测试健康检查
    print("1. 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 健康检查通过: {health_data['status']}")
            print(f"   服务: {health_data['service']}")
            print(f"   版本: {health_data['version']}")
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")
        return False
    
    print()
    
    # 2. 测试MCP初始化
    print("2. 测试MCP初始化...")
    
    # 构造标准的MCP初始化请求
    initialize_request = {
        "jsonrpc": "2.0",
        "id": "test-init-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "Dify Test Client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/mcp",
            json=initialize_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            init_result = response.json()
            print("✅ MCP初始化成功")
            print(f"   响应格式: {json.dumps(init_result, ensure_ascii=False, indent=2)}")
            
            # 验证必需字段
            result = init_result.get("result", {})
            required_fields = ["protocolVersion", "capabilities", "serverInfo"]
            missing_fields = []
            
            for field in required_fields:
                if field not in result:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 缺少必需字段: {missing_fields}")
                return False
            else:
                print("✅ 所有必需字段都存在")
                print(f"   协议版本: {result['protocolVersion']}")
                print(f"   服务器信息: {result['serverInfo']}")
                print(f"   能力: {list(result['capabilities'].keys())}")
                
        else:
            print(f"❌ MCP初始化失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ MCP初始化失败: {str(e)}")
        return False
    
    print()
    
    # 3. 测试工具列表
    print("3. 测试工具列表...")
    
    tools_request = {
        "jsonrpc": "2.0",
        "id": "test-tools-1", 
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(
            f"{base_url}/mcp",
            json=tools_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            tools_result = response.json()
            tools = tools_result.get("result", {}).get("tools", [])
            print(f"✅ 工具列表获取成功，共 {len(tools)} 个工具")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
        else:
            print(f"❌ 工具列表获取失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 工具列表获取失败: {str(e)}")
        return False
    
    print()
    print("🎉 所有测试通过！MCP Bridge服务运行正常")
    return True

def test_dify_compatibility():
    """测试与Dify的兼容性"""
    
    print("\n=== Dify兼容性测试 ===")
    
    # 模拟Dify发送的初始化请求
    dify_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize", 
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "Dify",
                "version": "0.6.0"
            }
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8082/mcp",
            json=dify_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 检查是否符合Dify期望的格式
            if "result" in result:
                init_result = result["result"]
                if all(field in init_result for field in ["protocolVersion", "capabilities", "serverInfo"]):
                    print("✅ 与Dify完全兼容")
                    print("   现在可以在Dify中使用以下配置:")
                    print("   MCP服务URL: http://localhost:8082/mcp")
                    print("   或者如果从外部访问: http://8.148.70.18:8082/mcp")
                    return True
                else:
                    print("❌ 响应格式不符合Dify要求")
                    return False
            else:
                print("❌ 响应缺少result字段")
                return False
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Dify兼容性测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试CapCut MCP Bridge...")
    print("请确保MCP Bridge服务已启动 (运行 ./start_capcut_mcp_bridge.sh)")
    print()
    
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(2)
    
    # 运行测试
    if test_mcp_bridge():
        test_dify_compatibility()
    else:
        print("\n❌ 基础测试失败，请检查服务状态")
        sys.exit(1)