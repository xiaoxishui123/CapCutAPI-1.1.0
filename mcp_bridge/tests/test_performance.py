"""
MCP Bridge 性能测试套件
验证系统在高负载下的表现和性能指标
"""

import asyncio
import pytest
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, patch
import aiohttp
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_bridge.core.bridge_server import BridgeServer
from mcp_bridge.core.router import RouterManager, RoutingStrategy
from mcp_bridge.core.cache import CacheManager, CacheConfig, CacheStrategy


class TestPerformanceBenchmarks(AioHTTPTestCase):
    """性能基准测试"""
    
    async def get_application(self):
        """创建测试应用"""
        config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080,
                'workers': 1
            },
            'services': {
                'mcp_services': [
                    {
                        'name': 'capcut_service',
                        'type': 'mcp',
                        'endpoint': 'ws://localhost:3001/mcp',
                        'priority': 1,
                        'weight': 100,
                        'timeout': 30,
                        'enabled': True
                    }
                ]
            },
            'fallback': {'enabled': True},
            'cache': {
                'enabled': True,
                'strategy': 'LRU',
                'max_size': 10000,
                'default_ttl': 300
            },
            'monitoring': {'enabled': True}
        }
        
        self.bridge_server = BridgeServer(config)
        await self.bridge_server.initialize()
        
        return self.bridge_server.app
    
    async def tearDownAsync(self):
        """异步清理"""
        if hasattr(self, 'bridge_server'):
            await self.bridge_server.shutdown()
        await super().tearDownAsync()
    
    @unittest_run_loop
    async def test_single_request_latency(self):
        """测试单个请求延迟"""
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            mock_route.return_value = {
                'success': True,
                'data': {'result': 'test_data'}
            }
            
            request_data = {
                'method': 'capcut_create_draft',
                'params': {'title': 'Latency Test'}
            }
            
            # 预热
            for _ in range(5):
                await self.client.request(
                    'POST',
                    '/api/mcp/request',
                    json=request_data
                )
            
            # 测量延迟
            latencies = []
            for _ in range(100):
                start_time = time.time()
                
                resp = await self.client.request(
                    'POST',
                    '/api/mcp/request',
                    json=request_data
                )
                
                end_time = time.time()
                latency = (end_time - start_time) * 1000  # 转换为毫秒
                latencies.append(latency)
                
                self.assertEqual(resp.status, 200)
            
            # 计算统计信息
            avg_latency = statistics.mean(latencies)
            p50_latency = statistics.median(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
            
            print(f"\n单请求延迟统计:")
            print(f"平均延迟: {avg_latency:.2f}ms")
            print(f"P50延迟: {p50_latency:.2f}ms")
            print(f"P95延迟: {p95_latency:.2f}ms")
            print(f"P99延迟: {p99_latency:.2f}ms")
            
            # 性能断言（根据实际需求调整）
            assert avg_latency < 50, f"平均延迟过高: {avg_latency:.2f}ms"
            assert p95_latency < 100, f"P95延迟过高: {p95_latency:.2f}ms"
    
    @unittest_run_loop
    async def test_concurrent_requests_throughput(self):
        """测试并发请求吞吐量"""
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            mock_route.return_value = {
                'success': True,
                'data': {'result': 'concurrent_test'}
            }
            
            async def make_request(request_id: int):
                """发送单个请求"""
                request_data = {
                    'method': 'capcut_create_draft',
                    'params': {'title': f'Concurrent Test {request_id}'}
                }
                
                start_time = time.time()
                resp = await self.client.request(
                    'POST',
                    '/api/mcp/request',
                    json=request_data
                )
                end_time = time.time()
                
                return {
                    'status': resp.status,
                    'latency': (end_time - start_time) * 1000,
                    'request_id': request_id
                }
            
            # 测试不同并发级别
            concurrency_levels = [10, 50, 100, 200]
            
            for concurrency in concurrency_levels:
                print(f"\n测试并发级别: {concurrency}")
                
                start_time = time.time()
                
                # 创建并发任务
                tasks = [make_request(i) for i in range(concurrency)]
                results = await asyncio.gather(*tasks)
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # 计算吞吐量
                successful_requests = sum(1 for r in results if r['status'] == 200)
                throughput = successful_requests / total_time
                
                # 计算延迟统计
                latencies = [r['latency'] for r in results if r['status'] == 200]
                avg_latency = statistics.mean(latencies) if latencies else 0
                
                print(f"成功请求: {successful_requests}/{concurrency}")
                print(f"总耗时: {total_time:.2f}s")
                print(f"吞吐量: {throughput:.2f} req/s")
                print(f"平均延迟: {avg_latency:.2f}ms")
                
                # 性能断言
                assert successful_requests == concurrency, "部分请求失败"
                assert throughput > 50, f"吞吐量过低: {throughput:.2f} req/s"
    
    @unittest_run_loop
    async def test_sustained_load_performance(self):
        """测试持续负载性能"""
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            mock_route.return_value = {
                'success': True,
                'data': {'result': 'sustained_load_test'}
            }
            
            async def sustained_load_worker():
                """持续负载工作器"""
                request_data = {
                    'method': 'capcut_create_draft',
                    'params': {'title': 'Sustained Load Test'}
                }
                
                results = []
                for _ in range(50):  # 每个工作器发送50个请求
                    start_time = time.time()
                    
                    resp = await self.client.request(
                        'POST',
                        '/api/mcp/request',
                        json=request_data
                    )
                    
                    end_time = time.time()
                    
                    results.append({
                        'status': resp.status,
                        'latency': (end_time - start_time) * 1000,
                        'timestamp': end_time
                    })
                    
                    # 模拟真实负载间隔
                    await asyncio.sleep(0.01)
                
                return results
            
            print(f"\n持续负载测试 (10个并发工作器，每个50个请求)")
            
            start_time = time.time()
            
            # 启动10个并发工作器
            workers = [sustained_load_worker() for _ in range(10)]
            worker_results = await asyncio.gather(*workers)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 合并所有结果
            all_results = []
            for worker_result in worker_results:
                all_results.extend(worker_result)
            
            # 计算统计信息
            successful_requests = sum(1 for r in all_results if r['status'] == 200)
            total_requests = len(all_results)
            success_rate = successful_requests / total_requests * 100
            
            latencies = [r['latency'] for r in all_results if r['status'] == 200]
            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]
            
            throughput = successful_requests / total_time
            
            print(f"总请求数: {total_requests}")
            print(f"成功请求数: {successful_requests}")
            print(f"成功率: {success_rate:.2f}%")
            print(f"总耗时: {total_time:.2f}s")
            print(f"平均吞吐量: {throughput:.2f} req/s")
            print(f"平均延迟: {avg_latency:.2f}ms")
            print(f"P95延迟: {p95_latency:.2f}ms")
            
            # 性能断言
            assert success_rate >= 99, f"成功率过低: {success_rate:.2f}%"
            assert avg_latency < 100, f"平均延迟过高: {avg_latency:.2f}ms"
            assert throughput > 30, f"吞吐量过低: {throughput:.2f} req/s"


class TestCachePerformance:
    """缓存性能测试"""
    
    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器"""
        config = CacheConfig(
            enabled=True,
            redis_url=None,  # 使用内存缓存
            default_ttl=300,
            max_size=10000,
            strategy=CacheStrategy.LRU
        )
        return CacheManager(config)
    
    @pytest.mark.asyncio
    async def test_cache_write_performance(self, cache_manager):
        """测试缓存写入性能"""
        await cache_manager.initialize()
        
        # 测试数据
        test_data = {'key': 'value', 'number': 12345, 'list': [1, 2, 3, 4, 5]}
        
        # 预热
        for i in range(100):
            await cache_manager.set(f'warmup_key_{i}', test_data)
        
        # 性能测试
        write_times = []
        for i in range(1000):
            start_time = time.time()
            await cache_manager.set(f'perf_key_{i}', test_data)
            end_time = time.time()
            
            write_times.append((end_time - start_time) * 1000)  # 转换为毫秒
        
        # 统计信息
        avg_write_time = statistics.mean(write_times)
        p95_write_time = statistics.quantiles(write_times, n=20)[18]
        
        print(f"\n缓存写入性能:")
        print(f"平均写入时间: {avg_write_time:.3f}ms")
        print(f"P95写入时间: {p95_write_time:.3f}ms")
        print(f"写入吞吐量: {1000/avg_write_time:.0f} ops/ms")
        
        # 性能断言
        assert avg_write_time < 1, f"缓存写入过慢: {avg_write_time:.3f}ms"
    
    @pytest.mark.asyncio
    async def test_cache_read_performance(self, cache_manager):
        """测试缓存读取性能"""
        await cache_manager.initialize()
        
        # 准备测试数据
        test_data = {'key': 'value', 'number': 12345, 'list': [1, 2, 3, 4, 5]}
        
        # 写入测试数据
        for i in range(1000):
            await cache_manager.set(f'read_key_{i}', test_data)
        
        # 性能测试
        read_times = []
        for i in range(1000):
            start_time = time.time()
            result = await cache_manager.get(f'read_key_{i}')
            end_time = time.time()
            
            assert result is not None
            read_times.append((end_time - start_time) * 1000)  # 转换为毫秒
        
        # 统计信息
        avg_read_time = statistics.mean(read_times)
        p95_read_time = statistics.quantiles(read_times, n=20)[18]
        
        print(f"\n缓存读取性能:")
        print(f"平均读取时间: {avg_read_time:.3f}ms")
        print(f"P95读取时间: {p95_read_time:.3f}ms")
        print(f"读取吞吐量: {1000/avg_read_time:.0f} ops/ms")
        
        # 性能断言
        assert avg_read_time < 0.5, f"缓存读取过慢: {avg_read_time:.3f}ms"
    
    @pytest.mark.asyncio
    async def test_cache_concurrent_access(self, cache_manager):
        """测试缓存并发访问性能"""
        await cache_manager.initialize()
        
        # 准备测试数据
        test_data = {'concurrent': 'test', 'data': list(range(100))}
        
        async def concurrent_worker(worker_id: int, operation_count: int):
            """并发工作器"""
            results = []
            
            for i in range(operation_count):
                key = f'concurrent_key_{worker_id}_{i}'
                
                # 写入
                start_time = time.time()
                await cache_manager.set(key, test_data)
                write_time = time.time() - start_time
                
                # 读取
                start_time = time.time()
                result = await cache_manager.get(key)
                read_time = time.time() - start_time
                
                results.append({
                    'write_time': write_time * 1000,
                    'read_time': read_time * 1000,
                    'success': result is not None
                })
            
            return results
        
        print(f"\n缓存并发访问测试 (10个工作器，每个100次操作)")
        
        start_time = time.time()
        
        # 启动并发工作器
        workers = [concurrent_worker(i, 100) for i in range(10)]
        worker_results = await asyncio.gather(*workers)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 合并结果
        all_results = []
        for worker_result in worker_results:
            all_results.extend(worker_result)
        
        # 统计信息
        total_operations = len(all_results) * 2  # 每个结果包含读写两个操作
        successful_operations = sum(2 for r in all_results if r['success'])
        
        write_times = [r['write_time'] for r in all_results]
        read_times = [r['read_time'] for r in all_results]
        
        avg_write_time = statistics.mean(write_times)
        avg_read_time = statistics.mean(read_times)
        
        throughput = total_operations / total_time
        
        print(f"总操作数: {total_operations}")
        print(f"成功操作数: {successful_operations}")
        print(f"总耗时: {total_time:.2f}s")
        print(f"操作吞吐量: {throughput:.2f} ops/s")
        print(f"平均写入时间: {avg_write_time:.3f}ms")
        print(f"平均读取时间: {avg_read_time:.3f}ms")
        
        # 性能断言
        assert successful_operations == total_operations, "部分操作失败"
        assert throughput > 1000, f"并发吞吐量过低: {throughput:.2f} ops/s"


class TestRouterPerformance:
    """路由器性能测试"""
    
    @pytest.fixture
    def router_manager(self):
        """创建路由管理器"""
        from mcp_bridge.core.router import ServiceEndpoint
        
        router = RouterManager()
        
        # 添加多个服务
        for i in range(10):
            service = ServiceEndpoint(
                name=f"service_{i}",
                service_type="mcp",
                endpoint=f"ws://localhost:300{i}/mcp",
                priority=i % 3 + 1,
                weight=100 - i * 5,
                timeout=30,
                enabled=True
            )
            router.register_service(service)
        
        return router
    
    def test_routing_decision_performance(self, router_manager):
        """测试路由决策性能"""
        # 测试不同路由策略的性能
        strategies = [
            RoutingStrategy.PRIORITY,
            RoutingStrategy.ROUND_ROBIN,
            RoutingStrategy.WEIGHTED,
            RoutingStrategy.LEAST_CONNECTIONS
        ]
        
        for strategy in strategies:
            router_manager.set_routing_strategy(strategy)
            
            # 性能测试
            start_time = time.time()
            
            for _ in range(10000):
                service = router_manager.get_next_service("test_method")
                assert service is not None
            
            end_time = time.time()
            total_time = end_time - start_time
            
            decisions_per_second = 10000 / total_time
            
            print(f"\n{strategy.value} 路由策略性能:")
            print(f"10000次路由决策耗时: {total_time:.3f}s")
            print(f"路由决策速度: {decisions_per_second:.0f} decisions/s")
            
            # 性能断言
            assert decisions_per_second > 50000, f"{strategy.value} 路由决策过慢"
    
    def test_service_metrics_update_performance(self, router_manager):
        """测试服务指标更新性能"""
        service_names = [f"service_{i}" for i in range(10)]
        
        # 性能测试
        start_time = time.time()
        
        for _ in range(1000):
            for service_name in service_names:
                # 模拟请求结果记录
                success = True
                response_time = 0.1
                router_manager.record_request_result(service_name, success, response_time)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        updates_per_second = 10000 / total_time  # 1000 * 10 services
        
        print(f"\n服务指标更新性能:")
        print(f"10000次指标更新耗时: {total_time:.3f}s")
        print(f"指标更新速度: {updates_per_second:.0f} updates/s")
        
        # 验证指标正确性
        for service_name in service_names:
            metrics = router_manager.get_service_metrics(service_name)
            assert metrics['total_requests'] == 1000
            assert metrics['successful_requests'] == 1000
            assert metrics['success_rate'] == 1.0
        
        # 性能断言
        assert updates_per_second > 10000, f"指标更新过慢: {updates_per_second:.0f} updates/s"


if __name__ == '__main__':
    # 运行性能测试
    pytest.main([__file__, '-v', '--tb=short', '-s'])  # -s 显示print输出