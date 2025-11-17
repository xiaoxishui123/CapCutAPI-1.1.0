#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCutAPI 性能基准测试

对比 v1 和 v2 API 的性能差异
"""

import requests
import time
import statistics
import json
from typing import List, Dict, Tuple
from datetime import datetime

# ===== 配置 =====
API_BASE = "http://localhost:9000"
TEST_ITERATIONS = 10  # 每个测试迭代次数
WARMUP_ITERATIONS = 2  # 预热次数


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def measure_request(method: str, url: str, **kwargs) -> Tuple[float, int, bool]:
    """
    测量单个请求的性能

    Returns:
        (响应时间(ms), 状态码, 是否成功)
    """
    start = time.time()
    try:
        if method == "POST":
            response = requests.post(url, **kwargs)
        elif method == "GET":
            response = requests.get(url, **kwargs)
        else:
            raise ValueError(f"不支持的方法: {method}")

        elapsed = (time.time() - start) * 1000  # 转换为毫秒
        return elapsed, response.status_code, response.status_code < 400
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return elapsed, 0, False


def run_benchmark(name: str, method: str, url: str, iterations: int = TEST_ITERATIONS, **kwargs) -> Dict:
    """
    运行基准测试

    Args:
        name: 测试名称
        method: HTTP 方法
        url: 请求 URL
        iterations: 迭代次数
        **kwargs: 请求参数

    Returns:
        测试结果统计
    """
    print(f"\n{Colors.CYAN}测试: {name}{Colors.END}")

    times = []
    success_count = 0

    # 预热
    print(f"  预热中 ({WARMUP_ITERATIONS} 次)...", end=' ')
    for _ in range(WARMUP_ITERATIONS):
        measure_request(method, url, **kwargs)
    print("✓")

    # 正式测试
    print(f"  执行测试 ({iterations} 次)...", end=' ')
    for i in range(iterations):
        elapsed, status_code, success = measure_request(method, url, **kwargs)
        times.append(elapsed)
        if success:
            success_count += 1
    print("✓")

    # 统计
    result = {
        'name': name,
        'iterations': iterations,
        'min': min(times),
        'max': max(times),
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'success_rate': (success_count / iterations) * 100,
        'times': times
    }

    # 打印结果
    print(f"  {Colors.GREEN}结果:{Colors.END}")
    print(f"    平均: {result['mean']:.2f}ms")
    print(f"    中位数: {result['median']:.2f}ms")
    print(f"    范围: {result['min']:.2f}ms - {result['max']:.2f}ms")
    print(f"    标准差: {result['stdev']:.2f}ms")
    print(f"    成功率: {result['success_rate']:.1f}%")

    return result


def create_test_draft() -> str:
    """创建测试草稿"""
    print(f"\n{Colors.BOLD}准备测试环境{Colors.END}")
    print("  创建测试草稿...", end=' ')

    try:
        response = requests.post(f"{API_BASE}/create_draft", json={
            "width": 1080,
            "height": 1920
        })

        if response.status_code == 200:
            draft_id = response.json().get('draft_id')
            print(f"✓ ({draft_id})")

            # 添加视频
            print("  添加测试视频...", end=' ')
            requests.post(f"{API_BASE}/add_video", json={
                "draft_id": draft_id,
                "url": "https://www.w3schools.com/html/mov_bbb.mp4"
            })
            print("✓")

            # 保存草稿
            print("  保存草稿...", end=' ')
            requests.post(f"{API_BASE}/save_draft", json={
                "draft_id": draft_id
            })
            print("✓")

            time.sleep(2)  # 等待保存完成
            return draft_id
        else:
            print(f"{Colors.RED}✗{Colors.END}")
            return "test_draft_fallback"
    except Exception as e:
        print(f"{Colors.RED}✗ ({e}){Colors.END}")
        return "test_draft_fallback"


def benchmark_download_url(draft_id: str) -> Tuple[Dict, Dict]:
    """基准测试：生成下载链接"""
    print(f"\n{Colors.BOLD}═══ 基准测试 1: 生成下载链接 ═══{Colors.END}")

    # v1 测试
    v1_result = run_benchmark(
        name="v1 - POST /generate_draft_url",
        method="POST",
        url=f"{API_BASE}/generate_draft_url",
        json={
            "draft_id": draft_id,
            "client_os": "windows"
        }
    )

    # v2 测试
    v2_result = run_benchmark(
        name="v2 - POST /api/v2/drafts/<id>/download/url",
        method="POST",
        url=f"{API_BASE}/api/v2/drafts/{draft_id}/download/url",
        json={
            "client_os": "windows"
        }
    )

    # 对比
    print_comparison(v1_result, v2_result)

    return v1_result, v2_result


def benchmark_stream_download(draft_id: str) -> Tuple[Dict, Dict]:
    """基准测试：流式下载"""
    print(f"\n{Colors.BOLD}═══ 基准测试 2: 流式下载 ═══{Colors.END}")

    # v1 测试
    v1_result = run_benchmark(
        name="v1 - GET /api/drafts/download/proxy/<id>",
        method="GET",
        url=f"{API_BASE}/api/drafts/download/proxy/{draft_id}",
        params={
            "client_os": "windows"
        },
        stream=True,
        iterations=5  # 下载测试减少次数
    )

    # v2 测试
    v2_result = run_benchmark(
        name="v2 - GET /api/v2/drafts/<id>/download/stream",
        method="GET",
        url=f"{API_BASE}/api/v2/drafts/{draft_id}/download/stream",
        params={
            "client_os": "windows"
        },
        stream=True,
        iterations=5
    )

    # 对比
    print_comparison(v1_result, v2_result)

    return v1_result, v2_result


def benchmark_batch_download(draft_id: str) -> Tuple[Dict, Dict]:
    """基准测试：批量下载"""
    print(f"\n{Colors.BOLD}═══ 基准测试 3: 批量下载 ═══{Colors.END}")

    draft_ids = [draft_id, "fake_1", "fake_2"]

    # v1 测试
    v1_result = run_benchmark(
        name="v1 - POST /api/drafts/batch-download",
        method="POST",
        url=f"{API_BASE}/api/drafts/batch-download",
        json={
            "draft_ids": draft_ids,
            "client_os": "windows"
        }
    )

    # v2 测试
    v2_result = run_benchmark(
        name="v2 - POST /api/v2/drafts/batch/download",
        method="POST",
        url=f"{API_BASE}/api/v2/drafts/batch/download",
        json={
            "draft_ids": draft_ids,
            "client_os": "windows"
        }
    )

    # 对比
    print_comparison(v1_result, v2_result)

    return v1_result, v2_result


def benchmark_decorator_overhead(draft_id: str) -> Dict:
    """基准测试：装饰器开销"""
    print(f"\n{Colors.BOLD}═══ 基准测试 4: 装饰器开销 ═══{Colors.END}")

    # 测试状态检查端点（无装饰器）
    no_decorator = run_benchmark(
        name="无装饰器 - GET /health",
        method="GET",
        url=f"{API_BASE}/health",
        iterations=20
    )

    # 测试 v2 端点（有装饰器）
    with_decorator = run_benchmark(
        name="有装饰器 - GET /api/v2/drafts/<id>/status",
        method="GET",
        url=f"{API_BASE}/api/v2/drafts/{draft_id}/status",
        params={"client_os": "windows"},
        iterations=20
    )

    # 计算开销
    overhead = with_decorator['mean'] - no_decorator['mean']
    overhead_pct = (overhead / no_decorator['mean']) * 100 if no_decorator['mean'] > 0 else 0

    print(f"\n{Colors.YELLOW}装饰器开销分析:{Colors.END}")
    print(f"  无装饰器平均响应时间: {no_decorator['mean']:.2f}ms")
    print(f"  有装饰器平均响应时间: {with_decorator['mean']:.2f}ms")
    print(f"  装饰器额外开销: {overhead:.2f}ms ({overhead_pct:.1f}%)")

    if overhead < 5:
        print(f"  {Colors.GREEN}✓ 开销可忽略 (< 5ms){Colors.END}")
    elif overhead < 20:
        print(f"  {Colors.YELLOW}⚠ 开销较小 (5-20ms){Colors.END}")
    else:
        print(f"  {Colors.RED}✗ 开销较大 (> 20ms){Colors.END}")

    return {
        'no_decorator': no_decorator,
        'with_decorator': with_decorator,
        'overhead_ms': overhead,
        'overhead_pct': overhead_pct
    }


def print_comparison(v1: Dict, v2: Dict):
    """打印 v1 vs v2 对比"""
    print(f"\n{Colors.YELLOW}性能对比:{Colors.END}")

    improvement = ((v1['mean'] - v2['mean']) / v1['mean']) * 100 if v1['mean'] > 0 else 0

    print(f"  v1 平均响应时间: {v1['mean']:.2f}ms")
    print(f"  v2 平均响应时间: {v2['mean']:.2f}ms")

    if improvement > 5:
        print(f"  {Colors.GREEN}✓ v2 快 {improvement:.1f}%{Colors.END}")
    elif improvement < -5:
        print(f"  {Colors.RED}✗ v2 慢 {abs(improvement):.1f}%{Colors.END}")
    else:
        print(f"  {Colors.CYAN}≈ 性能相当 ({improvement:+.1f}%){Colors.END}")


def generate_report(results: Dict):
    """生成性能报告"""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}性能基准测试报告{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")

    print(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试迭代: {TEST_ITERATIONS} 次")
    print(f"预热迭代: {WARMUP_ITERATIONS} 次")

    # 总结表格
    print(f"\n{Colors.BOLD}性能总结:{Colors.END}")
    print("\n┌─────────────────────────────┬──────────┬──────────┬──────────┐")
    print("│ 测试项目                    │ v1 (ms)  │ v2 (ms)  │ 差异     │")
    print("├─────────────────────────────┼──────────┼──────────┼──────────┤")

    for test_name, (v1, v2) in results.items():
        if test_name != 'decorator_overhead':
            improvement = ((v1['mean'] - v2['mean']) / v1['mean']) * 100 if v1['mean'] > 0 else 0
            diff_color = Colors.GREEN if improvement > 0 else Colors.RED if improvement < -5 else Colors.CYAN
            print(f"│ {test_name:27} │ {v1['mean']:8.2f} │ {v2['mean']:8.2f} │ {diff_color}{improvement:+7.1f}%{Colors.END} │")

    print("└─────────────────────────────┴──────────┴──────────┴──────────┘")

    # 装饰器开销
    if 'decorator_overhead' in results:
        overhead = results['decorator_overhead']
        print(f"\n{Colors.BOLD}装饰器开销:{Colors.END}")
        print(f"  额外延迟: {overhead['overhead_ms']:.2f}ms ({overhead['overhead_pct']:.1f}%)")

        if overhead['overhead_ms'] < 5:
            print(f"  {Colors.GREEN}✓ 可忽略{Colors.END}")
        else:
            print(f"  {Colors.YELLOW}⚠ 需要关注{Colors.END}")

    # 建议
    print(f"\n{Colors.BOLD}性能建议:{Colors.END}")

    # 计算平均改善
    improvements = []
    for test_name, (v1, v2) in results.items():
        if test_name != 'decorator_overhead':
            improvement = ((v1['mean'] - v2['mean']) / v1['mean']) * 100 if v1['mean'] > 0 else 0
            improvements.append(improvement)

    avg_improvement = sum(improvements) / len(improvements) if improvements else 0

    if avg_improvement > 5:
        print(f"  {Colors.GREEN}✓ v2 API 整体性能优于 v1 (平均快 {avg_improvement:.1f}%){Colors.END}")
        print(f"  {Colors.GREEN}✓ 建议尽快迁移到 v2 API{Colors.END}")
    elif avg_improvement < -5:
        print(f"  {Colors.YELLOW}⚠ v2 API 性能略低于 v1 (平均慢 {abs(avg_improvement):.1f}%){Colors.END}")
        print(f"  {Colors.YELLOW}⚠ 需要进一步优化装饰器逻辑{Colors.END}")
    else:
        print(f"  {Colors.CYAN}≈ v2 API 性能与 v1 相当{Colors.END}")
        print(f"  {Colors.CYAN}≈ 可以安全迁移，性能不会有明显影响{Colors.END}")

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")


def main():
    """主函数"""
    print(f"""
{Colors.BOLD}╔════════════════════════════════════════════════════════════╗
║          CapCutAPI 性能基准测试工具                        ║
║                                                            ║
║  对比 v1 和 v2 API 的性能差异                              ║
║  测试项目：                                                ║
║    1. 生成下载链接                                         ║
║    2. 流式下载                                            ║
║    3. 批量下载                                            ║
║    4. 装饰器开销                                          ║
╚════════════════════════════════════════════════════════════╝{Colors.END}
    """)

    # 创建测试草稿
    draft_id = create_test_draft()

    # 运行基准测试
    results = {}

    try:
        # 测试 1: 生成下载链接
        v1, v2 = benchmark_download_url(draft_id)
        results['生成下载链接'] = (v1, v2)

        # 测试 2: 流式下载
        # v1, v2 = benchmark_stream_download(draft_id)
        # results['流式下载'] = (v1, v2)
        # 注释掉流式下载测试，因为可能比较慢

        # 测试 3: 批量下载
        v1, v2 = benchmark_batch_download(draft_id)
        results['批量下载'] = (v1, v2)

        # 测试 4: 装饰器开销
        overhead = benchmark_decorator_overhead(draft_id)
        results['decorator_overhead'] = overhead

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠ 测试被用户中断{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}✗ 测试出错: {e}{Colors.END}")
        import traceback
        traceback.print_exc()

    # 生成报告
    if results:
        generate_report(results)

    print(f"\n{Colors.GREEN}测试完成！{Colors.END}\n")


if __name__ == '__main__':
    main()
