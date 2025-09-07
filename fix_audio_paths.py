#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复剪映草稿中音频文件路径问题的脚本
解决剪映客户端无法识别音频文件的问题

问题原因：
音频文件在 draft_info.json 中的 path 字段使用了错误的 Linux 绝对路径，
剪映客户端在 Windows 上无法根据这个路径找到实际的音频文件。

解决方案：
将音频材料的 path 字段从错误的 Linux 路径改为正确的 Windows 路径。
"""

import os
import json
import logging
import sys
from typing import List, Dict, Any
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_audio_paths.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_correct_audio_path(old_path: str, draft_folder_path: str) -> str:
    """
    根据错误的音频路径生成正确的 Windows 路径
    
    Args:
        old_path (str): 错误的音频路径 (如: /tmp/capcut_temp_drafts/dfd_cat_xxx/assets/audio/xxx.mp3)
        draft_folder_path (str): 草稿文件夹的绝对路径
    
    Returns:
        str: 正确的 Windows 路径
    """
    try:
        # 提取文件名部分 (assets/audio/xxx.mp3)
        if "/assets/audio/" in old_path:
            audio_filename = old_path.split("/assets/audio/")[-1]
            # 构建正确的 Windows 路径
            correct_path = os.path.join(draft_folder_path, "assets", "audio", audio_filename)
            return correct_path.replace('/', '\\')
        else:
            logger.warning(f"无法解析音频路径: {old_path}")
            return old_path
    except Exception as e:
        logger.error(f"生成正确音频路径失败: {e}")
        return old_path

def fix_audio_paths_in_draft(draft_folder_path: str) -> bool:
    """
    修复单个草稿中的音频路径问题
    
    Args:
        draft_folder_path (str): 草稿文件夹的绝对路径
    
    Returns:
        bool: 修复是否成功
    """
    logger.info(f"开始修复草稿音频路径: {draft_folder_path}")
    
    # 检查草稿文件夹是否存在
    if not os.path.exists(draft_folder_path):
        logger.error(f"草稿文件夹不存在: {draft_folder_path}")
        return False
    
    # 构建 draft_info.json 文件路径
    draft_info_path = os.path.join(draft_folder_path, "draft_info.json")
    
    if not os.path.exists(draft_info_path):
        logger.error(f"draft_info.json 文件不存在: {draft_info_path}")
        return False
    
    try:
        # 备份原文件
        backup_path = draft_info_path + ".backup"
        shutil.copy2(draft_info_path, backup_path)
        logger.info(f"已创建备份文件: {backup_path}")
        
        # 读取草稿信息
        with open(draft_info_path, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        # 检查并修复音频素材路径
        materials = draft_data.get('materials', {})
        audios = materials.get('audios', [])
        
        fixed_count = 0
        for audio in audios:
            old_path = audio.get('path', '')
            
            # 检查是否是需要修复的错误路径
            if old_path.startswith('/tmp/capcut_temp_drafts/'):
                # 生成正确的 Windows 路径
                correct_path = get_correct_audio_path(old_path, draft_folder_path)
                
                # 检查目标音频文件是否存在
                # 在Linux服务器上，实际的文件路径是draft_folder_path的原始形式
                audio_filename = old_path.split("/assets/audio/")[-1]
                actual_file_path = os.path.join(draft_folder_path, "assets", "audio", audio_filename)
                
                if os.path.exists(actual_file_path):
                    # 更新路径为正确的Windows格式
                    audio['path'] = correct_path
                    fixed_count += 1
                    logger.info(f"✅ 修复音频路径:")
                    logger.info(f"   原路径: {old_path}")
                    logger.info(f"   新路径: {correct_path}")
                    logger.info(f"   实际文件: {actual_file_path}")
                else:
                    logger.warning(f"⚠️  音频文件不存在，跳过修复:")
                    logger.warning(f"   预期文件: {actual_file_path}")
                    logger.warning(f"   目标路径: {correct_path}")
            elif '/tmp/' in old_path or old_path.startswith('/'):
                # 其他 Linux 路径也尝试修复
                correct_path = get_correct_audio_path(old_path, draft_folder_path)
                if os.path.exists(correct_path):
                    audio['path'] = correct_path
                    fixed_count += 1
                    logger.info(f"✅ 修复Linux路径:")
                    logger.info(f"   原路径: {old_path}")
                    logger.info(f"   新路径: {correct_path}")
        
        if fixed_count > 0:
            # 写回文件
            with open(draft_info_path, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 成功修复 {fixed_count} 个音频文件的路径配置")
            return True
        else:
            logger.info("未发现需要修复的音频路径配置")
            # 删除不必要的备份文件
            if os.path.exists(backup_path):
                os.remove(backup_path)
            return True
        
    except Exception as e:
        logger.error(f"修复音频路径配置失败: {e}")
        return False

def batch_fix_audio_paths(directory: str) -> int:
    """
    批量修复指定目录下所有草稿的音频路径问题
    
    Args:
        directory (str): 包含草稿文件夹的目录
    
    Returns:
        int: 成功修复的草稿数量
    """
    if not os.path.exists(directory):
        logger.error(f"目录不存在: {directory}")
        return 0
    
    fixed_count = 0
    total_count = 0
    
    # 遍历目录中的所有子文件夹
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        
        # 检查是否为草稿文件夹（包含 draft_info.json）
        if (os.path.isdir(item_path) and 
            os.path.exists(os.path.join(item_path, "draft_info.json"))):
            
            total_count += 1
            logger.info(f"发现草稿文件夹: {item}")
            
            if fix_audio_paths_in_draft(item_path):
                fixed_count += 1
                logger.info(f"✅ 修复成功: {item}")
            else:
                logger.error(f"❌ 修复失败: {item}")
    
    logger.info(f"批量修复完成，处理 {total_count} 个草稿，成功修复 {fixed_count} 个")
    return fixed_count

def verify_audio_paths(draft_folder_path: str) -> bool:
    """
    验证草稿中的音频路径是否正确
    
    Args:
        draft_folder_path (str): 草稿文件夹的绝对路径
    
    Returns:
        bool: 所有音频路径是否都正确
    """
    draft_info_path = os.path.join(draft_folder_path, "draft_info.json")
    
    if not os.path.exists(draft_info_path):
        logger.error(f"draft_info.json 文件不存在: {draft_info_path}")
        return False
    
    try:
        with open(draft_info_path, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        materials = draft_data.get('materials', {})
        audios = materials.get('audios', [])
        
        all_correct = True
        for i, audio in enumerate(audios):
            audio_path = audio.get('path', '')
            audio_name = audio.get('name', f'audio_{i+1}')
            
            if os.path.exists(audio_path):
                logger.info(f"✅ 音频文件路径正确: {audio_name}")
                logger.info(f"   路径: {audio_path}")
            else:
                logger.error(f"❌ 音频文件路径错误: {audio_name}")
                logger.error(f"   路径: {audio_path}")
                all_correct = False
        
        return all_correct
        
    except Exception as e:
        logger.error(f"验证音频路径失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始修复音频文件路径问题")
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  修复单个草稿: python fix_audio_paths.py <草稿路径>")
        print("  批量修复: python fix_audio_paths.py --batch <目录路径>")
        print("  验证路径: python fix_audio_paths.py --verify <草稿路径>")
        print("")
        print("示例:")
        print("  python fix_audio_paths.py './dfd_cat_1757225762_d7fd0202'")
        print("  python fix_audio_paths.py --batch './F:\\jianyin\\cgwz\\JianyingPro Drafts'")
        print("  python fix_audio_paths.py --verify './dfd_cat_1757225762_d7fd0202'")
        return False
    
    if sys.argv[1] == "--batch":
        # 批量修复模式
        if len(sys.argv) < 3:
            print("请指定目录路径")
            return False
        
        directory = sys.argv[2]
        fixed_count = batch_fix_audio_paths(directory)
        print(f"批量修复完成，成功修复 {fixed_count} 个草稿")
        return fixed_count > 0
    
    elif sys.argv[1] == "--verify":
        # 验证模式
        if len(sys.argv) < 3:
            print("请指定草稿路径")
            return False
        
        draft_path = sys.argv[2]
        success = verify_audio_paths(draft_path)
        if success:
            print(f"✅ 音频路径验证通过: {draft_path}")
        else:
            print(f"❌ 音频路径验证失败: {draft_path}")
        return success
    
    else:
        # 单个草稿修复模式
        draft_path = sys.argv[1]
        success = fix_audio_paths_in_draft(draft_path)
        if success:
            print(f"✅ 音频路径修复成功: {draft_path}")
            # 验证修复结果
            if verify_audio_paths(draft_path):
                print("✅ 修复验证通过，音频文件应该可以被剪映识别")
            else:
                print("⚠️  修复验证失败，请检查音频文件是否存在")
        else:
            print(f"❌ 音频路径修复失败: {draft_path}")
        return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
