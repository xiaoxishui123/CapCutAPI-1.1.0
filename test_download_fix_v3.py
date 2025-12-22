#!/usr/bin/env python3
"""
测试下载功能修复 - v3
测试前端页面和下载API的集成
"""

import requests
import json
import sys

BASE_URL = "http://localhost:9000"
DRAFT_ID = "dfd_cat_1763463074_18073ad0"


def test_preview_page():
    """测试1: 预览页面是否正常加载"""
    print("\n" + "="*60)
    print("测试1: 预览页面加载")
    print("="*60)

    url = f"{BASE_URL}/draft/preview/{DRAFT_ID}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # 检查关键元素是否存在
            content = response.text
            checks = [
                ("下载草稿按钮", 'onclick="startCustomDownload' in content),
                ("直接下载按钮", 'onclick="directDownload' in content),
                ("JavaScript存在", '<script>' in content and 'function' in content),
                ("页面结构完整", '</html>' in content and '<head>' in content)
            ]

            print(f"✅ 页面加载成功 (HTTP {response.status_code})")
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"{status} {check_name}: {'通过' if result else '失败'}")

            return all(result for _, result in checks)
        else:
            print(f"❌ 页面加载失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_path_config_api():
    """测试2: 路径配置API"""
    print("\n" + "="*60)
    print("测试2: 路径配置API")
    print("="*60)

    # 测试GET请求
    url = f"{BASE_URL}/api/draft/path/config"
    try:
        response = requests.get(url, timeout=5)
        print(f"GET /api/draft/path/config: HTTP {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✅ 路径配置API正常工作")
            return True
        else:
            print(f"⚠️ 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_download_api():
    """测试3: 下载API"""
    print("\n" + "="*60)
    print("测试3: 下载API")
    print("="*60)

    url = f"{BASE_URL}/api/draft/download"
    payload = {
        "draft_id": DRAFT_ID,
        "use_custom_path": False,
        "draft_folder": "",
        "client_os": "windows"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"POST /api/draft/download: HTTP {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")

            # 检查响应结构
            checks = [
                ("成功标志", data.get('success') == True),
                ("下载URL", 'download_url' in data.get('data', {})),
                ("草稿ID", data.get('draft_id') == DRAFT_ID)
            ]

            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"{status} {check_name}: {'通过' if result else '失败'}")

            return all(result for _, result in checks)
        else:
            print(f"❌ API请求失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_stream_download_api():
    """测试4: 流式下载API"""
    print("\n" + "="*60)
    print("测试4: 流式下载API")
    print("="*60)

    url = f"{BASE_URL}/api/v2/drafts/{DRAFT_ID}/download/stream"

    try:
        # 只获取头部信息
        response = requests.head(url, timeout=10)
        print(f"HEAD {url}: HTTP {response.status_code}")

        if response.status_code == 200:
            print(f"✅ 流式下载端点可访问")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {response.headers.get('Content-Length')} bytes")
            print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
            return True
        else:
            print(f"❌ 流式下载失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_download_with_custom_path():
    """测试5: 使用自定义路径下载"""
    print("\n" + "="*60)
    print("测试5: 使用自定义路径下载")
    print("="*60)

    url = f"{BASE_URL}/api/draft/download"
    payload = {
        "draft_id": DRAFT_ID,
        "use_custom_path": True,
        "draft_folder": "/tmp/test_drafts",
        "client_os": "linux"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"POST /api/draft/download (自定义路径): HTTP {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✅ 自定义路径下载API正常工作")
            return True
        else:
            print(f"⚠️ 返回状态码: {response.status_code}")
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 下载功能修复测试套件 - v3")
    print("="*60)
    print(f"测试服务器: {BASE_URL}")
    print(f"测试草稿ID: {DRAFT_ID}")

    tests = [
        ("预览页面加载", test_preview_page),
        ("路径配置API", test_path_config_api),
        ("下载API", test_download_api),
        ("流式下载API", test_stream_download_api),
        ("自定义路径下载", test_download_with_custom_path)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 异常: {e}")
            results.append((test_name, False))

    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！下载功能修复成功！")
        return 0
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败，请检查日志")
        return 1


if __name__ == "__main__":
    sys.exit(main())
