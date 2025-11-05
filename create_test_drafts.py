#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
创建测试草稿 - 验证剪映的路径识别机制

生成3个不同配置的草稿版本，测试剪映支持哪种路径格式：
1. 相对路径 + 空root_path
2. 相对路径 + 设置root_path  
3. 绝对路径 + 设置root_path
"""

import json
import os
import sys
import zipfile
import tempfile
import shutil
from oss import _ensure_bucket

def create_test_version(draft_id, version_name, path_mode):
    """
    创建测试版本的草稿
    
    path_mode:
    - 'relative_empty': 相对路径 + draft_root_path=""
    - 'relative_with_root': 相对路径 + draft_root_path设置
    - 'absolute': 绝对路径 + draft_root_path设置
    """
    
    print(f"\n{'='*80}")
    print(f"创建测试版本: {version_name} ({path_mode})")
    print(f"{'='*80}")
    
    bucket = _ensure_bucket()
    base_key = f"{draft_id}.zip"
    
    # 下载基础ZIP
    with tempfile.TemporaryDirectory() as tmpdir:
        base_zip_path = os.path.join(tmpdir, "base.zip")
        bucket.get_object_to_file(base_key, base_zip_path)
        
        # 解压
        extract_dir = os.path.join(tmpdir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(base_zip_path, 'r') as zf:
            zf.extractall(extract_dir)
        
        # 修改配置
        draft_info_path = os.path.join(extract_dir, 'draft_info.json')
        draft_meta_path = os.path.join(extract_dir, 'draft_meta_info.json')
        
        # 读取并修改draft_info.json
        with open(draft_info_path, 'r', encoding='utf-8') as f:
            draft_info = json.load(f)
        
        # 读取并修改draft_meta_info.json
        with open(draft_meta_path, 'r', encoding='utf-8') as f:
            draft_meta = json.load(f)
        
        # 根据模式设置路径
        if path_mode == 'relative_empty':
            print("配置: 相对路径 + draft_root_path为空")
            # draft_info.json中使用相对路径
            modify_paths_in_dict(draft_info, lambda p: to_relative_path(p))
            # draft_meta_info.json中清空路径
            draft_meta['draft_root_path'] = ""
            draft_meta['draft_fold_path'] = ""
            
        elif path_mode == 'relative_with_root':
            print("配置: 相对路径 + 设置draft_root_path")
            # draft_info.json中使用相对路径
            modify_paths_in_dict(draft_info, lambda p: to_relative_path(p))
            # draft_meta_info.json中设置根路径（但素材路径仍是相对的）
            draft_meta['draft_root_path'] = "F:\\jianyin\\cgwz\\JianyingPro Drafts"
            draft_meta['draft_fold_path'] = f"F:\\jianyin\\cgwz\\JianyingPro Drafts\\{draft_id}"
            
        elif path_mode == 'absolute':
            print("配置: 绝对路径 + 设置draft_root_path")
            # draft_info.json中使用绝对路径
            modify_paths_in_dict(draft_info, lambda p: to_absolute_path(p, draft_id))
            # draft_meta_info.json中设置根路径
            draft_meta['draft_root_path'] = "F:\\jianyin\\cgwz\\JianyingPro Drafts"
            draft_meta['draft_fold_path'] = f"F:\\jianyin\\cgwz\\JianyingPro Drafts\\{draft_id}"
        
        # 保存修改后的文件
        with open(draft_info_path, 'w', encoding='utf-8') as f:
            json.dump(draft_info, f, ensure_ascii=False, separators=(',', ':'))
        
        with open(draft_meta_path, 'w', encoding='utf-8') as f:
            json.dump(draft_meta, f, ensure_ascii=False, separators=(',', ':'))
        
        # 打印配置示例
        print("\n配置示例:")
        print(f"  draft_root_path: {draft_meta['draft_root_path']}")
        print(f"  draft_fold_path: {draft_meta['draft_fold_path'][:60] if draft_meta['draft_fold_path'] else '(空)'}")
        
        # 查找第一个素材路径示例
        sample_path = find_first_material_path(draft_info)
        if sample_path:
            print(f"  素材路径示例: {sample_path[:70]}")
        
        # 重新打包
        new_zip_path = os.path.join(tmpdir, f"test_{version_name}.zip")
        with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, extract_dir)
                    zf.write(file_path, arcname)
        
        # 上传到OSS（可选）
        # test_key = f"{draft_id}__test_{version_name}.zip"
        # bucket.put_object_from_file(test_key, new_zip_path)
        # print(f"✅ 已上传到OSS: {test_key}")
        
        # 或者保存到本地
        output_dir = "/home/CapCutAPI-1.1.0/test_drafts"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{draft_id}__{version_name}.zip")
        shutil.copy2(new_zip_path, output_path)
        print(f"✅ 已保存到: {output_path}")
        
        return output_path


def modify_paths_in_dict(obj, path_func):
    """递归修改字典中的路径"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and 'assets' in value.lower():
                obj[key] = path_func(value)
            else:
                modify_paths_in_dict(value, path_func)
    elif isinstance(obj, list):
        for item in obj:
            modify_paths_in_dict(item, path_func)


def to_relative_path(path):
    """转换为相对路径"""
    if 'assets' not in path.lower():
        return path
    
    path_lower = path.replace('\\', '/').lower()
    idx = path_lower.find('assets/')
    if idx >= 0:
        # 提取assets/xxx部分
        relative = path[idx:]
        # 转换为Windows路径分隔符
        return relative.replace('/', '\\')
    return path


def to_absolute_path(path, draft_id):
    """转换为绝对路径"""
    relative = to_relative_path(path)
    # 构建绝对路径
    return f"F:\\jianyin\\cgwz\\JianyingPro Drafts\\{draft_id}\\{relative}"


def find_first_material_path(obj, depth=0):
    """查找第一个素材路径"""
    if depth > 10:
        return None
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and 'assets' in value.lower():
                return value
            else:
                result = find_first_material_path(value, depth+1)
                if result:
                    return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_first_material_path(item, depth+1)
            if result:
                return result
    
    return None


def main():
    if len(sys.argv) < 2:
        print("使用方法: python3.9 create_test_drafts.py <草稿ID>")
        print("示例: python3.9 create_test_drafts.py dfd_cat_1762313389_ae978ee4")
        sys.exit(1)
    
    draft_id = sys.argv[1]
    
    print("="*80)
    print("  创建测试草稿 - 验证剪映路径识别机制")
    print("="*80)
    print(f"\n草稿ID: {draft_id}")
    print("\n将创建3个测试版本:")
    print("  1. 版本A: 相对路径 + draft_root_path为空")
    print("  2. 版本B: 相对路径 + 设置draft_root_path")
    print("  3. 版本C: 绝对路径 + 设置draft_root_path")
    
    # 创建3个测试版本
    test_versions = [
        ('version_A_relative_empty', 'relative_empty'),
        ('version_B_relative_with_root', 'relative_with_root'),
        ('version_C_absolute', 'absolute'),
    ]
    
    outputs = []
    for version_name, path_mode in test_versions:
        try:
            output_path = create_test_version(draft_id, version_name, path_mode)
            outputs.append((version_name, output_path))
        except Exception as e:
            print(f"❌ 创建 {version_name} 失败: {e}")
    
    # 打印结果
    print("\n" + "="*80)
    print("  创建完成")
    print("="*80)
    print("\n测试文件位置:")
    for version_name, output_path in outputs:
        print(f"  {version_name}: {output_path}")
    
    print("\n测试步骤:")
    print("  1. 下载这3个ZIP文件到Windows")
    print("  2. 分别解压到剪映草稿目录")
    print("  3. 用剪映打开，观察哪个能正确识别素材")
    print("  4. 记录结果并反馈")
    print("\n" + "="*80)


if __name__ == '__main__':
    main()


