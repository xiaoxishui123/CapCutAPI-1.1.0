#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试：验证下载草稿时路径是否正确设置
模拟完整的下载流程，检查生成的 ZIP 文件中的路径
"""

import json
import os
import sys
import tempfile
import zipfile
import requests
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_api_server():
    """检查 API 服务器是否运行"""
    try:
        response = requests.get('http://localhost:9000/', timeout=5)
        return response.status_code == 200
    except:
        return False


def get_path_config():
    """获取当前路径配置"""
    try:
        response = requests.get('http://localhost:9000/api/draft/path/config')
        data = response.json()
        return data.get('custom_path', '') if data.get('success') else ''
    except Exception as e:
        print(f"获取路径配置失败: {e}")
        return ''


def get_draft_list():
    """获取草稿列表"""
    try:
        response = requests.get('http://localhost:9000/api/v2/drafts')
        data = response.json()
        if data.get('success') and data.get('drafts'):
            return data['drafts']
        return []
    except Exception as e:
        print(f"获取草稿列表失败: {e}")
        return []


def download_draft_and_check(draft_id: str, draft_folder: str, client_os: str = 'windows'):
    """下载草稿并检查路径"""
    print(f"\n🔍 开始检查草稿: {draft_id}")
    print(f"   目标路径: {draft_folder}")
    print(f"   操作系统: {client_os}")
    
    try:
        # 调用下载 API
        response = requests.post(
            'http://localhost:9000/api/draft/download',
            json={
                'draft_id': draft_id,
                'use_custom_path': True,
                'draft_folder': draft_folder,
                'client_os': client_os
            },
            timeout=60
        )
        
        data = response.json()
        
        if not data.get('success'):
            print(f"   ❌ API 返回失败: {data.get('error')}")
            return False
        
        download_url = data.get('data', {}).get('download_url') or data.get('download_url')
        
        if not download_url:
            print(f"   ❌ 未获取到下载链接")
            return False
        
        print(f"   ✅ 获取到下载链接")
        
        # 下载文件到临时目录
        print(f"   📥 正在下载文件...")
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, f"{draft_id}.zip")
            
            # 下载文件
            file_response = requests.get(download_url, timeout=120)
            if file_response.status_code != 200:
                print(f"   ❌ 下载失败: HTTP {file_response.status_code}")
                return False
            
            with open(zip_path, 'wb') as f:
                f.write(file_response.content)
            
            file_size_mb = os.path.getsize(zip_path) / 1024 / 1024
            print(f"   ✅ 文件下载完成: {file_size_mb:.2f} MB")
            
            # 检查 ZIP 内容
            return check_zip_paths(zip_path, draft_id, draft_folder, client_os)
            
    except Exception as e:
        print(f"   ❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_zip_paths(zip_path: str, draft_id: str, expected_folder: str, client_os: str) -> bool:
    """检查 ZIP 文件中的路径设置"""
    print(f"\n   📦 检查 ZIP 文件内容...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # 列出文件
            file_list = zf.namelist()
            print(f"   📁 ZIP 包含 {len(file_list)} 个文件/目录")
            
            # 查找 draft_info.json
            draft_info_path = None
            draft_meta_path = None
            
            for f in file_list:
                f_lower = f.lower()
                if f_lower.endswith('draft_info.json'):
                    draft_info_path = f
                elif f_lower.endswith('draft_meta_info.json'):
                    draft_meta_path = f
            
            results = []
            
            # 检查 draft_info.json
            if draft_info_path:
                print(f"\n   📄 检查 {draft_info_path}:")
                raw = zf.read(draft_info_path)
                info = json.loads(raw.decode('utf-8'))
                
                # 检查素材路径
                materials = info.get('materials', {})
                
                for video in materials.get('videos', [])[:3]:
                    path = video.get('path', '')
                    if path:
                        result = verify_path(path, draft_id, expected_folder, client_os, 'video')
                        results.append(result)
                        status = "✅" if result else "❌"
                        print(f"      {status} 视频路径: {path[:80]}...")
                
                for audio in materials.get('audios', [])[:3]:
                    path = audio.get('path', '')
                    if path:
                        result = verify_path(path, draft_id, expected_folder, client_os, 'audio')
                        results.append(result)
                        status = "✅" if result else "❌"
                        print(f"      {status} 音频路径: {path[:80]}...")
                
                for image in materials.get('images', [])[:3]:
                    path = image.get('path', '')
                    if path:
                        result = verify_path(path, draft_id, expected_folder, client_os, 'image')
                        results.append(result)
                        status = "✅" if result else "❌"
                        print(f"      {status} 图片路径: {path[:80]}...")
            else:
                print("   ⚠️ 未找到 draft_info.json")
            
            # 检查 draft_meta_info.json
            if draft_meta_path:
                print(f"\n   📄 检查 {draft_meta_path}:")
                raw = zf.read(draft_meta_path)
                meta = json.loads(raw.decode('utf-8'))
                
                root_path = meta.get('draft_root_path', '')
                fold_path = meta.get('draft_fold_path', '')
                draft_name = meta.get('draft_name', '')
                
                print(f"      draft_root_path: {root_path}")
                print(f"      draft_fold_path: {fold_path}")
                print(f"      draft_name: {draft_name}")
                
                # 验证路径
                if expected_folder:
                    # 绝对路径模式
                    expected_fold = expected_folder.rstrip('/\\')
                    if client_os == 'windows':
                        expected_fold = expected_fold.replace('/', '\\')
                        expected_draft_fold = f"{expected_fold}\\{draft_id}"
                    else:
                        expected_fold = expected_fold.replace('\\', '/')
                        expected_draft_fold = f"{expected_fold}/{draft_id}"
                    
                    root_ok = (root_path.replace('/', '\\') == expected_fold.replace('/', '\\'))
                    fold_ok = (fold_path.replace('/', '\\') == expected_draft_fold.replace('/', '\\'))
                    
                    print(f"      {'✅' if root_ok else '❌'} draft_root_path 验证: 期望 {expected_fold}")
                    print(f"      {'✅' if fold_ok else '❌'} draft_fold_path 验证: 期望 {expected_draft_fold}")
                    
                    results.append(root_ok)
                    results.append(fold_ok)
                else:
                    # 相对路径模式
                    root_ok = (root_path == '')
                    fold_ok = (fold_path == '')
                    
                    print(f"      {'✅' if root_ok else '❌'} 相对路径模式: draft_root_path 应为空")
                    print(f"      {'✅' if fold_ok else '❌'} 相对路径模式: draft_fold_path 应为空")
                    
                    results.append(root_ok)
                    results.append(fold_ok)
            else:
                print("   ⚠️ 未找到 draft_meta_info.json")
            
            # 返回结果
            if all(results):
                print(f"\n   ✅ 所有路径验证通过!")
                return True
            else:
                print(f"\n   ❌ 部分路径验证失败")
                return False
                
    except Exception as e:
        print(f"   ❌ 检查 ZIP 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_path(path: str, draft_id: str, expected_folder: str, client_os: str, asset_type: str) -> bool:
    """验证单个路径是否正确"""
    if not path:
        return False
    
    if expected_folder:
        # 绝对路径模式
        expected_base = expected_folder.rstrip('/\\')
        if client_os == 'windows':
            expected_pattern = f"{expected_base}\\{draft_id}\\assets\\{asset_type}\\"
            expected_pattern = expected_pattern.replace('/', '\\')
            path_normalized = path.replace('/', '\\')
        else:
            expected_pattern = f"{expected_base}/{draft_id}/assets/{asset_type}/"
            expected_pattern = expected_pattern.replace('\\', '/')
            path_normalized = path.replace('\\', '/')
        
        return expected_pattern.lower() in path_normalized.lower()
    else:
        # 相对路径模式
        path_normalized = path.replace('\\', '/')
        return path_normalized.startswith(f"assets/{asset_type}/")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🧪 端到端测试：下载草稿路径验证")
    print("=" * 70)
    
    # 检查 API 服务器
    print("\n1️⃣ 检查 API 服务器...")
    if not check_api_server():
        print("   ❌ API 服务器未运行，请先启动服务器")
        print("   提示: 运行 python capcut_server.py 启动服务器")
        return 1
    print("   ✅ API 服务器正常运行")
    
    # 获取路径配置
    print("\n2️⃣ 获取路径配置...")
    custom_path = get_path_config()
    print(f"   配置的路径: {custom_path or '(未配置，使用相对路径模式)'}")
    
    # 获取草稿列表
    print("\n3️⃣ 获取草稿列表...")
    drafts = get_draft_list()
    
    if not drafts:
        print("   ⚠️ 没有可用的草稿")
        print("\n💡 手动测试步骤:")
        print("   1. 创建一个测试草稿")
        print("   2. 在网页界面点击下载按钮")
        print("   3. 解压 ZIP 文件并检查 draft_info.json 中的路径")
        return 0
    
    print(f"   找到 {len(drafts)} 个草稿")
    
    # 选择一个草稿进行测试
    test_draft = drafts[0]
    draft_id = test_draft.get('id') or test_draft.get('draft_id')
    
    print(f"\n4️⃣ 测试草稿下载...")
    
    # 测试场景 1: 使用配置的自定义路径
    if custom_path:
        print("\n" + "-" * 50)
        print("📋 场景 1: 自定义路径模式")
        result1 = download_draft_and_check(draft_id, custom_path, 'windows')
    else:
        print("\n" + "-" * 50)
        print("📋 场景 1: 相对路径模式（无自定义路径配置）")
        result1 = download_draft_and_check(draft_id, '', 'windows')
    
    # 测试场景 2: 指定特定路径
    print("\n" + "-" * 50)
    print("📋 场景 2: 指定路径模式")
    test_path = "F:\\test\\JianyingPro Drafts"
    result2 = download_draft_and_check(draft_id, test_path, 'windows')
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    all_passed = result1 and result2
    
    print(f"   场景 1 ({'自定义' if custom_path else '相对'}路径模式): {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"   场景 2 (指定路径模式): {'✅ 通过' if result2 else '❌ 失败'}")
    
    if all_passed:
        print("\n✅ 所有测试通过!")
        print("\n📝 剪映使用说明:")
        print("   1. 下载 ZIP 文件")
        if custom_path:
            print(f"   2. 解压到配置的目录: {custom_path}")
        else:
            print(f"   2. 解压到剪映草稿目录")
        print("   3. 打开剪映，草稿会自动识别")
        print("   4. 素材路径会自动指向正确位置")
    else:
        print("\n❌ 部分测试失败，请检查日志")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

