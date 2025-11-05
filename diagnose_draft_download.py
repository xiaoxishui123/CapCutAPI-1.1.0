#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
草稿下载诊断工具

功能：分析草稿文件，检查路径和draft_id配置，帮助诊断剪映识别不到素材的问题
使用方法：
    python3.9 diagnose_draft_download.py <草稿ID>
    
示例：
    python3.9 diagnose_draft_download.py dfd_cat_1762313389_ae978ee4
"""

import json
import os
import sys
import zipfile
import tempfile
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/draft_diagnose.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('draft_diagnose')


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def check_draft_structure(draft_path):
    """检查草稿文件夹结构"""
    print_section("📁 草稿文件夹结构检查")
    
    required_files = [
        'draft_info.json',
        'draft_meta_info.json'
    ]
    
    required_dirs = [
        'assets/audio',
        'assets/image',
        'assets/video'
    ]
    
    all_ok = True
    
    # 检查必需文件
    print("\n必需文件：")
    for file in required_files:
        file_path = os.path.join(draft_path, file)
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        print(f"  {status} {file}")
        if not exists:
            all_ok = False
    
    # 检查必需目录
    print("\n必需目录：")
    for dir_name in required_dirs:
        dir_path = os.path.join(draft_path, dir_name)
        exists = os.path.isdir(dir_path)
        status = "✅" if exists else "⚠️"
        
        if exists:
            # 统计素材数量
            files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
            count = len(files)
            print(f"  {status} {dir_name} ({count} 个文件)")
        else:
            print(f"  {status} {dir_name} (不存在)")
    
    return all_ok


def analyze_draft_info(draft_path):
    """分析draft_info.json中的路径配置"""
    print_section("📄 draft_info.json 路径分析")
    
    draft_info_path = os.path.join(draft_path, 'draft_info.json')
    if not os.path.exists(draft_info_path):
        print("❌ draft_info.json 文件不存在")
        return None
    
    with open(draft_info_path, 'r', encoding='utf-8') as f:
        draft_info = json.load(f)
    
    # 分析路径类型
    path_types = {
        '相对路径': 0,  # assets/audio/xxx.mp3
        '绝对路径(Windows)': 0,  # F:\path\to\xxx.mp3
        '绝对路径(Linux)': 0,  # /path/to/xxx.mp3
        '其他': 0
    }
    
    sample_paths = {
        '相对路径': [],
        '绝对路径(Windows)': [],
        '绝对路径(Linux)': [],
        '其他': []
    }
    
    def analyze_path(path_str):
        """分析路径类型"""
        if not path_str or not isinstance(path_str, str):
            return None
        
        # 检查是否包含素材路径
        if 'assets' not in path_str.lower():
            return None
        
        path_lower = path_str.replace('\\', '/').lower()
        
        # 相对路径：以assets开头
        if path_lower.startswith('assets/'):
            return '相对路径'
        
        # Windows绝对路径：包含盘符
        if ':' in path_str and ('\\' in path_str or '/' in path_str):
            return '绝对路径(Windows)'
        
        # Linux绝对路径：以/开头且包含assets
        if path_str.startswith('/') and 'assets' in path_lower:
            return '绝对路径(Linux)'
        
        return '其他'
    
    def scan_dict(obj, path_key='path'):
        """递归扫描字典中的路径字段"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and ('path' in key.lower() or key == 'replace_path'):
                    path_type = analyze_path(value)
                    if path_type:
                        path_types[path_type] += 1
                        if len(sample_paths[path_type]) < 3:
                            sample_paths[path_type].append(value)
                else:
                    scan_dict(value, path_key)
        elif isinstance(obj, list):
            for item in obj:
                scan_dict(item, path_key)
    
    scan_dict(draft_info)
    
    # 打印统计结果
    print("\n路径类型统计：")
    total_paths = sum(path_types.values())
    
    if total_paths == 0:
        print("  ⚠️  未检测到任何素材路径")
        return None
    
    for path_type, count in path_types.items():
        if count > 0:
            percentage = (count / total_paths) * 100
            print(f"  {path_type}: {count} 个 ({percentage:.1f}%)")
    
    # 打印示例路径
    print("\n示例路径：")
    for path_type, paths in sample_paths.items():
        if paths:
            print(f"\n  {path_type}:")
            for i, path in enumerate(paths[:3], 1):
                # 截断过长的路径
                display_path = path if len(path) <= 80 else path[:77] + '...'
                print(f"    {i}. {display_path}")
    
    # 判断是否存在问题
    issues = []
    
    if path_types['绝对路径(Windows)'] > 0:
        issues.append("⚠️  检测到Windows绝对路径，可能导致在其他位置无法识别素材")
    
    if path_types['绝对路径(Linux)'] > 0:
        issues.append("⚠️  检测到Linux绝对路径，在Windows上可能无法识别素材")
    
    if path_types['其他'] > 0:
        issues.append("⚠️  检测到异常路径格式")
    
    if path_types['相对路径'] == total_paths:
        print("\n✅ 所有路径都是相对路径，符合最佳实践")
    elif issues:
        print("\n问题：")
        for issue in issues:
            print(f"  {issue}")
    
    return path_types


def analyze_meta_info(draft_path):
    """分析draft_meta_info.json配置"""
    print_section("📋 draft_meta_info.json 配置分析")
    
    meta_info_path = os.path.join(draft_path, 'draft_meta_info.json')
    if not os.path.exists(meta_info_path):
        print("❌ draft_meta_info.json 文件不存在")
        return None
    
    with open(meta_info_path, 'r', encoding='utf-8') as f:
        meta_info = json.load(f)
    
    # 关键字段
    key_fields = {
        'draft_id': '草稿ID (剪映用于识别草稿的唯一标识)',
        'draft_name': '草稿名称',
        'draft_root_path': '草稿根路径',
        'draft_fold_path': '草稿完整路径',
        'tm_draft_create': '创建时间戳',
        'tm_draft_modified': '修改时间戳'
    }
    
    print("\n关键字段：")
    for field, description in key_fields.items():
        value = meta_info.get(field, '(未设置)')
        
        # 格式化显示
        if field.startswith('tm_'):
            # 时间戳转换为可读格式
            if isinstance(value, (int, float)) and value > 0:
                import datetime
                timestamp_sec = value / 1000000  # 微秒转秒
                dt = datetime.datetime.fromtimestamp(timestamp_sec)
                readable_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                print(f"  {field}:")
                print(f"    值: {value}")
                print(f"    时间: {readable_time}")
            else:
                print(f"  {field}: {value}")
        else:
            # 截断过长的值
            if isinstance(value, str) and len(value) > 60:
                display_value = value[:57] + '...'
            else:
                display_value = value
            print(f"  {field}:")
            print(f"    {display_value}")
    
    # 判断配置是否正确
    print("\n配置检查：")
    
    issues = []
    warnings = []
    
    # 检查draft_root_path
    draft_root_path = meta_info.get('draft_root_path', '')
    if draft_root_path == '':
        print("  ✅ draft_root_path 为空（相对路径模式）")
    else:
        warnings.append(f"⚠️  draft_root_path 不为空: {draft_root_path[:50]}")
        warnings.append("   这可能导致在不同位置无法识别素材")
    
    # 检查draft_fold_path
    draft_fold_path = meta_info.get('draft_fold_path', '')
    if draft_fold_path == '':
        print("  ✅ draft_fold_path 为空（相对路径模式）")
    else:
        warnings.append(f"⚠️  draft_fold_path 不为空: {draft_fold_path[:50]}")
        warnings.append("   这可能导致在不同位置无法识别素材")
    
    # 检查draft_id
    draft_id = meta_info.get('draft_id', '')
    if not draft_id:
        issues.append("❌ draft_id 为空，这会导致剪映无法识别草稿")
    else:
        # 检查UUID格式
        try:
            import uuid
            uuid.UUID(draft_id)
            print(f"  ✅ draft_id 格式正确: {draft_id}")
        except ValueError:
            warnings.append(f"⚠️  draft_id 格式不是标准UUID: {draft_id}")
    
    # 检查时间戳
    tm_create = meta_info.get('tm_draft_create', 0)
    tm_modified = meta_info.get('tm_draft_modified', 0)
    
    if tm_create == 0:
        warnings.append("⚠️  创建时间戳为0")
    
    if tm_modified == 0:
        warnings.append("⚠️  修改时间戳为0")
    
    # 打印警告和错误
    if issues:
        print("\n❌ 错误：")
        for issue in issues:
            print(f"  {issue}")
    
    if warnings:
        print("\n⚠️  警告：")
        for warning in warnings:
            print(f"  {warning}")
    
    if not issues and not warnings:
        print("\n✅ 所有配置检查通过")
    
    return meta_info


def check_actual_materials(draft_path):
    """检查实际的素材文件"""
    print_section("🎬 素材文件完整性检查")
    
    assets_dir = os.path.join(draft_path, 'assets')
    if not os.path.isdir(assets_dir):
        print("❌ assets 目录不存在")
        return
    
    # 统计各类素材
    asset_types = ['audio', 'video', 'image']
    total_files = 0
    
    print("\n素材统计：")
    for asset_type in asset_types:
        asset_dir = os.path.join(assets_dir, asset_type)
        if os.path.isdir(asset_dir):
            files = [f for f in os.listdir(asset_dir) if os.path.isfile(os.path.join(asset_dir, f))]
            count = len(files)
            total_files += count
            
            size_total = sum(os.path.getsize(os.path.join(asset_dir, f)) for f in files)
            size_mb = size_total / (1024 * 1024)
            
            print(f"  {asset_type}: {count} 个文件, 总大小: {size_mb:.2f} MB")
            
            # 显示示例文件
            if count > 0:
                sample_files = files[:3]
                print(f"    示例文件:")
                for f in sample_files:
                    file_path = os.path.join(asset_dir, f)
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    print(f"      - {f} ({file_size:.1f} KB)")
    
    if total_files == 0:
        print("\n⚠️  未检测到任何素材文件")
    else:
        print(f"\n✅ 总共 {total_files} 个素材文件")


def generate_recommendations(path_types, meta_info):
    """生成修复建议"""
    print_section("💡 诊断结果和修复建议")
    
    has_issues = False
    
    # 检查路径类型问题
    if path_types:
        if path_types.get('绝对路径(Windows)', 0) > 0 or path_types.get('绝对路径(Linux)', 0) > 0:
            has_issues = True
            print("\n❌ 问题1：检测到绝对路径")
            print("   原因：草稿中的素材路径使用了绝对路径格式")
            print("   影响：草稿移动到其他位置后，剪映无法找到素材文件")
            print("\n   解决方案：")
            print("   1. 重新使用'智能下载'功能下载草稿（推荐）")
            print("      - 访问：http://8.148.70.18:9000/draft/preview/<草稿ID>")
            print("      - 点击：🧠 智能下载")
            print("   2. 或使用路径转换工具修复已下载的草稿")
    
    # 检查draft_meta_info配置问题
    if meta_info:
        draft_root_path = meta_info.get('draft_root_path', '')
        draft_fold_path = meta_info.get('draft_fold_path', '')
        
        if draft_root_path or draft_fold_path:
            has_issues = True
            print("\n❌ 问题2：draft_meta_info.json 中配置了绝对路径")
            print(f"   draft_root_path: {draft_root_path[:50] if draft_root_path else '(空)'}")
            print(f"   draft_fold_path: {draft_fold_path[:50] if draft_fold_path else '(空)'}")
            print("   影响：剪映会尝试在配置的路径中查找素材，如果路径不匹配会导致素材丢失")
            print("\n   解决方案：")
            print("   使用刷新工具清空路径配置：")
            print("   python3.9 tools/refresh_draft_id.py <草稿文件夹路径>")
    
    if not has_issues:
        print("\n✅ 未检测到明显问题")
        print("\n如果剪映仍然识别不到素材，可能的原因：")
        print("  1. 草稿文件夹名称与draft_meta_info.json中的draft_name不一致")
        print("  2. 素材文件损坏或格式不支持")
        print("  3. 剪映数据库缓存问题（尝试重启剪映）")
        print("  4. 草稿版本不兼容（检查是否使用了正确的剪映版本）")
    
    print("\n" + "=" * 80)


def diagnose_local_draft(draft_id):
    """诊断本地草稿文件夹"""
    # 查找草稿文件夹
    current_dir = os.path.dirname(os.path.abspath(__file__))
    draft_path = os.path.join(current_dir, draft_id)
    
    if not os.path.exists(draft_path):
        # 尝试在drafts目录中查找
        draft_path = os.path.join(current_dir, 'drafts', draft_id)
    
    if not os.path.exists(draft_path):
        logger.error(f"❌ 找不到草稿文件夹: {draft_id}")
        logger.info(f"   已搜索路径:")
        logger.info(f"   - {os.path.join(current_dir, draft_id)}")
        logger.info(f"   - {os.path.join(current_dir, 'drafts', draft_id)}")
        return False
    
    logger.info(f"✅ 找到草稿文件夹: {draft_path}")
    
    # 执行各项检查
    check_draft_structure(draft_path)
    path_types = analyze_draft_info(draft_path)
    meta_info = analyze_meta_info(draft_path)
    check_actual_materials(draft_path)
    generate_recommendations(path_types, meta_info)
    
    return True


def diagnose_zip_file(zip_path):
    """诊断ZIP压缩包"""
    logger.info(f"正在分析 ZIP 文件: {zip_path}")
    
    if not os.path.exists(zip_path):
        logger.error(f"❌ 找不到 ZIP 文件: {zip_path}")
        return False
    
    # 解压到临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"解压到临时目录: {temp_dir}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 查找草稿文件夹（ZIP中可能直接是草稿内容，也可能包含草稿文件夹）
        items = os.listdir(temp_dir)
        
        if len(items) == 1 and os.path.isdir(os.path.join(temp_dir, items[0])):
            # ZIP包含单个文件夹
            draft_path = os.path.join(temp_dir, items[0])
        else:
            # ZIP直接包含草稿内容
            draft_path = temp_dir
        
        # 执行检查
        check_draft_structure(draft_path)
        path_types = analyze_draft_info(draft_path)
        meta_info = analyze_meta_info(draft_path)
        check_actual_materials(draft_path)
        generate_recommendations(path_types, meta_info)
    
    return True


def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  诊断本地草稿文件夹:")
        print("    python3.9 diagnose_draft_download.py <草稿ID>")
        print("  诊断ZIP文件:")
        print("    python3.9 diagnose_draft_download.py <ZIP文件路径>")
        print("\n示例:")
        print("    python3.9 diagnose_draft_download.py dfd_cat_1762313389_ae978ee4")
        print("    python3.9 diagnose_draft_download.py /path/to/draft.zip")
        sys.exit(1)
    
    target = sys.argv[1]
    
    print("=" * 80)
    print("  🔍 剪映草稿诊断工具")
    print("=" * 80)
    print(f"\n目标: {target}\n")
    
    # 判断是ZIP文件还是草稿ID
    if target.endswith('.zip'):
        success = diagnose_zip_file(target)
    else:
        success = diagnose_local_draft(target)
    
    if success:
        print("\n✅ 诊断完成！请查看上面的分析结果和建议。")
        print(f"\n详细日志已保存到: logs/draft_diagnose.log")
    else:
        print("\n❌ 诊断失败，请检查输入参数。")
        sys.exit(1)


if __name__ == '__main__':
    main()


