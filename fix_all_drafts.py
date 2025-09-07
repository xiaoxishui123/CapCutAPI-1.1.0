#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复所有草稿脚本
自动修复指定目录下的所有草稿文件
"""

import os
import sys
from fix_draft_paths import fix_draft_paths

def fix_all_drafts(drafts_directory: str):
    """批量修复所有草稿"""
    if not os.path.exists(drafts_directory):
        print(f"错误: 目录不存在: {drafts_directory}")
        return False
    
    print(f"开始扫描目录: {drafts_directory}")
    
    fixed_count = 0
    error_count = 0
    
    # 遍历目录中的所有子目录
    for item in os.listdir(drafts_directory):
        item_path = os.path.join(drafts_directory, item)
        
        # 检查是否为目录
        if os.path.isdir(item_path):
            # 检查是否为草稿文件夹（包含必要的文件）
            draft_info = os.path.join(item_path, "draft_info.json")
            draft_meta = os.path.join(item_path, "draft_meta_info.json")
            
            if os.path.exists(draft_info) and os.path.exists(draft_meta):
                print(f"发现草稿: {item}")
                
                # 修复草稿
                try:
                    if fix_draft_paths(item_path, "windows"):
                        print(f"  ✅ 修复成功")
                        fixed_count += 1
                    else:
                        print(f"  ❌ 修复失败")
                        error_count += 1
                except Exception as e:
                    print(f"  ❌ 修复出错: {e}")
                    error_count += 1
    
    print(f"\n修复完成!")
    print(f"成功修复: {fixed_count} 个草稿")
    print(f"修复失败: {error_count} 个草稿")
    
    return error_count == 0

if __name__ == "__main__":
    # 默认修复 Jianying 草稿目录
    default_drafts_dir = "F:\\jianyin\\cgwz\\JianyingPro Drafts"
    
    if len(sys.argv) > 1:
        drafts_dir = sys.argv[1]
    else:
        drafts_dir = default_drafts_dir
        print(f"未指定目录，使用默认目录: {drafts_dir}")
    
    success = fix_all_drafts(drafts_dir)
    sys.exit(0 if success else 1)