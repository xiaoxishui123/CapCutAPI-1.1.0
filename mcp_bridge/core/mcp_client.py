#!/usr/bin/env python3
"""
MCP 协议客户端实现

这个模块实现了真正的 MCP (Model Context Protocol) 客户端，
用于与 MCP 服务器进行通信。

作者：AI Assistant
版本：v1.0.0
更新时间：2025年1月14日
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from .models import MCPRequest, MCPResponse, ServiceEndpoint


logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP 消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


@dataclass
class MCPMessage:
    """MCP 消息基类"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPClientError(Exception):
    """MCP 客户端异常"""
    pass


class MCPConnectionError(MCPClientError):
    """MCP 连接异常"""
    pass


class MCPTimeoutError(MCPClientError):
    """MCP 超时异常"""
    pass


class MCPClient:
    """
    MCP 协议客户端
    
    实现与 MCP 服务器的 WebSocket 连接和消息交换
    """
    
    def __init__(
        self,
        endpoint: ServiceEndpoint,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        初始化 MCP 客户端
        
        Args:
            endpoint: MCP 服务端点配置
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间（秒）
        """
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
        # 连接状态
        self._connection_lock = asyncio.Lock()
        self._last_ping = 0
        self._ping_interval = 30  # 心跳间隔（秒）
        
        # 统计信息
        self.stats = {
            'requests_sent': 0,
            'responses_received': 0,
            'errors_count': 0,
            'connection_count': 0,
            'last_activity': 0
        }
    
    async def connect(self) -> bool:
        """
        连接到 MCP 服务器
        
        Returns:
            bool: 连接是否成功
        """
        async with self._connection_lock:
            if self.is_connected:
                return True
            
            try:
                # 解析 WebSocket URL
                ws_url = self._get_websocket_url()
                
                # 建立 WebSocket 连接
                self.websocket = await websockets.connect(
                    ws_url,
                    timeout=self.timeout,
                    ping_interval=self._ping_interval,
                    ping_timeout=10
                )
                
                self.is_connected = True
                self.stats['connection_count'] += 1
                self.stats['last_activity'] = time.time()
                
                # 启动消息处理任务
                asyncio.create_task(self._message_handler())
                asyncio.create_task(self._heartbeat_task())
                
                logger.info(f"已连接到 MCP 服务器: {ws_url}")
                
                # 发送初始化消息
                await self._send_initialize()
                
                return True
                
            except Exception as e:
                logger.error(f"连接 MCP 服务器失败: {e}")
                self.is_connected = False
                return False
    
    async def disconnect(self):
        """断开与 MCP 服务器的连接"""
        async with self._connection_lock:
            if self.websocket and not self.websocket.closed:
                await self.websocket.close()
            
            self.is_connected = False
            self.websocket = None
            
            # 取消所有待处理的请求
            for request_id, future in self.pending_requests.items():
                if not future.done():
                    future.set_exception(MCPConnectionError("连接已断开"))
            
            self.pending_requests.clear()
            logger.info("已断开 MCP 服务器连接")
    
    async def call_method(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        调用 MCP 方法
        
        Args:
            method: 方法名
            params: 方法参数
            timeout: 超时时间（秒）
            
        Returns:
            Any: 方法返回结果
            
        Raises:
            MCPClientError: 调用失败
            MCPTimeoutError: 调用超时
        """
        if not self.is_connected:
            await self.connect()
        
        if not self.is_connected:
            raise MCPConnectionError("无法连接到 MCP 服务器")
        
        # 生成请求 ID
        request_id = str(uuid.uuid4())
        
        # 创建请求消息
        message = MCPMessage(
            id=request_id,
            method=method,
            params=params or {}
        )
        
        # 创建 Future 等待响应
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        try:
            # 发送请求
            await self._send_message(message)
            self.stats['requests_sent'] += 1
            
            # 等待响应
            actual_timeout = timeout or self.timeout
            result = await asyncio.wait_for(future, timeout=actual_timeout)
            
            return result
            
        except asyncio.TimeoutError:
            # 清理超时请求
            self.pending_requests.pop(request_id, None)
            self.stats['errors_count'] += 1
            raise MCPTimeoutError(f"方法调用超时: {method}")
            
        except Exception as e:
            # 清理失败请求
            self.pending_requests.pop(request_id, None)
            self.stats['errors_count'] += 1
            raise MCPClientError(f"方法调用失败: {method}, 错误: {e}")
    
    async def _send_message(self, message: MCPMessage):
        """发送消息到 MCP 服务器"""
        if not self.websocket or self.websocket.closed:
            raise MCPConnectionError("WebSocket 连接未建立")
        
        # 序列化消息
        message_data = {
            "jsonrpc": message.jsonrpc,
        }
        
        if message.id:
            message_data["id"] = message.id
        if message.method:
            message_data["method"] = message.method
        if message.params is not None:
            message_data["params"] = message.params
        if message.result is not None:
            message_data["result"] = message.result
        if message.error is not None:
            message_data["error"] = message.error
        
        message_json = json.dumps(message_data)
        
        try:
            await self.websocket.send(message_json)
            self.stats['last_activity'] = time.time()
            logger.debug(f"发送 MCP 消息: {message_json}")
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            raise MCPConnectionError(f"发送消息失败: {e}")
    
    async def _message_handler(self):
        """处理来自 MCP 服务器的消息"""
        try:
            async for message in self.websocket:
                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(f"处理消息失败: {e}")
                    
        except ConnectionClosed:
            logger.warning("MCP 服务器连接已关闭")
            self.is_connected = False
            
        except Exception as e:
            logger.error(f"消息处理器异常: {e}")
            self.is_connected = False
    
    async def _process_message(self, message_data: str):
        """处理单个消息"""
        try:
            message = json.loads(message_data)
            self.stats['last_activity'] = time.time()
            
            logger.debug(f"收到 MCP 消息: {message_data}")
            
            # 检查是否是响应消息
            if "id" in message:
                request_id = message["id"]
                future = self.pending_requests.pop(request_id, None)
                
                if future and not future.done():
                    if "error" in message:
                        # 错误响应
                        error = message["error"]
                        future.set_exception(
                            MCPClientError(f"MCP 错误: {error}")
                        )
                    else:
                        # 成功响应
                        result = message.get("result")
                        future.set_result(result)
                        self.stats['responses_received'] += 1
            
            # 检查是否是通知消息
            elif "method" in message:
                method = message["method"]
                params = message.get("params", {})
                
                # 调用注册的处理器
                handler = self.message_handlers.get(method)
                if handler:
                    await handler(params)
                else:
                    logger.debug(f"未处理的通知: {method}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"解析 JSON 消息失败: {e}")
        except Exception as e:
            logger.error(f"处理消息异常: {e}")
    
    async def _send_initialize(self):
        """发送初始化消息"""
        try:
            # 发送 initialize 请求
            result = await self.call_method(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {
                            "listChanged": True
                        },
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "MCP Bridge Client",
                        "version": "1.0.0"
                    }
                }
            )
            
            logger.info(f"MCP 初始化成功: {result}")
            
            # 发送 initialized 通知
            await self._send_message(MCPMessage(
                method="notifications/initialized"
            ))
            
        except Exception as e:
            logger.error(f"MCP 初始化失败: {e}")
            raise
    
    async def _heartbeat_task(self):
        """心跳任务"""
        while self.is_connected:
            try:
                await asyncio.sleep(self._ping_interval)
                
                if self.is_connected and self.websocket:
                    # 发送 ping
                    await self.websocket.ping()
                    self._last_ping = time.time()
                    
            except Exception as e:
                logger.error(f"心跳失败: {e}")
                self.is_connected = False
                break
    
    def _get_websocket_url(self) -> str:
        """获取 WebSocket URL"""
        url = self.endpoint.url
        
        # 转换 HTTP URL 为 WebSocket URL
        if url.startswith("http://"):
            url = url.replace("http://", "ws://", 1)
        elif url.startswith("https://"):
            url = url.replace("https://", "wss://", 1)
        elif not url.startswith(("ws://", "wss://")):
            # 假设是 WebSocket URL
            url = f"ws://{url}"
        
        return url
    
    def register_notification_handler(
        self,
        method: str,
        handler: Callable[[Dict[str, Any]], None]
    ):
        """
        注册通知处理器
        
        Args:
            method: 通知方法名
            handler: 处理器函数
        """
        self.message_handlers[method] = handler
    
    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            **self.stats,
            'is_connected': self.is_connected,
            'pending_requests': len(self.pending_requests),
            'last_ping': self._last_ping
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()


class MCPClientPool:
    """
    MCP 客户端连接池
    
    管理多个 MCP 客户端连接，提供负载均衡和故障转移
    """
    
    def __init__(self, max_clients: int = 10):
        """
        初始化客户端池
        
        Args:
            max_clients: 最大客户端数量
        """
        self.max_clients = max_clients
        self.clients: List[MCPClient] = []
        self.current_index = 0
        self._lock = asyncio.Lock()
    
    async def add_client(self, endpoint: ServiceEndpoint) -> MCPClient:
        """
        添加客户端到池中
        
        Args:
            endpoint: MCP 服务端点
            
        Returns:
            MCPClient: 创建的客户端
        """
        async with self._lock:
            if len(self.clients) >= self.max_clients:
                raise MCPClientError("客户端池已满")
            
            client = MCPClient(endpoint)
            await client.connect()
            
            self.clients.append(client)
            return client
    
    async def get_client(self) -> Optional[MCPClient]:
        """
        获取可用的客户端（轮询方式）
        
        Returns:
            Optional[MCPClient]: 可用的客户端，如果没有则返回 None
        """
        async with self._lock:
            if not self.clients:
                return None
            
            # 轮询选择客户端
            for _ in range(len(self.clients)):
                client = self.clients[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.clients)
                
                if client.is_connected:
                    return client
            
            return None
    
    async def call_method(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        使用池中的客户端调用方法
        
        Args:
            method: 方法名
            params: 方法参数
            timeout: 超时时间
            
        Returns:
            Any: 方法返回结果
        """
        client = await self.get_client()
        if not client:
            raise MCPClientError("没有可用的 MCP 客户端")
        
        return await client.call_method(method, params, timeout)
    
    async def close_all(self):
        """关闭所有客户端连接"""
        async with self._lock:
            for client in self.clients:
                await client.disconnect()
            self.clients.clear()
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        return {
            'total_clients': len(self.clients),
            'connected_clients': sum(1 for c in self.clients if c.is_connected),
            'max_clients': self.max_clients,
            'current_index': self.current_index
        }