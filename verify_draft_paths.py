#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
验证草稿路径配置

下载并检查实际生成的草稿文件，确认路径格式
"""

import json
import os
import sys
import zipfile
import tempfile
from oss import _ensure_bucket

def download_and_check_draft(draft_id):
    """下载并检查草稿的实际配置"""
    
    print("=" * 80)
    print(f"  检查草稿: {draft_id}")
    print("=" * 80)
    
    bucket = _ensure_bucket()
    
    # 1. 检查基础ZIP
    print("\n【1】检查基础ZIP (dfd_cat_xxx.zip)")
    print("-" * 80)
    base_key = f"{draft_id}.zip"
    
    try:
        if bucket.object_exists(base_key):
            print(f"✅ 基础ZIP存在: {base_key}")
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "base.zip")
                bucket.get_object_to_file(base_key, zip_path)
                check_zip_content(zip_path, "基础ZIP")
        else:
            print(f"❌ 基础ZIP不存在: {base_key}")
    except Exception as e:
        print(f"❌ 检查基础ZIP失败: {e}")
    
    # 2. 检查Windows定制ZIP
    print("\n【2】检查Windows智能下载版本")
    print("-" * 80)
    
    # 尝试找到Windows定制版本
    try:
        # 列出所有相关的ZIP文件
        for obj in bucket.list_objects(prefix=f"{draft_id}__windows__").object_list:
            print(f"✅ 找到定制ZIP: {obj.key}")
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "custom.zip")
                bucket.get_object_to_file(obj.key, zip_path)
                check_zip_content(zip_path, "Windows定制ZIP")
            break
        else:
            print(f"⚠️  未找到Windows定制版本")
    except Exception as e:
        print(f"❌ 检查定制ZIP失败: {e}")


def check_zip_content(zip_path, version_name):
    """检查ZIP内容"""
    print(f"\n分析 {version_name}:")
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # 检查draft_info.json
        if 'draft_info.json' in zf.namelist():
            print("\n  📄 draft_info.json:")
            data = json.loads(zf.read('draft_info.json').decode('utf-8'))
            
            # 查找素材路径
            paths_found = []
            
            def find_paths(obj, depth=0):
                if depth > 10:  # 防止递归过深
                    return
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, str) and 'assets' in value.lower():
                            paths_found.append((key, value))
                        else:
                            find_paths(value, depth+1)
                elif isinstance(obj, list):
                    for item in obj:
                        find_paths(item, depth+1)
            
            find_paths(data)
            
            if paths_found:
                print(f"    找到 {len(paths_found)} 个素材路径")
                # 分类统计
                relative_paths = 0
                absolute_paths = 0
                
                for key, path in paths_found[:10]:  # 只显示前10个
                    path_lower = path.replace('\\', '/').lower()
                    if path_lower.startswith('assets/'):
                        relative_paths += 1
                        print(f"    ✅ 相对路径: {path[:70]}")
                    elif ':' in path or path.startswith('/'):
                        absolute_paths += 1
                        print(f"    ❌ 绝对路径: {path[:70]}")
                
                print(f"\n    统计: 相对路径={relative_paths}, 绝对路径={absolute_paths}")
            else:
                print("    ⚠️  未找到素材路径")
        
        # 检查draft_meta_info.json
        if 'draft_meta_info.json' in zf.namelist():
            print("\n  📋 draft_meta_info.json:")
            meta = json.loads(zf.read('draft_meta_info.json').decode('utf-8'))
            
            print(f"    draft_id: {meta.get('draft_id', 'N/A')}")
            print(f"    draft_name: {meta.get('draft_name', 'N/A')}")
            
            draft_root_path = meta.get('draft_root_path', '')
            draft_fold_path = meta.get('draft_fold_path', '')
            
            if draft_root_path == '':
                print(f"    ✅ draft_root_path: (空字符串)")
            else:
                print(f"    ❌ draft_root_path: {draft_root_path[:60]}")
            
            if draft_fold_path == '':
                print(f"    ✅ draft_fold_path: (空字符串)")
            else:
                print(f"    ❌ draft_fold_path: {draft_fold_path[:60]}")
        
        # 检查实际素材文件
        print("\n  📁 素材文件:")
        asset_files = {
            'audio': [],
            'video': [],
            'image': []
        }
        
        for name in zf.namelist():
            name_lower = name.lower()
            if 'assets/audio/' in name_lower:
                asset_files['audio'].append(name)
            elif 'assets/video/' in name_lower:
                asset_files['video'].append(name)
            elif 'assets/image/' in name_lower:
                asset_files['image'].append(name)
        
        for asset_type, files in asset_files.items():
            if files:
                print(f"    {asset_type}: {len(files)} 个文件")
                for f in files[:3]:
                    print(f"      - {f}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法: python3.9 verify_draft_paths.py <草稿ID>")
        print("示例: python3.9 verify_draft_paths.py dfd_cat_1762313389_ae978ee4")
        sys.exit(1)
    
    draft_id = sys.argv[1]
    download_and_check_draft(draft_id)
    
    print("\n" + "=" * 80)
    print("  检查完成")
    print("=" * 80)


