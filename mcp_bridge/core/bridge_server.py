#!/usr/bin/env python3
"""
MCP Bridge 核心服务器实现

这是MCP Bridge的核心组件，负责：
1. 接收和处理来自Dify的MCP请求
2. 智能路由到最佳服务端点
3. 自动降级和故障恢复
4. 监控和健康检查

作者：AI Assistant
版本：v1.0.0
更新时间：2025年1月14日
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

import aiohttp
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """服务类型枚举"""
    MCP = "mcp"
    HTTP = "http"
    CACHE = "cache"
    DEFAULT = "default"


class ServiceStatus(Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceEndpoint:
    """服务端点配置"""
    name: str
    service_type: ServiceType
    url: str
    timeout: int = 30
    retry_count: int = 3
    priority: int = 1  # 优先级，数字越小优先级越高
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: float = field(default_factory=time.time)
    error_count: int = 0
    success_count: int = 0


class MCPRequest(BaseModel):
    """MCP请求模型"""
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any]
    id: Union[int, str]


class MCPResponse(BaseModel):
    """MCP响应模型"""
    jsonrpc: str = "2.0"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Union[int, str]


class BridgeMetrics:
    """桥接服务指标收集器"""
    
    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.service_metrics: Dict[str, Dict[str, Any]] = {}
    
    def record_request(self, service_name: str, response_time: float, success: bool):
        """记录请求指标"""
        self.request_count += 1
        self.total_response_time += response_time
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        # 记录服务级别指标
        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = {
                'request_count': 0,
                'success_count': 0,
                'error_count': 0,
                'total_response_time': 0.0
            }
        
        metrics = self.service_metrics[service_name]
        metrics['request_count'] += 1
        metrics['total_response_time'] += response_time
        
        if success:
            metrics['success_count'] += 1
        else:
            metrics['error_count'] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        success_rate = (
            self.success_count / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            'total_requests': self.request_count,
            'success_rate': success_rate,
            'error_rate': 1 - success_rate,
            'avg_response_time': avg_response_time,
            'service_metrics': self.service_metrics
        }


class FallbackController:
    """降级控制器"""
    
    def __init__(self, error_threshold: float = 0.2, timeout_threshold: int = 30):
        self.error_threshold = error_threshold  # 错误率阈值
        self.timeout_threshold = timeout_threshold  # 超时阈值（秒）
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
    
    def should_fallback(self, service: ServiceEndpoint) -> bool:
        """判断是否应该降级"""
        # 检查服务状态
        if service.status == ServiceStatus.UNHEALTHY:
            return True
        
        # 检查错误率
        total_requests = service.error_count + service.success_count
        if total_requests > 10:  # 至少有10个请求样本
            error_rate = service.error_count / total_requests
            if error_rate > self.error_threshold:
                logger.warning(f"Service {service.name} error rate {error_rate:.2%} exceeds threshold")
                return True
        
        # 检查熔断器状态
        breaker = self.circuit_breakers.get(service.name)
        if breaker and breaker['state'] == 'open':
            # 检查是否可以尝试半开状态
            if time.time() - breaker['opened_at'] > 60:  # 60秒后尝试半开
                breaker['state'] = 'half_open'
                logger.info(f"Circuit breaker for {service.name} entering half-open state")
                return False
            return True
        
        return False
    
    def record_success(self, service_name: str):
        """记录成功请求"""
        breaker = self.circuit_breakers.get(service_name)
        if breaker and breaker['state'] == 'half_open':
            breaker['state'] = 'closed'
            logger.info(f"Circuit breaker for {service_name} closed")
    
    def record_failure(self, service_name: str):
        """记录失败请求"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = {
                'state': 'closed',
                'failure_count': 0,
                'opened_at': None
            }
        
        breaker = self.circuit_breakers[service_name]
        breaker['failure_count'] += 1
        
        # 检查是否需要打开熔断器
        if breaker['failure_count'] >= 5 and breaker['state'] == 'closed':
            breaker['state'] = 'open'
            breaker['opened_at'] = time.time()
            logger.warning(f"Circuit breaker for {service_name} opened")


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = 300):
        self.redis_url = redis_url
        self.ttl = ttl
        self.redis_client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存数据"""
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(f"mcp_bridge:{key}")
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Dict[str, Any]):
        """设置缓存数据"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.setex(
                f"mcp_bridge:{key}",
                self.ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """删除缓存数据"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.delete(f"mcp_bridge:{key}")
        except Exception as e:
            logger.error(f"Cache delete error: {e}")


class RouterManager:
    """路由管理器"""
    
    def __init__(self):
        self.services: List[ServiceEndpoint] = []
        self.fallback_controller = FallbackController()
        self.cache_manager = CacheManager()
        self.metrics = BridgeMetrics()
    
    async def initialize(self):
        """初始化路由管理器"""
        await self.cache_manager.initialize()
        await self._load_service_config()
        await self._start_health_check()
    
    async def _load_service_config(self):
        """加载服务配置"""
        # 默认服务配置 - 简化架构，直接使用HTTP服务
        default_services = [
            ServiceEndpoint(
                name="capcut_http",
                service_type=ServiceType.HTTP,
                url="http://localhost:9000",
                priority=1  # 提升为最高优先级
            )
        ]
        
        self.services.extend(default_services)
        logger.info(f"Loaded {len(self.services)} service endpoints")
    
    async def _start_health_check(self):
        """启动健康检查"""
        asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self._check_all_services()
                await asyncio.sleep(30)  # 每30秒检查一次
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)  # 出错时延长检查间隔
    
    async def _check_all_services(self):
        """检查所有服务健康状态"""
        for service in self.services:
            await self._check_service_health(service)
    
    async def _check_service_health(self, service: ServiceEndpoint):
        """检查单个服务健康状态"""
        try:
            if service.service_type == ServiceType.HTTP:
                async with aiohttp.ClientSession() as session:
                    # 对于capcut_http服务，使用根端点而不是/health端点
                    health_endpoint = service.url
                    if service.name == "capcut_http":
                        # CapCutAPI使用根端点进行健康检查，并需要JSON Accept头
                        headers = {"Accept": "application/json"}
                    else:
                        # 其他服务使用标准的/health端点
                        health_endpoint = f"{service.url}/health"
                        headers = {}
                    
                    async with session.get(
                        health_endpoint,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            # 对于capcut_http，还需要验证响应内容
                            if service.name == "capcut_http":
                                try:
                                    data = await response.json()
                                    if data.get("success") and "CapCutAPI" in data.get("output", {}).get("message", ""):
                                        service.status = ServiceStatus.HEALTHY
                                        service.success_count += 1
                                    else:
                                        service.status = ServiceStatus.DEGRADED
                                        service.error_count += 1
                                except:
                                    service.status = ServiceStatus.DEGRADED
                                    service.error_count += 1
                            else:
                                service.status = ServiceStatus.HEALTHY
                                service.success_count += 1
                        else:
                            service.status = ServiceStatus.DEGRADED
                            service.error_count += 1
            elif service.service_type == ServiceType.MCP:
                # MCP服务健康检查（简化实现）
                service.status = ServiceStatus.HEALTHY
                service.success_count += 1
            
            service.last_check = time.time()
            
        except Exception as e:
            logger.warning(f"Health check failed for {service.name}: {e}")
            service.status = ServiceStatus.UNHEALTHY
            service.error_count += 1
            service.last_check = time.time()
    
    def get_best_service(self, method: str) -> Optional[ServiceEndpoint]:
        """获取最佳服务端点"""
        # 按优先级排序可用服务
        available_services = [
            s for s in self.services 
            if not self.fallback_controller.should_fallback(s)
        ]
        
        if not available_services:
            # 如果没有可用服务，返回优先级最高的服务（强制使用）
            return min(self.services, key=lambda s: s.priority) if self.services else None
        
        # 返回优先级最高的可用服务
        return min(available_services, key=lambda s: s.priority)
    
    async def route_request(self, request: MCPRequest) -> MCPResponse:
        """路由请求到最佳服务"""
        start_time = time.time()
        service = self.get_best_service(request.method)
        
        if not service:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32000,
                    "message": "No available service endpoints"
                }
            )
        
        # 尝试从缓存获取
        cache_key = f"{request.method}:{hash(json.dumps(request.params, sort_keys=True))}"
        cached_result = await self.cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for {request.method}")
            return MCPResponse(id=request.id, result=cached_result)
        
        # 调用服务
        try:
            result = await self._call_service(service, request)
            response_time = time.time() - start_time
            
            # 记录成功指标
            self.metrics.record_request(service.name, response_time, True)
            self.fallback_controller.record_success(service.name)
            service.success_count += 1
            
            # 缓存结果
            if result.result:
                await self.cache_manager.set(cache_key, result.result)
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Service call failed for {service.name}: {e}")
            
            # 记录失败指标
            self.metrics.record_request(service.name, response_time, False)
            self.fallback_controller.record_failure(service.name)
            service.error_count += 1
            
            # 尝试降级
            return await self._try_fallback(request, service)
    
    async def _call_service(self, service: ServiceEndpoint, request: MCPRequest) -> MCPResponse:
        """调用具体服务"""
        if service.service_type == ServiceType.HTTP:
            return await self._call_http_service(service, request)
        elif service.service_type == ServiceType.MCP:
            return await self._call_mcp_service(service, request)
        else:
            raise ValueError(f"Unsupported service type: {service.service_type}")
    
    async def _call_http_service(self, service: ServiceEndpoint, request: MCPRequest) -> MCPResponse:
        """调用HTTP服务"""
        # 将MCP请求转换为HTTP请求
        http_endpoint = self._mcp_to_http_endpoint(request.method)
        url = f"{service.url}{http_endpoint}"
        
        # 根据方法确定HTTP方法
        http_method = self._get_http_method(request.method)
        
        async with aiohttp.ClientSession() as session:
            if http_method == "GET":
                # GET请求，参数作为查询参数
                async with session.get(
                    url,
                    params=request.params,
                    timeout=aiohttp.ClientTimeout(total=service.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return MCPResponse(id=request.id, result=result)
                    else:
                        error_text = await response.text()
                        return MCPResponse(
                            id=request.id,
                            error={
                                "code": response.status,
                                "message": f"HTTP error: {error_text}"
                            }
                        )
            else:
                # POST请求，参数作为JSON body
                async with session.post(
                    url,
                    json=request.params,
                    timeout=aiohttp.ClientTimeout(total=service.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return MCPResponse(id=request.id, result=result)
                    else:
                        error_text = await response.text()
                        return MCPResponse(
                            id=request.id,
                            error={
                                "code": response.status,
                                "message": f"HTTP error: {error_text}"
                            }
                        )
    
    async def _call_mcp_service(self, service: ServiceEndpoint, request: MCPRequest) -> MCPResponse:
        """调用MCP服务"""
        # 这里应该实现真正的MCP客户端调用
        # 为了演示，我们返回一个模拟响应
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        return MCPResponse(
            id=request.id,
            result={
                "status": "success",
                "message": f"MCP service {service.name} processed {request.method}",
                "data": request.params
            }
        )
    
    def _mcp_to_http_endpoint(self, mcp_method: str) -> str:
        """将MCP方法名转换为HTTP端点"""
        method_mapping = {
            "get_intro_animation_types": "/get_intro_animation_types",
            "get_outro_animation_types": "/get_outro_animation_types",
            "get_transition_types": "/get_transition_types",
            "get_mask_types": "/get_mask_types",
            "get_font_types": "/get_font_types",
            "capcut_create_draft": "/create_draft",
            "capcut_add_video": "/add_video",
            "capcut_add_audio": "/add_audio",
            "capcut_add_text": "/add_text",
            "capcut_add_subtitle": "/add_subtitle",
            "capcut_add_image": "/add_image",
            "capcut_add_effect": "/add_effect",
            "capcut_add_sticker": "/add_sticker",
            "capcut_save_draft": "/save_draft"
        }
        
        return method_mapping.get(mcp_method, f"/api/{mcp_method}")
    
    def _get_http_method(self, mcp_method: str) -> str:
        """确定MCP方法对应的HTTP方法"""
        # GET方法的端点列表
        get_methods = {
            "get_intro_animation_types",
            "get_outro_animation_types",
            "get_transition_types",
            "get_mask_types",
            "get_font_types"
        }
        
        return "GET" if mcp_method in get_methods else "POST"
    
    async def _try_fallback(self, request: MCPRequest, failed_service: ServiceEndpoint) -> MCPResponse:
        """尝试降级处理"""
        # 尝试其他可用服务
        other_services = [
            s for s in self.services 
            if s != failed_service and s.status != ServiceStatus.UNHEALTHY
        ]
        
        for service in sorted(other_services, key=lambda s: s.priority):
            try:
                logger.info(f"Falling back to service {service.name}")
                return await self._call_service(service, request)
            except Exception as e:
                logger.warning(f"Fallback service {service.name} also failed: {e}")
                continue
        
        # 所有服务都失败，返回默认响应
        return MCPResponse(
            id=request.id,
            error={
                "code": -32001,
                "message": "All services unavailable, please try again later"
            }
        )


# 创建FastAPI应用
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    router_manager = RouterManager()
    await router_manager.initialize()
    app.state.router_manager = router_manager
    
    logger.info("MCP Bridge server started successfully")
    yield
    
    # 关闭时清理
    logger.info("MCP Bridge server shutting down")


app = FastAPI(
    title="MCP Bridge Server",
    description="智能MCP桥接服务，提供统一接口管理和自动降级能力",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/mcp", response_model=MCPResponse)
async def handle_mcp_request(request: MCPRequest):
    """处理MCP请求"""
    try:
        router_manager: RouterManager = app.state.router_manager
        response = await router_manager.route_request(request)
        return response
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return MCPResponse(
            id=request.id,
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        )


@app.get("/health")
async def health_check():
    """健康检查端点"""
    router_manager: RouterManager = app.state.router_manager
    
    service_status = {}
    for service in router_manager.services:
        service_status[service.name] = {
            "status": service.status.value,
            "last_check": service.last_check,
            "success_count": service.success_count,
            "error_count": service.error_count
        }
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": service_status
    }


@app.get("/metrics")
async def get_metrics():
    """获取服务指标"""
    router_manager: RouterManager = app.state.router_manager
    return router_manager.metrics.get_summary()


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "MCP Bridge Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health", 
            "metrics": "/metrics"
        }
    }


if __name__ == "__main__":
    import os
    
    # 从环境变量读取端口配置，默认为8080
    port = int(os.getenv("SERVER_PORT", "8080"))
    
    # 运行服务器
    uvicorn.run(
        "bridge_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )