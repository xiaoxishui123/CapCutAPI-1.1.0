#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSS功能验证脚本
验证修复后的OSS上传和下载功能
"""

import requests
import json
import time

# 服务器配置
SERVER_URL = "http://8.148.70.18:9000"

def test_oss_functionality():
    """测试OSS完整功能"""
    print("🚀 OSS功能验证开始")
    print(f"服务器地址: {SERVER_URL}")
    
    # 生成唯一的草稿ID
    draft_id = f"oss_test_{int(time.time())}"
    print(f"测试草稿ID: {draft_id}")
    
    try:
        # 1. 创建草稿
        print("\n📝 步骤1: 创建草稿")
        create_response = requests.post(f"{SERVER_URL}/create_draft", json={
            "draft_id": draft_id,
            "width": 1080,
            "height": 1920
        }, timeout=30)
        
        if create_response.status_code == 200:
            result = create_response.json()
            if result.get("success"):
                print("✅ 草稿创建成功")
            else:
                print(f"❌ 草稿创建失败: {result.get('error')}")
                return False
        else:
            print(f"❌ 草稿创建请求失败: HTTP {create_response.status_code}")
            return False
        
        # 2. 添加视频素材
        print("\n🎥 步骤2: 添加视频素材")
        video_response = requests.post(f"{SERVER_URL}/add_video", json={
            "draft_id": draft_id,
            "video_url": "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4",
            "start": 0,
            "end": 5,
            "track_name": "main_video"
        }, timeout=30)
        
        if video_response.status_code == 200:
            result = video_response.json()
            if result.get("success"):
                print("✅ 视频添加成功")
            else:
                print(f"❌ 视频添加失败: {result.get('error')}")
                return False
        else:
            print(f"❌ 视频添加请求失败: HTTP {video_response.status_code}")
            return False
        
        # 3. 添加文本
        print("\n📝 步骤3: 添加文本")
        text_response = requests.post(f"{SERVER_URL}/add_text", json={
            "draft_id": draft_id,
            "text": "OSS修复测试 ✨",
            "start": 1,
            "end": 4,
            "font": "ZY_Courage",
            "font_color": "#ffffff",
            "font_size": 6.0
        }, timeout=30)
        
        if text_response.status_code == 200:
            result = text_response.json()
            if result.get("success"):
                print("✅ 文本添加成功")
            else:
                print(f"❌ 文本添加失败: {result.get('error')}")
                return False
        else:
            print(f"❌ 文本添加请求失败: HTTP {text_response.status_code}")
            return False
        
        # 4. 保存草稿到OSS
        print("\n☁️ 步骤4: 保存草稿到OSS")
        save_response = requests.post(f"{SERVER_URL}/save_draft", json={
            "draft_id": draft_id
        }, timeout=180)
        
        if save_response.status_code == 200:
            result = save_response.json()
            if result.get("success"):
                task_id = result.get("task_id")
                print(f"✅ OSS保存任务启动成功，任务ID: {task_id}")
                
                # 5. 监控保存进度
                print("\n📊 步骤5: 监控保存进度")
                oss_url = monitor_save_progress(task_id)
                
                if oss_url:
                    # 6. 测试下载链接
                    print("\n⬇️ 步骤6: 测试OSS下载链接")
                    return test_oss_download(oss_url)
                else:
                    print("❌ OSS保存失败")
                    return False
            else:
                print(f"❌ OSS保存失败: {result.get('error')}")
                return False
        else:
            print(f"❌ OSS保存请求失败: HTTP {save_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False

def monitor_save_progress(task_id):
    """监控保存进度"""
    max_attempts = 30
    
    for attempt in range(max_attempts):
        try:
            status_response = requests.post(f"{SERVER_URL}/query_draft_status", json={
                "task_id": task_id
            }, timeout=30)
            
            if status_response.status_code == 200:
                result = status_response.json()
                if result.get("success"):
                    status = result.get("status")
                    progress = result.get("progress", 0)
                    message = result.get("message", "")
                    
                    # 进度条显示
                    progress_bar = "█" * int(progress/5) + "░" * (20 - int(progress/5))
                    print(f"   [{progress_bar}] {progress}% - {status}: {message}")
                    
                    if status == "completed":
                        oss_url = result.get("draft_url", "")
                        print(f"✅ OSS保存完成!")
                        print(f"🔗 下载链接: {oss_url}")
                        return oss_url
                    elif status == "failed":
                        print(f"❌ OSS保存失败: {message}")
                        return None
                    
                    time.sleep(5)
                else:
                    print(f"❌ 状态查询失败: {result.get('error')}")
                    time.sleep(5)
            else:
                print(f"❌ 状态查询请求失败: HTTP {status_response.status_code}")
                time.sleep(5)
                
        except Exception as e:
            print(f"❌ 状态查询异常: {str(e)}")
            time.sleep(5)
    
    print("❌ OSS保存超时")
    return None

def test_oss_download(oss_url):
    """测试OSS下载链接"""
    try:
        print(f"🔗 测试下载链接: {oss_url}")
        
        # 使用HEAD请求测试下载链接
        response = requests.head(oss_url, timeout=30)
        
        if response.status_code == 200:
            content_length = response.headers.get('Content-Length')
            content_type = response.headers.get('Content-Type')
            
            print("✅ OSS下载链接测试成功!")
            print(f"📦 文件大小: {content_length} bytes" if content_length else "📦 文件大小: 未知")
            print(f"📄 文件类型: {content_type}" if content_type else "📄 文件类型: 未知")
            return True
        else:
            print(f"❌ OSS下载链接测试失败: HTTP {response.status_code}")
            if response.status_code == 403:
                print("   这可能是签名问题，需要检查OSS配置")
            return False
            
    except Exception as e:
        print(f"❌ OSS下载测试异常: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔧 CapCutAPI OSS功能修复验证")
    print("=" * 60)
    
    success = test_oss_functionality()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有OSS功能测试通过！")
        print("✅ OSS签名修复成功")
        print("✅ 草稿创建、保存、下载功能正常")
    else:
        print("⚠️ OSS功能测试失败")
        print("🔧 请检查服务器日志获取详细错误信息")
    print("=" * 60)

if __name__ == "__main__":
    main() 