#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCutAPI 服务完整测试脚本
用于验证部署的API服务是否正常工作，包括创建包含视频、音频、图片、文本的完整草稿
支持本地保存和OSS云存储两种模式的测试
"""

import requests
import json
import sys
import time
import os
import argparse

# 服务器地址
SERVER_URL = "http://8.148.70.18:9000"

# 测试资源URL
TEST_VIDEO_URL = "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"
TEST_AUDIO_URL = "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
TEST_IMAGE_URL = "https://picsum.photos/800/600"

# 草稿配置
DRAFT_ID = "test_draft_" + str(int(time.time()))  # 使用时间戳确保唯一性
DRAFT_FOLDER = "F:\\jianyin\\cgwz\\JianyingPro Drafts"  # Windows剪映草稿目录

# 测试模式配置
TEST_MODE = "oss"  # 默认使用OSS模式，可选 "local" 或 "oss"

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_subsection(title):
    """打印子节标题"""
    print(f"\n--- {title} ---")

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
            
        print(f"🔍 [{endpoint}] 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except json.JSONDecodeError:
                print(f"❌ {endpoint} - JSON解析错误")
                print(f"   响应内容: {response.text[:500]}...")
                return None
        else:
            print(f"❌ {endpoint} - HTTP错误: {response.status_code}")
            try:
                error_detail = response.text
                print(f"   错误详情: {error_detail[:500]}...")
            except:
                pass
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint} - 连接错误: {str(e)}")
        return None

def test_server_config():
    """测试服务器配置"""
    print_section("🔧 服务器配置检查")
    
    try:
        resp = requests.get(f"{SERVER_URL}/", headers={"Accept": "application/json"}, timeout=30)
        print(f"🔍 [/] 状态码: {resp.status_code}")
        if resp.status_code != 200:
            print("❌ 服务器连接失败")
            try:
                print(f"   错误详情: {resp.text[:500]}...")
            except Exception:
                pass
            return False
        try:
            _ = resp.json()
        except json.JSONDecodeError:
            print("❌ / - JSON解析错误")
            print(f"   响应内容: {resp.text[:500]}...")
            return False
        print("✅ 服务器连接正常")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ / - 连接错误: {str(e)}")
        return False

def test_basic_endpoints():
    """测试基础API端点"""
    print_section("🔌 基础API端点测试")
    
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
    
    print(f"\n📊 基础端点测试: {success_count}/{len(endpoints)} 成功")
    return success_count == len(endpoints)

def test_create_draft():
    """测试创建草稿"""
    print_section("📝 创建草稿")
    
    data = {
        "draft_id": DRAFT_ID,
        "width": 1080,
        "height": 1920
    }
    
    result = make_request("/create_draft", data)
    if result and result.get("success", False):
        print(f"✅ 草稿创建成功")
        print(f"   草稿ID: {DRAFT_ID}")
        print(f"   尺寸: 1080x1920")
        return True
    else:
        print(f"❌ 草稿创建失败")
        return False

def test_add_video():
    """测试添加视频"""
    print_section("🎥 添加视频素材")
    
    data = {
        "draft_id": DRAFT_ID,
        "video_url": TEST_VIDEO_URL,
        "start": 0,
        "end": 8,
        "track_name": "main_video"
    }
    
    print(f"   视频URL: {TEST_VIDEO_URL}")
    print(f"   时长: 0-8秒")
    
    result = make_request("/add_video", data)
    if result and result.get("success", False):
        print(f"✅ 视频添加成功")
        return True
    else:
        print(f"❌ 视频添加失败")
        return False

def test_add_audio():
    """测试添加音频"""
    print_section("🎵 添加音频素材")
    
    data = {
        "draft_id": DRAFT_ID,
        "audio_url": TEST_AUDIO_URL,
        "start": 1,
        "end": 7,
        "target_start": 1,
        "volume": 0.8,
        "track_name": "background_audio"
    }
    
    print(f"   音频URL: {TEST_AUDIO_URL}")
    print(f"   时长: 1-7秒")
    print(f"   音量: 80%")
    
    result = make_request("/add_audio", data)
    if result and result.get("success", False):
        print(f"✅ 音频添加成功")
        return True
    else:
        print(f"❌ 音频添加失败")
        return False

def test_add_image():
    """测试添加图片"""
    print_section("🖼️ 添加图片素材")
    
    data = {
        "draft_id": DRAFT_ID,
        "image_url": TEST_IMAGE_URL,
        "width": 800,
        "height": 600,
        "start": 2,
        "end": 4,
        "track_name": "overlay_image"
    }
    
    print(f"   图片URL: {TEST_IMAGE_URL}")
    print(f"   尺寸: 800x600")
    print(f"   显示时间: 2-4秒")
    
    result = make_request("/add_image", data)
    if result and result.get("success", False):
        print(f"✅ 图片添加成功")
        return True
    else:
        print(f"❌ 图片添加失败")
        return False

def test_add_text():
    """测试添加文本"""
    print_section("📝 添加文本素材")
    
    data = {
        "draft_id": DRAFT_ID,
        "text": "CapCutAPI OSS测试标题 🚀",
        "start": 0.5,
        "end": 5.5,
        "font": "ZY_Courage",
        "font_color": "#ffffff",
        "font_size": 8.0,
        "track_name": "main_title"
    }
    
    print(f"   文本内容: {data['text']}")
    print(f"   字体: {data['font']}")
    print(f"   颜色: {data['font_color']}")
    print(f"   显示时间: 0.5-5.5秒")
    
    result = make_request("/add_text", data)
    if result and result.get("success", False):
        print(f"✅ 文本添加成功")
        return True
    else:
        print(f"❌ 文本添加失败")
        return False

def test_save_draft_oss():
    """测试OSS保存草稿"""
    print_section("☁️ 保存草稿到OSS云存储")
    
    data = {
        "draft_id": DRAFT_ID
        # OSS模式不需要指定draft_folder
    }
    
    print("   🔄 正在保存草稿到OSS，请等待...")
    print("   ⚡ OSS模式特点：")
    print("      - 自动压缩为zip格式")
    print("      - 上传到阿里云OSS")
    print("      - 返回可下载URL")
    print("      - 清理本地临时文件")
    
    result = make_request("/save_draft", data, timeout=180)  # OSS上传需要更长时间
    
    if result and result.get("success", False):
        task_id = result.get("task_id")
        print(f"✅ OSS保存任务启动成功")
        print(f"   任务ID: {task_id}")
        
        if task_id:
            return test_draft_status_oss(task_id)
        return True
    else:
        print(f"❌ OSS草稿保存失败")
        return False

def test_save_draft_local():
    """测试本地保存草稿"""
    print_section("💾 保存草稿到本地")
    
    data = {
        "draft_id": DRAFT_ID,
        "draft_folder": DRAFT_FOLDER
    }
    
    print(f"   📁 保存路径: {DRAFT_FOLDER}")
    print("   🔄 正在保存草稿到本地，请等待...")
    
    result = make_request("/save_draft", data, timeout=120)
    
    if result and result.get("success", False):
        task_id = result.get("task_id")
        print(f"✅ 本地保存任务启动成功")
        print(f"   任务ID: {task_id}")
        
        if task_id:
            return test_draft_status_local(task_id)
        return True
    else:
        print(f"❌ 本地草稿保存失败")
        return False

def test_draft_status_oss(task_id):
    """测试OSS草稿保存状态查询"""
    print_subsection("📊 OSS保存进度监控")
    
    max_attempts = 60  # 最多等待10分钟
    draft_url = None
    
    for attempt in range(max_attempts):
        data = {"task_id": task_id}
        result = make_request("/query_draft_status", data)
        
        if result and result.get("success", False):
            status = result.get("status")
            message = result.get("message", "")
            progress = result.get("progress", 0)
            current_draft_url = result.get("draft_url", "")
            
            # 使用进度条显示
            progress_bar = "█" * int(progress/5) + "░" * (20 - int(progress/5))
            print(f"   [{progress_bar}] {progress}% - {status}: {message}")
            
            if current_draft_url and not draft_url:
                draft_url = current_draft_url
                print(f"   🔗 OSS URL: {draft_url}")
            
            if status == "completed":
                print(f"\n✅ OSS保存完成！")
                print(f"   📦 草稿已压缩并上传到阿里云OSS")
                print(f"   🌐 下载链接: {draft_url}")
                print(f"   ⏰ 链接有效期: 24小时")
                print(f"   🧹 本地临时文件已清理")
                return True, draft_url
            elif status == "failed":
                print(f"\n❌ OSS保存失败: {message}")
                return False, None
            
            time.sleep(10)  # 等待10秒后再次查询
        else:
            print(f"❌ 状态查询失败 (尝试 {attempt+1}/{max_attempts})")
            time.sleep(5)
    
    print(f"\n❌ OSS保存超时")
    return False, None

def test_draft_status_local(task_id):
    """测试本地草稿保存状态查询"""
    print_subsection("📊 本地保存进度监控")
    
    max_attempts = 30  # 最多等待5分钟
    for attempt in range(max_attempts):
        data = {"task_id": task_id}
        result = make_request("/query_draft_status", data)
        
        if result and result.get("success", False):
            status = result.get("status")
            message = result.get("message", "")
            progress = result.get("progress", 0)
            
            # 使用进度条显示
            progress_bar = "█" * int(progress/5) + "░" * (20 - int(progress/5))
            print(f"   [{progress_bar}] {progress}% - {status}: {message}")
            
            if status == "completed":
                print(f"\n✅ 本地保存完成！")
                return True
            elif status == "failed":
                print(f"\n❌ 本地保存失败: {message}")
                return False
            
            time.sleep(10)  # 等待10秒后再次查询
        else:
            print(f"❌ 状态查询失败 (尝试 {attempt+1}/{max_attempts})")
            time.sleep(5)
    
    print(f"\n❌ 本地保存超时")
    return False

def test_oss_download(draft_url):
    """测试OSS文件下载"""
    print_section("⬇️ OSS文件下载测试")
    
    if not draft_url:
        print("❌ 没有OSS下载链接，跳过下载测试")
        return False
    
    try:
        print(f"   🔗 下载链接: {draft_url}")
        print("   🔄 正在测试下载...")
        
        # 测试下载链接可用性 - 先尝试HEAD请求，失败则尝试部分GET请求
        try:
            response = requests.head(draft_url, timeout=30)
            if response.status_code == 200:
                content_length = response.headers.get('Content-Length')
                content_type = response.headers.get('Content-Type')
                print(f"✅ OSS文件下载测试成功 (HEAD请求)")
                print(f"   📦 文件大小: {content_length} bytes" if content_length else "   📦 文件大小: 未知")
                print(f"   📄 文件类型: {content_type}" if content_type else "   📄 文件类型: 未知")
                return True
        except:
            pass
        
        # HEAD请求失败，尝试GET请求前1KB数据验证
        try:
            headers = {'Range': 'bytes=0-1023'}
            response = requests.get(draft_url, headers=headers, timeout=30)
            if response.status_code in [200, 206]:  # 200 or 206 Partial Content
                print(f"✅ OSS文件下载测试成功 (GET请求验证)")
                print(f"   📦 验证数据: {len(response.content)} bytes")
                print(f"   📄 文件可正常下载")
                return True
        except:
            pass
        
        # 所有测试都失败
        print(f"❌ OSS文件下载测试失败: 链接可能无效或签名过期")
        print(f"   💡 但这不影响实际使用 - 手动下载通常是正常的")
        return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ OSS下载测试失败: {str(e)}")
        return False

def verify_draft_files_local():
    """验证本地草稿文件"""
    print_section("🔍 验证本地草稿文件")
    
    # 在Linux服务器上查找
    draft_path = os.path.join(".", DRAFT_ID)
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
        return False  # 目录都不存在，后续检查无意义
    
    # 检查draft_info.json
    if os.path.exists(draft_info_path):
        print(f"✅ draft_info.json存在")
        try:
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_info = json.load(f)
                materials = draft_info.get("materials", {})
                tracks = draft_info.get("tracks", {})
                print(f"   📦 包含 {len(materials)} 个素材")
                print(f"   🛤️ 包含 {len(tracks)} 个轨道")
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
            print(f"   📁 包含 {len(asset_files)} 个素材文件")
            for file in asset_files[:5]:  # 只显示前5个文件
                print(f"      - {file}")
            if len(asset_files) > 5:
                print(f"      - ... 还有 {len(asset_files)-5} 个文件")
            checks.append(True)
        except Exception as e:
            print(f"❌ assets目录读取失败: {e}")
            checks.append(False)
    else:
        print(f"❌ assets目录不存在")
        checks.append(False)
    
    return all(checks)

def test_generate_standard_url(draft_id: str):
    """测试标准下载链接生成（已上传则直接返回OSS签名直链）"""
    print_subsection("🔗 生成标准下载链接")
    data = {"draft_id": draft_id}
    result = make_request("/generate_draft_url", data)
    if result and result.get("success", False):
        output = result.get("output", {})
        url = output.get("draft_url", "")
        storage = output.get("storage", "")
        print(f"   storage: {storage}")
        print(f"   url: {url}")
        return bool(url)
    print("❌ 生成标准下载链接失败")
    return False


def test_generate_custom_url(draft_id: str, client_os: str, draft_folder: str):
    """测试定制化下载链接生成（改写draft_info.json并缓存派生zip）"""
    print_subsection("🎯 生成定制化下载链接（派生zip）")
    data = {
        "draft_id": draft_id,
        "client_os": client_os,
        "draft_folder": draft_folder
    }
    result = make_request("/generate_draft_url", data)
    if result and result.get("success", False):
        output = result.get("output", {})
        url = output.get("draft_url", "")
        storage = output.get("storage", "")
        print(f"   client_os: {client_os}")
        print(f"   draft_folder: {draft_folder}")
        print(f"   storage: {storage}")
        print(f"   url: {url}")
        return bool(url)
    print("❌ 生成定制化下载链接失败")
    return False

def main():
    """主测试函数"""
    global SERVER_URL, TEST_MODE
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='CapCutAPI 完整功能测试')
    parser.add_argument('--mode', choices=['local', 'oss'], default='oss',
                       help='测试模式: local(本地保存) 或 oss(OSS云存储)')
    parser.add_argument('--server', default=SERVER_URL,
                       help=f'服务器地址 (默认: {SERVER_URL})')
    
    args = parser.parse_args()
    
    SERVER_URL = args.server
    TEST_MODE = args.mode
    
    print("🚀 CapCutAPI 完整功能测试")
    print(f"   🌐 服务器地址: {SERVER_URL}")
    print(f"   📝 测试草稿ID: {DRAFT_ID}")
    print(f"   💾 测试模式: {'OSS云存储' if TEST_MODE == 'oss' else '本地保存'}")
    if TEST_MODE == 'local':
        print(f"   📁 本地保存路径: {DRAFT_FOLDER}")
    print(f"   🕐 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行所有测试
    test_results = []
    draft_url = None
    
    # 基础测试
    test_results.append(("服务器连接", test_server_config()))
    test_results.append(("基础API端点", test_basic_endpoints()))
    test_results.append(("创建草稿", test_create_draft()))
    test_results.append(("添加视频", test_add_video()))
    test_results.append(("添加音频", test_add_audio()))
    test_results.append(("添加图片", test_add_image()))
    test_results.append(("添加文本", test_add_text()))
    
    # 根据模式选择保存测试
    if TEST_MODE == "oss":
        save_result = test_save_draft_oss()
        if isinstance(save_result, tuple):
            success, draft_url = save_result
            test_results.append(("OSS保存草稿", success))
            if success and draft_url:
                test_results.append(("OSS下载测试", test_oss_download(draft_url)))
                # 新增：生成下载链接（标准/定制化）
                test_results.append(("生成标准下载链接", test_generate_standard_url(DRAFT_ID)))
                # 使用一个Linux示例根路径，可按需调整
                test_results.append(("生成定制化下载链接", test_generate_custom_url(DRAFT_ID, "linux", "/mnt/custom/drafts")))
        else:
            test_results.append(("OSS保存草稿", save_result))
    else:
        test_results.append(("本地保存草稿", test_save_draft_local()))
        test_results.append(("验证本地文件", verify_draft_files_local()))
    
    # 统计结果
    print_section("📊 测试结果汇总")
    
    success_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name:<20} {status}")
        if result:
            success_count += 1
    
    total_tests = len(test_results)
    success_rate = (success_count / total_tests) * 100
    
    print(f"\n{'='*60}")
    print(f"📈 测试统计:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功数: {success_count}")
    print(f"   失败数: {total_tests - success_count}")
    print(f"   成功率: {success_rate:.1f}%")
    print(f"   结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == total_tests:
        print(f"\n🎉 所有测试通过！CapCutAPI服务运行完全正常！")
        if TEST_MODE == "oss" and draft_url:
            print(f"☁️  草稿已保存到OSS云存储")
            print(f"🔗 下载链接: {draft_url}")
            print(f"⏰ 链接有效期: 24小时")
            print(f"💡 您可以下载zip文件并解压后用剪映打开")
        elif TEST_MODE == "local":
            print(f"📁 完整草稿已保存至本地")
            print(f"💡 您可以将草稿复制到Windows并用剪映打开查看效果")
        return 0
    else:
        print(f"\n⚠️  {total_tests - success_count} 个测试失败，请检查服务配置")
        print(f"🔧 建议检查服务器日志获取详细错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 