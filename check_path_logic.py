#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查配置路径下载草稿的逻辑
验证所有涉及路径的地方是否都使用了配置的路径
"""

import json
import os
from typing import Dict, List, Any, Set

def find_all_path_fields(data: Any, parent_key: str = "", path_fields: Set[str] = None) -> Set[str]:
    """
    递归查找JSON中所有的路径字段
    返回所有包含路径的字段名
    """
    if path_fields is None:
        path_fields = set()
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_key = f"{parent_key}.{key}" if parent_key else key
            
            # 检查是否是路径字段（包含常见路径特征）
            if isinstance(value, str):
                # 路径字段通常包含这些特征
                path_indicators = ['path', 'file', 'dir', 'folder']
                if any(indicator in key.lower() for indicator in path_indicators):
                    path_fields.add(current_key)
                
                # 或者值本身看起来像路径
                if any(pattern in value for pattern in ['/', '\\', 'assets', '.mp3', '.mp4', '.png', '.jpg']):
                    if len(value) > 10:  # 避免误报短字符串
                        path_fields.add(current_key)
            
            # 递归检查
            find_all_path_fields(value, current_key, path_fields)
    
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            current_key = f"{parent_key}[{idx}]"
            find_all_path_fields(item, current_key, path_fields)
    
    return path_fields


def extract_path_values(data: Any, path_type: str = "all") -> List[Dict[str, str]]:
    """
    提取所有路径值
    path_type: 'all' | 'assets_only' | 'non_assets'
    """
    paths = []
    
    def extract_recursive(obj, parent_path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{parent_path}.{key}" if parent_path else key
                
                if isinstance(value, str):
                    # 检查是否是路径
                    if any(indicator in key.lower() for indicator in ['path', 'file']):
                        contains_assets = 'assets/' in value.lower() or 'assets\\' in value.lower()
                        
                        if path_type == "all" or \
                           (path_type == "assets_only" and contains_assets) or \
                           (path_type == "non_assets" and not contains_assets):
                            paths.append({
                                'field': current_path,
                                'value': value,
                                'contains_assets': contains_assets
                            })
                
                extract_recursive(value, current_path)
        
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                extract_recursive(item, f"{parent_path}[{idx}]")
    
    extract_recursive(data)
    return paths


def simulate_path_rewrite(path: str, draft_id: str, client_os: str, draft_folder: str) -> str:
    """
    模拟 customize_zip.py 中的路径重写逻辑
    """
    lower = path.replace("\\", "/").lower()
    if "assets/" not in lower:
        return path  # 不包含 assets/，不重写
    
    # 找到 assets/ 的位置
    idx = lower.find("assets/")
    rel = path[idx:]  # 从 assets/ 开始的相对路径
    
    # 构建新路径
    base = draft_folder.rstrip("/\\")
    joined = f"{base}/{draft_id}/" + rel
    
    # 根据操作系统标准化路径
    if client_os == 'windows':
        return joined.replace('/', '\\')
    else:
        return joined.replace('\\', '/')


def check_draft_paths(draft_path: str, draft_id: str, client_os: str, draft_folder: str):
    """
    检查草稿文件中的路径配置
    """
    draft_info_path = os.path.join(draft_path, "draft_info.json")
    
    if not os.path.exists(draft_info_path):
        print(f"❌ 草稿文件不存在: {draft_info_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"检查草稿: {draft_id}")
    print(f"草稿路径: {draft_path}")
    print(f"配置的下载路径: {draft_folder}")
    print(f"客户端系统: {client_os}")
    print(f"{'='*80}\n")
    
    # 读取草稿文件
    with open(draft_info_path, 'r', encoding='utf-8') as f:
        draft_data = json.load(f)
    
    # 1. 查找所有路径字段
    print("📋 步骤 1: 查找所有路径字段")
    path_fields = find_all_path_fields(draft_data)
    print(f"找到 {len(path_fields)} 个路径字段:\n")
    for field in sorted(path_fields):
        print(f"  - {field}")
    
    # 2. 提取所有路径值
    print(f"\n📋 步骤 2: 提取所有路径值")
    all_paths = extract_path_values(draft_data, "all")
    assets_paths = [p for p in all_paths if p['contains_assets']]
    non_assets_paths = [p for p in all_paths if not p['contains_assets']]
    
    print(f"包含 assets/ 的路径: {len(assets_paths)} 个")
    print(f"不包含 assets/ 的路径: {len(non_assets_paths)} 个")
    
    # 3. 显示包含 assets/ 的路径及其重写结果
    print(f"\n📋 步骤 3: 验证 assets/ 路径重写")
    print(f"\n✅ 包含 assets/ 的路径（会被重写）:")
    for idx, p in enumerate(assets_paths[:5], 1):  # 只显示前5个
        original = p['value']
        rewritten = simulate_path_rewrite(original, draft_id, client_os, draft_folder)
        print(f"\n  {idx}. 字段: {p['field']}")
        print(f"     原始路径: {original}")
        print(f"     重写路径: {rewritten}")
        print(f"     重写正确: {'✅' if draft_folder in rewritten else '❌'}")
    
    if len(assets_paths) > 5:
        print(f"\n  ... 还有 {len(assets_paths) - 5} 个路径")
    
    # 4. 显示不包含 assets/ 的路径（不会被重写）
    print(f"\n⚠️  不包含 assets/ 的路径（不会被重写）:")
    if non_assets_paths:
        for idx, p in enumerate(non_assets_paths[:5], 1):
            print(f"\n  {idx}. 字段: {p['field']}")
            print(f"     路径值: {p['value']}")
            print(f"     ⚠️ 警告: 此路径不会被重写！")
        
        if len(non_assets_paths) > 5:
            print(f"\n  ... 还有 {len(non_assets_paths) - 5} 个路径")
    else:
        print(f"\n  ✅ 没有发现不包含 assets/ 的路径")
    
    # 5. 总结
    print(f"\n{'='*80}")
    print("📊 检查总结:")
    print(f"{'='*80}")
    print(f"总路径字段数: {len(path_fields)}")
    print(f"包含 assets/ 的路径: {len(assets_paths)} ✅ 会被正确重写")
    print(f"不包含 assets/ 的路径: {len(non_assets_paths)} {'⚠️ 需要注意' if non_assets_paths else '✅ 无问题'}")
    
    if non_assets_paths:
        print(f"\n⚠️  警告: 发现 {len(non_assets_paths)} 个不包含 'assets/' 的路径")
        print("   这些路径不会被 customize_zip.py 重写！")
        print("   如果这些路径指向素材文件，可能导致剪映无法找到文件。")
    else:
        print(f"\n✅ 所有路径都包含 'assets/'，会被正确重写为配置的路径！")
    
    print(f"{'='*80}\n")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("配置路径下载草稿逻辑检查工具")
    print("="*80)
    
    # 读取配置的路径
    config_path = '/home/CapCutAPI-1.1.0/path_config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            configured_path = config.get('custom_download_path', '')
    else:
        configured_path = 'D:\\test'  # 默认配置路径
    
    print(f"\n📁 当前配置的下载路径: {configured_path}")
    
    # 查找草稿文件夹
    base_dir = '/home/CapCutAPI-1.1.0'
    draft_folders = []
    
    # 检查多个可能的草稿位置
    possible_locations = [
        'F:/jianyin/cgwz/JianyingPro Drafts',
        'JianyingPro Drafts',
        'drafts',
        'cgwz'
    ]
    
    for location in possible_locations:
        full_path = os.path.join(base_dir, location)
        if os.path.exists(full_path):
            for item in os.listdir(full_path):
                if item.startswith('dfd_'):
                    draft_path = os.path.join(full_path, item)
                    if os.path.isdir(draft_path):
                        draft_folders.append((item, draft_path))
    
    if not draft_folders:
        print("❌ 没有找到任何草稿文件夹")
        return
    
    print(f"\n找到 {len(draft_folders)} 个草稿文件夹")
    
    # 检查前3个草稿
    for draft_id, draft_path in draft_folders[:3]:
        check_draft_paths(
            draft_path=draft_path,
            draft_id=draft_id,
            client_os='windows',
            draft_folder=configured_path
        )
    
    if len(draft_folders) > 3:
        print(f"\n... 还有 {len(draft_folders) - 3} 个草稿未检查")


if __name__ == '__main__':
    main()

