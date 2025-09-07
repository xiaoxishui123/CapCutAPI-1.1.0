#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复脚本
用于快速修复音频文件识别问题
"""

import os
import sys
from fix_draft_paths import fix_draft_paths

def quick_fix(draft_path: str):
    """快速修复单个草稿"""
    if not os.path.exists(draft_path):
        print(f"错误: 草稿路径不存在: {draft_path}")
        return False
    
    # 检查必要的文件
    draft_info = os.path.join(draft_path, "draft_info.json")
    draft_meta = os.path.join(draft_path, "draft_meta_info.json")
    
    if not os.path.exists(draft_info):
        print(f"错误: draft_info.json 不存在于 {draft_path}")
        return False
    
    if not os.path.exists(draft_meta):
        print(f"错误: draft_meta_info.json 不存在于 {draft_path}")
        return False
    
    # 执行修复
    print(f"正在修复草稿: {draft_path}")
    success = fix_draft_paths(draft_path, "windows")
    
    if success:
        print("✅ 修复完成!")
        return True
    else:
        print("❌ 修复失败!")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python quick_fix.py <草稿路径>")
        sys.exit(1)
    
    draft_path = sys.argv[1]
    success = quick_fix(draft_path)
    sys.exit(0 if success else 1)