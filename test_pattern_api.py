#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pattern API 测试脚本

测试 Pattern 模板库的所有 API 端点
"""

import requests
import json

BASE_URL = "http://localhost:9000"

def test_list_patterns():
    """测试列出所有模板"""
    print("=" * 50)
    print("测试: 列出所有 Pattern 模板")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/api/patterns/list")

    print(f"状态码: {response.status_code}")
    print(f"响应:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'patterns' in data
    assert data['count'] > 0

    print(f"✅ 测试通过: 找到 {data['count']} 个模板\n")
    return data['patterns']


def test_get_pattern(pattern_id):
    """测试获取模板详情"""
    print("=" * 50)
    print(f"测试: 获取模板详情 ({pattern_id})")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/api/patterns/get/{pattern_id}")

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"模板名称: {data['pattern']['name']}")
        print(f"模板类型: {data['pattern']['type']}")
        print(f"模板描述: {data['pattern']['description']}")
        print(f"内容长度: {len(data['pattern']['content'])} 字符")

        if data['pattern'].get('video_url'):
            print(f"演示视频: {data['pattern']['video_url']}")

        assert data['success'] == True
        assert 'content' in data['pattern']
        print(f"✅ 测试通过\n")
    else:
        print(f"❌ 测试失败: {response.text}\n")


def test_download_pattern(pattern_id):
    """测试下载模板文件"""
    print("=" * 50)
    print(f"测试: 下载模板文件 ({pattern_id})")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/api/patterns/download/{pattern_id}")

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        content_length = len(response.content)
        print(f"下载内容长度: {content_length} 字节")

        # 检查 Content-Disposition 头
        if 'Content-Disposition' in response.headers:
            print(f"Content-Disposition: {response.headers['Content-Disposition']}")

        assert content_length > 0
        print(f"✅ 测试通过\n")
    else:
        print(f"❌ 测试失败: {response.text}\n")


def test_nonexistent_pattern():
    """测试不存在的模板"""
    print("=" * 50)
    print("测试: 访问不存在的模板")
    print("=" * 50)

    pattern_id = "nonexistent-pattern"
    response = requests.get(f"{BASE_URL}/api/patterns/get/{pattern_id}")

    print(f"状态码: {response.status_code}")

    assert response.status_code == 404
    print(f"✅ 测试通过: 正确返回 404\n")


def main():
    """运行所有测试"""
    print("\n" + "🧪 " * 25)
    print("Pattern API 功能测试")
    print("🧪 " * 25 + "\n")

    try:
        # 1. 列出所有模板
        patterns = test_list_patterns()

        # 2. 测试每个模板的详情
        for pattern in patterns:
            test_get_pattern(pattern['id'])

        # 3. 测试下载第一个模板
        if patterns:
            test_download_pattern(patterns[0]['id'])

        # 4. 测试错误处理
        test_nonexistent_pattern()

        print("=" * 50)
        print("✅ 所有测试通过!")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接到服务器: {BASE_URL}")
        print("请确保 CapCutAPI 服务正在运行")
        return 1
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
