#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映草稿路径修复工具
解决剪映客户端无法识别音频文件的问题

问题原因：
1. draft_meta_info.json中的路径配置使用固定的macOS模板路径
2. 剪映客户端根据这些路径来定位草稿和素材文件
3. 路径不匹配导致音频文件无法被识别

解决方案：
动态更新draft_meta_info.json中的draft_fold_path和draft_root_path
使其与用户实际的下载路径匹配
"""

import os
import json
import logging
from typing import Optional
from os_path_config import get_os_path_config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_draft_meta_paths(draft_path: str, target_draft_folder: str, client_os: str = "windows") -> bool:
    """
    更新草稿元数据文件中的路径配置
    
    Args:
        draft_path (str): 草稿文件夹的完整路径
        target_draft_folder (str): 目标草稿根目录路径
        client_os (str): 客户端操作系统类型
    
    Returns:
        bool: 更新是否成功
    """
    try:
        # 构建draft_meta_info.json文件路径
        meta_info_path = os.path.join(draft_path, "draft_meta_info.json")
        
        if not os.path.exists(meta_info_path):
            logger.error(f"draft_meta_info.json文件不存在: {meta_info_path}")
            return False
        
        # 读取现有的元数据
        with open(meta_info_path, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
        
        # 获取草稿文件夹名称
        draft_folder_name = os.path.basename(draft_path)
        
        # 根据客户端操作系统设置路径格式
        if client_os.lower() == "windows":
            # Windows路径格式
            draft_root_path = target_draft_folder.replace('/', '\\')
            draft_fold_path = os.path.join(draft_root_path, draft_folder_name).replace('/', '\\')
        else:
            # Unix/Linux/macOS路径格式
            draft_root_path = target_draft_folder.replace('\\', '/')
            draft_fold_path = os.path.join(draft_root_path, draft_folder_name).replace('\\', '/')
        
        # 更新路径配置
        meta_data["draft_root_path"] = draft_root_path
        meta_data["draft_fold_path"] = draft_fold_path
        meta_data["draft_name"] = draft_folder_name
        
        # 写回文件
        with open(meta_info_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, separators=(',', ':'))
        
        logger.info(f"成功更新草稿元数据路径:")
        logger.info(f"  draft_root_path: {draft_root_path}")
        logger.info(f"  draft_fold_path: {draft_fold_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"更新草稿元数据路径失败: {e}")
        return False

def fix_audio_paths_in_draft_info(draft_path: str) -> bool:
    """
    修复draft_info.json中音频文件的路径配置
    移除replace_path字段，让音频文件使用相对路径模式
    
    Args:
        draft_path (str): 草稿文件夹的完整路径
    
    Returns:
        bool: 修复是否成功
    """
    try:
        # 构建draft_info.json文件路径
        draft_info_path = os.path.join(draft_path, "draft_info.json")
        
        if not os.path.exists(draft_info_path):
            logger.error(f"draft_info.json文件不存在: {draft_info_path}")
            return False
        
        # 读取草稿信息
        with open(draft_info_path, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        # 检查并修复音频素材路径
        materials = draft_data.get('materials', {})
        audios = materials.get('audios', [])
        
        fixed_count = 0
        for audio in audios:
            # 移除replace_path字段，让音频使用相对路径模式
            if 'replace_path' in audio:
                del audio['replace_path']
                fixed_count += 1
                logger.info(f"移除音频素材的replace_path字段: {audio.get('path', 'unknown')}")
        
        if fixed_count > 0:
            # 写回文件
            with open(draft_info_path, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"成功修复 {fixed_count} 个音频素材的路径配置")
        else:
            logger.info("未发现需要修复的音频路径配置")
        
        return True
        
    except Exception as e:
        logger.error(f"修复音频路径配置失败: {e}")
        return False

def get_target_draft_folder(client_os: str = "windows") -> str:
    """
    获取目标草稿文件夹路径
    
    Args:
        client_os (str): 客户端操作系统类型
    
    Returns:
        str: 目标草稿文件夹路径
    """
    # 优先读取用户自定义路径配置
    try:
        config_file = 'path_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                custom_path = config.get('custom_download_path', '')
                if custom_path:
                    logger.info(f"使用用户自定义路径: {custom_path}")
                    return custom_path
    except Exception as e:
        logger.warning(f"读取自定义路径配置失败: {e}")
    
    # 使用操作系统默认路径
    try:
        os_config = get_os_path_config()
        default_path = os_config.get_default_draft_path(client_os.lower())
        logger.info(f"使用{client_os}默认路径: {default_path}")
        return default_path
    except Exception as e:
        logger.error(f"获取默认路径失败: {e}")
        # 兜底路径
        if client_os.lower() == "windows":
            return "C:\\Users\\Public\\Documents\\JianyingPro Drafts"
        else:
            return "/tmp/JianyingPro Drafts"

def fix_draft_paths(draft_path: str, client_os: str = "windows") -> bool:
    """
    修复草稿路径配置的主函数
    
    Args:
        draft_path (str): 草稿文件夹的完整路径
        client_os (str): 客户端操作系统类型
    
    Returns:
        bool: 修复是否成功
    """
    logger.info(f"开始修复草稿路径配置: {draft_path}")
    
    # 获取目标草稿文件夹路径
    target_draft_folder = get_target_draft_folder(client_os)
    
    # 更新draft_meta_info.json中的路径
    meta_success = update_draft_meta_paths(draft_path, target_draft_folder, client_os)
    
    # 修复draft_info.json中的音频路径
    audio_success = fix_audio_paths_in_draft_info(draft_path)
    
    success = meta_success and audio_success
    
    if success:
        logger.info(f"草稿路径配置修复完成: {draft_path}")
    else:
        logger.error(f"草稿路径配置修复失败: {draft_path}")
    
    return success

def batch_fix_drafts(drafts_directory: str, client_os: str = "windows") -> int:
    """
    批量修复指定目录下所有草稿的路径配置
    
    Args:
        drafts_directory (str): 包含草稿文件夹的目录
        client_os (str): 客户端操作系统类型
    
    Returns:
        int: 成功修复的草稿数量
    """
    if not os.path.exists(drafts_directory):
        logger.error(f"草稿目录不存在: {drafts_directory}")
        return 0
    
    fixed_count = 0
    
    for item in os.listdir(drafts_directory):
        item_path = os.path.join(drafts_directory, item)
        
        # 检查是否为草稿文件夹（包含draft_info.json和draft_meta_info.json）
        if (os.path.isdir(item_path) and 
            os.path.exists(os.path.join(item_path, "draft_info.json")) and
            os.path.exists(os.path.join(item_path, "draft_meta_info.json"))):
            
            logger.info(f"发现草稿文件夹: {item}")
            
            if fix_draft_paths(item_path, client_os):
                fixed_count += 1
                logger.info(f"✅ 修复成功: {item}")
            else:
                logger.error(f"❌ 修复失败: {item}")
    
    logger.info(f"批量修复完成，成功修复 {fixed_count} 个草稿")
    return fixed_count

if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  修复单个草稿: python fix_draft_paths.py <草稿路径> [客户端OS]")
        print("  批量修复: python fix_draft_paths.py --batch <草稿目录> [客户端OS]")
        print("")
        print("客户端OS选项: windows, macos, linux (默认: windows)")
        sys.exit(1)
    
    client_os = sys.argv[3] if len(sys.argv) > 3 else "windows"
    
    if sys.argv[1] == "--batch":
        # 批量修复模式
        drafts_dir = sys.argv[2]
        fixed_count = batch_fix_drafts(drafts_dir, client_os)
        print(f"批量修复完成，成功修复 {fixed_count} 个草稿")
    else:
        # 单个草稿修复模式
        draft_path = sys.argv[1]
        if fix_draft_paths(draft_path, client_os):
            print(f"草稿路径修复成功: {draft_path}")
        else:
            print(f"草稿路径修复失败: {draft_path}")