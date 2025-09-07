#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复音频文件识别问题的脚本
解决剪映客户端无法识别音频文件的问题
"""

import os
import json
import logging
import sys
from typing import List, Tuple
from fix_draft_paths import fix_draft_paths, batch_fix_drafts
from os_path_config import get_os_path_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_audio_issues.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_and_fix_single_draft(draft_path: str, client_os: str = "windows") -> bool:
    """
    检查并修复单个草稿的音频识别问题
    
    Args:
        draft_path (str): 草稿文件夹路径
        client_os (str): 客户端操作系统类型
    
    Returns:
        bool: 修复是否成功
    """
    logger.info(f"开始检查和修复草稿: {draft_path}")
    
    # 检查草稿文件夹是否存在
    if not os.path.exists(draft_path):
        logger.error(f"草稿文件夹不存在: {draft_path}")
        return False
    
    # 检查必要的文件是否存在
    draft_info_path = os.path.join(draft_path, "draft_info.json")
    draft_meta_path = os.path.join(draft_path, "draft_meta_info.json")
    
    if not os.path.exists(draft_info_path):
        logger.error(f"draft_info.json 文件不存在: {draft_info_path}")
        return False
    
    if not os.path.exists(draft_meta_path):
        logger.error(f"draft_meta_info.json 文件不存在: {draft_meta_path}")
        return False
    
    # 修复路径配置
    success = fix_draft_paths(draft_path, client_os)
    
    if success:
        logger.info(f"✅ 草稿修复成功: {draft_path}")
    else:
        logger.error(f"❌ 草稿修复失败: {draft_path}")
    
    return success

def check_and_fix_batch_drafts(drafts_directory: str, client_os: str = "windows") -> int:
    """
    批量检查和修复草稿的音频识别问题
    
    Args:
        drafts_directory (str): 包含草稿文件夹的目录
        client_os (str): 客户端操作系统类型
    
    Returns:
        int: 成功修复的草稿数量
    """
    logger.info(f"开始批量检查和修复草稿目录: {drafts_directory}")
    
    return batch_fix_drafts(drafts_directory, client_os)

def verify_custom_path_config() -> bool:
    """
    验证自定义路径配置是否正确
    
    Returns:
        bool: 配置是否正确
    """
    logger.info("开始验证自定义路径配置")
    
    # 检查 path_config.json 文件
    config_file = 'path_config.json'
    if not os.path.exists(config_file):
        logger.warning(f"配置文件不存在: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        custom_path = config.get('custom_download_path', '')
        if not custom_path:
            logger.warning("自定义下载路径未设置")
            return False
        
        logger.info(f"当前自定义下载路径: {custom_path}")
        
        # 验证路径格式（Windows路径应该包含盘符）
        if ':' not in custom_path or len(custom_path) < 3:
            logger.warning("自定义下载路径格式不正确，应该为Windows格式（如 F:\\jianyin\\cgwz\\JianyingPro Drafts）")
            return False
        
        # 检查路径是否存在
        if not os.path.exists(custom_path):
            logger.warning(f"自定义下载路径不存在: {custom_path}")
            # 尝试创建路径
            try:
                os.makedirs(custom_path, exist_ok=True)
                logger.info(f"已创建自定义下载路径: {custom_path}")
            except Exception as e:
                logger.error(f"创建自定义下载路径失败: {e}")
                return False
        
        logger.info("✅ 自定义路径配置验证通过")
        return True
        
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        return False

def verify_system_config() -> bool:
    """
    验证系统配置是否正确
    
    Returns:
        bool: 配置是否正确
    """
    logger.info("开始验证系统配置")
    
    try:
        # 检查 config.json 文件
        config_file = 'config.json'
        if not os.path.exists(config_file):
            logger.error(f"系统配置文件不存在: {config_file}")
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查 draft_paths 配置
        draft_paths = config.get('draft_paths', {})
        if not draft_paths:
            logger.warning("draft_paths 配置缺失")
            return False
        
        # 检查 Windows 路径配置
        windows_path = draft_paths.get('windows', '')
        if not windows_path:
            logger.warning("Windows 草稿路径配置缺失")
            return False
        
        logger.info(f"系统 Windows 草稿路径配置: {windows_path}")
        
        # 验证路径格式
        if ':' not in windows_path or len(windows_path) < 3:
            logger.warning("Windows 草稿路径格式不正确")
            return False
        
        logger.info("✅ 系统配置验证通过")
        return True
        
    except Exception as e:
        logger.error(f"验证系统配置失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始修复音频文件识别问题")
    
    # 1. 验证配置
    config_ok = verify_custom_path_config() and verify_system_config()
    if not config_ok:
        logger.error("配置验证失败，请检查配置文件")
        return False
    
    # 2. 获取参数
    if len(sys.argv) < 2:
        print("用法:")
        print("  修复单个草稿: python fix_audio_recognition_issues.py <草稿路径> [客户端OS]")
        print("  批量修复: python fix_audio_recognition_issues.py --batch <草稿目录> [客户端OS]")
        print("  验证配置: python fix_audio_recognition_issues.py --check")
        print("")
        print("客户端OS选项: windows, macos, linux (默认: windows)")
        return False
    
    client_os = sys.argv[3] if len(sys.argv) > 3 else "windows"
    
    # 3. 根据参数执行相应操作
    if sys.argv[1] == "--check":
        # 配置检查模式
        custom_ok = verify_custom_path_config()
        system_ok = verify_system_config()
        if custom_ok and system_ok:
            print("✅ 所有配置检查通过")
            return True
        else:
            print("❌ 配置检查失败")
            return False
    
    elif sys.argv[1] == "--batch":
        # 批量修复模式
        if len(sys.argv) < 3:
            print("请指定草稿目录")
            return False
        
        drafts_dir = sys.argv[2]
        fixed_count = check_and_fix_batch_drafts(drafts_dir, client_os)
        print(f"批量修复完成，成功修复 {fixed_count} 个草稿")
        return fixed_count > 0
    
    else:
        # 单个草稿修复模式
        draft_path = sys.argv[1]
        success = check_and_fix_single_draft(draft_path, client_os)
        if success:
            print(f"✅ 草稿修复成功: {draft_path}")
            return True
        else:
            print(f"❌ 草稿修复失败: {draft_path}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)