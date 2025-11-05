#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相对路径下载功能使用示例
Relative Path Download Feature Usage Example

作者：CapCutAPI Team
版本：1.0.0
日期：2025-11-04
"""

import requests
import json

# API服务器地址
API_BASE_URL = "http://8.148.70.18:9000"


def example_1_relative_path_download():
    """
    示例1：使用相对路径下载草稿
    
    功能说明：
    - 使用相对于项目根目录的路径
    - 系统会自动转换为绝对路径
    """
    print("=" * 70)
    print("示例1：使用相对路径下载草稿")
    print("=" * 70)
    
    # 草稿ID（请替换为实际的草稿ID）
    draft_id = "dfd_cat_1756104121_cb774809"
    
    # 使用相对路径（相对于项目根目录 /home/CapCutAPI-1.1.0）
    draft_folder = "./downloads/drafts"
    
    # 请求参数
    payload = {
        "draft_id": draft_id,
        "draft_folder": draft_folder,  # 相对路径
        "client_os": "windows"
    }
    
    print(f"\n请求参数：")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    # 发送请求
    response = requests.post(f"{API_BASE_URL}/save_draft", json=payload)
    
    print(f"\n响应结果：")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    # 说明
    print("\n路径转换说明：")
    print(f"  输入路径: {draft_folder}")
    print(f"  转换为: /home/CapCutAPI-1.1.0/downloads/drafts")
    print()


def example_2_parent_directory():
    """
    示例2：使用上级目录路径
    
    功能说明：
    - 使用 ../ 访问上级目录
    - 适合在共享目录下保存草稿
    """
    print("=" * 70)
    print("示例2：使用上级目录路径")
    print("=" * 70)
    
    draft_id = "dfd_cat_1756104121_cb774809"
    
    # 使用上级目录
    draft_folder = "../shared_output"
    
    payload = {
        "draft_id": draft_id,
        "draft_folder": draft_folder,
        "client_os": "linux"
    }
    
    print(f"\n请求参数：")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    print("\n路径转换说明：")
    print(f"  输入路径: {draft_folder}")
    print(f"  转换为: /home/shared_output")
    print()


def example_3_user_home_directory():
    """
    示例3：使用用户主目录
    
    功能说明：
    - 使用 ~ 表示用户主目录
    - 自动展开为完整路径
    """
    print("=" * 70)
    print("示例3：使用用户主目录")
    print("=" * 70)
    
    draft_id = "dfd_cat_1756104121_cb774809"
    
    # 使用用户主目录
    draft_folder = "~/Documents/CapCut/Projects"
    
    payload = {
        "draft_id": draft_id,
        "draft_folder": draft_folder,
        "client_os": "darwin"  # macOS
    }
    
    print(f"\n请求参数：")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    print("\n路径转换说明：")
    print(f"  输入路径: {draft_folder}")
    print(f"  转换为: /root/Documents/CapCut/Projects (Linux)")
    print(f"       或: C:\\Users\\username\\Documents\\CapCut\\Projects (Windows)")
    print()


def example_4_absolute_path():
    """
    示例4：使用绝对路径（原有方式）
    
    功能说明：
    - 直接使用绝对路径
    - 兼容旧版本的使用方式
    """
    print("=" * 70)
    print("示例4：使用绝对路径（原有方式）")
    print("=" * 70)
    
    draft_id = "dfd_cat_1756104121_cb774809"
    
    # 使用绝对路径（Windows格式）
    draft_folder = "F:\\jianying\\cgwz\\JianyingPro Drafts"
    
    payload = {
        "draft_id": draft_id,
        "draft_folder": draft_folder,
        "client_os": "windows"
    }
    
    print(f"\n请求参数：")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    print("\n说明：")
    print(f"  绝对路径直接使用，不进行转换")
    print(f"  支持Windows盘符格式")
    print()


def example_5_mixed_paths():
    """
    示例5：批量处理，使用多种路径格式
    
    功能说明：
    - 演示在同一个应用中使用多种路径格式
    - 系统会根据路径类型自动处理
    """
    print("=" * 70)
    print("示例5：批量处理，使用多种路径格式")
    print("=" * 70)
    
    # 多个草稿使用不同的路径格式
    drafts = [
        {
            "draft_id": "dfd_cat_1_abc",
            "draft_folder": "./downloads/draft1",
            "description": "相对路径（当前目录）"
        },
        {
            "draft_id": "dfd_cat_2_def",
            "draft_folder": "../output/draft2",
            "description": "相对路径（上级目录）"
        },
        {
            "draft_id": "dfd_cat_3_ghi",
            "draft_folder": "~/Documents/draft3",
            "description": "用户主目录"
        },
        {
            "draft_id": "dfd_cat_4_jkl",
            "draft_folder": "/tmp/draft4",
            "description": "绝对路径"
        }
    ]
    
    print("\n路径格式对比：")
    print("-" * 70)
    for draft in drafts:
        print(f"\n草稿ID: {draft['draft_id']}")
        print(f"  路径类型: {draft['description']}")
        print(f"  输入路径: {draft['draft_folder']}")
        
        # 这里不实际发送请求，仅展示
        # response = requests.post(f"{API_BASE_URL}/save_draft", json={
        #     "draft_id": draft['draft_id'],
        #     "draft_folder": draft['draft_folder'],
        #     "client_os": "linux"
        # })
    
    print("\n" + "=" * 70)
    print("说明：所有路径格式都可以在同一个应用中混合使用")
    print("=" * 70)
    print()


def main():
    """
    主函数：运行所有示例
    """
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "          相对路径下载功能使用示例集合          ".center(68) + "*")
    print("*" + "     Relative Path Download Feature Examples     ".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print()
    
    print("📌 提示：以下示例仅展示用法，不实际发送请求")
    print("📌 如需测试，请取消注释相应的requests.post()调用")
    print()
    
    # 运行所有示例
    example_1_relative_path_download()
    example_2_parent_directory()
    example_3_user_home_directory()
    example_4_absolute_path()
    example_5_mixed_paths()
    
    # 总结
    print("\n")
    print("=" * 70)
    print("✅ 所有示例展示完成")
    print("=" * 70)
    print("\n支持的路径格式总结：")
    print("  1. ✅ 相对路径: ./downloads, ../output, output/videos")
    print("  2. ✅ 用户主目录: ~/Documents, ~/Downloads")
    print("  3. ✅ 绝对路径: /home/user/path, F:\\Windows\\Path")
    print("  4. ✅ 自动路径转换和验证")
    print("  5. ✅ 跨平台支持: Windows, Linux, macOS")
    print()
    print("📖 更多信息请查看: README.md")
    print("🔧 技术文档请查看: path_utils.py")
    print()


if __name__ == "__main__":
    main()

