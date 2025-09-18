"""
MCP Bridge 降级控制器
实现熔断器模式、自动降级和故障恢复机制
"""

import asyncio
import time
from typing import Dict, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import logging
from contextlib import asynccontextmanager

from mcp_bridge.core.models import ServiceType, ServiceStatus, ServiceEndpoint


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"       # 关闭状态，正常工作
    OPEN = "open"           # 开启状态，拒绝请求
    HALF_OPEN = "half_open" # 半开状态，尝试恢复


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5          # 失败阈值
    recovery_timeout: float = 60.0      # 恢复超时时间（秒）
    success_threshold: int = 3          # 半开状态成功阈值
    timeout: float = 30.0               # 请求超时时间
    error_rate_threshold: float = 0.5   # 错误率阈值


@dataclass
class CircuitBreakerMetrics:
    """熔断器指标"""
    failure_count: int = 0
    success_count: int = 0
    total_requests: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    @property
    def error_rate(self) -> float:
        """错误率计算"""
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        """
        初始化熔断器
        
        Args:
            name: 熔断器名称
            config: 熔断器配置
        """
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._lock = asyncio.Lock()
        
        logger.info(f"熔断器初始化: {name}")
    
    async def can_execute(self) -> bool:
        """
        检查是否可以执行请求
        
        Returns:
            是否可以执行
        """
        async with self._lock:
            current_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                # 检查是否可以尝试恢复
                if current_time - self.metrics.last_failure_time >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.metrics.consecutive_successes = 0
                    logger.info(f"熔断器进入半开状态: {self.name}")
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return True
            
            return False
    
    async def record_success(self) -> None:
        """记录成功执行"""
        async with self._lock:
            self.metrics.success_count += 1
            self.metrics.total_requests += 1
            self.metrics.last_success_time = time.time()
            self.metrics.consecutive_failures = 0
            self.metrics.consecutive_successes += 1
            
            # 半开状态下，连续成功达到阈值则关闭熔断器
            if (self.state == CircuitState.HALF_OPEN and 
                self.metrics.consecutive_successes >= self.config.success_threshold):
                self.state = CircuitState.CLOSED
                logger.info(f"熔断器恢复正常: {self.name}")
    
    async def record_failure(self) -> None:
        """记录失败执行"""
        async with self._lock:
            self.metrics.failure_count += 1
            self.metrics.total_requests += 1
            self.metrics.last_failure_time = time.time()
            self.metrics.consecutive_successes = 0
            self.metrics.consecutive_failures += 1
            
            # 检查是否需要开启熔断器
            if (self.state == CircuitState.CLOSED and 
                self.metrics.consecutive_failures >= self.config.failure_threshold):
                self.state = CircuitState.OPEN
                logger.warning(f"熔断器开启: {self.name}, 连续失败: {self.metrics.consecutive_failures}")
            elif (self.state == CircuitState.HALF_OPEN):
                self.state = CircuitState.OPEN
                logger.warning(f"熔断器重新开启: {self.name}")
    
    async def get_state(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        async with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "metrics": {
                    "failure_count": self.metrics.failure_count,
                    "success_count": self.metrics.success_count,
                    "total_requests": self.metrics.total_requests,
                    "error_rate": self.metrics.error_rate,
                    "consecutive_failures": self.metrics.consecutive_failures,
                    "consecutive_successes": self.metrics.consecutive_successes,
                    "last_failure_time": self.metrics.last_failure_time,
                    "last_success_time": self.metrics.last_success_time
                },
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "success_threshold": self.config.success_threshold,
                    "timeout": self.config.timeout,
                    "error_rate_threshold": self.config.error_rate_threshold
                }
            }
    
    async def reset(self) -> None:
        """重置熔断器"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.metrics = CircuitBreakerMetrics()
            logger.info(f"熔断器已重置: {self.name}")


class FallbackController:
    """降级控制器 - 管理服务降级和故障恢复"""
    
    def __init__(self):
        """初始化降级控制器"""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.fallback_rules: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        logger.info("降级控制器初始化完成")
    
    async def register_service(self, service: ServiceEndpoint, config: CircuitBreakerConfig) -> None:
        """
        注册服务的熔断器
        
        Args:
            service: 服务端点
            config: 熔断器配置
        """
        async with self._lock:
            service_key = f"{service.service_type.value}_{service.name}"
            self.circuit_breakers[service_key] = CircuitBreaker(service_key, config)
            
            logger.info(f"服务熔断器注册成功: {service.name}")
    
    async def unregister_service(self, service_name: str, service_type: ServiceType) -> None:
        """
        注销服务的熔断器
        
        Args:
            service_name: 服务名称
            service_type: 服务类型
        """
        async with self._lock:
            service_key = f"{service_type.value}_{service_name}"
            if service_key in self.circuit_breakers:
                del self.circuit_breakers[service_key]
                logger.info(f"服务熔断器注销成功: {service_name}")
    
    @asynccontextmanager
    async def execute_with_fallback(self, service: ServiceEndpoint):
        """
        使用降级机制执行请求的上下文管理器
        
        Args:
            service: 目标服务
            
        Yields:
            执行上下文
        """
        service_key = f"{service.service_type.value}_{service.name}"
        circuit_breaker = self.circuit_breakers.get(service_key)
        
        if not circuit_breaker:
            # 没有熔断器，直接执行
            yield
            return
        
        # 检查熔断器状态
        can_execute = await circuit_breaker.can_execute()
        if not can_execute:
            raise CircuitBreakerOpenError(f"熔断器开启，拒绝请求: {service.name}")
        
        start_time = time.time()
        success = False
        
        try:
            yield
            success = True
            await circuit_breaker.record_success()
            
        except Exception as e:
            await circuit_breaker.record_failure()
            logger.error(f"服务请求失败: {service.name}, 错误: {str(e)}")
            raise
        
        finally:
            execution_time = time.time() - start_time
            logger.debug(f"服务执行完成: {service.name}, 耗时: {execution_time:.3f}s, 成功: {success}")
    
    async def should_fallback(self, service: ServiceEndpoint) -> bool:
        """
        检查是否应该降级
        
        Args:
            service: 服务端点
            
        Returns:
            是否应该降级
        """
        service_key = f"{service.service_type.value}_{service.name}"
        circuit_breaker = self.circuit_breakers.get(service_key)
        
        if not circuit_breaker:
            return False
        
        can_execute = await circuit_breaker.can_execute()
        return not can_execute
    
    async def add_fallback_rule(self, method: str, rule: Dict[str, Any]) -> None:
        """
        添加降级规则
        
        Args:
            method: MCP方法名
            rule: 降级规则配置
        """
        async with self._lock:
            self.fallback_rules[method] = rule
            logger.info(f"降级规则添加成功: {method}")
    
    async def get_fallback_rule(self, method: str) -> Optional[Dict[str, Any]]:
        """
        获取降级规则
        
        Args:
            method: MCP方法名
            
        Returns:
            降级规则配置
        """
        return self.fallback_rules.get(method)
    
    async def get_circuit_breaker_status(self, service_name: str = None) -> Dict[str, Any]:
        """
        获取熔断器状态
        
        Args:
            service_name: 特定服务名称，为None时返回所有熔断器状态
            
        Returns:
            熔断器状态字典
        """
        if service_name:
            # 查找特定服务的熔断器
            for service_key, breaker in self.circuit_breakers.items():
                if service_name in service_key:
                    return await breaker.get_state()
            return {}
        else:
            # 返回所有熔断器状态
            result = {}
            for service_key, breaker in self.circuit_breakers.items():
                result[service_key] = await breaker.get_state()
            return result
    
    async def reset_circuit_breaker(self, service_name: str = None) -> None:
        """
        重置熔断器
        
        Args:
            service_name: 特定服务名称，为None时重置所有熔断器
        """
        if service_name:
            for service_key, breaker in self.circuit_breakers.items():
                if service_name in service_key:
                    await breaker.reset()
                    logger.info(f"熔断器重置成功: {service_name}")
        else:
            for breaker in self.circuit_breakers.values():
                await breaker.reset()
            logger.info("所有熔断器已重置")
    
    async def get_fallback_statistics(self) -> Dict[str, Any]:
        """
        获取降级统计信息
        
        Returns:
            降级统计数据
        """
        stats = {
            "total_circuit_breakers": len(self.circuit_breakers),
            "open_circuit_breakers": 0,
            "half_open_circuit_breakers": 0,
            "closed_circuit_breakers": 0,
            "total_requests": 0,
            "total_failures": 0,
            "overall_error_rate": 0.0,
            "services": {}
        }
        
        total_requests = 0
        total_failures = 0
        
        for service_key, breaker in self.circuit_breakers.items():
            state_info = await breaker.get_state()
            
            # 统计熔断器状态
            if state_info["state"] == CircuitState.OPEN.value:
                stats["open_circuit_breakers"] += 1
            elif state_info["state"] == CircuitState.HALF_OPEN.value:
                stats["half_open_circuit_breakers"] += 1
            else:
                stats["closed_circuit_breakers"] += 1
            
            # 累计请求和失败数
            metrics = state_info["metrics"]
            total_requests += metrics["total_requests"]
            total_failures += metrics["failure_count"]
            
            stats["services"][service_key] = {
                "state": state_info["state"],
                "error_rate": metrics["error_rate"],
                "total_requests": metrics["total_requests"],
                "failure_count": metrics["failure_count"],
                "consecutive_failures": metrics["consecutive_failures"]
            }
        
        stats["total_requests"] = total_requests
        stats["total_failures"] = total_failures
        stats["overall_error_rate"] = total_failures / total_requests if total_requests > 0 else 0.0
        
        return stats


class CircuitBreakerOpenError(Exception):
    """熔断器开启异常"""
    pass


class FallbackExecutionError(Exception):
    """降级执行异常"""
    pass


# 降级策略装饰器
def with_fallback(fallback_func: Optional[Callable] = None, timeout: float = 30.0):
    """
    降级策略装饰器
    
    Args:
        fallback_func: 降级函数
        timeout: 超时时间
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        async def wrapper(*args, **kwargs):
            try:
                # 设置超时
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except (asyncio.TimeoutError, CircuitBreakerOpenError) as e:
                logger.warning(f"主要服务不可用，尝试降级: {str(e)}")
                if fallback_func:
                    return await fallback_func(*args, **kwargs)
                else:
                    raise FallbackExecutionError(f"降级失败: {str(e)}")
            except Exception as e:
                logger.error(f"服务执行异常: {str(e)}")
                if fallback_func:
                    try:
                        return await fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"降级函数也失败: {str(fallback_error)}")
                        raise FallbackExecutionError(f"主要服务和降级服务都失败: {str(e)}")
                else:
                    raise
        
        return wrapper
    return decorator