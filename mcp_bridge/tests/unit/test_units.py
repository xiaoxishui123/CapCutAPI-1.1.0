"""
MCP Bridge 单元测试套件
测试各个组件的独立功能
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_bridge.core.router import RouterManager, RoutingStrategy, ServiceEndpoint
from mcp_bridge.core.fallback import FallbackController, CircuitBreaker, CircuitBreakerConfig, CircuitState
from mcp_bridge.core.cache import CacheManager, CacheConfig, CacheStrategy
from mcp_bridge.core.monitoring import MonitoringSystem, HealthCheck, HealthStatus, AlertLevel


class TestRouterManager:
    """路由管理器单元测试"""
    
    @pytest.fixture
    def router_manager(self):
        """创建路由管理器实例"""
        return RouterManager()
    
    @pytest.fixture
    def sample_services(self):
        """示例服务配置"""
        return [
            ServiceEndpoint(
                name="capcut_mcp",
                service_type="mcp",
                endpoint="ws://localhost:3001/mcp",
                priority=1,
                weight=100,
                timeout=30,
                enabled=True
            ),
            ServiceEndpoint(
                name="capcut_http",
                service_type="http",
                endpoint="http://localhost:3000/api",
                priority=2,
                weight=50,
                timeout=15,
                enabled=True
            )
        ]
    
    def test_service_registration(self, router_manager, sample_services):
        """测试服务注册"""
        for service in sample_services:
            router_manager.register_service(service)
        
        # 验证服务已注册
        assert len(router_manager.services) == 2
        assert "capcut_mcp" in router_manager.services
        assert "capcut_http" in router_manager.services
        
        # 验证服务配置
        mcp_service = router_manager.services["capcut_mcp"]
        assert mcp_service.priority == 1
        assert mcp_service.weight == 100
        assert mcp_service.enabled is True
    
    def test_service_unregistration(self, router_manager, sample_services):
        """测试服务注销"""
        # 注册服务
        for service in sample_services:
            router_manager.register_service(service)
        
        # 注销一个服务
        router_manager.unregister_service("capcut_mcp")
        
        # 验证服务已注销
        assert len(router_manager.services) == 1
        assert "capcut_mcp" not in router_manager.services
        assert "capcut_http" in router_manager.services
    
    def test_priority_routing_strategy(self, router_manager, sample_services):
        """测试优先级路由策略"""
        # 注册服务
        for service in sample_services:
            router_manager.register_service(service)
        
        # 设置优先级策略
        router_manager.set_routing_strategy(RoutingStrategy.PRIORITY)
        
        # 获取路由服务
        selected_service = router_manager.get_next_service("test_method")
        
        # 应该选择优先级最高的服务（priority=1）
        assert selected_service.name == "capcut_mcp"
        assert selected_service.priority == 1
    
    def test_round_robin_routing_strategy(self, router_manager, sample_services):
        """测试轮询路由策略"""
        # 注册服务
        for service in sample_services:
            router_manager.register_service(service)
        
        # 设置轮询策略
        router_manager.set_routing_strategy(RoutingStrategy.ROUND_ROBIN)
        
        # 多次获取服务，验证轮询
        services = []
        for _ in range(4):
            service = router_manager.get_next_service("test_method")
            services.append(service.name)
        
        # 验证轮询模式
        expected = ["capcut_mcp", "capcut_http", "capcut_mcp", "capcut_http"]
        assert services == expected
    
    def test_weighted_routing_strategy(self, router_manager, sample_services):
        """测试权重路由策略"""
        # 注册服务
        for service in sample_services:
            router_manager.register_service(service)
        
        # 设置权重策略
        router_manager.set_routing_strategy(RoutingStrategy.WEIGHTED)
        
        # 多次获取服务，统计分布
        service_counts = {}
        for _ in range(150):  # 足够的样本数
            service = router_manager.get_next_service("test_method")
            service_counts[service.name] = service_counts.get(service.name, 0) + 1
        
        # 验证权重分布（capcut_mcp权重100，capcut_http权重50）
        # 期望比例约为 2:1
        mcp_count = service_counts.get("capcut_mcp", 0)
        http_count = service_counts.get("capcut_http", 0)
        
        ratio = mcp_count / http_count if http_count > 0 else float('inf')
        assert 1.5 < ratio < 2.5  # 允许一定的误差范围
    
    def test_service_health_tracking(self, router_manager, sample_services):
        """测试服务健康状态跟踪"""
        # 注册服务
        service = sample_services[0]
        router_manager.register_service(service)
        
        # 记录成功请求
        router_manager.record_request_result(service.name, True, 0.1)
        
        # 获取指标
        metrics = router_manager.get_service_metrics(service.name)
        assert metrics['total_requests'] == 1
        assert metrics['successful_requests'] == 1
        assert metrics['failed_requests'] == 0
        assert metrics['success_rate'] == 1.0
        
        # 记录失败请求
        router_manager.record_request_result(service.name, False, 0.2)
        
        # 重新获取指标
        metrics = router_manager.get_service_metrics(service.name)
        assert metrics['total_requests'] == 2
        assert metrics['successful_requests'] == 1
        assert metrics['failed_requests'] == 1
        assert metrics['success_rate'] == 0.5
    
    def test_disabled_service_exclusion(self, router_manager, sample_services):
        """测试禁用服务的排除"""
        # 禁用第一个服务
        sample_services[0].enabled = False
        
        # 注册服务
        for service in sample_services:
            router_manager.register_service(service)
        
        # 获取服务
        selected_service = router_manager.get_next_service("test_method")
        
        # 应该只选择启用的服务
        assert selected_service.name == "capcut_http"
        assert selected_service.enabled is True


class TestCircuitBreaker:
    """熔断器单元测试"""
    
    @pytest.fixture
    def circuit_config(self):
        """熔断器配置"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=5,
            half_open_max_calls=2
        )
    
    @pytest.fixture
    def circuit_breaker(self, circuit_config):
        """创建熔断器实例"""
        return CircuitBreaker("test_service", circuit_config)
    
    def test_initial_state(self, circuit_breaker):
        """测试初始状态"""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.can_execute() is True
    
    def test_failure_threshold_trigger(self, circuit_breaker):
        """测试失败阈值触发"""
        # 记录失败请求，但未达到阈值
        for _ in range(2):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.can_execute() is True
        
        # 再记录一次失败，达到阈值
        circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.can_execute() is False
    
    def test_success_reset_failure_count(self, circuit_breaker):
        """测试成功请求重置失败计数"""
        # 记录一些失败
        for _ in range(2):
            circuit_breaker.record_failure()
        
        # 记录成功
        circuit_breaker.record_success()
        
        # 失败计数应该被重置
        assert circuit_breaker.metrics.failure_count == 0
        assert circuit_breaker.state == CircuitState.CLOSED
    
    def test_half_open_state_transition(self, circuit_breaker):
        """测试半开状态转换"""
        # 触发熔断器打开
        for _ in range(3):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # 等待恢复时间（模拟）
        circuit_breaker.last_failure_time = time.time() - 10  # 10秒前
        
        # 检查是否可以执行（应该进入半开状态）
        assert circuit_breaker.can_execute() is True
        assert circuit_breaker.state == CircuitState.HALF_OPEN
    
    def test_half_open_success_recovery(self, circuit_breaker):
        """测试半开状态成功恢复"""
        # 进入半开状态
        circuit_breaker.state = CircuitState.HALF_OPEN
        circuit_breaker.metrics.half_open_calls = 0
        
        # 记录成功请求
        for _ in range(2):  # half_open_max_calls = 2
            circuit_breaker.record_success()
        
        # 应该恢复到关闭状态
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.metrics.failure_count == 0
    
    def test_half_open_failure_reopen(self, circuit_breaker):
        """测试半开状态失败重新打开"""
        # 进入半开状态
        circuit_breaker.state = CircuitState.HALF_OPEN
        circuit_breaker.metrics.half_open_calls = 0
        
        # 记录失败请求
        circuit_breaker.record_failure()
        
        # 应该重新打开
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.can_execute() is False


class TestFallbackController:
    """降级控制器单元测试"""
    
    @pytest.fixture
    def fallback_controller(self):
        """创建降级控制器实例"""
        config = {
            'enabled': True,
            'circuit_breaker': {
                'failure_threshold': 3,
                'recovery_timeout': 5,
                'half_open_max_calls': 2
            }
        }
        return FallbackController(config)
    
    @pytest.fixture
    def sample_services(self):
        """示例服务配置"""
        return [
            {
                'name': 'primary_service',
                'type': 'mcp',
                'endpoint': 'ws://localhost:3001/mcp',
                'priority': 1
            },
            {
                'name': 'fallback_service',
                'type': 'http',
                'endpoint': 'http://localhost:3000/api',
                'priority': 2
            }
        ]
    
    def test_service_registration(self, fallback_controller, sample_services):
        """测试服务注册"""
        for service in sample_services:
            fallback_controller.register_service(
                service['name'],
                service['type'],
                service['endpoint']
            )
        
        assert len(fallback_controller.circuit_breakers) == 2
        assert 'primary_service' in fallback_controller.circuit_breakers
        assert 'fallback_service' in fallback_controller.circuit_breakers
    
    @pytest.mark.asyncio
    async def test_successful_execution(self, fallback_controller):
        """测试成功执行"""
        fallback_controller.register_service('test_service', 'mcp', 'ws://test')
        
        # 模拟成功的操作
        async def success_operation():
            return {'success': True, 'data': 'test_result'}
        
        result = await fallback_controller.execute_with_fallback(
            'test_service',
            success_operation
        )
        
        assert result['success'] is True
        assert result['data'] == 'test_result'
    
    @pytest.mark.asyncio
    async def test_fallback_execution(self, fallback_controller):
        """测试降级执行"""
        fallback_controller.register_service('primary', 'mcp', 'ws://primary')
        fallback_controller.register_service('fallback', 'http', 'http://fallback')
        
        # 模拟主服务失败
        async def failing_operation():
            raise Exception("Primary service failed")
        
        # 模拟降级服务成功
        async def fallback_operation():
            return {'success': True, 'data': 'fallback_result', 'source': 'fallback'}
        
        # 触发熔断器
        for _ in range(3):
            try:
                await fallback_controller.execute_with_fallback(
                    'primary',
                    failing_operation
                )
            except:
                pass
        
        # 现在应该使用降级服务
        with patch.object(fallback_controller, '_execute_fallback', return_value=await fallback_operation()):
            result = await fallback_controller.execute_with_fallback(
                'primary',
                failing_operation,
                fallback_services=['fallback']
            )
            
            assert result['success'] is True
            assert result['source'] == 'fallback'


class TestCacheManager:
    """缓存管理器单元测试"""
    
    @pytest.fixture
    def cache_config(self):
        """缓存配置"""
        return CacheConfig(
            enabled=True,
            redis_url=None,  # 使用内存缓存进行测试
            default_ttl=300,
            max_size=1000,
            strategy=CacheStrategy.LRU
        )
    
    @pytest.fixture
    def cache_manager(self, cache_config):
        """创建缓存管理器实例"""
        return CacheManager(cache_config)
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache_manager):
        """测试缓存设置和获取"""
        await cache_manager.initialize()
        
        # 设置缓存
        await cache_manager.set('test_key', {'data': 'test_value'}, ttl=60)
        
        # 获取缓存
        result = await cache_manager.get('test_key')
        
        assert result is not None
        assert result['data'] == 'test_value'
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_manager):
        """测试缓存过期"""
        await cache_manager.initialize()
        
        # 设置短期缓存
        await cache_manager.set('expire_key', {'data': 'expire_value'}, ttl=1)
        
        # 立即获取应该成功
        result = await cache_manager.get('expire_key')
        assert result is not None
        
        # 等待过期
        await asyncio.sleep(1.1)
        
        # 再次获取应该为空
        result = await cache_manager.get('expire_key')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache_manager):
        """测试缓存删除"""
        await cache_manager.initialize()
        
        # 设置缓存
        await cache_manager.set('delete_key', {'data': 'delete_value'})
        
        # 验证存在
        result = await cache_manager.get('delete_key')
        assert result is not None
        
        # 删除缓存
        await cache_manager.delete('delete_key')
        
        # 验证已删除
        result = await cache_manager.get('delete_key')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, cache_manager):
        """测试缓存清空"""
        await cache_manager.initialize()
        
        # 设置多个缓存项
        for i in range(5):
            await cache_manager.set(f'key_{i}', {'data': f'value_{i}'})
        
        # 验证缓存项存在
        for i in range(5):
            result = await cache_manager.get(f'key_{i}')
            assert result is not None
        
        # 清空缓存
        await cache_manager.clear()
        
        # 验证所有缓存项已清空
        for i in range(5):
            result = await cache_manager.get(f'key_{i}')
            assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_metrics(self, cache_manager):
        """测试缓存指标"""
        await cache_manager.initialize()
        
        # 执行一些缓存操作
        await cache_manager.set('metrics_key', {'data': 'metrics_value'})
        
        # 命中
        await cache_manager.get('metrics_key')
        await cache_manager.get('metrics_key')
        
        # 未命中
        await cache_manager.get('nonexistent_key')
        
        # 获取指标
        info = await cache_manager.get_cache_info()
        metrics = info['metrics']
        
        assert metrics['hits'] >= 2
        assert metrics['misses'] >= 1
        assert metrics['sets'] >= 1


class TestMonitoringSystem:
    """监控系统单元测试"""
    
    @pytest.fixture
    def monitoring_config(self):
        """监控配置"""
        return {
            'enabled': True,
            'check_interval': 1,
            'thresholds': {
                'cpu_percent': 80,
                'memory_percent': 85,
                'disk_percent': 90
            },
            'alerts': {
                'enabled': True,
                'webhook_url': 'http://localhost:9999/webhook'
            }
        }
    
    @pytest.fixture
    def monitoring_system(self, monitoring_config):
        """创建监控系统实例"""
        return MonitoringSystem(monitoring_config)
    
    def test_health_check_registration(self, monitoring_system):
        """测试健康检查注册"""
        # 注册健康检查
        def test_check():
            return HealthStatus.HEALTHY, "Test service is healthy"
        
        monitoring_system.register_health_check("test_service", test_check)
        
        assert "test_service" in monitoring_system.health_checks
        assert monitoring_system.health_checks["test_service"].check_func == test_check
    
    @pytest.mark.asyncio
    async def test_health_check_execution(self, monitoring_system):
        """测试健康检查执行"""
        # 注册健康检查
        def healthy_check():
            return HealthStatus.HEALTHY, "Service is healthy"
        
        def unhealthy_check():
            return HealthStatus.UNHEALTHY, "Service is down"
        
        monitoring_system.register_health_check("healthy_service", healthy_check)
        monitoring_system.register_health_check("unhealthy_service", unhealthy_check)
        
        # 执行健康检查
        results = await monitoring_system.run_health_checks()
        
        assert len(results) == 2
        assert results["healthy_service"]["status"] == HealthStatus.HEALTHY
        assert results["unhealthy_service"]["status"] == HealthStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_system_metrics_collection(self, monitoring_system):
        """测试系统指标收集"""
        metrics = await monitoring_system.collect_system_metrics()
        
        # 验证基本指标存在
        assert 'cpu_percent' in metrics
        assert 'memory_percent' in metrics
        assert 'disk_percent' in metrics
        assert 'timestamp' in metrics
        
        # 验证指标值的合理性
        assert 0 <= metrics['cpu_percent'] <= 100
        assert 0 <= metrics['memory_percent'] <= 100
        assert 0 <= metrics['disk_percent'] <= 100
    
    def test_alert_threshold_checking(self, monitoring_system):
        """测试告警阈值检查"""
        # 模拟超过阈值的指标
        high_metrics = {
            'cpu_percent': 85,  # 超过80%阈值
            'memory_percent': 90,  # 超过85%阈值
            'disk_percent': 75   # 未超过90%阈值
        }
        
        alerts = monitoring_system.check_alert_conditions(high_metrics)
        
        # 应该有2个告警
        assert len(alerts) == 2
        
        # 验证告警内容
        cpu_alert = next((a for a in alerts if 'CPU' in a.message), None)
        memory_alert = next((a for a in alerts if 'Memory' in a.message), None)
        
        assert cpu_alert is not None
        assert memory_alert is not None
        assert cpu_alert.level == AlertLevel.WARNING
        assert memory_alert.level == AlertLevel.WARNING


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])