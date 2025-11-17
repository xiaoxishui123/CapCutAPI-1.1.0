#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCutAPI v2 端点测试套件

测试内容：
1. POST /api/v2/drafts/<draft_id>/download/url - 生成下载链接
2. GET /api/v2/drafts/<draft_id>/download/stream - 流式下载
3. POST /api/v2/drafts/batch/download - 批量下载
4. GET /api/v2/drafts/<draft_id>/status - 状态检查
5. 废弃警告系统测试
6. 错误处理测试
"""

import unittest
import requests
import json
import time
from typing import Dict, List

# ===== 配置 =====
API_BASE = "http://localhost:9000"
TEST_DRAFT_ID = None  # 将在测试中创建


class TestAPIv2Download(unittest.TestCase):
    """API v2 下载端点测试"""

    @classmethod
    def setUpClass(cls):
        """测试前准备：创建测试草稿"""
        print("\n" + "=" * 60)
        print("开始 API v2 测试套件")
        print("=" * 60)

        # 创建测试草稿
        try:
            response = requests.post(f"{API_BASE}/create_draft", json={
                "width": 1080,
                "height": 1920
            })
            if response.status_code == 200:
                result = response.json()
                cls.test_draft_id = result.get('draft_id')
                print(f"✅ 测试草稿创建成功: {cls.test_draft_id}")

                # 添加测试视频素材
                video_response = requests.post(f"{API_BASE}/add_video", json={
                    "draft_id": cls.test_draft_id,
                    "url": "https://www.w3schools.com/html/mov_bbb.mp4",
                    "start_time": 0
                })
                if video_response.status_code == 200:
                    print("✅ 测试视频添加成功")

                # 保存草稿
                save_response = requests.post(f"{API_BASE}/save_draft", json={
                    "draft_id": cls.test_draft_id
                })
                if save_response.status_code == 200:
                    print("✅ 测试草稿保存成功")
                    time.sleep(2)  # 等待保存完成

        except Exception as e:
            print(f"⚠️ 测试草稿创建失败: {e}")
            cls.test_draft_id = "test_draft_id_fallback"

    def test_01_v2_generate_download_url(self):
        """测试 v2 生成下载链接端点"""
        print("\n[测试 1] v2 生成下载链接")

        response = requests.post(
            f"{API_BASE}/api/v2/drafts/{self.test_draft_id}/download/url",
            json={
                "client_os": "windows",
                "draft_folder": "",
                "force_save": False
            }
        )

        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # 验证响应格式
        self.assertEqual(response.status_code, 200)
        self.assertTrue(result.get('success'), "响应应该成功")
        self.assertIn('data', result, "响应应该包含 data 字段")
        self.assertIn('message', result, "响应应该包含 message 字段")

        # 验证 data 字段
        data = result.get('data', {})
        self.assertIn('draft_id', data, "data 应该包含 draft_id")
        self.assertIn('download_url', data, "data 应该包含 download_url")

        print("✅ v2 生成下载链接测试通过")

    def test_02_v2_stream_download(self):
        """测试 v2 流式下载端点"""
        print("\n[测试 2] v2 流式下载")

        response = requests.get(
            f"{API_BASE}/api/v2/drafts/{self.test_draft_id}/download/stream",
            params={
                "client_os": "windows",
                "draft_folder": ""
            },
            stream=True
        )

        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")

        # 验证响应
        # 注意：如果草稿不存在，可能返回 404 或 JSON 错误
        if response.status_code == 200:
            self.assertIn('application', response.headers.get('Content-Type', ''))
            print("✅ v2 流式下载测试通过（返回文件流）")
        else:
            # 如果失败，检查是否是标准错误响应
            result = response.json()
            self.assertIn('success', result)
            self.assertIn('error', result)
            self.assertIn('error_code', result)
            print(f"⚠️ v2 流式下载返回错误（这是正常的）: {result.get('error')}")

    def test_03_v2_batch_download(self):
        """测试 v2 批量下载端点"""
        print("\n[测试 3] v2 批量下载")

        response = requests.post(
            f"{API_BASE}/api/v2/drafts/batch/download",
            json={
                "draft_ids": [self.test_draft_id, "fake_draft_id_1", "fake_draft_id_2"],
                "client_os": "windows",
                "draft_folder": ""
            }
        )

        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # 验证响应格式
        self.assertEqual(response.status_code, 200)
        self.assertTrue(result.get('success'))
        self.assertIn('data', result)
        self.assertIn('message', result)

        # 验证 data 字段
        data = result.get('data', {})
        self.assertIn('total', data)
        self.assertIn('succeeded', data)
        self.assertIn('failed', data)
        self.assertIn('results', data)

        # 验证统计数据
        self.assertEqual(data['total'], 3, "总数应该是3")
        self.assertIsInstance(data['results'], list, "results 应该是列表")

        print(f"✅ v2 批量下载测试通过 - 成功: {data['succeeded']}, 失败: {data['failed']}")

    def test_04_v2_check_status(self):
        """测试 v2 状态检查端点"""
        print("\n[测试 4] v2 状态检查")

        response = requests.get(
            f"{API_BASE}/api/v2/drafts/{self.test_draft_id}/status",
            params={
                "client_os": "windows",
                "draft_folder": ""
            }
        )

        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # 验证响应格式
        self.assertEqual(response.status_code, 200)
        self.assertTrue(result.get('success'))
        self.assertIn('data', result)

        # 验证 data 字段
        data = result.get('data', {})
        self.assertIn('draft_id', data)
        # 状态字段可能存在也可能不存在，取决于实现
        # 这里只验证基本结构

        print("✅ v2 状态检查测试通过")

    def test_05_v2_error_handling(self):
        """测试 v2 错误处理"""
        print("\n[测试 5] v2 错误处理")

        # 测试不存在的草稿
        response = requests.post(
            f"{API_BASE}/api/v2/drafts/non_existent_draft_id/download/url",
            json={
                "client_os": "windows"
            }
        )

        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # 验证错误响应格式
        self.assertFalse(result.get('success'), "应该返回失败")
        self.assertIn('error', result, "应该包含 error 字段")
        self.assertIn('error_type', result, "应该包含 error_type 字段")
        self.assertIn('error_code', result, "应该包含 error_code 字段")

        # 验证错误码
        error_code = result.get('error_code')
        self.assertIsInstance(error_code, int, "error_code 应该是整数")
        self.assertGreaterEqual(error_code, 4000, "客户端错误码应该 >= 4000")

        print(f"✅ v2 错误处理测试通过 - 错误码: {error_code}, 类型: {result.get('error_type')}")

    def test_06_v2_batch_download_validation(self):
        """测试 v2 批量下载参数验证"""
        print("\n[测试 6] v2 批量下载参数验证")

        # 测试缺少 draft_ids
        response = requests.post(
            f"{API_BASE}/api/v2/drafts/batch/download",
            json={
                "client_os": "windows"
            }
        )

        print(f"状态码: {response.status_code}")
        result = response.json()

        # 应该返回错误
        self.assertFalse(result.get('success'))
        self.assertIn('error_code', result)
        print(f"✅ 缺少参数验证通过: {result.get('error')}")

        # 测试 draft_ids 超过限制
        response = requests.post(
            f"{API_BASE}/api/v2/drafts/batch/download",
            json={
                "draft_ids": [f"draft_{i}" for i in range(60)],  # 超过50个
                "client_os": "windows"
            }
        )

        result = response.json()
        self.assertFalse(result.get('success'))
        print(f"✅ 数量限制验证通过: {result.get('error')}")


class TestAPIv1Deprecation(unittest.TestCase):
    """API v1 废弃警告测试"""

    @classmethod
    def setUpClass(cls):
        """使用与 v2 相同的测试草稿"""
        cls.test_draft_id = TestAPIv2Download.test_draft_id

    def test_01_v1_deprecation_headers(self):
        """测试 v1 端点废弃警告 HTTP 头"""
        print("\n[测试 7] v1 废弃警告 HTTP 头")

        response = requests.post(
            f"{API_BASE}/generate_draft_url",
            json={
                "draft_id": self.test_draft_id,
                "client_os": "windows"
            }
        )

        print(f"状态码: {response.status_code}")

        # 检查废弃警告头
        headers = response.headers
        print(f"X-API-Deprecated: {headers.get('X-API-Deprecated')}")
        print(f"X-API-Alternative: {headers.get('X-API-Alternative')}")
        print(f"X-API-Sunset: {headers.get('X-API-Sunset')}")

        # 验证废弃警告头存在
        self.assertEqual(headers.get('X-API-Deprecated'), 'true')
        self.assertIsNotNone(headers.get('X-API-Alternative'))
        self.assertIsNotNone(headers.get('X-API-Sunset'))

        print("✅ v1 废弃警告 HTTP 头测试通过")

    def test_02_v1_deprecation_body(self):
        """测试 v1 端点废弃警告响应体"""
        print("\n[测试 8] v1 废弃警告响应体")

        response = requests.post(
            f"{API_BASE}/generate_draft_url",
            json={
                "draft_id": self.test_draft_id,
                "client_os": "windows"
            }
        )

        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # 检查响应体中的废弃警告
        self.assertIn('_deprecation_warning', result, "响应应该包含废弃警告")

        warning = result.get('_deprecation_warning', {})
        self.assertTrue(warning.get('deprecated'))
        self.assertIsNotNone(warning.get('alternative'))
        self.assertIsNotNone(warning.get('sunset_date'))

        print(f"✅ v1 废弃警告响应体测试通过")
        print(f"   替代端点: {warning.get('alternative')}")
        print(f"   下线日期: {warning.get('sunset_date')}")


class TestResponseFormat(unittest.TestCase):
    """响应格式对比测试"""

    @classmethod
    def setUpClass(cls):
        cls.test_draft_id = TestAPIv2Download.test_draft_id

    def test_01_v1_vs_v2_response_format(self):
        """测试 v1 vs v2 响应格式差异"""
        print("\n[测试 9] v1 vs v2 响应格式对比")

        # v1 响应
        v1_response = requests.post(
            f"{API_BASE}/generate_draft_url",
            json={
                "draft_id": self.test_draft_id,
                "client_os": "windows"
            }
        )
        v1_result = v1_response.json()

        # v2 响应
        v2_response = requests.post(
            f"{API_BASE}/api/v2/drafts/{self.test_draft_id}/download/url",
            json={
                "client_os": "windows"
            }
        )
        v2_result = v2_response.json()

        print("\nv1 响应结构:")
        print(f"  - success: {v1_result.get('success')}")
        print(f"  - output: {'存在' if 'output' in v1_result else '不存在'}")
        print(f"  - error: {'存在' if 'error' in v1_result else '不存在'}")

        print("\nv2 响应结构:")
        print(f"  - success: {v2_result.get('success')}")
        print(f"  - data: {'存在' if 'data' in v2_result else '不存在'}")
        print(f"  - message: {'存在' if 'message' in v2_result else '不存在'}")
        print(f"  - error: {'存在' if 'error' in v2_result else '不存在'}")

        # 验证结构差异
        if v1_result.get('success'):
            self.assertIn('output', v1_result, "v1 成功响应应该有 output 字段")

        if v2_result.get('success'):
            self.assertIn('data', v2_result, "v2 成功响应应该有 data 字段")
            self.assertIn('message', v2_result, "v2 成功响应应该有 message 字段")

        print("✅ v1 vs v2 响应格式对比测试通过")


class TestPerformance(unittest.TestCase):
    """性能基准测试"""

    @classmethod
    def setUpClass(cls):
        cls.test_draft_id = TestAPIv2Download.test_draft_id

    def test_01_v2_response_time(self):
        """测试 v2 端点响应时间"""
        print("\n[测试 10] v2 端点响应时间")

        endpoints = [
            ("生成下载链接", "POST", f"/api/v2/drafts/{self.test_draft_id}/download/url", {"client_os": "windows"}),
            ("状态检查", "GET", f"/api/v2/drafts/{self.test_draft_id}/status", None),
        ]

        for name, method, path, data in endpoints:
            times = []
            for _ in range(5):  # 测试5次取平均
                start = time.time()
                if method == "POST":
                    requests.post(f"{API_BASE}{path}", json=data)
                else:
                    requests.get(f"{API_BASE}{path}")
                elapsed = (time.time() - start) * 1000  # 转换为毫秒
                times.append(elapsed)

            avg_time = sum(times) / len(times)
            print(f"  {name}: 平均 {avg_time:.2f}ms (范围: {min(times):.2f}-{max(times):.2f}ms)")

            # 验证响应时间合理（< 2秒）
            self.assertLess(avg_time, 2000, f"{name} 响应时间应该 < 2秒")

        print("✅ v2 端点响应时间测试通过")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestAPIv2Download))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIv1Deprecation))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseFormat))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════╗
║           CapCutAPI v2 端点测试套件                        ║
║                                                            ║
║  测试内容:                                                  ║
║  1. v2 API 端点功能测试                                     ║
║  2. 废弃警告系统测试                                        ║
║  3. 响应格式对比测试                                        ║
║  4. 性能基准测试                                           ║
║                                                            ║
║  使用方法:                                                  ║
║    python test_api_v2.py                                   ║
╚════════════════════════════════════════════════════════════╝
    """)

    success = run_tests()
    exit(0 if success else 1)
