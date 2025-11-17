#!/usr/bin/env python3
"""
草稿下载功能测试脚本
用于验证草稿下载功能的修复
"""

import requests
import json
import sys

BASE_URL = "http://localhost:9000"

def test_health_check():
    """测试健康检查端点"""
    print("\n" + "="*50)
    print("测试 1: 健康检查")
    print("="*50)

    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print("❌ 健康检查失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_draft_check(draft_id):
    """测试草稿存在性检查"""
    print("\n" + "="*50)
    print(f"测试 2: 检查草稿是否存在 - {draft_id}")
    print("="*50)

    try:
        response = requests.get(f"{BASE_URL}/api/drafts/check/{draft_id}")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

        if response.status_code == 200:
            print(f"✅ 草稿检查完成")
            print(f"   - 存在于OSS: {result.get('exists_in_oss')}")
            print(f"   - 存在于数据库: {result.get('exists_in_database')}")
            print(f"   - 存在于缓存: {result.get('exists_in_cache')}")
            return result
        else:
            print("❌ 草稿检查失败")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def test_smart_download(draft_id):
    """测试智能下载功能"""
    print("\n" + "="*50)
    print(f"测试 3: 智能下载 - {draft_id}")
    print("="*50)

    try:
        data = {
            "draft_id": draft_id,
            "draft_folder": "",  # 相对路径模式
            "client_os": "windows"
        }

        response = requests.post(
            f"{BASE_URL}/generate_draft_url",
            json=data
        )

        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

        if response.status_code == 200 and result.get('success'):
            print("✅ 智能下载链接生成成功")
            if result.get('regenerated'):
                print("⚡ 草稿已自动重新生成")
            return result
        else:
            print("❌ 智能下载失败")
            print(f"错误: {result.get('error')}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def test_proxy_download(draft_id):
    """测试代理下载功能"""
    print("\n" + "="*50)
    print(f"测试 4: 代理下载 - {draft_id}")
    print("="*50)

    try:
        response = requests.get(
            f"{BASE_URL}/api/drafts/download/proxy/{draft_id}",
            params={"client_os": "windows", "draft_folder": ""},
            stream=True
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            # 检查响应头
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")

            # 不实际下载，只检查前1KB
            content_preview = next(response.iter_content(1024), None)
            if content_preview:
                print(f"文件大小预览: 已接收 {len(content_preview)} 字节")
                print("✅ 代理下载测试通过")
                return True
        else:
            try:
                error = response.json()
                print(f"错误响应: {json.dumps(error, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误响应: {response.text[:200]}")
            print("❌ 代理下载失败")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("CapCutAPI 草稿下载功能测试")
    print("="*60)

    # 从命令行参数获取draft_id，或使用默认值
    if len(sys.argv) > 1:
        draft_id = sys.argv[1]
    else:
        # 使用最近的draft_id
        draft_id = "dfd_cat_1763382269_293b5e69"

    print(f"\n测试草稿ID: {draft_id}")

    # 运行测试
    test_results = []

    # 测试1: 健康检查
    test_results.append(("健康检查", test_health_check()))

    # 测试2: 草稿检查
    check_result = test_draft_check(draft_id)
    test_results.append(("草稿检查", check_result is not None))

    # 如果草稿存在，继续测试下载功能
    if check_result and check_result.get('exists_in_database'):
        # 测试3: 智能下载
        smart_result = test_smart_download(draft_id)
        test_results.append(("智能下载", smart_result is not None and smart_result.get('success')))

        # 测试4: 代理下载
        test_results.append(("代理下载", test_proxy_download(draft_id)))
    else:
        print(f"\n⚠️  草稿 {draft_id} 不存在于数据库，跳过下载测试")
        test_results.append(("智能下载", None))
        test_results.append(("代理下载", None))

    # 打印测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    passed = 0
    failed = 0
    skipped = 0

    for test_name, result in test_results:
        if result is True:
            status = "✅ 通过"
            passed += 1
        elif result is False:
            status = "❌ 失败"
            failed += 1
        else:
            status = "⏭️  跳过"
            skipped += 1

        print(f"{test_name:20s} - {status}")

    print("\n" + "-"*60)
    print(f"总计: {len(test_results)} 个测试")
    print(f"通过: {passed} | 失败: {failed} | 跳过: {skipped}")
    print("="*60)

    # 返回退出码
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
