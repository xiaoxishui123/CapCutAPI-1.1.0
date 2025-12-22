#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
草稿下载修复测试脚本
测试场景：
1. 正常草稿下载
2. 基础文件不存在的草稿下载
3. 批量下载（包含正常和异常草稿）
"""

def test_single_download_existing():
    """测试1：下载存在的草稿"""
    print("\n" + "="*60)
    print("测试1：下载存在的草稿")
    print("="*60)

    from services.download_service import DraftDownloadService

    service = DraftDownloadService()

    # 使用之前测试成功的草稿ID
    draft_id = "dfd_cat_1763436047_920e2b1e"
    client_os = "windows"
    draft_folder = ""

    print(f"\n测试参数:")
    print(f"  draft_id: {draft_id}")
    print(f"  client_os: {client_os}")
    print(f"  draft_folder: '{draft_folder}'")

    try:
        result = service.get_download_url(draft_id, client_os, draft_folder)

        print(f"\n结果:")
        print(f"  success: {result.get('success')}")
        if result.get('success'):
            print(f"  ✅ 下载链接生成成功")
            print(f"  storage: {result.get('storage')}")
            print(f"  draft_url: {result.get('draft_url', '')[:100]}...")
        else:
            print(f"  ❌ 失败: {result.get('error')}")
            print(f"  error_type: {result.get('error_type')}")
            print(f"  suggestion: {result.get('suggestion')}")

    except Exception as e:
        print(f"\n❌ 异常: {type(e).__name__}: {e}")


def test_single_download_not_exists():
    """测试2：下载不存在的草稿"""
    print("\n" + "="*60)
    print("测试2：下载不存在的草稿（基础文件不存在）")
    print("="*60)

    from services.download_service import DraftDownloadService

    service = DraftDownloadService()

    # 使用一个不存在的草稿ID
    draft_id = "non_existent_draft_99999"
    client_os = "windows"
    draft_folder = ""

    print(f"\n测试参数:")
    print(f"  draft_id: {draft_id}")
    print(f"  client_os: {client_os}")
    print(f"  draft_folder: '{draft_folder}'")

    try:
        result = service.get_download_url(draft_id, client_os, draft_folder)

        print(f"\n结果:")
        print(f"  success: {result.get('success')}")
        if result.get('success'):
            print(f"  ⚠️  预期应该失败，但返回了成功")
            print(f"  draft_url: {result.get('draft_url', '')[:100]}")
        else:
            print(f"  ✅ 正确识别为失败")
            print(f"  error: {result.get('error')}")
            print(f"  error_type: {result.get('error_type')}")
            print(f"  suggestion: {result.get('suggestion')}")

    except Exception as e:
        print(f"\n❌ 异常: {type(e).__name__}: {e}")


def test_batch_download():
    """测试3：批量下载（包含存在和不存在的草稿）"""
    print("\n" + "="*60)
    print("测试3：批量下载（混合正常和异常草稿）")
    print("="*60)

    from services.download_service import DraftDownloadService

    service = DraftDownloadService()

    # 混合：1个存在的，2个不存在的
    draft_ids = [
        "dfd_cat_1763436047_920e2b1e",  # 存在
        "non_existent_draft_11111",      # 不存在
        "non_existent_draft_22222"       # 不存在
    ]
    client_os = "windows"
    draft_folder = ""

    print(f"\n测试参数:")
    print(f"  draft_ids数量: {len(draft_ids)}")
    print(f"  client_os: {client_os}")
    print(f"  draft_folder: '{draft_folder}'")

    try:
        results = service.batch_download(draft_ids, client_os, draft_folder)

        print(f"\n批量下载结果:")
        print(f"  总数: {len(results)}")

        succeeded = sum(1 for r in results if r.get('success'))
        failed = len(results) - succeeded

        print(f"  成功: {succeeded}")
        print(f"  失败: {failed}")

        print(f"\n详细结果:")
        for i, result in enumerate(results, 1):
            print(f"\n  [{i}] {result.get('draft_id', 'N/A')}")
            print(f"      success: {result.get('success')}")
            if result.get('success'):
                print(f"      storage: {result.get('storage')}")
                print(f"      url: {result.get('draft_url', '')[:80]}...")
            else:
                print(f"      error: {result.get('error')}")
                error_type = result.get('error_type')
                if error_type:
                    print(f"      error_type: {error_type}")
                suggestion = result.get('suggestion')
                if suggestion:
                    print(f"      suggestion: {suggestion}")

    except Exception as e:
        print(f"\n❌ 异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("草稿下载修复测试")
    print("="*60)

    # 运行所有测试
    test_single_download_existing()
    test_single_download_not_exists()
    test_batch_download()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    main()
