#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Bridge与Dify工作流集成测试脚本
测试优化版短视频生成工作流的各个组件
"""

import json
import requests
import time
import os
import yaml
from typing import Dict, Any, List

class WorkflowIntegrationTester:
    """工作流集成测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.mcp_bridge_url = "http://localhost:8082"
        self.capcut_api_url = "http://localhost:9000"
        self.dify_api_url = "http://localhost:8080"
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: Dict = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   详情: {json.dumps(details, ensure_ascii=False, indent=2)}")
        print()

    def test_service_connectivity(self) -> bool:
        """测试服务连通性"""
        print("🔍 测试服务连通性...")
        
        # 测试MCP Bridge
        try:
            response = requests.get(f"{self.mcp_bridge_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.log_test(
                    "MCP Bridge连通性",
                    True,
                    "MCP Bridge服务正常",
                    {"status": health_data.get("status"), "services": list(health_data.get("services", {}).keys())}
                )
            else:
                self.log_test("MCP Bridge连通性", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("MCP Bridge连通性", False, f"连接失败: {str(e)}")
            return False
        
        # 测试CapCut API
        try:
            response = requests.get(f"{self.capcut_api_url}/get_intro_animation_types", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "CapCut API连通性",
                    True,
                    "CapCut API服务正常",
                    {"success": data.get("success"), "animation_types_count": len(data.get("data", []))}
                )
            else:
                self.log_test("CapCut API连通性", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("CapCut API连通性", False, f"连接失败: {str(e)}")
            return False
        
        # 测试Dify API
        try:
            response = requests.get(f"{self.dify_api_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Dify API连通性", True, "Dify API服务正常")
            else:
                self.log_test("Dify API连通性", False, f"HTTP状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Dify API连通性", False, f"连接失败: {str(e)}")
            return False
        
        return True

    def test_mcp_bridge_operations(self) -> bool:
        """测试MCP Bridge核心操作"""
        print("🔧 测试MCP Bridge核心操作...")
        
        # 测试创建草稿
        try:
            create_draft_payload = {
                "id": "test-draft-1",
                "method": "create_draft",
                "params": {
                    "title": "测试短视频项目",
                    "width": 1080,
                    "height": 1920
                }
            }
            
            response = requests.post(
                f"{self.mcp_bridge_url}/mcp",
                json=create_draft_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("error") is None and result.get("result", {}).get("status") == "success":
                    self.log_test(
                        "MCP创建草稿",
                        True,
                        "草稿创建成功",
                        {"result": result.get("result")}
                    )
                    return True
                else:
                    self.log_test("MCP创建草稿", False, "MCP调用失败", result)
                    return False
            else:
                self.log_test("MCP创建草稿", False, f"HTTP状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("MCP创建草稿", False, f"操作失败: {str(e)}")
            return False

    def test_http_fallback(self) -> bool:
        """测试HTTP降级机制"""
        print("🔄 测试HTTP降级机制...")
        
        # 测试CapCut HTTP API直接调用
        try:
            create_draft_payload = {
                "title": "HTTP降级测试项目",
                "width": 1080,
                "height": 1920
            }
            
            response = requests.post(
                f"{self.capcut_api_url}/create_draft",
                json=create_draft_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.log_test(
                        "HTTP降级机制",
                        True,
                        "HTTP直接调用成功",
                        {"draft_id": result.get("draft_id")}
                    )
                    return True
                else:
                    self.log_test("HTTP降级机制", False, "API返回失败", result)
                    return False
            else:
                self.log_test("HTTP降级机制", False, f"HTTP状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("HTTP降级机制", False, f"降级失败: {str(e)}")
            return False

    def test_workflow_configuration(self) -> bool:
        """测试工作流配置文件"""
        print("📋 测试工作流配置文件...")
        
        try:
            # 读取工作流配置文件
            workflow_path = "/home/dify/优化版短视频工作流.yml"
            if not os.path.exists(workflow_path):
                self.log_test("工作流配置文件", False, "配置文件不存在")
                return False
            
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_config = yaml.safe_load(f)
            
            # 验证配置结构
            required_sections = ['app', 'workflow']
            for section in required_sections:
                if section not in workflow_config:
                    self.log_test("工作流配置文件", False, f"缺少必需的配置节: {section}")
                    return False
            
            # 验证节点数量
            nodes = workflow_config.get('workflow', {}).get('graph', {}).get('nodes', [])
            if len(nodes) != 11:
                self.log_test("工作流配置文件", False, f"节点数量不正确，期望11个，实际{len(nodes)}个")
                return False
            
            # 验证环境变量
            env_vars = workflow_config.get('workflow', {}).get('environment_variables', [])
            required_env_vars = ['MCP_BRIDGE_URL', 'CAPCUT_API_URL', 'ENABLE_HTTP_FALLBACK']
            
            env_var_names = [var.get('name') for var in env_vars]
            missing_vars = [var for var in required_env_vars if var not in env_var_names]
            
            if missing_vars:
                self.log_test("工作流配置文件", False, f"缺少环境变量: {missing_vars}")
                return False
            
            self.log_test(
                "工作流配置文件",
                True,
                "配置文件结构正确",
                {
                    "nodes_count": len(nodes),
                    "env_vars_count": len(env_vars),
                    "app_name": workflow_config.get('app', {}).get('name')
                }
            )
            return True
            
        except Exception as e:
            self.log_test("工作流配置文件", False, f"配置验证失败: {str(e)}")
            return False

    def test_performance_metrics(self) -> bool:
        """测试性能指标"""
        print("⚡ 测试性能指标...")
        
        # 测试MCP Bridge响应时间
        try:
            start_time = time.time()
            response = requests.get(f"{self.mcp_bridge_url}/health", timeout=5)
            mcp_response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            if response.status_code == 200:
                self.log_test(
                    "MCP Bridge响应时间",
                    mcp_response_time < 1000,  # 期望小于1秒
                    f"响应时间: {mcp_response_time:.2f}ms",
                    {"response_time_ms": mcp_response_time}
                )
            else:
                self.log_test("MCP Bridge响应时间", False, "健康检查失败")
                return False
                
        except Exception as e:
            self.log_test("MCP Bridge响应时间", False, f"测试失败: {str(e)}")
            return False
        
        # 测试CapCut API响应时间
        try:
            start_time = time.time()
            response = requests.get(f"{self.capcut_api_url}/get_intro_animation_types", timeout=5)
            capcut_response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                self.log_test(
                    "CapCut API响应时间",
                    capcut_response_time < 2000,  # 期望小于2秒
                    f"响应时间: {capcut_response_time:.2f}ms",
                    {"response_time_ms": capcut_response_time}
                )
            else:
                self.log_test("CapCut API响应时间", False, "API调用失败")
                return False
                
        except Exception as e:
            self.log_test("CapCut API响应时间", False, f"测试失败: {str(e)}")
            return False
        
        return True

    def test_error_handling(self) -> bool:
        """测试错误处理机制"""
        print("🛡️ 测试错误处理机制...")
        
        # 测试无效请求处理
        try:
            invalid_payload = {
                "id": "test-error-1",
                "method": "invalid_method",
                "params": {}
            }
            
            response = requests.post(
                f"{self.mcp_bridge_url}/mcp",
                json=invalid_payload,
                timeout=5
            )
            
            # 期望返回错误信息而不是崩溃
            if response.status_code == 200:
                result = response.json()
                if result.get("error") is not None:
                    self.log_test(
                        "错误处理机制",
                        True,
                        "无效请求得到正确的错误响应",
                        {"error": result.get("error")}
                    )
                else:
                    self.log_test("错误处理机制", False, "期望返回错误但没有错误信息", result)
                    return False
            elif response.status_code in [400, 404, 500]:
                self.log_test(
                    "错误处理机制",
                    True,
                    "无效请求得到正确的HTTP错误响应",
                    {"status_code": response.status_code}
                )
            else:
                self.log_test("错误处理机制", False, f"意外的状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("错误处理机制", False, f"测试失败: {str(e)}")
            return False
        
        return True

    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{success_rate:.1f}%",
                "test_time": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "test_results": self.test_results,
            "recommendations": []
        }
        
        # 生成建议
        if success_rate < 80:
            report["recommendations"].append("集成成功率较低，建议检查服务配置和网络连接")
        
        if failed_tests > 0:
            failed_test_names = [r["test_name"] for r in self.test_results if not r["success"]]
            report["recommendations"].append(f"以下测试失败，需要重点关注: {', '.join(failed_test_names)}")
        
        if success_rate >= 95:
            report["recommendations"].append("集成测试表现优秀，可以投入生产使用")
        elif success_rate >= 80:
            report["recommendations"].append("集成基本稳定，建议进行更多测试后投入使用")
        
        return report

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 开始MCP Bridge与Dify工作流集成测试\n")
        print("=" * 60)
        
        # 执行所有测试
        tests = [
            self.test_service_connectivity,
            self.test_mcp_bridge_operations,
            self.test_http_fallback,
            self.test_workflow_configuration,
            self.test_performance_metrics,
            self.test_error_handling
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_test(test_func.__name__, False, f"测试执行异常: {str(e)}")
            
            time.sleep(1)  # 测试间隔
        
        # 生成报告
        report = self.generate_test_report()
        
        print("=" * 60)
        print("📊 测试报告摘要:")
        print(f"   总测试数: {report['summary']['total_tests']}")
        print(f"   通过测试: {report['summary']['passed_tests']}")
        print(f"   失败测试: {report['summary']['failed_tests']}")
        print(f"   成功率: {report['summary']['success_rate']}")
        print(f"   测试时间: {report['summary']['test_time']}")
        
        if report["recommendations"]:
            print("\n💡 建议:")
            for rec in report["recommendations"]:
                print(f"   • {rec}")
        
        return report

def main():
    """主函数"""
    tester = WorkflowIntegrationTester()
    report = tester.run_all_tests()
    
    # 保存测试报告
    report_path = "/home/dify/integration_test_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细测试报告已保存到: {report_path}")
    
    # 返回成功率作为退出码
    success_rate = float(report['summary']['success_rate'].rstrip('%'))
    if success_rate >= 80:
        print("\n✅ 集成测试通过！")
        return 0
    else:
        print("\n❌ 集成测试失败！")
        return 1

if __name__ == "__main__":
    exit(main())