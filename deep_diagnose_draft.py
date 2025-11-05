#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度诊断工具 - 检查剪映草稿为何识别不到素材
特别针对：结构正确但仍然无法识别的情况
"""

import os
import json
import sys
from pathlib import Path


def deep_check_draft(draft_path):
    """深度检查草稿，找出为何识别不到素材"""
    print(f"\n{'='*70}")
    print(f"🔬 深度诊断: {draft_path}")
    print(f"{'='*70}\n")
    
    issues = []
    warnings = []
    
    # 1. 基础检查
    print("1️⃣  基础结构检查...")
    draft_info_path = os.path.join(draft_path, 'draft_info.json')
    draft_meta_path = os.path.join(draft_path, 'draft_meta_info.json')
    draft_content_path = os.path.join(draft_path, 'draft_content.json')
    assets_path = os.path.join(draft_path, 'assets')
    
    has_draft_info = os.path.exists(draft_info_path)
    has_draft_meta = os.path.exists(draft_meta_path)
    has_draft_content = os.path.exists(draft_content_path)
    has_assets = os.path.exists(assets_path)
    
    print(f"   {'✅' if has_draft_info else '❌'} draft_info.json")
    print(f"   {'✅' if has_draft_meta else '❌'} draft_meta_info.json")
    print(f"   {'⚠️' if has_draft_content else '  '} draft_content.json {'(不常见)' if has_draft_content else ''}")
    print(f"   {'✅' if has_assets else '❌'} assets/")
    
    if has_draft_content:
        warnings.append("发现draft_content.json - 通常只应该有draft_info.json")
    
    # 2. 检查assets内容
    print(f"\n2️⃣  Assets文件夹内容检查...")
    if has_assets:
        audio_path = os.path.join(assets_path, 'audio')
        video_path = os.path.join(assets_path, 'video')
        image_path = os.path.join(assets_path, 'image')
        
        # 统计文件
        audio_files = []
        if os.path.exists(audio_path):
            audio_files = [f for f in os.listdir(audio_path) if f.endswith('.mp3')]
            print(f"   ✅ audio/ - {len(audio_files)} 个文件")
            if len(audio_files) > 0:
                for i, f in enumerate(audio_files[:3], 1):
                    print(f"      {i}. {f}")
                if len(audio_files) > 3:
                    print(f"      ... 还有 {len(audio_files) - 3} 个")
            else:
                issues.append("audio文件夹是空的！")
        else:
            print(f"   ❌ audio/ - 不存在")
            issues.append("缺少assets/audio/文件夹")
        
        video_files = []
        if os.path.exists(video_path):
            video_files = [f for f in os.listdir(video_path) if f.endswith(('.mp4', '.mov', '.avi'))]
            print(f"   {'✅' if len(video_files) > 0 else 'ℹ️ '} video/ - {len(video_files)} 个文件")
        
        image_files = []
        if os.path.exists(image_path):
            image_files = [f for f in os.listdir(image_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
            print(f"   {'✅' if len(image_files) > 0 else 'ℹ️ '} image/ - {len(image_files)} 个文件")
    else:
        issues.append("assets文件夹不存在！")
    
    # 3. 深度检查draft_info.json
    print(f"\n3️⃣  draft_info.json 深度检查...")
    if has_draft_info:
        try:
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                content = f.read()
                draft_info = json.loads(content)
            
            # 检查路径引用
            path_refs = []
            missing_files = []
            wrong_separator = []
            
            def extract_paths(data, prefix=""):
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key == 'path' and isinstance(value, str) and value:
                            path_refs.append((prefix, value))
                            
                            # 检查文件是否存在
                            if 'assets' in value.lower():
                                # 提取相对路径
                                if '\\assets\\' in value or '/assets/' in value:
                                    idx = value.lower().find('assets')
                                    rel_path = value[idx:].replace('/', os.sep).replace('\\', os.sep)
                                elif value.startswith('assets'):
                                    rel_path = value.replace('/', os.sep).replace('\\', os.sep)
                                else:
                                    rel_path = None
                                
                                if rel_path:
                                    full_path = os.path.join(draft_path, rel_path)
                                    if not os.path.exists(full_path):
                                        missing_files.append((value, rel_path))
                                    
                                    # 检查分隔符
                                    if os.name == 'nt':  # Windows
                                        if '/' in value and '\\' not in value:
                                            wrong_separator.append(value)
                        else:
                            extract_paths(value, f"{prefix}.{key}" if prefix else key)
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        extract_paths(item, f"{prefix}[{i}]")
            
            extract_paths(draft_info)
            
            print(f"   找到 {len(path_refs)} 个路径引用")
            
            if wrong_separator:
                print(f"\n   ⚠️  发现 {len(wrong_separator)} 个路径使用了错误的分隔符:")
                for path in wrong_separator[:3]:
                    print(f"      ❌ {path[:60]}...")
                    print(f"         应该使用反斜杠 '\\\\' 而不是正斜杠 '/'")
                issues.append(f"有{len(wrong_separator)}个路径使用了正斜杠，在Windows下应该用反斜杠")
            
            if missing_files:
                print(f"\n   ❌ 发现 {len(missing_files)} 个引用的文件不存在:")
                for orig_path, rel_path in missing_files[:5]:
                    print(f"      文件不存在: {rel_path}")
                issues.append(f"有{len(missing_files)}个引用的文件实际不存在")
            
            if not wrong_separator and not missing_files and path_refs:
                print(f"   ✅ 所有路径格式正确且文件都存在")
            
            # 显示示例路径
            if path_refs:
                print(f"\n   路径示例:")
                for prefix, path in path_refs[:2]:
                    path_display = path if len(path) <= 60 else path[:57] + "..."
                    print(f"      {path_display}")
                    
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON解析失败: {e}")
            issues.append(f"draft_info.json格式错误: {e}")
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
            issues.append(f"无法读取draft_info.json: {e}")
    
    # 4. 检查draft_meta_info.json
    print(f"\n4️⃣  draft_meta_info.json 检查...")
    if has_draft_meta:
        try:
            with open(draft_meta_path, 'r', encoding='utf-8') as f:
                meta_info = json.load(f)
            
            draft_fold_path = meta_info.get('draft_fold_path', None)
            draft_root_path = meta_info.get('draft_root_path', None)
            
            print(f"   draft_fold_path: '{draft_fold_path}'")
            print(f"   draft_root_path: '{draft_root_path}'")
            
            if draft_fold_path == "" and draft_root_path == "":
                print(f"   ✅ 相对路径模式（字段为空）")
            elif draft_fold_path and draft_root_path:
                print(f"   ℹ️  绝对路径模式")
                # 检查路径是否正确
                current_location = os.path.dirname(draft_path)
                if draft_fold_path and draft_fold_path != draft_path:
                    warnings.append(f"draft_fold_path指向其他位置: {draft_fold_path}")
                    print(f"   ⚠️  draft_fold_path与当前位置不匹配!")
                    print(f"      配置的: {draft_fold_path}")
                    print(f"      实际的: {draft_path}")
            
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
            issues.append(f"无法读取draft_meta_info.json: {e}")
    
    # 5. 特殊检查
    print(f"\n5️⃣  特殊情况检查...")
    
    # 检查是否有.locked文件
    locked_file = os.path.join(draft_path, '.locked')
    if os.path.exists(locked_file):
        print(f"   ⚠️  发现.locked文件 - 草稿可能被锁定")
        warnings.append("草稿被锁定，可能影响剪映读取")
    
    # 检查文件编码
    if has_draft_info:
        try:
            with open(draft_info_path, 'rb') as f:
                raw = f.read()
                # 检查BOM
                if raw.startswith(b'\xef\xbb\xbf'):
                    print(f"   ℹ️  draft_info.json 使用UTF-8 BOM编码")
                elif raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
                    print(f"   ⚠️  draft_info.json 使用UTF-16编码（可能有问题）")
                    warnings.append("draft_info.json使用UTF-16编码，建议转换为UTF-8")
        except:
            pass
    
    # 检查draft_content.json是否覆盖了draft_info.json
    if has_draft_content and has_draft_info:
        info_mtime = os.path.getmtime(draft_info_path)
        content_mtime = os.path.getmtime(draft_content_path)
        
        if content_mtime > info_mtime:
            print(f"   ⚠️  draft_content.json比draft_info.json更新")
            warnings.append("draft_content.json可能覆盖了draft_info.json的内容")
            print(f"      剪映可能读取draft_content.json而不是draft_info.json")
    
    # 6. 输出诊断结果
    print(f"\n{'='*70}")
    print("📊 诊断结果总结:")
    print(f"{'='*70}")
    
    if not issues and not warnings:
        print("\n✅ 未发现明显问题！")
        print("\n可能的其他原因:")
        print("   1. 剪映版本过旧或过新")
        print("   2. 剪映缓存问题（尝试重启剪映）")
        print("   3. Windows权限问题")
        print("   4. 草稿数据库损坏")
    else:
        if issues:
            print(f"\n❌ 发现 {len(issues)} 个问题:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        
        if warnings:
            print(f"\n⚠️  发现 {len(warnings)} 个警告:")
            for i, warning in enumerate(warnings, 1):
                print(f"   {i}. {warning}")
    
    # 7. 建议的解决方案
    if issues or warnings:
        print(f"\n💡 建议的解决方案:")
        
        if any('分隔符' in issue for issue in issues):
            print("\n   【修复路径分隔符】")
            print("   问题: 路径使用了正斜杠'/'，Windows下应该用反斜杠'\\'")
            print("   解决: 需要重新生成草稿，或手动修改draft_info.json")
        
        if any('不存在' in issue for issue in issues):
            print("\n   【文件缺失】")
            print("   问题: draft_info.json引用的文件不存在")
            print("   解决: 重新下载草稿，确保素材完整下载")
        
        if any('draft_content.json' in warning for warning in warnings):
            print("\n   【文件冲突】")
            print("   问题: 存在draft_content.json可能干扰draft_info.json")
            print("   解决: 尝试删除或重命名draft_content.json")
        
        if any('draft_fold_path' in warning for warning in warnings):
            print("\n   【路径不匹配】")
            print("   问题: draft_meta_info.json中的路径与实际位置不符")
            print("   解决: 修改draft_meta_info.json或移动草稿到正确位置")
    
    print(f"\n{'='*70}\n")
    return len(issues) == 0


def main():
    if len(sys.argv) < 2:
        print("\n用法: python deep_diagnose_draft.py <草稿文件夹路径>")
        print("\n示例:")
        print("  python deep_diagnose_draft.py \"F:\\jianying\\cgwz\\JianyingPro Drafts\\dfd_cat_xxx\"")
        return
    
    draft_path = sys.argv[1]
    
    if not os.path.exists(draft_path):
        print(f"\n❌ 错误: 路径不存在: {draft_path}")
        return
    
    if not os.path.isdir(draft_path):
        print(f"\n❌ 错误: 不是文件夹: {draft_path}")
        return
    
    success = deep_check_draft(draft_path)
    
    if not success:
        print("提示: 如果需要帮助解决这些问题，请将诊断结果发送给技术支持。\n")


if __name__ == '__main__':
    main()

