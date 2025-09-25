"""
MCP Bridge 集成测试套件
验证完整的系统功能和工作流程
"""

import asyncio
import pytest
import json
import time
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_bridge.core.bridge_server import BridgeServer, ServiceConfig
from mcp_bridge.core.router import RouterManager, RoutingStrategy
from mcp_bridge.core.fallback import FallbackController, CircuitBreakerConfig
from mcp_bridge.core.cache import CacheManager, CacheConfig
from mcp_bridge.core.monitoring import MonitoringSystem, HealthCheck, HealthStatus


class TestMCPBridgeIntegration(AioHTTPTestCase):
    """MCP Bridge 集成测试"""
    
    async def get_application(self):
        """创建测试应用"""
        # 测试配置
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
                ],
                'http_services': [
                    {
                        'name': 'capcut_http',
                        'type': 'http',
                        'endpoint': 'http://localhost:3000/api',
                        'priority': 2,
                        'weight': 50,
                        'timeout': 15,
                        'enabled': True
                    }
                ]
            },
            'fallback': {
                'enabled': True,
                'circuit_breaker': {
                    'failure_threshold': 5,
                    'recovery_timeout': 30,
                    'half_open_max_calls': 3
                }
            },
            'cache': {
                'enabled': True,
                'redis_url': 'redis://localhost:6379',
                'default_ttl': 300
            },
            'monitoring': {
                'enabled': True,
                'thresholds': {
                    'cpu_percent': 80,
                    'memory_percent': 85
                }
            }
        }
        
        # 创建Bridge服务器
        self.bridge_server = BridgeServer(config)
        await self.bridge_server.initialize()
        
        return self.bridge_server.app
    
    async def setUpAsync(self):
        """异步设置"""
        await super().setUpAsync()
        
        # 模拟外部服务
        self.mock_mcp_responses = {}
        self.mock_http_responses = {}
        
        # 设置模拟响应
        self._setup_mock_responses()
    
    async def tearDownAsync(self):
        """异步清理"""
        if hasattr(self, 'bridge_server'):
            await self.bridge_server.shutdown()
        await super().tearDownAsync()
    
    def _setup_mock_responses(self):
        """设置模拟响应"""
        # CapCut API 模拟响应
        self.mock_mcp_responses = {
            'capcut_create_draft': {
                'success': True,
                'data': {
                    'draft_id': 'test_draft_123',
                    'status': 'created',
                    'created_at': '2024-01-01T00:00:00Z'
                }
            },
            'capcut_upload_video': {
                'success': True,
                'data': {
                    'upload_id': 'upload_456',
                    'status': 'uploaded',
                    'file_url': 'https://example.com/video.mp4'
                }
            },
            'capcut_get_draft': {
                'success': True,
                'data': {
                    'draft_id': 'test_draft_123',
                    'status': 'ready',
                    'assets': ['video1.mp4', 'audio1.mp3']
                }
            }
        }
        
        self.mock_http_responses = {
            '/api/capcut/create_draft': {
                'status': 200,
                'data': self.mock_mcp_responses['capcut_create_draft']
            },
            '/api/capcut/upload_video': {
                'status': 200,
                'data': self.mock_mcp_responses['capcut_upload_video']
            }
        }
    
    @unittest_run_loop
    async def test_basic_mcp_request_routing(self):
        """测试基本MCP请求路由"""
        # 模拟MCP服务响应
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            mock_route.return_value = self.mock_mcp_responses['capcut_create_draft']
            
            # 发送请求
            request_data = {
                'method': 'capcut_create_draft',
                'params': {
                    'title': 'Test Video',
                    'description': 'Integration test video'
                }
            }
            
            resp = await self.client.request(
                'POST',
                '/api/mcp/request',
                json=request_data
            )
            
            self.assertEqual(resp.status, 200)
            
            response_data = await resp.json()
            self.assertTrue(response_data['success'])
            self.assertEqual(response_data['data']['draft_id'], 'test_draft_123')
            
            # 验证路由器被调用
            mock_route.assert_called_once()
    
    @unittest_run_loop
    async def test_fallback_mechanism(self):
        """测试降级机制"""
        # 模拟MCP服务失败，HTTP服务成功
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            # 第一次调用MCP失败
            mock_route.side_effect = [
                Exception("MCP service unavailable"),
                self.mock_http_responses['/api/capcut/create_draft']['data']
            ]
            
            request_data = {
                'method': 'capcut_create_draft',
                'params': {
                    'title': 'Test Video',
                    'description': 'Fallback test'
                }
            }
            
            resp = await self.client.request(
                'POST',
                '/api/mcp/request',
                json=request_data
            )
            
            self.assertEqual(resp.status, 200)
            
            response_data = await resp.json()
            self.assertTrue(response_data['success'])
            # 验证使用了降级服务
            self.assertIn('fallback', response_data.get('metadata', {}))
    
    @unittest_run_loop
    async def test_caching_functionality(self):
        """测试缓存功能"""
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            mock_route.return_value = self.mock_mcp_responses['capcut_get_draft']
            
            request_data = {
                'method': 'capcut_get_draft',
                'params': {
                    'draft_id': 'test_draft_123'
                }
            }
            
            # 第一次请求
            resp1 = await self.client.request(
                'POST',
                '/api/mcp/request',
                json=request_data
            )
            
            self.assertEqual(resp1.status, 200)
            
            # 第二次请求（应该使用缓存）
            resp2 = await self.client.request(
                'POST',
                '/api/mcp/request',
                json=request_data
            )
            
            self.assertEqual(resp2.status, 200)
            
            # 验证只调用了一次实际服务
            self.assertEqual(mock_route.call_count, 1)
            
            # 检查缓存指标
            cache_info = await self.bridge_server.cache_manager.get_cache_info()
            self.assertGreater(cache_info['metrics']['hits'], 0)
    
    @unittest_run_loop
    async def test_health_check_endpoint(self):
        """测试健康检查端点"""
        resp = await self.client.request('GET', '/health')
        
        self.assertEqual(resp.status, 200)
        
        health_data = await resp.json()
        self.assertIn('status', health_data)
        self.assertIn('checks', health_data)
        self.assertIn('timestamp', health_data)
    
    @unittest_run_loop
    async def test_metrics_endpoint(self):
        """测试指标端点"""
        resp = await self.client.request('GET', '/metrics')
        
        self.assertEqual(resp.status, 200)
        
        metrics_text = await resp.text()
        self.assertIn('mcp_bridge_requests_total', metrics_text)
        self.assertIn('mcp_bridge_request_duration_seconds', metrics_text)
    
    @unittest_run_loop
    async def test_circuit_breaker_functionality(self):
        """测试熔断器功能"""
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            # 模拟连续失败
            mock_route.side_effect = Exception("Service error")
            
            request_data = {
                'method': 'capcut_create_draft',
                'params': {'title': 'Test'}
            }
            
            # 发送多个失败请求触发熔断器
            for i in range(6):  # 超过failure_threshold(5)
                resp = await self.client.request(
                    'POST',
                    '/api/mcp/request',
                    json=request_data
                )
                
                if i < 5:
                    self.assertEqual(resp.status, 500)  # 服务错误
                else:
                    # 熔断器打开，应该快速失败
                    self.assertEqual(resp.status, 503)  # 服务不可用
    
    @unittest_run_loop
    async def test_concurrent_requests(self):
        """测试并发请求处理"""
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            mock_route.return_value = self.mock_mcp_responses['capcut_create_draft']
            
            # 创建多个并发请求
            async def make_request(i):
                request_data = {
                    'method': 'capcut_create_draft',
                    'params': {
                        'title': f'Test Video {i}',
                        'description': f'Concurrent test {i}'
                    }
                }
                
                resp = await self.client.request(
                    'POST',
                    '/api/mcp/request',
                    json=request_data
                )
                
                return resp.status, await resp.json()
            
            # 发送10个并发请求
            tasks = [make_request(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            
            # 验证所有请求都成功
            for status, data in results:
                self.assertEqual(status, 200)
                self.assertTrue(data['success'])
    
    @unittest_run_loop
    async def test_request_timeout_handling(self):
        """测试请求超时处理"""
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            # 模拟超时
            async def slow_response():
                await asyncio.sleep(2)  # 超过默认超时时间
                return self.mock_mcp_responses['capcut_create_draft']
            
            mock_route.side_effect = slow_response
            
            request_data = {
                'method': 'capcut_create_draft',
                'params': {'title': 'Timeout Test'}
            }
            
            resp = await self.client.request(
                'POST',
                '/api/mcp/request',
                json=request_data
            )
            
            # 应该返回超时错误
            self.assertEqual(resp.status, 408)
    
    @unittest_run_loop
    async def test_service_discovery_and_routing(self):
        """测试服务发现和路由"""
        # 获取服务列表
        resp = await self.client.request('GET', '/api/services')
        
        self.assertEqual(resp.status, 200)
        
        services_data = await resp.json()
        self.assertIn('mcp_services', services_data)
        self.assertIn('http_services', services_data)
        
        # 验证服务配置
        mcp_services = services_data['mcp_services']
        self.assertTrue(len(mcp_services) > 0)
        
        capcut_service = next(
            (s for s in mcp_services if s['name'] == 'capcut_service'),
            None
        )
        self.assertIsNotNone(capcut_service)
        self.assertTrue(capcut_service['enabled'])
    
    @unittest_run_loop
    async def test_error_handling_and_logging(self):
        """测试错误处理和日志记录"""
        # 发送无效请求
        invalid_request = {
            'method': '',  # 空方法名
            'params': {}
        }
        
        resp = await self.client.request(
            'POST',
            '/api/mcp/request',
            json=invalid_request
        )
        
        self.assertEqual(resp.status, 400)
        
        error_data = await resp.json()
        self.assertFalse(error_data['success'])
        self.assertIn('error', error_data)
        self.assertIn('message', error_data['error'])
    
    @unittest_run_loop
    async def test_configuration_reload(self):
        """测试配置重载"""
        # 获取当前配置
        resp = await self.client.request('GET', '/api/config')
        
        self.assertEqual(resp.status, 200)
        
        config_data = await resp.json()
        self.assertIn('services', config_data)
        self.assertIn('fallback', config_data)
        self.assertIn('cache', config_data)


class TestShortVideoWorkflow(AioHTTPTestCase):
    """短视频工作流集成测试"""
    
    async def get_application(self):
        """创建测试应用"""
        # 使用与主测试相同的配置
        config = {
            'server': {'host': '127.0.0.1', 'port': 8080, 'workers': 1},
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
            'cache': {'enabled': True},
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
    async def test_complete_video_creation_workflow(self):
        """测试完整的视频创建工作流"""
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            # 模拟工作流步骤
            workflow_responses = [
                # 1. 创建草稿
                {
                    'success': True,
                    'data': {
                        'draft_id': 'draft_123',
                        'status': 'created'
                    }
                },
                # 2. 上传视频
                {
                    'success': True,
                    'data': {
                        'upload_id': 'upload_456',
                        'status': 'uploaded'
                    }
                },
                # 3. 上传音频
                {
                    'success': True,
                    'data': {
                        'upload_id': 'upload_789',
                        'status': 'uploaded'
                    }
                },
                # 4. 添加字幕
                {
                    'success': True,
                    'data': {
                        'subtitle_id': 'subtitle_101',
                        'status': 'added'
                    }
                },
                # 5. 导出视频
                {
                    'success': True,
                    'data': {
                        'export_id': 'export_202',
                        'status': 'exporting',
                        'estimated_time': 120
                    }
                },
                # 6. 获取导出状态
                {
                    'success': True,
                    'data': {
                        'export_id': 'export_202',
                        'status': 'completed',
                        'download_url': 'https://example.com/final_video.mp4'
                    }
                }
            ]
            
            mock_route.side_effect = workflow_responses
            
            # 执行工作流步骤
            workflow_steps = [
                ('capcut_create_draft', {'title': 'Test Video', 'description': 'Workflow test'}),
                ('capcut_upload_video', {'draft_id': 'draft_123', 'file_path': '/tmp/video.mp4'}),
                ('capcut_upload_audio', {'draft_id': 'draft_123', 'file_path': '/tmp/audio.mp3'}),
                ('capcut_add_subtitle', {'draft_id': 'draft_123', 'subtitle_text': 'Hello World'}),
                ('capcut_export_video', {'draft_id': 'draft_123', 'quality': 'HD'}),
                ('capcut_get_export_status', {'export_id': 'export_202'})
            ]
            
            results = []
            for method, params in workflow_steps:
                request_data = {
                    'method': method,
                    'params': params
                }
                
                resp = await self.client.request(
                    'POST',
                    '/api/mcp/request',
                    json=request_data
                )
                
                self.assertEqual(resp.status, 200)
                
                response_data = await resp.json()
                self.assertTrue(response_data['success'])
                results.append(response_data)
                
                # 模拟步骤间的延迟
                await asyncio.sleep(0.1)
            
            # 验证工作流完成
            final_result = results[-1]
            self.assertEqual(final_result['data']['status'], 'completed')
            self.assertIn('download_url', final_result['data'])
    
    @unittest_run_loop
    async def test_workflow_error_recovery(self):
        """测试工作流错误恢复"""
        with patch.object(self.bridge_server.router_manager, 'route_request') as mock_route:
            # 模拟第二步失败，然后重试成功
            workflow_responses = [
                # 1. 创建草稿成功
                {
                    'success': True,
                    'data': {'draft_id': 'draft_123', 'status': 'created'}
                },
                # 2. 上传视频失败
                Exception("Upload failed"),
                # 3. 重试上传视频成功
                {
                    'success': True,
                    'data': {'upload_id': 'upload_456', 'status': 'uploaded'}
                }
            ]
            
            mock_route.side_effect = workflow_responses
            
            # 步骤1：创建草稿
            resp1 = await self.client.request(
                'POST',
                '/api/mcp/request',
                json={
                    'method': 'capcut_create_draft',
                    'params': {'title': 'Error Recovery Test'}
                }
            )
            
            self.assertEqual(resp1.status, 200)
            
            # 步骤2：上传视频（失败）
            resp2 = await self.client.request(
                'POST',
                '/api/mcp/request',
                json={
                    'method': 'capcut_upload_video',
                    'params': {'draft_id': 'draft_123', 'file_path': '/tmp/video.mp4'}
                }
            )
            
            self.assertEqual(resp2.status, 500)  # 应该返回错误
            
            # 步骤3：重试上传视频（成功）
            resp3 = await self.client.request(
                'POST',
                '/api/mcp/request',
                json={
                    'method': 'capcut_upload_video',
                    'params': {'draft_id': 'draft_123', 'file_path': '/tmp/video.mp4'}
                }
            )
            
            self.assertEqual(resp3.status, 200)
            
            response_data = await resp3.json()
            self.assertTrue(response_data['success'])


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])