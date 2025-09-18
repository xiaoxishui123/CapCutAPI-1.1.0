#!/usr/bin/env python3
"""
服务连接测试脚本
测试CapCut API和MCP Bridge服务的连接状态
"""

import requests
import json
import sys
from datetime import datetime

def test_capcut_api():
    """测试CapCut API服务"""
    print("🔍 测试CapCut API服务 (端口9000)...")
    try:
        response = requests.get("http://localhost:9000/get_intro_animation_types", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ CapCut API服务正常 - 返回{len(data.get('data', []))}个入场动画类型")
            return True
        else:
            print(f"❌ CapCut API服务异常 - 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ CapCut API服务连接失败: {e}")
        return False

def test_mcp_bridge():
    """测试MCP Bridge服务"""
    print("🔍 测试MCP Bridge服务 (端口8082)...")
    try:
        response = requests.get("http://localhost:8082/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            print(f"✅ MCP Bridge服务正常 - 状态: {status}")
            
            # 显示各个服务的状态
            services = data.get('services', {})
            for service_name, service_info in services.items():
                service_status = service_info.get('status', 'unknown')
                print(f"   - {service_name}: {service_status}")
            
            return True
        else:
            print(f"❌ MCP Bridge服务异常 - 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ MCP Bridge服务连接失败: {e}")
        return False

def test_mcp_bridge_mcp_endpoint():
    """测试MCP Bridge的MCP端点功能"""
    print("🔍 测试MCP Bridge的MCP端点功能...")
    try:
        # 构造MCP请求
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "capcut_create_draft",
                "arguments": {
                    "draft_name": "测试草稿",
                    "description": "MCP Bridge测试"
                }
            },
            "id": 1
        }
        
        # 发送MCP请求到Bridge
        response = requests.post(
            "http://localhost:8082/mcp", 
            json=mcp_request,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data or "error" in data:
                print(f"✅ MCP Bridge MCP端点正常 - 响应格式正确")
                return True
            else:
                print(f"❌ MCP Bridge MCP端点异常 - 响应格式错误: {data}")
                return False
        else:
            print(f"❌ MCP Bridge MCP端点异常 - 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ MCP Bridge MCP端点测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print(f"🚀 服务连接测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    
    # 测试CapCut API
    results.append(test_capcut_api())
    print()
    
    # 测试MCP Bridge
    results.append(test_mcp_bridge())
    print()
    
    # 测试MCP Bridge MCP端点功能
    results.append(test_mcp_bridge_mcp_endpoint())
    print()
    
    # 总结
    print("=" * 60)
    print("📊 测试结果总结:")
    print("=" * 60)
    
    test_names = ["CapCut API", "MCP Bridge", "MCP Bridge MCP端点"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 正常" if result else "❌ 异常"
        print(f"{i+1}. {name}: {status}")
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 所有服务测试通过！")
        print("\n📝 服务访问地址:")
        print("   - CapCut API: http://localhost:9000")
        print("   - MCP Bridge: http://localhost:8082")
        print("   - MCP Bridge健康检查: http://localhost:8082/health")
        print("   - MCP Bridge MCP端点: http://localhost:8082/mcp")
    else:
        print("\n⚠️  部分服务测试失败，请检查服务状态")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())