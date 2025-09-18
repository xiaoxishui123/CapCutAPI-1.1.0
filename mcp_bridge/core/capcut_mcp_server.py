#!/usr/bin/env python3
"""
CapCut API MCP 服务器实现

这个模块实现了 CapCut API 的 MCP (Model Context Protocol) 服务器，
将 CapCut API 功能封装为 MCP 工具，供 Dify 等 AI 工作流平台调用。

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
import websockets
from websockets.exceptions import ConnectionClosed
import requests
from urllib.parse import urljoin

from .models import MCPRequest, MCPResponse


logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


@dataclass
class MCPResource:
    """MCP 资源定义"""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


class CapCutMCPServer:
    """
    CapCut API MCP 服务器
    
    实现 MCP 协议，将 CapCut API 功能暴露为 MCP 工具
    """
    
    def __init__(
        self,
        capcut_api_base_url: str = "http://localhost:9000",
        host: str = "localhost",
        port: int = 8080
    ):
        """
        初始化 CapCut MCP 服务器
        
        Args:
            capcut_api_base_url: CapCut API 基础 URL
            host: MCP 服务器监听地址
            port: MCP 服务器监听端口
        """
        self.capcut_api_base_url = capcut_api_base_url.rstrip('/')
        self.host = host
        self.port = port
        
        # 服务器状态
        self.is_running = False
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        
        # 统计信息
        self.stats = {
            'clients_connected': 0,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': 0
        }
        
        # 定义可用的工具
        self.tools = self._define_tools()
        
        # 定义可用的资源
        self.resources = self._define_resources()
    
    def _define_tools(self) -> List[MCPTool]:
        """定义 CapCut API 工具"""
        return [
            MCPTool(
                name="get_intro_animation_types",
                description="获取 CapCut 入场动画类型列表",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            MCPTool(
                name="get_outro_animation_types",
                description="获取 CapCut 出场动画类型列表",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            MCPTool(
                name="get_transition_types",
                description="获取 CapCut 转场类型列表",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            MCPTool(
                name="get_mask_types",
                description="获取 CapCut 遮罩类型列表",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            MCPTool(
                name="get_font_types",
                description="获取 CapCut 字体类型列表",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            MCPTool(
                name="create_draft",
                description="创建 CapCut 草稿项目",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "项目名称"
                        },
                        "resolution": {
                            "type": "string",
                            "description": "视频分辨率，如 '1920x1080'",
                            "default": "1920x1080"
                        },
                        "fps": {
                            "type": "integer",
                            "description": "帧率",
                            "default": 30
                        }
                    },
                    "required": ["project_name"]
                }
            ),
            MCPTool(
                name="add_video",
                description="向 CapCut 项目添加视频",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "draft_id": {
                            "type": "string",
                            "description": "草稿 ID"
                        },
                        "video_path": {
                            "type": "string",
                            "description": "视频文件路径"
                        },
                        "start_time": {
                            "type": "number",
                            "description": "开始时间（秒）",
                            "default": 0
                        },
                        "duration": {
                            "type": "number",
                            "description": "持续时间（秒）",
                            "default": -1
                        }
                    },
                    "required": ["draft_id", "video_path"]
                }
            ),
            MCPTool(
                name="add_audio",
                description="向 CapCut 项目添加音频",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "draft_id": {
                            "type": "string",
                            "description": "草稿 ID"
                        },
                        "audio_path": {
                            "type": "string",
                            "description": "音频文件路径"
                        },
                        "start_time": {
                            "type": "number",
                            "description": "开始时间（秒）",
                            "default": 0
                        },
                        "volume": {
                            "type": "number",
                            "description": "音量（0-1）",
                            "default": 1.0
                        }
                    },
                    "required": ["draft_id", "audio_path"]
                }
            ),
            MCPTool(
                name="add_text",
                description="向 CapCut 项目添加文本",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "draft_id": {
                            "type": "string",
                            "description": "草稿 ID"
                        },
                        "text": {
                            "type": "string",
                            "description": "文本内容"
                        },
                        "font_type": {
                            "type": "string",
                            "description": "字体类型"
                        },
                        "font_size": {
                            "type": "integer",
                            "description": "字体大小",
                            "default": 24
                        },
                        "color": {
                            "type": "string",
                            "description": "文本颜色（十六进制）",
                            "default": "#FFFFFF"
                        },
                        "position_x": {
                            "type": "number",
                            "description": "X 坐标",
                            "default": 0.5
                        },
                        "position_y": {
                            "type": "number",
                            "description": "Y 坐标",
                            "default": 0.5
                        },
                        "start_time": {
                            "type": "number",
                            "description": "开始时间（秒）",
                            "default": 0
                        },
                        "duration": {
                            "type": "number",
                            "description": "持续时间（秒）",
                            "default": 5
                        }
                    },
                    "required": ["draft_id", "text", "font_type"]
                }
            ),
            MCPTool(
                name="add_subtitle",
                description="向 CapCut 项目添加字幕",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "draft_id": {
                            "type": "string",
                            "description": "草稿 ID"
                        },
                        "subtitle_text": {
                            "type": "string",
                            "description": "字幕文本"
                        },
                        "start_time": {
                            "type": "number",
                            "description": "开始时间（秒）"
                        },
                        "end_time": {
                            "type": "number",
                            "description": "结束时间（秒）"
                        },
                        "font_type": {
                            "type": "string",
                            "description": "字体类型",
                            "default": "default"
                        }
                    },
                    "required": ["draft_id", "subtitle_text", "start_time", "end_time"]
                }
            ),
            MCPTool(
                name="add_image",
                description="向 CapCut 项目添加图片",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "draft_id": {
                            "type": "string",
                            "description": "草稿 ID"
                        },
                        "image_path": {
                            "type": "string",
                            "description": "图片文件路径"
                        },
                        "start_time": {
                            "type": "number",
                            "description": "开始时间（秒）",
                            "default": 0
                        },
                        "duration": {
                            "type": "number",
                            "description": "持续时间（秒）",
                            "default": 3
                        },
                        "position_x": {
                            "type": "number",
                            "description": "X 坐标",
                            "default": 0.5
                        },
                        "position_y": {
                            "type": "number",
                            "description": "Y 坐标",
                            "default": 0.5
                        },
                        "scale": {
                            "type": "number",
                            "description": "缩放比例",
                            "default": 1.0
                        }
                    },
                    "required": ["draft_id", "image_path"]
                }
            ),
            MCPTool(
                name="add_effect",
                description="向 CapCut 项目添加特效",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "draft_id": {
                            "type": "string",
                            "description": "草稿 ID"
                        },
                        "effect_type": {
                            "type": "string",
                            "description": "特效类型"
                        },
                        "target_track": {
                            "type": "string",
                            "description": "目标轨道",
                            "default": "video"
                        },
                        "start_time": {
                            "type": "number",
                            "description": "开始时间（秒）",
                            "default": 0
                        },
                        "duration": {
                            "type": "number",
                            "description": "持续时间（秒）",
                            "default": 2
                        }
                    },
                    "required": ["draft_id", "effect_type"]
                }
            ),
            MCPTool(
                name="add_sticker",
                description="向 CapCut 项目添加贴纸",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "draft_id": {
                            "type": "string",
                            "description": "草稿 ID"
                        },
                        "sticker_type": {
                            "type": "string",
                            "description": "贴纸类型"
                        },
                        "position_x": {
                            "type": "number",
                            "description": "X 坐标",
                            "default": 0.5
                        },
                        "position_y": {
                            "type": "number",
                            "description": "Y 坐标",
                            "default": 0.5
                        },
                        "scale": {
                            "type": "number",
                            "description": "缩放比例",
                            "default": 1.0
                        },
                        "start_time": {
                            "type": "number",
                            "description": "开始时间（秒）",
                            "default": 0
                        },
                        "duration": {
                            "type": "number",
                            "description": "持续时间（秒）",
                            "default": 3
                        }
                    },
                    "required": ["draft_id", "sticker_type"]
                }
            ),
            MCPTool(
                name="save_draft",
                description="保存 CapCut 草稿项目",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "draft_id": {
                            "type": "string",
                            "description": "草稿 ID"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径",
                            "default": ""
                        },
                        "quality": {
                            "type": "string",
                            "description": "输出质量",
                            "enum": ["low", "medium", "high"],
                            "default": "high"
                        }
                    },
                    "required": ["draft_id"]
                }
            )
        ]
    
    def _define_resources(self) -> List[MCPResource]:
        """定义 CapCut API 资源"""
        return [
            MCPResource(
                uri="capcut://api/status",
                name="CapCut API 状态",
                description="CapCut API 服务状态信息",
                mimeType="application/json"
            ),
            MCPResource(
                uri="capcut://api/docs",
                name="CapCut API 文档",
                description="CapCut API 使用文档",
                mimeType="text/markdown"
            )
        ]
    
    async def start_server(self):
        """启动 MCP 服务器"""
        self.stats['start_time'] = time.time()
        self.is_running = True
        
        logger.info(f"启动 CapCut MCP 服务器: {self.host}:{self.port}")
        
        # 启动 WebSocket 服务器
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        ):
            logger.info(f"CapCut MCP 服务器已启动: ws://{self.host}:{self.port}")
            
            # 保持服务器运行
            while self.is_running:
                await asyncio.sleep(1)
    
    async def stop_server(self):
        """停止 MCP 服务器"""
        self.is_running = False
        
        # 关闭所有客户端连接
        for client_id, websocket in self.clients.items():
            await websocket.close()
        
        self.clients.clear()
        logger.info("CapCut MCP 服务器已停止")
    
    async def handle_client(self, websocket, path):
        """处理客户端连接"""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        self.stats['clients_connected'] += 1
        
        logger.info(f"客户端已连接: {client_id}")
        
        try:
            async for message in websocket:
                await self.process_message(client_id, message)
                
        except ConnectionClosed:
            logger.info(f"客户端已断开: {client_id}")
        except Exception as e:
            logger.error(f"处理客户端消息异常: {e}")
        finally:
            self.clients.pop(client_id, None)
    
    async def process_message(self, client_id: str, message_data: str):
        """处理客户端消息"""
        try:
            message = json.loads(message_data)
            self.stats['total_requests'] += 1
            
            logger.debug(f"收到客户端 {client_id} 消息: {message}")
            
            # 处理不同类型的请求
            method = message.get("method")
            request_id = message.get("id")
            params = message.get("params", {})
            
            response = None
            
            if method == "initialize":
                response = await self.handle_initialize(params)
            elif method == "tools/list":
                response = await self.handle_list_tools(params)
            elif method == "tools/call":
                response = await self.handle_call_tool(params)
            elif method == "resources/list":
                response = await self.handle_list_resources(params)
            elif method == "resources/read":
                response = await self.handle_read_resource(params)
            else:
                response = {
                    "error": {
                        "code": -32601,
                        "message": f"未知方法: {method}"
                    }
                }
            
            # 发送响应
            if request_id:
                response_message = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    **response
                }
                
                await self.send_message(client_id, response_message)
                
                if "error" in response:
                    self.stats['failed_requests'] += 1
                else:
                    self.stats['successful_requests'] += 1
            
        except json.JSONDecodeError as e:
            logger.error(f"解析 JSON 消息失败: {e}")
            await self.send_error(client_id, -32700, "解析错误")
        except Exception as e:
            logger.error(f"处理消息异常: {e}")
            await self.send_error(client_id, -32603, f"内部错误: {e}")
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        return {
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": "CapCut MCP Server",
                    "version": "1.0.0"
                }
            }
        }
    
    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具列表请求"""
        tools_data = [asdict(tool) for tool in self.tools]
        return {
            "result": {
                "tools": tools_data
            }
        }
    
    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            # 调用对应的 CapCut API
            result = await self.call_capcut_api(tool_name, arguments)
            
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"调用工具失败: {tool_name}, 错误: {e}")
            return {
                "error": {
                    "code": -32000,
                    "message": f"工具调用失败: {e}"
                }
            }
    
    async def handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理资源列表请求"""
        resources_data = [asdict(resource) for resource in self.resources]
        return {
            "result": {
                "resources": resources_data
            }
        }
    
    async def handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理资源读取请求"""
        uri = params.get("uri")
        
        try:
            if uri == "capcut://api/status":
                # 返回 API 状态
                status = await self.get_capcut_api_status()
                content = json.dumps(status, ensure_ascii=False, indent=2)
            elif uri == "capcut://api/docs":
                # 返回 API 文档
                content = self.get_capcut_api_docs()
            else:
                raise ValueError(f"未知资源: {uri}")
            
            return {
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json" if uri.endswith("status") else "text/markdown",
                            "text": content
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"读取资源失败: {uri}, 错误: {e}")
            return {
                "error": {
                    "code": -32000,
                    "message": f"资源读取失败: {e}"
                }
            }
    
    async def call_capcut_api(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用 CapCut API"""
        # 构建 API URL
        if tool_name.startswith("get_"):
            # GET 请求
            api_path = tool_name
            url = f"{self.capcut_api_base_url}/{api_path}"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        else:
            # POST 请求
            api_path = tool_name
            url = f"{self.capcut_api_base_url}/{api_path}"
            
            response = requests.post(
                url,
                json=arguments,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
    
    async def get_capcut_api_status(self) -> Dict[str, Any]:
        """获取 CapCut API 状态"""
        try:
            response = requests.get(
                f"{self.capcut_api_base_url}/get_intro_animation_types",
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "status": "online",
                    "api_url": self.capcut_api_base_url,
                    "response_time": response.elapsed.total_seconds(),
                    "last_check": time.time()
                }
            else:
                return {
                    "status": "error",
                    "api_url": self.capcut_api_base_url,
                    "error_code": response.status_code,
                    "last_check": time.time()
                }
                
        except Exception as e:
            return {
                "status": "offline",
                "api_url": self.capcut_api_base_url,
                "error": str(e),
                "last_check": time.time()
            }
    
    def get_capcut_api_docs(self) -> str:
        """获取 CapCut API 文档"""
        return """# CapCut API MCP 服务器

## 概述

CapCut API MCP 服务器将 CapCut API 功能封装为 MCP 工具，供 AI 工作流平台使用。

## 可用工具

### 获取资源类型
- `get_intro_animation_types`: 获取入场动画类型
- `get_outro_animation_types`: 获取出场动画类型
- `get_transition_types`: 获取转场类型
- `get_mask_types`: 获取遮罩类型
- `get_font_types`: 获取字体类型

### 项目管理
- `create_draft`: 创建草稿项目
- `save_draft`: 保存草稿项目

### 内容添加
- `add_video`: 添加视频
- `add_audio`: 添加音频
- `add_text`: 添加文本
- `add_subtitle`: 添加字幕
- `add_image`: 添加图片
- `add_effect`: 添加特效
- `add_sticker`: 添加贴纸

## 使用示例

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "create_draft",
    "arguments": {
      "project_name": "我的视频项目",
      "resolution": "1920x1080",
      "fps": 30
    }
  }
}
```

## 资源

- `capcut://api/status`: API 状态信息
- `capcut://api/docs`: API 文档
"""
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """发送消息给客户端"""
        websocket = self.clients.get(client_id)
        if websocket:
            try:
                message_json = json.dumps(message, ensure_ascii=False)
                await websocket.send(message_json)
                logger.debug(f"发送消息给客户端 {client_id}: {message_json}")
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
    
    async def send_error(self, client_id: str, code: int, message: str):
        """发送错误消息给客户端"""
        error_message = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            }
        }
        await self.send_message(client_id, error_message)
    
    def get_server_stats(self) -> Dict[str, Any]:
        """获取服务器统计信息"""
        uptime = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        
        return {
            **self.stats,
            'is_running': self.is_running,
            'active_clients': len(self.clients),
            'uptime_seconds': uptime,
            'tools_count': len(self.tools),
            'resources_count': len(self.resources)
        }


async def main():
    """主函数 - 启动 CapCut MCP 服务器"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CapCut API MCP 服务器")
    parser.add_argument("--host", default="localhost", help="监听地址")
    parser.add_argument("--port", type=int, default=8080, help="监听端口")
    parser.add_argument("--capcut-api", default="http://localhost:9000", help="CapCut API 基础 URL")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并启动服务器
    server = CapCutMCPServer(
        capcut_api_base_url=args.capcut_api,
        host=args.host,
        port=args.port
    )
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止服务器...")
        await server.stop_server()


if __name__ == "__main__":
    asyncio.run(main())