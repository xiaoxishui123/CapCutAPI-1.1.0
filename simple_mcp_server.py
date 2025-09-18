#!/usr/bin/env python3
"""
CapCut API 简化版 MCP 服务器
适用于个人开发者的轻量级MCP实现

作者: AI助手
版本: 1.0.0
日期: 2025年1月14日
"""

import asyncio
import json
import logging
import sys
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

import aiohttp
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_mcp_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    """服务器配置类"""
    capcut_api_url: str = "http://localhost:9000"
    timeout: int = 30
    max_retries: int = 3
    log_level: str = "INFO"
    
    @classmethod
    def from_file(cls, config_path: str = "simple_config.json") -> "ServerConfig":
        """从配置文件加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
            return cls()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return cls()

class CapCutAPIClient:
    """CapCut API 客户端"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def call_api(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        调用CapCut API
        
        Args:
            endpoint: API端点
            method: HTTP方法
            data: 请求数据
            
        Returns:
            API响应数据
        """
        if not self.session:
            raise RuntimeError("API客户端未初始化")
        
        url = f"{self.config.capcut_api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"调用API: {method} {url} (尝试 {attempt + 1}/{self.config.max_retries})")
                
                if method.upper() == "GET":
                    async with self.session.get(url, params=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                elif method.upper() == "POST":
                    async with self.session.post(url, json=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                logger.info(f"API调用成功: {url}")
                return result
                
            except aiohttp.ClientError as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避
            except Exception as e:
                logger.error(f"API调用异常: {e}")
                raise

class SimpleMCPServer:
    """简化版MCP服务器"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.server = Server("capcut-simple-mcp")
        self.api_client = CapCutAPIClient(config)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置MCP处理器"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """列出可用的MCP工具"""
            return [
                Tool(
                    name="create_draft",
                    description="创建新的CapCut草稿",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "草稿标题"
                            },
                            "width": {
                                "type": "integer",
                                "description": "视频宽度",
                                "default": 1920
                            },
                            "height": {
                                "type": "integer", 
                                "description": "视频高度",
                                "default": 1080
                            },
                            "fps": {
                                "type": "integer",
                                "description": "帧率",
                                "default": 30
                            }
                        },
                        "required": ["title"]
                    }
                ),
                Tool(
                    name="add_video",
                    description="向草稿添加视频",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {
                                "type": "string",
                                "description": "草稿ID"
                            },
                            "video_path": {
                                "type": "string",
                                "description": "视频文件路径"
                            },
                            "start_time": {
                                "type": "number",
                                "description": "开始时间(秒)",
                                "default": 0
                            },
                            "duration": {
                                "type": "number",
                                "description": "持续时间(秒)"
                            }
                        },
                        "required": ["draft_id", "video_path"]
                    }
                ),
                Tool(
                    name="add_audio",
                    description="向草稿添加音频",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {
                                "type": "string",
                                "description": "草稿ID"
                            },
                            "audio_path": {
                                "type": "string",
                                "description": "音频文件路径"
                            },
                            "start_time": {
                                "type": "number",
                                "description": "开始时间(秒)",
                                "default": 0
                            },
                            "volume": {
                                "type": "number",
                                "description": "音量(0-1)",
                                "default": 1.0
                            }
                        },
                        "required": ["draft_id", "audio_path"]
                    }
                ),
                Tool(
                    name="add_text",
                    description="向草稿添加文本",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {
                                "type": "string",
                                "description": "草稿ID"
                            },
                            "text": {
                                "type": "string",
                                "description": "文本内容"
                            },
                            "x": {
                                "type": "number",
                                "description": "X坐标",
                                "default": 100
                            },
                            "y": {
                                "type": "number",
                                "description": "Y坐标", 
                                "default": 100
                            },
                            "font_size": {
                                "type": "integer",
                                "description": "字体大小",
                                "default": 24
                            },
                            "color": {
                                "type": "string",
                                "description": "文本颜色(十六进制)",
                                "default": "#FFFFFF"
                            }
                        },
                        "required": ["draft_id", "text"]
                    }
                ),
                Tool(
                    name="add_subtitle",
                    description="向草稿添加字幕",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {
                                "type": "string",
                                "description": "草稿ID"
                            },
                            "subtitle_text": {
                                "type": "string",
                                "description": "字幕文本"
                            },
                            "start_time": {
                                "type": "number",
                                "description": "开始时间(秒)"
                            },
                            "end_time": {
                                "type": "number",
                                "description": "结束时间(秒)"
                            },
                            "style": {
                                "type": "string",
                                "description": "字幕样式",
                                "default": "default"
                            }
                        },
                        "required": ["draft_id", "subtitle_text", "start_time", "end_time"]
                    }
                ),
                Tool(
                    name="save_draft",
                    description="保存草稿",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {
                                "type": "string",
                                "description": "草稿ID"
                            },
                            "output_path": {
                                "type": "string",
                                "description": "输出文件路径"
                            },
                            "quality": {
                                "type": "string",
                                "description": "输出质量",
                                "enum": ["low", "medium", "high"],
                                "default": "medium"
                            }
                        },
                        "required": ["draft_id"]
                    }
                ),
                Tool(
                    name="get_animation_types",
                    description="获取动画类型列表",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "animation_type": {
                                "type": "string",
                                "description": "动画类型",
                                "enum": ["intro", "outro", "transition"],
                                "default": "intro"
                            }
                        }
                    }
                ),
                Tool(
                    name="health_check",
                    description="检查服务器健康状态",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理MCP工具调用"""
            try:
                logger.info(f"调用工具: {name}, 参数: {arguments}")
                
                async with self.api_client:
                    result = await self._handle_tool_call(name, arguments)
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]
                
            except Exception as e:
                logger.error(f"工具调用失败: {name}, 错误: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "tool": name,
                        "arguments": arguments
                    }, ensure_ascii=False, indent=2)
                )]
    
    async def _handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理具体的工具调用"""
        
        if name == "create_draft":
            return await self.api_client.call_api(
                "create_draft",
                method="POST",
                data=arguments
            )
        
        elif name == "add_video":
            return await self.api_client.call_api(
                "add_video",
                method="POST", 
                data=arguments
            )
        
        elif name == "add_audio":
            return await self.api_client.call_api(
                "add_audio",
                method="POST",
                data=arguments
            )
        
        elif name == "add_text":
            return await self.api_client.call_api(
                "add_text",
                method="POST",
                data=arguments
            )
        
        elif name == "add_subtitle":
            return await self.api_client.call_api(
                "add_subtitle", 
                method="POST",
                data=arguments
            )
        
        elif name == "save_draft":
            return await self.api_client.call_api(
                "save_draft",
                method="POST",
                data=arguments
            )
        
        elif name == "get_animation_types":
            animation_type = arguments.get("animation_type", "intro")
            endpoint_map = {
                "intro": "get_intro_animation_types",
                "outro": "get_outro_animation_types", 
                "transition": "get_transition_types"
            }
            endpoint = endpoint_map.get(animation_type, "get_intro_animation_types")
            return await self.api_client.call_api(endpoint, method="GET")
        
        elif name == "health_check":
            try:
                # 检查CapCut API健康状态
                result = await self.api_client.call_api("health", method="GET")
                return {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "capcut_api": "available",
                    "details": result
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "timestamp": time.time(),
                    "capcut_api": "unavailable",
                    "error": str(e)
                }
        
        else:
            raise ValueError(f"未知的工具: {name}")
    
    async def run(self):
        """运行MCP服务器"""
        logger.info("启动简化版CapCut MCP服务器...")
        
        # 创建默认配置文件
        self._create_default_config()
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="capcut-simple-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )
    
    def _create_default_config(self):
        """创建默认配置文件"""
        config_path = "simple_config.json"
        if not Path(config_path).exists():
            default_config = {
                "capcut_api_url": "http://localhost:9000",
                "timeout": 30,
                "max_retries": 3,
                "log_level": "INFO"
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已创建默认配置文件: {config_path}")

def create_startup_script():
    """创建启动脚本"""
    startup_script = """#!/bin/bash
# CapCut 简化版 MCP 服务器启动脚本

echo "启动CapCut简化版MCP服务器..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -oP '\\d+\\.\\d+')
required_version="3.9"

if [ "$(printf '%s\\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "错误: 需要Python 3.9或更高版本，当前版本: $python_version"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/installed" ]; then
    echo "安装依赖包..."
    pip install --upgrade pip
    pip install aiohttp mcp
    touch venv/installed
fi

# 检查CapCut API服务
echo "检查CapCut API服务..."
if ! curl -s http://localhost:9000/health > /dev/null; then
    echo "警告: CapCut API服务(localhost:9000)不可用"
    echo "请确保CapCut API服务已启动"
fi

# 启动MCP服务器
echo "启动MCP服务器..."
python3 simple_mcp_server.py

echo "MCP服务器已停止"
"""
    
    with open("start_simple_mcp.sh", 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    # 设置执行权限
    import os
    os.chmod("start_simple_mcp.sh", 0o755)
    
    logger.info("已创建启动脚本: start_simple_mcp.sh")

def create_requirements_file():
    """创建依赖文件"""
    requirements = """# CapCut 简化版 MCP 服务器依赖
aiohttp>=3.8.0
mcp>=0.1.0

# 可选依赖
requests>=2.28.0
pydantic>=2.0.0
"""
    
    with open("simple_requirements.txt", 'w', encoding='utf-8') as f:
        f.write(requirements)
    
    logger.info("已创建依赖文件: simple_requirements.txt")

async def main():
    """主函数"""
    # 创建辅助文件
    create_startup_script()
    create_requirements_file()
    
    # 加载配置
    config = ServerConfig.from_file()
    
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, config.log_level.upper()))
    
    # 创建并运行服务器
    server = SimpleMCPServer(config)
    await server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)