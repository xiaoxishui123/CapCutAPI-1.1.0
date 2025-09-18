"""
MCP Bridge 路由管理器
负责智能路由、负载均衡和服务选择
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from urllib.parse import urlparse

from mcp_bridge.core.models import ServiceType, ServiceStatus, ServiceEndpoint, MCPRequest, MCPResponse


logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """路由策略枚举"""
    PRIORITY = "priority"           # 优先级路由
    ROUND_ROBIN = "round_robin"     # 轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    WEIGHTED = "weighted"           # 权重路由


@dataclass
class ServiceMetrics:
    """服务指标数据"""
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_response_time: float = 0.0
    last_request_time: float = 0.0
    active_connections: int = 0
    
    @property
    def success_rate(self) -> float:
        """成功率计算"""
        if self.request_count == 0:
            return 1.0
        return self.success_count / self.request_count
    
    @property
    def error_rate(self) -> float:
        """错误率计算"""
        return 1.0 - self.success_rate
    
    @property
    def avg_response_time(self) -> float:
        """平均响应时间"""
        if self.success_count == 0:
            return 0.0
        return self.total_response_time / self.success_count


@dataclass
class RouteResult:
    """路由结果"""
    service: ServiceEndpoint
    is_fallback: bool = False
    reason: str = ""
    metrics: Optional[ServiceMetrics] = None


class ServiceRouter:
    """服务路由器 - 负责智能路由和服务选择"""
    
    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.PRIORITY):
        """
        初始化路由器
        
        Args:
            strategy: 路由策略
        """
        self.strategy = strategy
        self.services: Dict[str, ServiceEndpoint] = {}
        self.metrics: Dict[str, ServiceMetrics] = {}
        self.round_robin_index: Dict[ServiceType, int] = {}
        self._lock = asyncio.Lock()
        
        logger.info(f"服务路由器初始化完成，策略: {strategy.value}")
    
    async def register_service(self, service: ServiceEndpoint) -> None:
        """
        注册服务端点
        
        Args:
            service: 服务端点配置
        """
        async with self._lock:
            service_id = f"{service.service_type.value}_{service.name}"
            self.services[service_id] = service
            self.metrics[service_id] = ServiceMetrics()
            
            logger.info(f"服务注册成功: {service.name} ({service.url})")
    
    async def unregister_service(self, service_name: str, service_type: ServiceType) -> None:
        """
        注销服务端点
        
        Args:
            service_name: 服务名称
            service_type: 服务类型
        """
        async with self._lock:
            service_id = f"{service_type.value}_{service_name}"
            if service_id in self.services:
                del self.services[service_id]
                del self.metrics[service_id]
                logger.info(f"服务注销成功: {service_name}")
    
    async def route_request(self, method: str, prefer_mcp: bool = True) -> Optional[RouteResult]:
        """
        路由请求到最佳服务
        
        Args:
            method: MCP方法名
            prefer_mcp: 是否优先选择MCP服务
            
        Returns:
            路由结果，包含选中的服务和相关信息
        """
        async with self._lock:
            # 获取可用服务列表
            available_services = self._get_available_services(method)
            
            if not available_services:
                logger.warning(f"没有可用的服务处理方法: {method}")
                return None
            
            # 根据策略选择服务
            if prefer_mcp:
                # 优先选择MCP服务
                mcp_services = [s for s in available_services if s.service_type == ServiceType.MCP]
                if mcp_services:
                    selected = await self._select_service(mcp_services, method)
                    return RouteResult(
                        service=selected,
                        is_fallback=False,
                        reason="MCP优先选择",
                        metrics=self.metrics.get(f"{selected.service_type.value}_{selected.name}")
                    )
                
                # MCP不可用，降级到HTTP
                http_services = [s for s in available_services if s.service_type == ServiceType.HTTP]
                if http_services:
                    selected = await self._select_service(http_services, method)
                    return RouteResult(
                        service=selected,
                        is_fallback=True,
                        reason="MCP服务不可用，降级到HTTP",
                        metrics=self.metrics.get(f"{selected.service_type.value}_{selected.name}")
                    )
            else:
                # 不区分服务类型，直接选择最佳服务
                selected = await self._select_service(available_services, method)
                return RouteResult(
                    service=selected,
                    is_fallback=False,
                    reason="策略选择",
                    metrics=self.metrics.get(f"{selected.service_type.value}_{selected.name}")
                )
            
            return None
    
    def _get_available_services(self, method: str) -> List[ServiceEndpoint]:
        """
        获取可处理指定方法的可用服务列表
        
        Args:
            method: MCP方法名
            
        Returns:
            可用服务列表
        """
        available = []
        
        for service_id, service in self.services.items():
            # 检查服务状态
            if service.status != ServiceStatus.HEALTHY:
                continue
            
            # 检查方法支持
            if service.supported_methods and method not in service.supported_methods:
                continue
            
            # 检查服务指标
            metrics = self.metrics.get(service_id)
            if metrics and metrics.error_rate > 0.5:  # 错误率过高
                continue
            
            available.append(service)
        
        return available
    
    async def _select_service(self, services: List[ServiceEndpoint], method: str) -> ServiceEndpoint:
        """
        根据策略从服务列表中选择最佳服务
        
        Args:
            services: 候选服务列表
            method: MCP方法名
            
        Returns:
            选中的服务
        """
        if len(services) == 1:
            return services[0]
        
        if self.strategy == RoutingStrategy.PRIORITY:
            return self._select_by_priority(services)
        elif self.strategy == RoutingStrategy.ROUND_ROBIN:
            return self._select_by_round_robin(services)
        elif self.strategy == RoutingStrategy.LEAST_CONNECTIONS:
            return self._select_by_least_connections(services)
        elif self.strategy == RoutingStrategy.WEIGHTED:
            return self._select_by_weighted(services)
        else:
            # 默认按优先级选择
            return self._select_by_priority(services)
    
    def _select_by_priority(self, services: List[ServiceEndpoint]) -> ServiceEndpoint:
        """按优先级选择服务"""
        return min(services, key=lambda s: s.priority)
    
    def _select_by_round_robin(self, services: List[ServiceEndpoint]) -> ServiceEndpoint:
        """轮询选择服务"""
        if not services:
            raise ValueError("服务列表为空")
        
        service_type = services[0].service_type
        current_index = self.round_robin_index.get(service_type, 0)
        selected = services[current_index % len(services)]
        self.round_robin_index[service_type] = (current_index + 1) % len(services)
        
        return selected
    
    def _select_by_least_connections(self, services: List[ServiceEndpoint]) -> ServiceEndpoint:
        """按最少连接数选择服务"""
        def get_connections(service: ServiceEndpoint) -> int:
            service_id = f"{service.service_type.value}_{service.name}"
            metrics = self.metrics.get(service_id)
            return metrics.active_connections if metrics else 0
        
        return min(services, key=get_connections)
    
    def _select_by_weighted(self, services: List[ServiceEndpoint]) -> ServiceEndpoint:
        """按权重选择服务（基于成功率和响应时间）"""
        def calculate_weight(service: ServiceEndpoint) -> float:
            service_id = f"{service.service_type.value}_{service.name}"
            metrics = self.metrics.get(service_id)
            
            if not metrics or metrics.request_count == 0:
                return 1.0  # 新服务给予默认权重
            
            # 权重 = 成功率 * (1 / 平均响应时间) * 优先级因子
            success_factor = metrics.success_rate
            speed_factor = 1.0 / max(metrics.avg_response_time, 0.1)
            priority_factor = 1.0 / max(service.priority, 1)
            
            return success_factor * speed_factor * priority_factor
        
        return max(services, key=calculate_weight)
    
    async def record_request_start(self, service: ServiceEndpoint) -> None:
        """记录请求开始"""
        async with self._lock:
            service_id = f"{service.service_type.value}_{service.name}"
            metrics = self.metrics.get(service_id)
            if metrics:
                metrics.request_count += 1
                metrics.active_connections += 1
                metrics.last_request_time = time.time()
    
    async def record_request_success(self, service: ServiceEndpoint, response_time: float) -> None:
        """记录请求成功"""
        async with self._lock:
            service_id = f"{service.service_type.value}_{service.name}"
            metrics = self.metrics.get(service_id)
            if metrics:
                metrics.success_count += 1
                metrics.total_response_time += response_time
                metrics.active_connections = max(0, metrics.active_connections - 1)
    
    async def record_request_error(self, service: ServiceEndpoint) -> None:
        """记录请求错误"""
        async with self._lock:
            service_id = f"{service.service_type.value}_{service.name}"
            metrics = self.metrics.get(service_id)
            if metrics:
                metrics.error_count += 1
                metrics.active_connections = max(0, metrics.active_connections - 1)
    
    async def get_service_metrics(self, service_name: str = None) -> Dict[str, Any]:
        """
        获取服务指标
        
        Args:
            service_name: 特定服务名称，为None时返回所有服务指标
            
        Returns:
            服务指标字典
        """
        async with self._lock:
            if service_name:
                # 查找特定服务
                for service_id, metrics in self.metrics.items():
                    if service_name in service_id:
                        return {
                            "service_id": service_id,
                            "request_count": metrics.request_count,
                            "success_count": metrics.success_count,
                            "error_count": metrics.error_count,
                            "success_rate": metrics.success_rate,
                            "error_rate": metrics.error_rate,
                            "avg_response_time": metrics.avg_response_time,
                            "active_connections": metrics.active_connections,
                            "last_request_time": metrics.last_request_time
                        }
                return {}
            else:
                # 返回所有服务指标
                result = {}
                for service_id, metrics in self.metrics.items():
                    result[service_id] = {
                        "request_count": metrics.request_count,
                        "success_count": metrics.success_count,
                        "error_count": metrics.error_count,
                        "success_rate": metrics.success_rate,
                        "error_rate": metrics.error_rate,
                        "avg_response_time": metrics.avg_response_time,
                        "active_connections": metrics.active_connections,
                        "last_request_time": metrics.last_request_time
                    }
                return result
    
    async def update_service_status(self, service_name: str, service_type: ServiceType, status: ServiceStatus) -> None:
        """
        更新服务状态
        
        Args:
            service_name: 服务名称
            service_type: 服务类型
            status: 新状态
        """
        async with self._lock:
            service_id = f"{service_type.value}_{service_name}"
            service = self.services.get(service_id)
            if service:
                old_status = service.status
                service.status = status
                logger.info(f"服务状态更新: {service_name} {old_status.value} -> {status.value}")
    
    async def get_healthy_services(self) -> List[ServiceEndpoint]:
        """获取所有健康的服务"""
        async with self._lock:
            return [
                service for service in self.services.values()
                if service.status == ServiceStatus.HEALTHY
            ]
    
    async def reset_metrics(self, service_name: str = None) -> None:
        """
        重置服务指标
        
        Args:
            service_name: 特定服务名称，为None时重置所有服务指标
        """
        async with self._lock:
            if service_name:
                for service_id in self.metrics:
                    if service_name in service_id:
                        self.metrics[service_id] = ServiceMetrics()
                        logger.info(f"服务指标已重置: {service_name}")
            else:
                for service_id in self.metrics:
                    self.metrics[service_id] = ServiceMetrics()
                logger.info("所有服务指标已重置")