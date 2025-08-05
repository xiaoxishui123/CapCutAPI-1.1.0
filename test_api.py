#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCutAPI 服务完整测试脚本
用于验证部署的API服务是否正常工作，包括创建包含视频、音频、图片、文本的完整草稿
"""

import requests
import json
import sys
import time
import os

# 服务器地址
SERVER_URL = "http://8.148.70.18:9000"

# 测试资源URL
TEST_VIDEO_URL = "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"
TEST_AUDIO_URL = "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
TEST_IMAGE_URL = "https://picsum.photos/800/600"

# 草稿配置
DRAFT_ID = "complete_test_draft"
DRAFT_FOLDER = "F:\\jianyin\\cgwz\\JianyingPro Drafts"  # Windows剪映草稿目录

def make_request(endpoint, data=None, method="POST", timeout=30):
    """发送API请求"""
    url = f"{SERVER_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            print(f"❌ 不支持的HTTP方法: {method}")
            return None
            
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except json.JSONDecodeError:
                print(f"❌ {endpoint} - JSON解析错误")
                return None
        else:
            print(f"❌ {endpoint} - HTTP错误: {response.status_code}")
            try:
                error_detail = response.text
                print(f"   错误详情: {error_detail}")
            except:
                pass
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint} - 连接错误: {str(e)}")
        return None

def test_basic_endpoints():
    """测试基础API端点"""
    print("=== 1. 测试基础API端点 ===")
    
    endpoints = [
        "/get_intro_animation_types",
        "/get_outro_animation_types", 
        "/get_transition_types",
        "/get_mask_types",
        "/get_font_types"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        result = make_request(endpoint, method="GET")
        if result and result.get("success", False):
            print(f"✅ {endpoint} - 成功")
            success_count += 1
        else:
            print(f"❌ {endpoint} - 失败")
    
    print(f"   基础端点测试: {success_count}/{len(endpoints)} 成功")
    return success_count == len(endpoints)

def test_create_draft():
    """测试创建草稿"""
    print("\n=== 2. 创建草稿 ===")
    
    data = {
        "draft_id": DRAFT_ID,
        "width": 1080,
        "height": 1920
    }
    
    result = make_request("/create_draft", data)
    if result and result.get("success", False):
        print(f"✅ 草稿创建成功: {DRAFT_ID}")
        return True
    else:
        print(f"❌ 草稿创建失败")
        return False

def test_add_video():
    """测试添加视频"""
    print("\n=== 3. 添加视频素材 ===")
    
    data = {
        "draft_id": DRAFT_ID,
        "video_url": TEST_VIDEO_URL,
        "start": 0,
        "end": 10,
        "track_name": "main_video"
    }
    
    result = make_request("/add_video", data)
    if result and result.get("success", False):
        print(f"✅ 视频添加成功")
        return True
    else:
        print(f"❌ 视频添加失败")
        return False

def test_add_audio():
    """测试添加音频"""
    print("\n=== 4. 添加音频素材 ===")
    
    data = {
        "draft_id": DRAFT_ID,
        "audio_url": TEST_AUDIO_URL,
        "start": 0,
        "end": 8,
        "target_start": 2,
        "volume": 0.8,
        "track_name": "background_audio"
    }
    
    result = make_request("/add_audio", data)
    if result and result.get("success", False):
        print(f"✅ 音频添加成功")
        return True
    else:
        print(f"❌ 音频添加失败")
        return False

def test_add_image():
    """测试添加图片"""
    print("\n=== 5. 添加图片素材 ===")
    
    data = {
        "draft_id": DRAFT_ID,
        "image_url": TEST_IMAGE_URL,
        "width": 800,
        "height": 600,
        "start": 5,
        "end": 8,
        "track_name": "overlay_image"
    }
    
    result = make_request("/add_image", data)
    if result and result.get("success", False):
        print(f"✅ 图片添加成功")
        return True
    else:
        print(f"❌ 图片添加失败")
        return False

def test_add_text():
    """测试添加文本"""
    print("\n=== 6. 添加文本素材 ===")
    
    data = {
        "draft_id": DRAFT_ID,
        "text": "CapCutAPI 测试标题",
        "start": 1,
        "end": 9,
        "font": "ZY_Courage",
        "font_color": "#ffffff",
        "font_size": 8.0,
        "track_name": "main_title"
    }
    
    result = make_request("/add_text", data)
    if result and result.get("success", False):
        print(f"✅ 文本添加成功")
        return True
    else:
        print(f"❌ 文本添加失败")
        return False

def test_save_draft():
    """测试保存草稿"""
    print("\n=== 7. 保存草稿 ===")
    
    data = {
        "draft_id": DRAFT_ID,
        "draft_folder": DRAFT_FOLDER
    }
    
    print("   正在保存草稿，请等待...")
    result = make_request("/save_draft", data, timeout=120)  # 增加超时时间
    
    if result and result.get("success", False):
        task_id = result.get("task_id")
        print(f"✅ 草稿保存任务启动成功，任务ID: {task_id}")
        
        if task_id:
            return test_draft_status(task_id)
        return True
    else:
        print(f"❌ 草稿保存失败")
        return False

def test_draft_status(task_id):
    """测试草稿状态查询"""
    print(f"\n=== 8. 查询保存状态 ===")
    
    max_attempts = 30  # 最多等待5分钟
    for attempt in range(max_attempts):
        data = {"task_id": task_id}
        result = make_request("/query_draft_status", data)
        
        if result and result.get("success", False):
            status = result.get("status")
            message = result.get("message", "")
            progress = result.get("progress", 0)
            
            print(f"   状态: {status}, 进度: {progress}%, 消息: {message}")
            
            if status == "completed":
                print(f"✅ 草稿保存完成！")
                return True
            elif status == "failed":
                print(f"❌ 草稿保存失败: {message}")
                return False
            
            time.sleep(10)  # 等待10秒后再次查询
        else:
            print(f"❌ 状态查询失败")
            return False
    
    print(f"❌ 草稿保存超时")
    return False

def verify_draft_files():
    """验证草稿文件"""
    print(f"\n=== 9. 验证草稿文件 ===")
    
    draft_path = os.path.join(DRAFT_FOLDER, DRAFT_ID)
    draft_info_path = os.path.join(draft_path, "draft_info.json")
    assets_path = os.path.join(draft_path, "assets")
    
    checks = []
    
    # 检查草稿目录
    if os.path.exists(draft_path):
        print(f"✅ 草稿目录存在: {draft_path}")
        checks.append(True)
    else:
        print(f"❌ 草稿目录不存在: {draft_path}")
        checks.append(False)
    
    # 检查draft_info.json
    if os.path.exists(draft_info_path):
        print(f"✅ draft_info.json存在")
        try:
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_info = json.load(f)
                materials = draft_info.get("materials", {})
                print(f"   - 包含 {len(materials)} 个素材")
                checks.append(True)
        except Exception as e:
            print(f"❌ draft_info.json读取失败: {e}")
            checks.append(False)
    else:
        print(f"❌ draft_info.json不存在")
        checks.append(False)
    
    # 检查assets目录
    if os.path.exists(assets_path):
        print(f"✅ assets目录存在")
        try:
            asset_files = []
            for root, dirs, files in os.walk(assets_path):
                asset_files.extend(files)
            print(f"   - 包含 {len(asset_files)} 个素材文件")
            checks.append(True)
        except Exception as e:
            print(f"❌ assets目录读取失败: {e}")
            checks.append(False)
    else:
        print(f"❌ assets目录不存在")
        checks.append(False)
    
    return all(checks)

def main():
    """主测试函数"""
    print("🚀 CapCutAPI 完整功能测试")
    print(f"服务器地址: {SERVER_URL}")
    print(f"测试草稿ID: {DRAFT_ID}")
    print(f"草稿保存路径: {DRAFT_FOLDER}")
    print("=" * 50)
    
    # 执行所有测试
    test_results = []
    
    test_results.append(("基础API端点", test_basic_endpoints()))
    test_results.append(("创建草稿", test_create_draft()))
    test_results.append(("添加视频", test_add_video()))
    test_results.append(("添加音频", test_add_audio()))
    test_results.append(("添加图片", test_add_image()))
    test_results.append(("添加文本", test_add_text()))
    test_results.append(("保存草稿", test_save_draft()))
    test_results.append(("验证文件", verify_draft_files()))
    
    # 统计结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    success_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<15} {status}")
        if result:
            success_count += 1
    
    total_tests = len(test_results)
    success_rate = (success_count / total_tests) * 100
    
    print("=" * 50)
    print(f"总测试数: {total_tests}")
    print(f"成功数: {success_count}")
    print(f"失败数: {total_tests - success_count}")
    print(f"成功率: {success_rate:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 所有测试通过！CapCutAPI服务运行完全正常！")
        print(f"📁 完整草稿已保存至: {os.path.join(DRAFT_FOLDER, DRAFT_ID)}")
        print("💡 您可以将草稿下载到Windows并用剪映打开查看效果")
        return 0
    else:
        print(f"\n⚠️  {total_tests - success_count} 个测试失败，请检查服务配置")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 