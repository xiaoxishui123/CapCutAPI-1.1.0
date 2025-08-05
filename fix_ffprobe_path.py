#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复ffprobe路径问题的脚本
确保CapCutAPI服务器能找到ffprobe命令
"""

import os
import subprocess
import json

def fix_ffprobe_path():
    """修复ffprobe路径问题"""
    
    # 1. 找到ffprobe的实际路径
    try:
        ffprobe_path = subprocess.check_output(['which', 'ffprobe']).decode().strip()
        print(f"✅ 找到ffprobe路径: {ffprobe_path}")
    except:
        print("❌ 系统中未找到ffprobe，请先安装ffmpeg")
        return False
    
    # 2. 创建修复后的环境变量脚本
    env_script = f"""#!/bin/bash
# CapCutAPI ffprobe路径修复脚本
export PATH="/usr/bin:/usr/local/bin:$PATH"
export FFPROBE_PATH="{ffprobe_path}"

# 启动CapCutAPI服务器
cd /home/CapCutAPI-1.1.0
python3 capcut_server.py
"""
    
    with open('start_capcut_with_ffprobe.sh', 'w') as f:
        f.write(env_script)
    
    os.chmod('start_capcut_with_ffprobe.sh', 0o755)
    print("✅ 创建了修复脚本: start_capcut_with_ffprobe.sh")
    
    return True

def fix_existing_drafts():
    """修复现有草稿的视频元数据"""
    
    # 获取所有草稿文件夹
    draft_folders = [f for f in os.listdir('.') if os.path.isdir(f) and os.path.exists(f'{f}/draft_info.json')]
    
    fixed_count = 0
    for folder in draft_folders:
        draft_file = f'{folder}/draft_info.json'
        
        try:
            with open(draft_file, 'r') as f:
                data = json.load(f)
            
            modified = False
            for video in data['materials']['videos']:
                if video['duration'] == 0:
                    # 查找对应的视频文件
                    video_file = None
                    for root, dirs, files in os.walk(f'{folder}/assets'):
                        for file in files:
                            if file.endswith('.mp4') and video['material_name'] in file:
                                video_file = os.path.join(root, file)
                                break
                    
                    if video_file and os.path.exists(video_file):
                        try:
                            # 使用ffprobe获取正确信息
                            result = subprocess.check_output([
                                'ffprobe', '-v', 'error', 
                                '-select_streams', 'v:0',
                                '-show_entries', 'stream=width,height,duration',
                                '-of', 'json', video_file
                            ])
                            info = json.loads(result)
                            stream = info['streams'][0]
                            
                            # 更新元数据
                            video['duration'] = int(float(stream['duration']) * 1000000)
                            video['width'] = int(stream['width'])
                            video['height'] = int(stream['height'])
                            modified = True
                            
                            print(f"✅ 修复了 {folder} 中的视频元数据")
                            
                        except Exception as e:
                            print(f"❌ 修复 {folder} 失败: {e}")
            
            if modified:
                with open(draft_file, 'w') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                fixed_count += 1
                
        except Exception as e:
            print(f"❌ 处理 {folder} 失败: {e}")
    
    print(f"✅ 总共修复了 {fixed_count} 个草稿")

if __name__ == "__main__":
    print("🛠️  CapCutAPI ffprobe问题修复工具")
    print("=" * 50)
    
    # 1. 修复ffprobe路径问题
    if fix_ffprobe_path():
        print("✅ ffprobe路径问题已修复")
    
    # 2. 修复现有草稿
    print("\n🔧 修复现有草稿的视频元数据...")
    fix_existing_drafts()
    
    print("\n📋 使用说明:")
    print("1. 以后启动服务器使用: ./start_capcut_with_ffprobe.sh")
    print("2. 或者手动设置环境变量后再启动python服务器")
    print("3. 现有草稿的视频元数据已经修复完成")
    print("\n🎉 现在所有草稿都应该能在剪映中正确识别素材了！") 