#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试下载草稿时的路径处理逻辑
验证 draft_folder 参数是否正确应用到素材路径
"""

import json
import os
import sys
import tempfile
import zipfile

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from customize_zip import _rewrite_paths_in_json, _rewrite_meta_info, REWRITE_VERSION


def test_path_rewrite():
    """测试路径重写逻辑"""
    print("=" * 60)
    print("测试 1: 路径重写逻辑")
    print("=" * 60)
    
    # 模拟 draft_info.json 中的素材数据
    sample_draft_info = {
        "materials": {
            "videos": [
                {
                    "id": "video_001",
                    "path": "/tmp/assets/video/sample.mp4",
                    "name": "sample.mp4"
                }
            ],
            "audios": [
                {
                    "id": "audio_001", 
                    "path": "/tmp/assets/audio/bgm.mp3",
                    "name": "bgm.mp3"
                }
            ]
        },
        "tracks": []
    }
    
    draft_id = "dfd_test_001"
    
    # 测试场景1: 有自定义路径 (Windows)
    print("\n🔧 场景 1: Windows + 自定义路径")
    print("-" * 40)
    draft_folder_win = "F:\\jianyin\\cgwz\\JianyingPro Drafts"
    result_win = _rewrite_paths_in_json(sample_draft_info, draft_id, "windows", draft_folder_win)
    
    for video in result_win.get("materials", {}).get("videos", []):
        print(f"  视频路径: {video.get('path')}")
        expected_path = f"F:\\jianyin\\cgwz\\JianyingPro Drafts\\{draft_id}\\assets/video/sample.mp4"
        # 验证路径是否包含自定义目录
        assert draft_folder_win.replace("/", "\\") in video.get('path', '').replace("/", "\\"), \
            f"路径未包含自定义目录: {video.get('path')}"
    
    for audio in result_win.get("materials", {}).get("audios", []):
        print(f"  音频路径: {audio.get('path')}")
    
    # 测试场景2: 有自定义路径 (Mac)
    print("\n🔧 场景 2: macOS + 自定义路径")
    print("-" * 40)
    draft_folder_mac = "/Users/Shared/JianyingPro Drafts"
    result_mac = _rewrite_paths_in_json(sample_draft_info, draft_id, "darwin", draft_folder_mac)
    
    for video in result_mac.get("materials", {}).get("videos", []):
        print(f"  视频路径: {video.get('path')}")
        assert draft_folder_mac in video.get('path', ''), \
            f"路径未包含自定义目录: {video.get('path')}"
    
    for audio in result_mac.get("materials", {}).get("audios", []):
        print(f"  音频路径: {audio.get('path')}")
    
    # 测试场景3: 无自定义路径 (相对路径模式)
    print("\n🔧 场景 3: 无自定义路径 (相对路径模式)")
    print("-" * 40)
    result_relative = _rewrite_paths_in_json(sample_draft_info, draft_id, "windows", "")
    
    for video in result_relative.get("materials", {}).get("videos", []):
        print(f"  视频路径: {video.get('path')}")
        # 相对路径模式应该只有 assets\video\xxx 格式
        assert video.get('path', '').startswith('assets'), \
            f"相对路径格式错误: {video.get('path')}"
    
    for audio in result_relative.get("materials", {}).get("audios", []):
        print(f"  音频路径: {audio.get('path')}")
    
    print("\n✅ 路径重写测试通过!")


def test_meta_rewrite():
    """测试 draft_meta_info.json 重写逻辑"""
    print("\n" + "=" * 60)
    print("测试 2: draft_meta_info.json 重写逻辑")
    print("=" * 60)
    
    sample_meta = {
        "draft_id": "OLD_DRAFT_ID",
        "draft_name": "old_name",
        "draft_root_path": "/old/path",
        "draft_fold_path": "/old/path/draft",
        "tm_draft_create": 1000000000,
        "tm_draft_modified": 1000000001,
        "other_field": "keep_this"
    }
    
    draft_id = "dfd_test_002"
    
    # 测试场景1: 有自定义路径 (Windows)
    print("\n🔧 场景 1: Windows + 自定义路径")
    print("-" * 40)
    draft_folder_win = "F:\\jianyin\\cgwz\\JianyingPro Drafts"
    result_win = _rewrite_meta_info(sample_meta, draft_id, "windows", draft_folder_win)
    
    print(f"  draft_id: {result_win.get('draft_id')} (已刷新)")
    print(f"  draft_name: {result_win.get('draft_name')}")
    print(f"  draft_root_path: {result_win.get('draft_root_path')}")
    print(f"  draft_fold_path: {result_win.get('draft_fold_path')}")
    
    assert result_win.get('draft_id') != sample_meta['draft_id'], "draft_id 应该被刷新"
    assert result_win.get('draft_name') == draft_id, f"draft_name 应该是 {draft_id}"
    assert draft_folder_win.replace("/", "\\") in result_win.get('draft_root_path', '').replace("/", "\\"), \
        "draft_root_path 应该包含自定义路径"
    
    # 测试场景2: 无自定义路径 (相对路径模式)
    print("\n🔧 场景 2: 无自定义路径 (相对路径模式)")
    print("-" * 40)
    result_relative = _rewrite_meta_info(sample_meta, draft_id, "windows", "")
    
    print(f"  draft_id: {result_relative.get('draft_id')} (已刷新)")
    print(f"  draft_name: {result_relative.get('draft_name')}")
    print(f"  draft_root_path: '{result_relative.get('draft_root_path')}'")
    print(f"  draft_fold_path: '{result_relative.get('draft_fold_path')}'")
    
    assert result_relative.get('draft_root_path') == '', "相对路径模式下 draft_root_path 应该为空"
    assert result_relative.get('draft_fold_path') == '', "相对路径模式下 draft_fold_path 应该为空"
    
    print("\n✅ draft_meta_info 重写测试通过!")


def test_path_config():
    """测试路径配置读取"""
    print("\n" + "=" * 60)
    print("测试 3: 路径配置文件")
    print("=" * 60)
    
    # 检查 path_config.json
    config_file = "path_config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"  path_config.json 内容:")
        print(f"    custom_download_path: {config.get('custom_download_path', '未设置')}")
    else:
        print("  ⚠️ path_config.json 不存在")
    
    # 检查 config.json
    main_config_file = "config.json"
    if os.path.exists(main_config_file):
        with open(main_config_file, 'r', encoding='utf-8') as f:
            main_config = json.load(f)
        print(f"\n  config.json 路径配置:")
        draft_paths = main_config.get('draft_paths', {})
        for os_type, path in draft_paths.items():
            print(f"    {os_type}: {path}")
        
        print(f"    windows_draft_folder: {main_config.get('windows_draft_folder', '未设置')}")
        print(f"    linux_draft_folder: {main_config.get('linux_draft_folder', '未设置')}")
    else:
        print("  ⚠️ config.json 不存在")


def test_jianying_compatibility():
    """测试剪映兼容性 - 验证路径格式是否符合剪映要求"""
    print("\n" + "=" * 60)
    print("测试 4: 剪映兼容性检查")
    print("=" * 60)
    
    # 剪映对路径的要求:
    # 1. Windows: 使用反斜杠 (\)
    # 2. 绝对路径模式: 路径必须指向正确的素材位置
    # 3. 相对路径模式: 素材位于草稿文件夹内的 assets 目录
    
    print("\n📋 剪映路径要求:")
    print("  1. Windows 系统使用反斜杠 (\\)")
    print("  2. macOS/Linux 系统使用正斜杠 (/)")
    print("  3. 绝对路径模式: 完整路径指向素材")
    print("  4. 相对路径模式: 素材在 assets/ 子目录下")
    
    # 模拟完整的草稿结构
    draft_id = "dfd_test_jianying"
    draft_folder = "F:\\jianyin\\cgwz\\JianyingPro Drafts"
    
    sample_path = f"/tmp/server/assets/video/test.mp4"
    
    print(f"\n🔧 测试路径转换:")
    print(f"  原始路径: {sample_path}")
    
    # Windows 绝对路径
    from util import normalize_path_by_os
    
    # 模拟 customize_zip 中的路径重写
    rel = "assets/video/test.mp4"
    base = draft_folder.rstrip("/\\")
    joined = f"{base}/{draft_id}/" + rel
    result_win = normalize_path_by_os(joined, "windows")
    print(f"  Windows 绝对路径: {result_win}")
    
    # 验证 Windows 路径格式
    assert "\\" in result_win, "Windows 路径应使用反斜杠"
    assert "F:" in result_win, "Windows 路径应包含盘符"
    
    # 相对路径模式
    result_relative = normalize_path_by_os(rel, "windows")
    print(f"  Windows 相对路径: {result_relative}")
    assert result_relative.startswith("assets"), "相对路径应以 assets 开头"
    
    print("\n✅ 剪映兼容性检查通过!")
    
    # 额外提示
    print("\n📝 剪映打开草稿时的注意事项:")
    print("  1. 解压 ZIP 文件到配置的目录")
    print("  2. 草稿文件夹名称应与 draft_id 一致")
    print("  3. 素材文件放在 assets/video/, assets/audio/, assets/image/ 下")
    print("  4. draft_info.json 中的路径必须与实际素材位置匹配")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🔍 下载草稿路径处理测试")
    print(f"   版本: {REWRITE_VERSION}")
    print("=" * 60)
    
    try:
        test_path_rewrite()
        test_meta_rewrite()
        test_path_config()
        test_jianying_compatibility()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        
        # 总结
        print("\n📋 路径处理总结:")
        print("  1. ✅ 自定义路径模式: draft_folder + draft_id + assets/type/file")
        print("  2. ✅ 相对路径模式: assets/type/file")
        print("  3. ✅ draft_id 每次下载都会刷新，避免剪映重命名问题")
        print("  4. ✅ 路径分隔符根据 client_os 自动转换")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

