#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
草稿结构诊断工具
用于检查智能下载的草稿文件夹结构是否正确
"""

import os
import json
import zipfile
import sys
from pathlib import Path


def check_draft_folder(draft_path):
    """检查草稿文件夹结构"""
    print(f"\n{'='*60}")
    print(f"📁 检查草稿文件夹: {draft_path}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(draft_path):
        print(f"❌ 错误：草稿文件夹不存在: {draft_path}")
        return False
    
    issues = []
    warnings = []
    
    # 1. 检查必需文件
    print("1️⃣ 检查必需文件...")
    required_files = {
        'draft_info.json': False,
        'draft_meta_info.json': False
    }
    
    for filename in required_files.keys():
        file_path = os.path.join(draft_path, filename)
        if os.path.exists(file_path):
            print(f"   ✅ {filename} - 存在")
            required_files[filename] = True
        else:
            print(f"   ❌ {filename} - 缺失")
            issues.append(f"缺少文件: {filename}")
    
    # 2. 检查assets文件夹
    print("\n2️⃣ 检查assets文件夹...")
    assets_path = os.path.join(draft_path, 'assets')
    if os.path.exists(assets_path):
        print(f"   ✅ assets/ - 存在")
        
        # 检查子文件夹
        subdirs = ['audio', 'video', 'image']
        for subdir in subdirs:
            subdir_path = os.path.join(assets_path, subdir)
            if os.path.exists(subdir_path):
                file_count = len([f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))])
                print(f"      ✅ assets/{subdir}/ - 存在 ({file_count} 个文件)")
            else:
                print(f"      ⚠️  assets/{subdir}/ - 不存在")
    else:
        print(f"   ❌ assets/ - 不存在")
        issues.append("缺少assets文件夹 - 这是导致素材识别失败的主要原因！")
    
    # 3. 检查draft_info.json中的路径
    print("\n3️⃣ 检查draft_info.json中的路径...")
    draft_info_path = os.path.join(draft_path, 'draft_info.json')
    if os.path.exists(draft_info_path):
        try:
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_info = json.load(f)
            
            # 查找所有包含path的字段
            paths_found = []
            
            def find_paths(data, prefix=""):
                if isinstance(data, dict):
                    for key, value in data.items():
                        if 'path' in key.lower() and isinstance(value, str) and value:
                            paths_found.append((f"{prefix}.{key}" if prefix else key, value))
                        else:
                            find_paths(value, f"{prefix}.{key}" if prefix else key)
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        find_paths(item, f"{prefix}[{i}]")
            
            find_paths(draft_info)
            
            if paths_found:
                print(f"   找到 {len(paths_found)} 个路径引用:")
                for i, (field, path) in enumerate(paths_found[:5], 1):  # 只显示前5个
                    path_display = path if len(path) <= 60 else path[:57] + "..."
                    print(f"      {i}. {field}: {path_display}")
                    
                    # 检查路径格式
                    if 'assets' in path.lower():
                        # 检查是否为相对路径
                        if path.startswith('assets') or '\\assets\\' in path or '/assets/' in path:
                            # 提取相对路径部分
                            if 'assets' in path.lower():
                                idx = path.lower().find('assets')
                                rel_path = path[idx:]
                                
                                # 检查实际文件是否存在
                                actual_file = os.path.join(draft_path, rel_path.replace('\\', os.sep).replace('/', os.sep))
                                if os.path.exists(actual_file):
                                    print(f"         ✅ 文件存在")
                                else:
                                    print(f"         ❌ 文件不存在: {rel_path}")
                                    issues.append(f"路径引用的文件不存在: {rel_path}")
                
                if len(paths_found) > 5:
                    print(f"      ... 还有 {len(paths_found) - 5} 个路径")
            else:
                print(f"   ⚠️  未找到路径引用")
                warnings.append("draft_info.json中没有找到素材路径引用")
                
        except Exception as e:
            print(f"   ❌ 读取draft_info.json失败: {e}")
            issues.append(f"无法读取draft_info.json: {e}")
    
    # 4. 检查draft_meta_info.json
    print("\n4️⃣ 检查draft_meta_info.json...")
    meta_info_path = os.path.join(draft_path, 'draft_meta_info.json')
    if os.path.exists(meta_info_path):
        try:
            with open(meta_info_path, 'r', encoding='utf-8') as f:
                meta_info = json.load(f)
            
            draft_fold_path = meta_info.get('draft_fold_path', None)
            draft_root_path = meta_info.get('draft_root_path', None)
            
            print(f"   draft_fold_path: '{draft_fold_path}'")
            print(f"   draft_root_path: '{draft_root_path}'")
            
            # 相对路径模式下，这两个字段应该为空
            if draft_fold_path == "" and draft_root_path == "":
                print(f"   ✅ 相对路径模式（draft_fold_path和draft_root_path为空）")
            elif draft_fold_path or draft_root_path:
                print(f"   ℹ️  绝对路径模式")
                warnings.append("使用绝对路径模式，需确保路径正确")
            
        except Exception as e:
            print(f"   ❌ 读取draft_meta_info.json失败: {e}")
            issues.append(f"无法读取draft_meta_info.json: {e}")
    
    # 5. 输出诊断结果
    print(f"\n{'='*60}")
    print("📊 诊断结果:")
    print(f"{'='*60}")
    
    if not issues and not warnings:
        print("✅ 草稿结构正常！")
        return True
    else:
        if issues:
            print(f"\n❌ 发现 {len(issues)} 个问题:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        
        if warnings:
            print(f"\n⚠️  发现 {len(warnings)} 个警告:")
            for i, warning in enumerate(warnings, 1):
                print(f"   {i}. {warning}")
        
        return len(issues) == 0


def check_zip_file(zip_path):
    """检查ZIP文件结构"""
    print(f"\n{'='*60}")
    print(f"📦 检查ZIP文件: {zip_path}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(zip_path):
        print(f"❌ 错误：ZIP文件不存在: {zip_path}")
        return False
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            file_list = zf.namelist()
            print(f"ZIP文件包含 {len(file_list)} 个项目:\n")
            
            # 检查关键文件和文件夹
            has_draft_info = any('draft_info.json' in f for f in file_list)
            has_draft_meta = any('draft_meta_info.json' in f for f in file_list)
            has_assets = any('assets/' in f or 'assets\\' in f for f in file_list)
            
            print(f"✅ draft_info.json: {'存在' if has_draft_info else '❌ 缺失'}")
            print(f"✅ draft_meta_info.json: {'存在' if has_draft_meta else '❌ 缺失'}")
            print(f"{'✅' if has_assets else '❌'} assets/ 文件夹: {'存在' if has_assets else '缺失'}")
            
            if has_assets:
                # 统计assets下的文件
                assets_files = [f for f in file_list if 'assets/' in f or 'assets\\' in f]
                audio_files = [f for f in assets_files if '/audio/' in f or '\\audio\\' in f]
                video_files = [f for f in assets_files if '/video/' in f or '\\video\\' in f]
                image_files = [f for f in assets_files if '/image/' in f or '\\image\\' in f]
                
                print(f"\n   assets/ 下的文件:")
                print(f"      audio: {len(audio_files)} 个文件")
                print(f"      video: {len(video_files)} 个文件")
                print(f"      image: {len(image_files)} 个文件")
                
                # 显示部分文件
                if audio_files:
                    print(f"\n   audio文件示例:")
                    for f in audio_files[:3]:
                        print(f"      - {os.path.basename(f)}")
                    if len(audio_files) > 3:
                        print(f"      ... 还有 {len(audio_files) - 3} 个")
            
            return has_draft_info and has_draft_meta and has_assets
            
    except Exception as e:
        print(f"❌ 读取ZIP文件失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🔍 剪映草稿结构诊断工具")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("\n用法:")
        print("  检查草稿文件夹: python diagnose_draft_structure.py <草稿文件夹路径>")
        print("  检查ZIP文件:    python diagnose_draft_structure.py <ZIP文件路径>")
        print("\n示例:")
        print("  python diagnose_draft_structure.py /path/to/dfd_cat_1234567890_abc123")
        print("  python diagnose_draft_structure.py /path/to/draft.zip")
        return
    
    path = sys.argv[1]
    
    if path.endswith('.zip'):
        success = check_zip_file(path)
    elif os.path.isdir(path):
        success = check_draft_folder(path)
    else:
        print(f"❌ 错误：无法识别的路径类型: {path}")
        print("   请提供草稿文件夹路径或ZIP文件路径")
        return
    
    print(f"\n{'='*60}")
    if success:
        print("✅ 诊断完成：结构正常")
    else:
        print("❌ 诊断完成：发现问题，请查看上方详情")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()

