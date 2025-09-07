#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义下载路径问题修复工具

问题：用户配置Windows路径但服务器在Linux上运行，导致路径不匹配
解决：提供正确的跨平台路径处理和用户指导
"""

import os
import json
import sys
from pathlib import Path

def analyze_current_config():
    """分析当前路径配置"""
    print("🔍 分析当前路径配置...")
    
    # 读取当前配置
    config_file = 'path_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            current_path = config.get('custom_download_path', '')
            print(f"当前配置路径: {current_path}")
            
            # 分析路径类型
            if current_path.startswith(('C:', 'D:', 'E:', 'F:', 'G:')):
                print("❌ 检测到Windows路径格式，但服务器运行在Linux上")
                return 'windows_path_on_linux'
            elif current_path.startswith('/'):
                print("✅ 检测到Linux路径格式")
                return 'linux_path'
            else:
                print("⚠️ 未知路径格式")
                return 'unknown'
    else:
        print("❌ 配置文件不存在")
        return 'no_config'

def check_actual_downloads():
    """检查实际的下载位置"""
    print("\n📁 检查实际下载位置...")
    
    possible_locations = [
        '/tmp/test_download',
        '/home/CapCutAPI-1.1.0/drafts',
        '/tmp/capcut_temp_drafts',
        '/tmp'
    ]
    
    found_downloads = []
    
    for location in possible_locations:
        if os.path.exists(location):
            print(f"✅ 找到目录: {location}")
            try:
                items = os.listdir(location)
                draft_folders = [item for item in items if item.startswith('dfd_cat_')]
                if draft_folders:
                    print(f"   📋 包含草稿: {draft_folders}")
                    found_downloads.extend([(location, folder) for folder in draft_folders])
            except PermissionError:
                print(f"   ❌ 无权限访问: {location}")
        else:
            print(f"❌ 目录不存在: {location}")
    
    return found_downloads

def provide_solutions():
    """提供解决方案"""
    print("\n💡 解决方案:")
    
    print("1. 🖥️ 如果你在Windows上使用:")
    print("   - 下载的文件实际在Linux服务器上")
    print("   - 你需要通过以下方式获取文件:")
    print("   a) 使用'直接下载'按钮，文件会下载到浏览器默认位置")
    print("   b) 或者配置一个服务器可访问的路径")
    
    print("\n2. 🔧 修复路径配置:")
    print("   - 将路径配置改为Linux格式，如: /tmp/my_downloads")
    print("   - 或者使用相对路径，如: downloads/")
    
    print("\n3. 📥 推荐的下载方式:")
    print("   a) 点击'直接下载'按钮 - 文件会自动下载到浏览器下载目录")
    print("   b) 使用代理下载链接 - 直接在浏览器中打开下载链接")
    
    print("\n4. 🌐 OSS云端下载:")
    print("   - 草稿已存储在云端OSS")
    print("   - 可以直接获取下载链接进行下载")

def fix_path_config():
    """修复路径配置"""
    print("\n🛠️ 修复路径配置...")
    
    # 提供合理的Linux路径
    recommended_path = "/tmp/capcut_downloads"
    
    try:
        # 创建推荐目录
        os.makedirs(recommended_path, exist_ok=True)
        
        # 更新配置文件
        config = {
            "custom_download_path": recommended_path
        }
        
        with open('path_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已将路径配置更新为: {recommended_path}")
        print(f"✅ 目录已创建并可写入")
        
        return True
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def test_download():
    """测试下载功能"""
    print("\n🧪 测试下载功能...")
    
    import requests
    
    test_data = {
        "draft_id": "dfd_cat_1757258119_1bafc9b8",
        "use_custom_path": True,
        "draft_folder": "/tmp/capcut_downloads"
    }
    
    try:
        response = requests.post(
            "http://localhost:9000/api/draft/download",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 下载测试成功!")
                print(f"📁 下载路径: {result.get('download_path')}")
                print(f"📋 复制文件数: {len(result.get('files_copied', []))}")
                
                # 验证文件是否真的存在
                download_path = result.get('download_path')
                if download_path and os.path.exists(download_path):
                    files = os.listdir(download_path)
                    print(f"✅ 确认文件存在: {len(files)} 个文件")
                    return True
                else:
                    print("❌ 下载路径不存在")
                    return False
            else:
                print(f"❌ 下载失败: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 自定义下载路径问题修复工具")
    print("=" * 50)
    
    # 1. 分析当前配置
    config_status = analyze_current_config()
    
    # 2. 检查实际下载位置
    downloads = check_actual_downloads()
    
    # 3. 提供解决方案
    provide_solutions()
    
    # 4. 询问是否修复
    print("\n❓ 是否要自动修复路径配置? (y/n): ", end='')
    choice = input().lower().strip()
    
    if choice in ['y', 'yes', '是']:
        if fix_path_config():
            # 5. 测试修复后的下载功能
            if test_download():
                print("\n🎉 修复完成! 自定义下载现在应该可以正常工作了。")
                print("\n📝 使用说明:")
                print("1. 在草稿预览页面点击'配置路径'")
                print("2. 输入: /tmp/capcut_downloads")
                print("3. 点击'自定义下载'")
                print("4. 文件将保存到服务器的 /tmp/capcut_downloads 目录")
            else:
                print("\n❌ 修复后测试失败，请检查日志。")
        else:
            print("\n❌ 自动修复失败。")
    else:
        print("\nℹ️ 未进行自动修复。请手动按照上述解决方案操作。")

if __name__ == "__main__":
    main()
