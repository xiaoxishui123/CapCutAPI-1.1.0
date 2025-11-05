#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows草稿检查脚本
用于快速检查草稿文件夹的完整性和路径格式

使用方法（在Windows上）：
1. 将此脚本放到草稿文件夹中
2. 双击运行，或在命令行运行: python windows_check.py
"""

import json
import os
import sys
import re

def check_draft():
    """检查草稿文件夹"""
    print("=" * 70)
    print("🔍 Windows草稿文件夹检查")
    print("=" * 70)
    print()
    
    # 获取当前目录
    current_dir = os.getcwd()
    print(f"📁 当前目录: {current_dir}")
    print()
    
    issues = []
    
    # 检查1: 必要的文件是否存在
    print("✓ 检查1: 必要文件检查")
    print("-" * 70)
    
    required_files = [
        'draft_info.json',
        'draft_meta_info.json',
        'draft_cover.jpg'
    ]
    
    for filename in required_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  ✅ {filename} ({size:,} 字节)")
        else:
            print(f"  ❌ {filename} 不存在")
            issues.append(f"{filename} 文件缺失")
    
    print()
    
    # 检查2: assets文件夹结构
    print("✓ 检查2: assets文件夹结构")
    print("-" * 70)
    
    if not os.path.exists('assets'):
        print("  ❌ assets 文件夹不存在！")
        issues.append("assets 文件夹缺失")
    else:
        print("  ✅ assets 文件夹存在")
        
        # 检查audio文件夹
        if not os.path.exists('assets/audio') and not os.path.exists('assets\\audio'):
            print("  ❌ assets/audio 文件夹不存在！")
            issues.append("assets/audio 文件夹缺失")
        else:
            audio_path = 'assets/audio' if os.path.exists('assets/audio') else 'assets\\audio'
            audio_files = [f for f in os.listdir(audio_path) if f.endswith('.mp3')]
            print(f"  ✅ assets/audio 存在，包含 {len(audio_files)} 个mp3文件")
            
            # 显示文件大小
            for audio_file in audio_files[:5]:  # 显示前5个
                file_path = os.path.join(audio_path, audio_file)
                size = os.path.getsize(file_path)
                size_kb = size / 1024
                status = "✅" if size > 1000 else "⚠️"
                print(f"    {status} {audio_file}: {size_kb:.1f} KB")
                if size < 1000:
                    issues.append(f"{audio_file} 文件大小异常 ({size} 字节)")
        
        # 检查image文件夹
        if not os.path.exists('assets/image') and not os.path.exists('assets\\image'):
            print("  ⚠️ assets/image 文件夹不存在")
        else:
            image_path = 'assets/image' if os.path.exists('assets/image') else 'assets\\image'
            image_files = [f for f in os.listdir(image_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
            print(f"  ✅ assets/image 存在，包含 {len(image_files)} 个图片文件")
    
    print()
    
    # 检查3: draft_meta_info.json 内容
    print("✓ 检查3: draft_meta_info.json 配置")
    print("-" * 70)
    
    if os.path.exists('draft_meta_info.json'):
        try:
            with open('draft_meta_info.json', 'r', encoding='utf-8') as f:
                meta_info = json.load(f)
            
            # 检查关键字段
            draft_root_path = meta_info.get('draft_root_path', '')
            draft_fold_path = meta_info.get('draft_fold_path', '')
            draft_name = meta_info.get('draft_name', '')
            
            print(f"  draft_name: '{draft_name}'")
            
            if draft_root_path == '':
                print(f"  ✅ draft_root_path: 空 (正确)")
            else:
                print(f"  ❌ draft_root_path: '{draft_root_path}' (应该为空)")
                issues.append(f"draft_root_path 不为空: {draft_root_path}")
            
            if draft_fold_path == '':
                print(f"  ✅ draft_fold_path: 空 (正确)")
            else:
                print(f"  ❌ draft_fold_path: '{draft_fold_path}' (应该为空)")
                issues.append(f"draft_fold_path 不为空: {draft_fold_path}")
                
        except Exception as e:
            print(f"  ❌ 读取失败: {e}")
            issues.append(f"无法读取 draft_meta_info.json: {e}")
    
    print()
    
    # 检查4: draft_info.json 路径格式
    print("✓ 检查4: draft_info.json 路径格式")
    print("-" * 70)
    
    if os.path.exists('draft_info.json'):
        try:
            with open('draft_info.json', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取所有path字段
            paths = re.findall(r'"path":"([^"]+)"', content)
            
            if paths:
                print(f"  找到 {len(paths)} 个路径引用")
                
                # 检查第一个路径
                first_path = paths[0]
                print(f"  第一个路径: {first_path[:80]}...")
                
                # 判断是相对路径还是绝对路径
                is_absolute = (
                    first_path.startswith('F:') or 
                    first_path.startswith('C:') or 
                    first_path.startswith('D:') or 
                    first_path.startswith('E:')
                )
                
                if is_absolute:
                    print(f"  ❌ 使用了绝对路径！这会导致素材无法识别！")
                    issues.append("draft_info.json 使用了绝对路径")
                else:
                    if first_path.startswith('assets\\') or first_path.startswith('assets/'):
                        print(f"  ✅ 使用相对路径 (正确)")
                    else:
                        print(f"  ⚠️ 路径格式可能有问题")
                        issues.append(f"路径格式异常: {first_path}")
            else:
                print(f"  ⚠️ 未找到任何路径引用")
                
        except Exception as e:
            print(f"  ❌ 读取失败: {e}")
            issues.append(f"无法读取 draft_info.json: {e}")
    
    print()
    
    # 总结
    print("=" * 70)
    print("📊 检查结果总结")
    print("=" * 70)
    
    if not issues:
        print("✅ 所有检查通过！草稿文件格式正确。")
        print()
        print("如果剪映仍然无法识别素材，可能的原因：")
        print("1. 剪映版本问题")
        print("2. 剪映数据库缓存问题")
        print("3. 文件夹名称与draft_name不匹配")
    else:
        print(f"❌ 发现 {len(issues)} 个问题：")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print()
        print("建议：")
        print("1. 重新下载草稿ZIP文件")
        print("2. 使用正规解压工具（如WinRAR、7-Zip）完整解压")
        print("3. 确保解压后文件夹结构完整")
    
    print()
    print("按回车键退出...")
    input()

if __name__ == '__main__':
    try:
        check_draft()
    except Exception as e:
        print(f"程序出错: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("按回车键退出...")
        input()

