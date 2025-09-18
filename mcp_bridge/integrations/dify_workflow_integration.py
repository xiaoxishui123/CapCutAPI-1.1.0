#!/usr/bin/env python3
"""
Dify 工作流集成实现

这个模块提供了与 Dify 工作流平台的集成功能，
包括 MCP 服务器注册、工作流节点配置和数据流处理。

作者：AI Assistant
版本：v1.0.0
更新时间：2025年1月14日
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import requests
from urllib.parse import urljoin, urlparse
import yaml

from ..core.mcp_client import MCPClient, MCPClientPool
from ..core.models import ServiceEndpoint


logger = logging.getLogger(__name__)


@dataclass
class DifyWorkflowNode:
    """Dify 工作流节点配置"""
    id: str
    type: str
    name: str
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    position: Dict[str, float]
    config: Dict[str, Any] = None


@dataclass
class DifyWorkflowTemplate:
    """Dify 工作流模板"""
    name: str
    description: str
    version: str
    nodes: List[DifyWorkflowNode]
    connections: List[Dict[str, Any]]
    variables: Dict[str, Any] = None


class DifyMCPIntegration:
    """
    Dify MCP 集成管理器
    
    负责管理 CapCut API MCP 服务器与 Dify 工作流的集成
    """
    
    def __init__(
        self,
        dify_api_base_url: str = "http://localhost:5001",
        dify_api_key: str = "",
        mcp_server_url: str = "ws://localhost:8080"
    ):
        """
        初始化 Dify MCP 集成
        
        Args:
            dify_api_base_url: Dify API 基础 URL
            dify_api_key: Dify API 密钥
            mcp_server_url: MCP 服务器 URL
        """
        self.dify_api_base_url = dify_api_base_url.rstrip('/')
        self.dify_api_key = dify_api_key
        self.mcp_server_url = mcp_server_url
        
        # MCP 客户端
        self.mcp_client: Optional[MCPClient] = None
        
        # 集成状态
        self.is_connected = False
        self.registered_tools = []
        
        # 统计信息
        self.stats = {
            'workflows_created': 0,
            'tools_registered': 0,
            'api_calls': 0,
            'errors': 0
        }
    
    async def initialize(self) -> bool:
        """
        初始化集成
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 连接到 MCP 服务器
            endpoint = ServiceEndpoint(
                name="capcut_mcp",
                url=self.mcp_server_url,
                description="CapCut API MCP 服务器"
            )
            
            self.mcp_client = MCPClient(endpoint)
            await self.mcp_client.connect()
            
            if not self.mcp_client.is_connected:
                logger.error("无法连接到 MCP 服务器")
                return False
            
            # 获取可用工具
            tools = await self.mcp_client.call_method("tools/list")
            self.registered_tools = tools.get("tools", [])
            
            logger.info(f"已连接到 MCP 服务器，发现 {len(self.registered_tools)} 个工具")
            
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"初始化集成失败: {e}")
            return False
    
    async def disconnect(self):
        """断开集成连接"""
        if self.mcp_client:
            await self.mcp_client.disconnect()
        self.is_connected = False
    
    def create_video_generation_workflow(
        self,
        workflow_name: str = "CapCut 视频生成工作流"
    ) -> DifyWorkflowTemplate:
        """
        创建视频生成工作流模板
        
        Args:
            workflow_name: 工作流名称
            
        Returns:
            DifyWorkflowTemplate: 工作流模板
        """
        nodes = [
            # 开始节点
            DifyWorkflowNode(
                id="start",
                type="start",
                name="开始",
                description="工作流开始节点",
                inputs={},
                outputs={
                    "project_name": {"type": "string", "description": "项目名称"},
                    "video_content": {"type": "string", "description": "视频内容描述"},
                    "style_preference": {"type": "string", "description": "风格偏好"}
                },
                position={"x": 100, "y": 100}
            ),
            
            # 内容分析节点
            DifyWorkflowNode(
                id="content_analysis",
                type="llm",
                name="内容分析",
                description="分析视频内容需求",
                inputs={
                    "content": {"from": "start.video_content"}
                },
                outputs={
                    "video_script": {"type": "string", "description": "视频脚本"},
                    "scene_list": {"type": "array", "description": "场景列表"},
                    "audio_requirements": {"type": "object", "description": "音频需求"}
                },
                position={"x": 300, "y": 100},
                config={
                    "model": "gpt-3.5-turbo",
                    "prompt": """
分析以下视频内容需求，生成详细的制作方案：

内容描述：{{content}}

请输出：
1. 详细的视频脚本
2. 场景分解列表
3. 音频和配乐需求
4. 视觉效果建议

输出格式为 JSON。
"""
                }
            ),
            
            # 创建 CapCut 项目节点
            DifyWorkflowNode(
                id="create_capcut_project",
                type="tool",
                name="创建 CapCut 项目",
                description="创建新的 CapCut 草稿项目",
                inputs={
                    "project_name": {"from": "start.project_name"}
                },
                outputs={
                    "draft_id": {"type": "string", "description": "草稿 ID"}
                },
                position={"x": 500, "y": 100},
                config={
                    "tool_name": "create_draft",
                    "tool_parameters": {
                        "project_name": "{{project_name}}",
                        "resolution": "1920x1080",
                        "fps": 30
                    }
                }
            ),
            
            # 添加文本内容节点
            DifyWorkflowNode(
                id="add_text_content",
                type="tool",
                name="添加文本内容",
                description="向项目添加文本和字幕",
                inputs={
                    "draft_id": {"from": "create_capcut_project.draft_id"},
                    "video_script": {"from": "content_analysis.video_script"}
                },
                outputs={
                    "text_added": {"type": "boolean", "description": "文本是否添加成功"}
                },
                position={"x": 700, "y": 100},
                config={
                    "tool_name": "add_text",
                    "tool_parameters": {
                        "draft_id": "{{draft_id}}",
                        "text": "{{video_script}}",
                        "font_type": "default",
                        "font_size": 24,
                        "color": "#FFFFFF"
                    }
                }
            ),
            
            # 添加视觉效果节点
            DifyWorkflowNode(
                id="add_visual_effects",
                type="tool",
                name="添加视觉效果",
                description="添加转场和特效",
                inputs={
                    "draft_id": {"from": "create_capcut_project.draft_id"},
                    "style_preference": {"from": "start.style_preference"}
                },
                outputs={
                    "effects_added": {"type": "boolean", "description": "效果是否添加成功"}
                },
                position={"x": 900, "y": 100},
                config={
                    "tool_name": "add_effect",
                    "tool_parameters": {
                        "draft_id": "{{draft_id}}",
                        "effect_type": "transition",
                        "duration": 2
                    }
                }
            ),
            
            # 保存项目节点
            DifyWorkflowNode(
                id="save_project",
                type="tool",
                name="保存项目",
                description="保存并导出视频项目",
                inputs={
                    "draft_id": {"from": "create_capcut_project.draft_id"}
                },
                outputs={
                    "output_path": {"type": "string", "description": "输出文件路径"},
                    "project_saved": {"type": "boolean", "description": "项目是否保存成功"}
                },
                position={"x": 1100, "y": 100},
                config={
                    "tool_name": "save_draft",
                    "tool_parameters": {
                        "draft_id": "{{draft_id}}",
                        "quality": "high"
                    }
                }
            ),
            
            # 结束节点
            DifyWorkflowNode(
                id="end",
                type="end",
                name="结束",
                description="工作流结束节点",
                inputs={
                    "output_path": {"from": "save_project.output_path"},
                    "project_saved": {"from": "save_project.project_saved"}
                },
                outputs={},
                position={"x": 1300, "y": 100}
            )
        ]
        
        # 定义节点连接
        connections = [
            {"source": "start", "target": "content_analysis"},
            {"source": "start", "target": "create_capcut_project"},
            {"source": "content_analysis", "target": "add_text_content"},
            {"source": "create_capcut_project", "target": "add_text_content"},
            {"source": "create_capcut_project", "target": "add_visual_effects"},
            {"source": "add_text_content", "target": "save_project"},
            {"source": "add_visual_effects", "target": "save_project"},
            {"source": "save_project", "target": "end"}
        ]
        
        # 定义工作流变量
        variables = {
            "project_name": {
                "type": "string",
                "description": "视频项目名称",
                "default": "我的视频项目"
            },
            "video_content": {
                "type": "string",
                "description": "视频内容描述",
                "required": True
            },
            "style_preference": {
                "type": "string",
                "description": "视频风格偏好",
                "options": ["简约", "动感", "商务", "创意"],
                "default": "简约"
            }
        }
        
        return DifyWorkflowTemplate(
            name=workflow_name,
            description="使用 CapCut API 自动生成视频的工作流",
            version="1.0.0",
            nodes=nodes,
            connections=connections,
            variables=variables
        )
    
    def create_batch_video_workflow(
        self,
        workflow_name: str = "CapCut 批量视频处理工作流"
    ) -> DifyWorkflowTemplate:
        """
        创建批量视频处理工作流模板
        
        Args:
            workflow_name: 工作流名称
            
        Returns:
            DifyWorkflowTemplate: 工作流模板
        """
        nodes = [
            # 开始节点
            DifyWorkflowNode(
                id="start",
                type="start",
                name="开始",
                description="批量处理开始",
                inputs={},
                outputs={
                    "video_list": {"type": "array", "description": "视频文件列表"},
                    "processing_config": {"type": "object", "description": "处理配置"}
                },
                position={"x": 100, "y": 100}
            ),
            
            # 循环处理节点
            DifyWorkflowNode(
                id="process_loop",
                type="loop",
                name="循环处理",
                description="循环处理每个视频",
                inputs={
                    "items": {"from": "start.video_list"}
                },
                outputs={
                    "current_video": {"type": "string", "description": "当前处理的视频"},
                    "results": {"type": "array", "description": "处理结果列表"}
                },
                position={"x": 300, "y": 100}
            ),
            
            # 创建项目节点
            DifyWorkflowNode(
                id="create_project_batch",
                type="tool",
                name="创建项目",
                description="为每个视频创建项目",
                inputs={
                    "video_path": {"from": "process_loop.current_video"}
                },
                outputs={
                    "draft_id": {"type": "string", "description": "草稿 ID"}
                },
                position={"x": 500, "y": 100},
                config={
                    "tool_name": "create_draft",
                    "tool_parameters": {
                        "project_name": "批量处理_{{video_path}}",
                        "resolution": "1920x1080",
                        "fps": 30
                    }
                }
            ),
            
            # 添加视频节点
            DifyWorkflowNode(
                id="add_video_batch",
                type="tool",
                name="添加视频",
                description="添加视频到项目",
                inputs={
                    "draft_id": {"from": "create_project_batch.draft_id"},
                    "video_path": {"from": "process_loop.current_video"}
                },
                outputs={
                    "video_added": {"type": "boolean", "description": "视频是否添加成功"}
                },
                position={"x": 700, "y": 100},
                config={
                    "tool_name": "add_video",
                    "tool_parameters": {
                        "draft_id": "{{draft_id}}",
                        "video_path": "{{video_path}}"
                    }
                }
            ),
            
            # 应用效果节点
            DifyWorkflowNode(
                id="apply_effects_batch",
                type="tool",
                name="应用效果",
                description="应用统一的视觉效果",
                inputs={
                    "draft_id": {"from": "create_project_batch.draft_id"},
                    "processing_config": {"from": "start.processing_config"}
                },
                outputs={
                    "effects_applied": {"type": "boolean", "description": "效果是否应用成功"}
                },
                position={"x": 900, "y": 100},
                config={
                    "tool_name": "add_effect",
                    "tool_parameters": {
                        "draft_id": "{{draft_id}}",
                        "effect_type": "{{processing_config.effect_type}}",
                        "duration": "{{processing_config.effect_duration}}"
                    }
                }
            ),
            
            # 保存项目节点
            DifyWorkflowNode(
                id="save_project_batch",
                type="tool",
                name="保存项目",
                description="保存处理后的项目",
                inputs={
                    "draft_id": {"from": "create_project_batch.draft_id"}
                },
                outputs={
                    "output_path": {"type": "string", "description": "输出路径"}
                },
                position={"x": 1100, "y": 100},
                config={
                    "tool_name": "save_draft",
                    "tool_parameters": {
                        "draft_id": "{{draft_id}}",
                        "quality": "high"
                    }
                }
            ),
            
            # 结果汇总节点
            DifyWorkflowNode(
                id="summarize_results",
                type="code",
                name="结果汇总",
                description="汇总所有处理结果",
                inputs={
                    "results": {"from": "process_loop.results"}
                },
                outputs={
                    "summary": {"type": "object", "description": "处理结果摘要"}
                },
                position={"x": 1300, "y": 100},
                config={
                    "code": """
def main(results):
    total = len(results)
    successful = sum(1 for r in results if r.get('success', False))
    failed = total - successful
    
    return {
        'total_processed': total,
        'successful': successful,
        'failed': failed,
        'success_rate': successful / total if total > 0 else 0,
        'results': results
    }
"""
                }
            ),
            
            # 结束节点
            DifyWorkflowNode(
                id="end",
                type="end",
                name="结束",
                description="批量处理结束",
                inputs={
                    "summary": {"from": "summarize_results.summary"}
                },
                outputs={},
                position={"x": 1500, "y": 100}
            )
        ]
        
        # 定义连接
        connections = [
            {"source": "start", "target": "process_loop"},
            {"source": "process_loop", "target": "create_project_batch"},
            {"source": "create_project_batch", "target": "add_video_batch"},
            {"source": "add_video_batch", "target": "apply_effects_batch"},
            {"source": "apply_effects_batch", "target": "save_project_batch"},
            {"source": "save_project_batch", "target": "process_loop"},
            {"source": "process_loop", "target": "summarize_results"},
            {"source": "summarize_results", "target": "end"}
        ]
        
        return DifyWorkflowTemplate(
            name=workflow_name,
            description="批量处理多个视频文件的工作流",
            version="1.0.0",
            nodes=nodes,
            connections=connections
        )
    
    async def register_mcp_server_to_dify(self) -> bool:
        """
        向 Dify 注册 MCP 服务器
        
        Returns:
            bool: 注册是否成功
        """
        try:
            # 构建注册请求
            registration_data = {
                "name": "CapCut API MCP Server",
                "description": "CapCut 视频编辑 API 的 MCP 服务器",
                "url": self.mcp_server_url,
                "type": "mcp",
                "capabilities": {
                    "tools": True,
                    "resources": True
                },
                "config": {
                    "timeout": 30,
                    "retry_count": 3
                }
            }
            
            # 发送注册请求到 Dify
            headers = {
                "Authorization": f"Bearer {self.dify_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.dify_api_base_url}/api/v1/mcp-servers",
                json=registration_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info("MCP 服务器已成功注册到 Dify")
                self.stats['tools_registered'] = len(self.registered_tools)
                return True
            else:
                logger.error(f"注册 MCP 服务器失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"注册 MCP 服务器异常: {e}")
            return False
    
    async def deploy_workflow_template(
        self,
        template: DifyWorkflowTemplate,
        app_name: str = None
    ) -> Optional[str]:
        """
        部署工作流模板到 Dify
        
        Args:
            template: 工作流模板
            app_name: 应用名称
            
        Returns:
            Optional[str]: 部署成功返回应用 ID，失败返回 None
        """
        try:
            # 构建应用数据
            app_data = {
                "name": app_name or template.name,
                "description": template.description,
                "mode": "workflow",
                "workflow": {
                    "nodes": [asdict(node) for node in template.nodes],
                    "connections": template.connections,
                    "variables": template.variables or {}
                }
            }
            
            # 发送部署请求
            headers = {
                "Authorization": f"Bearer {self.dify_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.dify_api_base_url}/api/v1/apps",
                json=app_data,
                headers=headers,
                timeout=60
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                app_id = result.get("id")
                logger.info(f"工作流模板已成功部署: {app_id}")
                self.stats['workflows_created'] += 1
                return app_id
            else:
                logger.error(f"部署工作流模板失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"部署工作流模板异常: {e}")
            return None
    
    async def test_integration(self) -> Dict[str, Any]:
        """
        测试集成功能
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        test_results = {
            "mcp_connection": False,
            "tools_available": False,
            "dify_api_accessible": False,
            "workflow_creation": False,
            "errors": []
        }
        
        try:
            # 测试 MCP 连接
            if self.mcp_client and self.mcp_client.is_connected:
                test_results["mcp_connection"] = True
                
                # 测试工具可用性
                tools = await self.mcp_client.call_method("tools/list")
                if tools and len(tools.get("tools", [])) > 0:
                    test_results["tools_available"] = True
            
            # 测试 Dify API 可访问性
            headers = {"Authorization": f"Bearer {self.dify_api_key}"}
            response = requests.get(
                f"{self.dify_api_base_url}/api/v1/apps",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                test_results["dify_api_accessible"] = True
            
            # 测试工作流创建
            template = self.create_video_generation_workflow("测试工作流")
            if template and len(template.nodes) > 0:
                test_results["workflow_creation"] = True
            
        except Exception as e:
            test_results["errors"].append(str(e))
            logger.error(f"集成测试异常: {e}")
        
        return test_results
    
    def export_workflow_config(
        self,
        template: DifyWorkflowTemplate,
        output_path: str
    ):
        """
        导出工作流配置到文件
        
        Args:
            template: 工作流模板
            output_path: 输出文件路径
        """
        try:
            config_data = {
                "workflow": asdict(template),
                "mcp_server": {
                    "url": self.mcp_server_url,
                    "tools": self.registered_tools
                },
                "export_time": time.time(),
                "version": "1.0.0"
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if output_path.endswith('.yaml') or output_path.endswith('.yml'):
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"工作流配置已导出到: {output_path}")
            
        except Exception as e:
            logger.error(f"导出工作流配置失败: {e}")
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """获取集成统计信息"""
        return {
            **self.stats,
            'is_connected': self.is_connected,
            'mcp_server_url': self.mcp_server_url,
            'dify_api_base_url': self.dify_api_base_url,
            'registered_tools_count': len(self.registered_tools),
            'mcp_client_stats': self.mcp_client.get_stats() if self.mcp_client else {}
        }


async def main():
    """主函数 - 演示集成功能"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dify MCP 集成管理器")
    parser.add_argument("--dify-api", default="http://localhost:5001", help="Dify API 基础 URL")
    parser.add_argument("--dify-key", default="", help="Dify API 密钥")
    parser.add_argument("--mcp-server", default="ws://localhost:8080", help="MCP 服务器 URL")
    parser.add_argument("--action", choices=["test", "register", "deploy"], default="test", help="执行的操作")
    parser.add_argument("--export-config", help="导出工作流配置文件路径")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建集成管理器
    integration = DifyMCPIntegration(
        dify_api_base_url=args.dify_api,
        dify_api_key=args.dify_key,
        mcp_server_url=args.mcp_server
    )
    
    try:
        # 初始化集成
        if not await integration.initialize():
            logger.error("集成初始化失败")
            return
        
        if args.action == "test":
            # 测试集成
            results = await integration.test_integration()
            print("集成测试结果:")
            print(json.dumps(results, ensure_ascii=False, indent=2))
            
        elif args.action == "register":
            # 注册 MCP 服务器
            success = await integration.register_mcp_server_to_dify()
            print(f"MCP 服务器注册: {'成功' if success else '失败'}")
            
        elif args.action == "deploy":
            # 部署工作流模板
            template = integration.create_video_generation_workflow()
            app_id = await integration.deploy_workflow_template(template)
            print(f"工作流部署: {'成功' if app_id else '失败'}")
            if app_id:
                print(f"应用 ID: {app_id}")
        
        # 导出配置
        if args.export_config:
            template = integration.create_video_generation_workflow()
            integration.export_workflow_config(template, args.export_config)
        
        # 显示统计信息
        stats = integration.get_integration_stats()
        print("\n集成统计信息:")
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        await integration.disconnect()


if __name__ == "__main__":
    asyncio.run(main())