#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试草稿路径修复功能
验证修复方案是否能解决剪映无法识别音频文件的问题
"""

import os
import json
import logging
import tempfile
import shutil
from fix_draft_paths import fix_draft_paths, batch_fix_drafts
from pyJianYingDraft.draft_folder import Draft_folder

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_draft_with_audio():
    """
    创建一个包含音频文件的测试草稿
    模拟实际的草稿结构和路径问题
    """
    # 创建临时目录作为测试草稿
    test_draft_dir = tempfile.mkdtemp(prefix="test_draft_")
    logger.info(f"创建测试草稿目录: {test_draft_dir}")
    
    # 创建draft_meta_info.json（包含错误的macOS路径）
    meta_info = {
        "draft_cover": "",
        "draft_fold_path": "/Users/sunguannan/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/5月16日",
        "draft_id": "test_draft_123",
        "draft_name": "test_draft",
        "draft_removable": True,
        "draft_root_path": "/Users/sunguannan/Movies/JianyingPro/User Data/Projects/com.lveditor.draft",
        "tm_draft_create": 1715875200000000,
        "tm_draft_modified": 1715875200000000
    }
    
    with open(os.path.join(test_draft_dir, "draft_meta_info.json"), 'w', encoding='utf-8') as f:
        json.dump(meta_info, f, ensure_ascii=False, separators=(',', ':'))
    
    # 创建draft_info.json（包含音频素材和replace_path字段）
    draft_info = {
        "fps": 30,
        "duration": 30000000,  # 30秒，单位为微秒
        "canvas_config": {
            "width": 1920,
            "height": 1080,
            "ratio": "original"
        },
        "materials": {
            "audios": [
                {
                    "id": "audio_001",
                    "path": "audio/test_audio.mp3",
                    "replace_path": "/home/linux_server/audio/test_audio.mp3",
                    "duration": 30000000,
                    "type": "audio"
                }
            ],
            "images": [
                {
                    "id": "image_001",
                    "path": "images/test_image.jpg",
                    "duration": 5000000,
                    "type": "image"
                }
            ],
            "videos": [],
            "texts": [],
            "stickers": [],
            "effects": [],
            "transitions": [],
            "filters": [],
            "sounds": [],
            "chromas": [],
            "adjusts": [],
            "speed": [],
            "volume": [],
            "template": [],
            "handwrites": [],
            "speech_to_songs": [],
            "beats": [],
            "color_curves": [],
            "hsl": [],
            "masks": [],
            "canvases": []
        },
        "tracks": [],
        "version": "1.0",
        "platform": "windows",
        "resolution": {
            "width": 1920,
            "height": 1080
        }
    }
    
    with open(os.path.join(test_draft_dir, "draft_info.json"), 'w', encoding='utf-8') as f:
        json.dump(draft_info, f, ensure_ascii=False, indent=2)
    
    # 创建素材文件夹和文件
    audio_dir = os.path.join(test_draft_dir, "audio")
    images_dir = os.path.join(test_draft_dir, "images")
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    
    # 创建测试音频文件（空文件）
    with open(os.path.join(audio_dir, "test_audio.mp3"), 'w') as f:
        f.write("# 测试音频文件")
    
    # 创建测试图片文件（空文件）
    with open(os.path.join(images_dir, "test_image.jpg"), 'w') as f:
        f.write("# 测试图片文件")
    
    return test_draft_dir

def verify_draft_paths(draft_path: str, expected_target_path: str) -> bool:
    """
    验证草稿路径是否已正确修复
    
    Args:
        draft_path (str): 草稿文件夹路径
        expected_target_path (str): 期望的目标路径
    
    Returns:
        bool: 验证是否通过
    """
    try:
        # 检查draft_meta_info.json
        meta_info_path = os.path.join(draft_path, "draft_meta_info.json")
        with open(meta_info_path, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
        
        draft_folder_name = os.path.basename(draft_path)
        expected_draft_fold_path = os.path.join(expected_target_path, draft_folder_name).replace('/', '\\')
        expected_draft_root_path = expected_target_path.replace('/', '\\')
        
        # 验证路径是否已更新
        actual_draft_fold_path = meta_data.get("draft_fold_path", "")
        actual_draft_root_path = meta_data.get("draft_root_path", "")
        
        logger.info(f"期望的draft_fold_path: {expected_draft_fold_path}")
        logger.info(f"实际的draft_fold_path: {actual_draft_fold_path}")
        logger.info(f"期望的draft_root_path: {expected_draft_root_path}")
        logger.info(f"实际的draft_root_path: {actual_draft_root_path}")
        
        paths_correct = (actual_draft_fold_path == expected_draft_fold_path and 
                        actual_draft_root_path == expected_draft_root_path)
        
        # 检查draft_info.json中的音频路径
        draft_info_path = os.path.join(draft_path, "draft_info.json")
        with open(draft_info_path, 'r', encoding='utf-8') as f:
            draft_data = json.load(f)
        
        audios = draft_data.get('materials', {}).get('audios', [])
        audio_paths_fixed = True
        
        for audio in audios:
            if 'replace_path' in audio:
                logger.warning(f"音频素材仍包含replace_path字段: {audio}")
                audio_paths_fixed = False
            else:
                logger.info(f"音频素材已移除replace_path字段: {audio.get('path', 'unknown')}")
        
        return paths_correct and audio_paths_fixed
        
    except Exception as e:
        logger.error(f"验证草稿路径时发生错误: {e}")
        return False

def test_single_draft_fix():
    """
    测试单个草稿的路径修复功能
    """
    logger.info("=== 测试单个草稿路径修复 ===")
    
    # 创建测试草稿
    test_draft_path = create_test_draft_with_audio()
    
    try:
        # 设置目标路径
        target_path = "C:\\Users\\Public\\Documents\\JianyingPro Drafts"
        
        # 临时修改fix_draft_paths模块中的get_target_draft_folder函数
        import fix_draft_paths
        original_get_target = fix_draft_paths.get_target_draft_folder
        fix_draft_paths.get_target_draft_folder = lambda client_os: target_path
        
        try:
            # 执行路径修复
            logger.info(f"开始修复草稿路径: {test_draft_path}")
            success = fix_draft_paths.fix_draft_paths(test_draft_path, "windows")
        finally:
            # 恢复原函数
            fix_draft_paths.get_target_draft_folder = original_get_target
        
        if success:
            logger.info("✅ 路径修复成功")
            
            # 验证修复结果
            if verify_draft_paths(test_draft_path, target_path):
                logger.info("✅ 路径验证通过")
                return True
            else:
                logger.error("❌ 路径验证失败")
                return False
        else:
            logger.error("❌ 路径修复失败")
            return False
            
    finally:
        # 清理测试文件
        shutil.rmtree(test_draft_path)
        logger.info(f"清理测试文件: {test_draft_path}")

def test_batch_draft_fix():
    """
    测试批量草稿路径修复功能
    """
    logger.info("=== 测试批量草稿路径修复 ===")
    
    # 创建临时目录作为草稿根目录
    temp_drafts_dir = tempfile.mkdtemp(prefix="test_drafts_")
    logger.info(f"创建测试草稿根目录: {temp_drafts_dir}")
    
    try:
        # 创建多个测试草稿
        test_drafts = []
        for i in range(3):
            draft_path = create_test_draft_with_audio()
            draft_name = f"test_draft_{i+1}"
            new_draft_path = os.path.join(temp_drafts_dir, draft_name)
            shutil.move(draft_path, new_draft_path)
            test_drafts.append(new_draft_path)
            logger.info(f"创建测试草稿 {i+1}: {new_draft_path}")
        
        # 临时修改get_target_draft_folder函数
        import fix_draft_paths
        original_get_target = fix_draft_paths.get_target_draft_folder
        target_path = "C:\\Users\\Public\\Documents\\JianyingPro Drafts"
        fix_draft_paths.get_target_draft_folder = lambda client_os: target_path
        
        try:
            # 执行批量修复
            logger.info(f"开始批量修复草稿路径: {temp_drafts_dir}")
            fixed_count = batch_fix_drafts(temp_drafts_dir, "windows")
        finally:
            # 恢复原函数
            fix_draft_paths.get_target_draft_folder = original_get_target
        
        if fixed_count == len(test_drafts):
            logger.info(f"✅ 批量修复成功，修复了 {fixed_count} 个草稿")
            
            # 验证所有草稿的修复结果
            all_verified = True
            
            for draft_path in test_drafts:
                if not verify_draft_paths(draft_path, target_path):
                    all_verified = False
                    break
            
            if all_verified:
                logger.info("✅ 所有草稿路径验证通过")
                return True
            else:
                logger.error("❌ 部分草稿路径验证失败")
                return False
        else:
            logger.error(f"❌ 批量修复失败，期望修复 {len(test_drafts)} 个，实际修复 {fixed_count} 个")
            return False
            
    finally:
        # 清理测试文件
        shutil.rmtree(temp_drafts_dir)
        logger.info(f"清理测试文件: {temp_drafts_dir}")

def test_draft_folder_integration():
    """
    测试与Draft_folder类的集成
    验证duplicate_as_template方法是否自动修复路径
    """
    logger.info("=== 测试Draft_folder集成 ===")
    
    # 创建临时目录作为草稿根目录
    temp_drafts_dir = tempfile.mkdtemp(prefix="test_integration_")
    logger.info(f"创建测试集成目录: {temp_drafts_dir}")
    
    try:
        # 创建原始模板草稿
        template_path = create_test_draft_with_audio()
        template_name = "template_draft"
        template_draft_path = os.path.join(temp_drafts_dir, template_name)
        shutil.move(template_path, template_draft_path)
        logger.info(f"创建模板草稿: {template_draft_path}")
        
        # 临时修改get_target_draft_folder函数
        import fix_draft_paths
        original_get_target = fix_draft_paths.get_target_draft_folder
        target_path = "C:\\Users\\Public\\Documents\\JianyingPro Drafts"
        fix_draft_paths.get_target_draft_folder = lambda client_os: target_path
        
        try:
            # 使用Draft_folder进行复制
            draft_folder = Draft_folder(temp_drafts_dir)
            new_draft_name = "copied_draft"
            
            logger.info(f"使用Draft_folder复制草稿: {template_name} -> {new_draft_name}")
            script_file = draft_folder.duplicate_as_template(template_name, new_draft_name)
            
            # 验证复制后的草稿路径是否已自动修复
            new_draft_path = os.path.join(temp_drafts_dir, new_draft_name)
        finally:
            # 恢复原函数
            fix_draft_paths.get_target_draft_folder = original_get_target
        
        if verify_draft_paths(new_draft_path, target_path):
            logger.info("✅ Draft_folder集成测试通过，路径已自动修复")
            return True
        else:
            logger.error("❌ Draft_folder集成测试失败，路径未正确修复")
            return False
            
    finally:
        # 清理测试文件
        shutil.rmtree(temp_drafts_dir)
        logger.info(f"清理测试文件: {temp_drafts_dir}")

def main():
    """
    运行所有测试
    """
    logger.info("开始测试草稿路径修复功能")
    
    tests = [
        ("单个草稿修复测试", test_single_draft_fix),
        ("批量草稿修复测试", test_batch_draft_fix),
        ("Draft_folder集成测试", test_draft_folder_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"运行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_func():
                logger.info(f"✅ {test_name} 通过")
                passed += 1
            else:
                logger.error(f"❌ {test_name} 失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 发生异常: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"测试结果: {passed}/{total} 通过")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 所有测试通过！草稿路径修复功能正常工作")
        return True
    else:
        logger.error(f"⚠️  有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)