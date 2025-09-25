#!/usr/bin/env python3
"""
CapCut API HTTP MCP Bridge
为Dify平台提供HTTP协议的MCP服务

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
from flask import Flask, request, jsonify
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('capcut_http_mcp_bridge.log'),
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
    http_port: int = 8083
    
    @classmethod
    def from_file(cls, config_path: str = "capcut_http_config.json") -> "ServerConfig":
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
    
    def call_api(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        调用CapCut API
        
        Args:
            endpoint: API端点
            method: HTTP方法
            data: 请求数据
            
        Returns:
            API响应数据
        """
        url = f"{self.config.capcut_api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"调用API: {method} {url} (尝试 {attempt + 1}/{self.config.max_retries})")
                
                if method.upper() == "GET":
                    response = requests.get(url, params=data, timeout=self.config.timeout)
                elif method.upper() == "POST":
                    response = requests.post(url, json=data, timeout=self.config.timeout)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"API调用成功: {url}")
                return result
                
            except requests.RequestException as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 指数退避
            except Exception as e:
                logger.error(f"API调用异常: {e}")
                raise

class CapCutHTTPMCPBridge:
    """CapCut HTTP MCP Bridge"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.api_client = CapCutAPIClient(config)
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """设置HTTP路由"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """健康检查端点"""
            try:
                # 检查CapCut API健康状态
                result = self.api_client.call_api("health", method="GET")
                return jsonify({
                    "status": "healthy",
                    "timestamp": time.time(),
                    "capcut_api": "available",
                    "details": result
                })
            except Exception as e:
                return jsonify({
                    "status": "unhealthy",
                    "timestamp": time.time(),
                    "capcut_api": "unavailable",
                    "error": str(e)
                }), 500
        
        @self.app.route('/mcp', methods=['GET', 'POST'])
        def handle_mcp_request():
            """处理MCP协议请求 - 支持JSON-RPC 2.0格式"""
            # 如果是GET请求，返回服务状态信息
            if request.method == 'GET':
                return jsonify({
                    "status": "ok",
                    "service": "CapCut HTTP MCP Bridge",
                    "version": "1.0.0",
                    "protocol": "JSON-RPC 2.0",
                    "endpoints": {
                        "health": "/health",
                        "mcp": "/mcp (POST for JSON-RPC requests)"
                    }
                })
            
            # POST请求处理MCP协议
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": "Parse error"},
                        "id": None
                    }), 400
                
                # 检查JSON-RPC 2.0格式
                jsonrpc_version = data.get('jsonrpc')
                method = data.get('method')
                params = data.get('params', {})
                request_id = data.get('id')
                
                logger.info(f"收到JSON-RPC请求: method={method}, id={request_id}")
                
                # 验证JSON-RPC 2.0格式
                if jsonrpc_version != "2.0":
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {"code": -32600, "message": "Invalid Request"},
                        "id": request_id
                    }), 400
                
                if not method:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {"code": -32600, "message": "Missing method"},
                        "id": request_id
                    }), 400
                
                # 处理不同的MCP方法
                if method == 'initialize':
                    result = self._handle_initialize(params)
                elif method == 'tools/list':
                    result = self._handle_list_tools(params)
                elif method == 'tools/call':
                    result = self._handle_call_tool(params)
                elif method == 'notifications/initialized':
                    # 处理初始化完成通知 - 这是一个通知消息，不需要返回结果
                    logger.info("收到初始化完成通知")
                    return '', 204  # 返回204 No Content表示成功处理通知
                else:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"Method not found: {method}"},
                        "id": request_id
                    }), 400
                
                # 返回JSON-RPC 2.0格式的响应
                return jsonify({
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                })
                    
            except Exception as e:
                logger.error(f"处理MCP请求失败: {e}")
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                    "id": data.get('id') if data else None
                }), 500
    
    def _handle_initialize(self, params: Dict) -> Dict:
        """
        处理MCP初始化请求
        返回符合Dify期望的InitializeResult格式
        """
        logger.info("处理MCP初始化请求")
        
        # 返回符合MCP协议的InitializeResult
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                },
                "logging": {},
                "experimental": {}
            },
            "serverInfo": {
                "name": "capcut-http-mcp-bridge",
                "version": "1.0.0",
                "description": "CapCut API HTTP MCP Bridge for Dify"
            }
        }
    
    def _handle_list_tools(self, params: Dict) -> Dict:
        """处理工具列表请求"""
        logger.info("处理工具列表请求")
        
        tools = [
            {
                "name": "create_draft",
                "description": "创建新的CapCut草稿",
                "inputSchema": {
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
            },
            {
                "name": "add_video",
                "description": "向草稿添加视频",
                "inputSchema": {
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
            },
            {
                "name": "add_text",
                "description": "向草稿添加文本",
                "inputSchema": {
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
                        }
                    },
                    "required": ["draft_id", "text"]
                }
            },
            {
                "name": "save_draft",
                "description": "保存草稿",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "draft_id": {
                            "type": "string",
                            "description": "草稿ID"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出路径"
                        }
                    },
                    "required": ["draft_id"]
                }
            },
            {
                "name": "health_check",
                "description": "检查CapCut API服务健康状态",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        
        return {"tools": tools}
    
    def _handle_call_tool(self, params: Dict) -> Dict:
        """处理工具调用请求"""
        name = params.get('name')
        arguments = params.get('arguments', {})
        
        logger.info(f"调用工具: {name}")
        
        try:
            if name == "create_draft":
                result = self.api_client.call_api(
                    "create_draft",
                    method="POST",
                    data=arguments
                )
            elif name == "add_video":
                result = self.api_client.call_api(
                    "add_video",
                    method="POST",
                    data=arguments
                )
            elif name == "add_text":
                result = self.api_client.call_api(
                    "add_text",
                    method="POST",
                    data=arguments
                )
            elif name == "save_draft":
                result = self.api_client.call_api(
                    "save_draft",
                    method="POST",
                    data=arguments
                )
            elif name == "health_check":
                try:
                    result = self.api_client.call_api("health", method="GET")
                    result = {
                        "status": "healthy",
                        "timestamp": time.time(),
                        "capcut_api": "available",
                        "details": result
                    }
                except Exception as e:
                    result = {
                        "status": "unhealthy",
                        "timestamp": time.time(),
                        "capcut_api": "unavailable",
                        "error": str(e)
                    }
            else:
                raise ValueError(f"未知的工具: {name}")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"工具调用失败: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"工具调用失败: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    def run(self):
        """运行HTTP MCP Bridge"""
        logger.info(f"启动CapCut HTTP MCP Bridge，端口: {self.config.http_port}")
        
        # 创建默认配置文件
        self._create_default_config()
        
        self.app.run(
            host='0.0.0.0',
            port=self.config.http_port,
            debug=False
        )
    
    def _create_default_config(self):
        """创建默认配置文件"""
        config_path = "capcut_http_config.json"
        if not Path(config_path).exists():
            default_config = {
                "capcut_api_url": "http://localhost:9000",
                "timeout": 30,
                "max_retries": 3,
                "log_level": "INFO",
                "http_port": 8083
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已创建默认配置文件: {config_path}")

def main():
    """主函数"""
    # 加载配置
    config = ServerConfig.from_file()
    
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, config.log_level.upper()))
    
    # 创建并运行HTTP MCP Bridge
    bridge = CapCutHTTPMCPBridge(config)
    bridge.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("HTTP MCP Bridge已停止")
    except Exception as e:
        logger.error(f"HTTP MCP Bridge启动失败: {e}")
        sys.exit(1)