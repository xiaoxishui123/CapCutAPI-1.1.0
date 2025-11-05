#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
剪映草稿ID刷新工具

功能：修改草稿的 draft_id 和时间戳，让剪映识别为全新草稿
用途：解决剪映自动重命名草稿文件夹的问题

使用方法：
    python3.9 refresh_draft_id.py <草稿文件夹路径>
    
示例：
    python3.9 refresh_draft_id.py /path/to/dfd_cat_1762263149_1d98171b
"""

import json
import os
import sys
import uuid
import time
import shutil
from pathlib import Path


def generate_new_draft_id():
    """生成新的草稿ID（UUID格式，大写）"""
    return str(uuid.uuid4()).upper()


def get_current_timestamp_microseconds():
    """获取当前时间戳（微秒）"""
    return int(time.time() * 1000000)


def backup_file(file_path):
    """备份文件"""
    backup_path = f"{file_path}.backup"
    shutil.copy2(file_path, backup_path)
    return backup_path


def refresh_draft_meta_info(draft_folder):
    """刷新 draft_meta_info.json 中的 draft_id 和时间戳"""
    meta_info_path = os.path.join(draft_folder, 'draft_meta_info.json')
    
    if not os.path.exists(meta_info_path):
        print(f"❌ 错误：找不到文件 {meta_info_path}")
        return False
    
    # 备份文件
    backup_path = backup_file(meta_info_path)
    print(f"✅ 已备份：{backup_path}")
    
    # 读取文件
    with open(meta_info_path, 'r', encoding='utf-8') as f:
        meta_info = json.load(f)
    
    # 记录旧值
    old_draft_id = meta_info.get('draft_id', 'N/A')
    old_tm_create = meta_info.get('tm_draft_create', 'N/A')
    old_tm_modified = meta_info.get('tm_draft_modified', 'N/A')
    
    # 生成新值
    new_draft_id = generate_new_draft_id()
    new_timestamp = get_current_timestamp_microseconds()
    
    # 更新字段
    meta_info['draft_id'] = new_draft_id
    meta_info['tm_draft_create'] = new_timestamp
    meta_info['tm_draft_modified'] = new_timestamp
    
    # 保存文件（格式化JSON，缩进2空格，确保中文不转义）
    with open(meta_info_path, 'w', encoding='utf-8') as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 成功更新 draft_meta_info.json:")
    print(f"   draft_id: {old_draft_id}")
    print(f"          → {new_draft_id}")
    print(f"   tm_draft_create: {old_tm_create}")
    print(f"                 → {new_timestamp}")
    print(f"   tm_draft_modified: {old_tm_modified}")
    print(f"                   → {new_timestamp}")
    
    return True


def refresh_draft_info(draft_folder):
    """
    刷新 draft_info.json 中的 draft_id（如果存在）
    注意：draft_info.json 可能很大，需要谨慎处理
    """
    draft_info_path = os.path.join(draft_folder, 'draft_info.json')
    
    if not os.path.exists(draft_info_path):
        print(f"⚠️ 警告：找不到文件 {draft_info_path}")
        return False
    
    # 检查文件大小
    file_size = os.path.getsize(draft_info_path)
    if file_size > 10 * 1024 * 1024:  # 大于10MB
        print(f"⚠️ 警告：draft_info.json 文件很大（{file_size / 1024 / 1024:.2f} MB）")
        print(f"   跳过修改 draft_info.json，只修改 draft_meta_info.json 应该就足够了")
        return True
    
    try:
        # 备份文件
        backup_path = backup_file(draft_info_path)
        print(f"✅ 已备份：{backup_path}")
        
        # 读取文件（draft_info.json 通常是一行JSON）
        with open(draft_info_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含 draft_id 字段
        if '"draft_id"' in content:
            # 解析JSON
            draft_info = json.loads(content)
            
            # 查找并更新 draft_id（可能在多个位置）
            old_draft_id = draft_info.get('draft_id', 'N/A')
            new_draft_id = generate_new_draft_id()
            
            # 递归更新所有 draft_id 字段
            def update_draft_id(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key == 'draft_id' and isinstance(value, str):
                            obj[key] = new_draft_id
                        else:
                            update_draft_id(value)
                elif isinstance(obj, list):
                    for item in obj:
                        update_draft_id(item)
            
            update_draft_id(draft_info)
            
            # 保存文件（不格式化，保持原样，只是一行）
            with open(draft_info_path, 'w', encoding='utf-8') as f:
                json.dump(draft_info, f, ensure_ascii=False, separators=(',', ':'))
            
            print(f"\n✅ 成功更新 draft_info.json:")
            print(f"   draft_id: {old_draft_id}")
            print(f"          → {new_draft_id}")
        else:
            print(f"ℹ️  draft_info.json 中没有 draft_id 字段，无需修改")
        
        return True
        
    except Exception as e:
        print(f"⚠️ 处理 draft_info.json 时出错：{e}")
        print(f"   只修改了 draft_meta_info.json，应该也能解决问题")
        return True


def main():
    """主函数"""
    print("=" * 70)
    print("🔄 剪映草稿ID刷新工具")
    print("=" * 70)
    print()
    
    # 检查参数
    if len(sys.argv) < 2:
        print("❌ 错误：请提供草稿文件夹路径")
        print()
        print("用法：")
        print(f"  {sys.argv[0]} <草稿文件夹路径>")
        print()
        print("示例：")
        print(f"  {sys.argv[0]} /home/CapCutAPI-1.1.0/drafts/dfd_cat_1762263149_1d98171b")
        print(f"  {sys.argv[0]} ./drafts/dfd_cat_1762263149_1d98171b")
        sys.exit(1)
    
    draft_folder = sys.argv[1]
    
    # 检查文件夹是否存在
    if not os.path.isdir(draft_folder):
        print(f"❌ 错误：草稿文件夹不存在：{draft_folder}")
        sys.exit(1)
    
    print(f"📁 草稿文件夹：{draft_folder}")
    print()
    
    # 刷新 draft_meta_info.json
    print("🔄 正在刷新 draft_meta_info.json...")
    if not refresh_draft_meta_info(draft_folder):
        print("❌ 刷新失败")
        sys.exit(1)
    
    print()
    
    # 刷新 draft_info.json（可选）
    print("🔄 正在检查 draft_info.json...")
    refresh_draft_info(draft_folder)
    
    print()
    print("=" * 70)
    print("✅ 草稿ID刷新完成！")
    print("=" * 70)
    print()
    print("📋 后续步骤：")
    print("1. 将草稿文件夹复制到Windows剪映草稿目录")
    print("   例如：F:\\jianying\\cgwz\\JianyingPro Drafts\\")
    print()
    print("2. 打开剪映，应该能看到这个草稿，且不会被重命名")
    print()
    print("3. 如果素材仍然丢失，请参考《Windows草稿素材识别问题诊断.md》")
    print()
    print("💡 提示：每次下载草稿后，都可以运行这个工具来刷新ID")
    print("   这样剪映就会把它识别为全新的草稿，不会重命名")
    print()


if __name__ == '__main__':
    main()

