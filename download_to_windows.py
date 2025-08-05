#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCutAPI Windows下载工具
自动下载服务器上的草稿到Windows本地，并确保路径兼容
"""

import os
import shutil
import requests
import json
from typing import Optional

class CapCutWindowsDownloader:
    """CapCut草稿Windows下载器"""
    
    def __init__(self, server_url: str, windows_draft_path: str):
        """
        初始化下载器
        
        Args:
            server_url: CapCutAPI服务器地址，如 "http://8.148.70.18:9000"
            windows_draft_path: Windows剪映草稿路径，如 "F:\\jianyin\\cgwz\\JianyingPro Drafts"
        """
        self.server_url = server_url.rstrip('/')
        self.windows_draft_path = windows_draft_path
        
    def create_windows_compatible_draft(self, draft_id: str, video_urls: list = None, 
                                      image_urls: list = None, audio_urls: list = None,
                                      texts: list = None) -> dict:
        """
        创建Windows兼容的草稿
        
        Args:
            draft_id: 草稿ID
            video_urls: 视频URL列表
            image_urls: 图片URL列表  
            audio_urls: 音频URL列表
            texts: 文本列表，格式: [{"text": "内容", "start": 0, "end": 5}]
            
        Returns:
            创建结果字典
        """
        try:
            # 1. 创建草稿
            print(f"🎬 创建草稿: {draft_id}")
            create_result = requests.post(f"{self.server_url}/create_draft", json={
                "draft_id": draft_id,
                "width": 1080,
                "height": 1920
            })
            
            if not create_result.json().get('success'):
                return {"success": False, "error": "创建草稿失败"}
            
            # 2. 添加视频
            if video_urls:
                for i, video_url in enumerate(video_urls):
                    print(f"📹 添加视频 {i+1}: {video_url[:50]}...")
                    requests.post(f"{self.server_url}/add_video", json={
                        "draft_id": draft_id,
                        "video_url": video_url,
                        "start": 0,
                        "end": 10,
                        "track_name": f"video_{i+1}"
                    })
            
            # 3. 添加图片
            if image_urls:
                for i, image_url in enumerate(image_urls):
                    print(f"🖼️ 添加图片 {i+1}: {image_url[:50]}...")
                    requests.post(f"{self.server_url}/add_image", json={
                        "draft_id": draft_id,
                        "image_url": image_url,
                        "start": i * 3,
                        "end": (i + 1) * 3,
                        "track_name": f"image_{i+1}"
                    })
            
            # 4. 添加音频
            if audio_urls:
                for i, audio_url in enumerate(audio_urls):
                    print(f"🎵 添加音频 {i+1}: {audio_url[:50]}...")
                    requests.post(f"{self.server_url}/add_audio", json={
                        "draft_id": draft_id,
                        "audio_url": audio_url,
                        "start": 0,
                        "end": 30,
                        "track_name": f"audio_{i+1}"
                    })
            
            # 5. 添加文本
            if texts:
                for i, text_info in enumerate(texts):
                    print(f"📝 添加文本 {i+1}: {text_info['text'][:20]}...")
                    requests.post(f"{self.server_url}/add_text", json={
                        "draft_id": draft_id,
                        "text": text_info["text"],
                        "start": text_info.get("start", 0),
                        "end": text_info.get("end", 5),
                        "font": "ZY_Courage",
                        "font_color": "#FFFFFF",
                        "font_size": 8.0,
                        "track_name": f"text_{i+1}"
                    })
            
            # 6. 🔑 使用Windows路径保存
            print(f"💾 保存草稿到Windows路径...")
            save_result = requests.post(f"{self.server_url}/save_draft", json={
                "draft_id": draft_id,
                "draft_folder": self.windows_draft_path
            })
            
            if save_result.json().get('success'):
                print(f"✅ 草稿创建成功！")
                print(f"📁 服务器路径: {draft_id}/")
                print(f"🪟 Windows目标路径: {self.windows_draft_path}\\{draft_id}\\")
                return {
                    "success": True, 
                    "draft_id": draft_id,
                    "server_path": f"{draft_id}/",
                    "windows_path": f"{self.windows_draft_path}\\{draft_id}\\"
                }
            else:
                return {"success": False, "error": "保存草稿失败"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_instructions(self, draft_id: str) -> str:
        """
        生成下载说明
        """
        return f"""
🚀 Windows下载说明：

1️⃣ 从Linux服务器下载草稿文件夹：
   scp -r user@server:/home/CapCutAPI-1.1.0/{draft_id} ./

2️⃣ 将文件夹复制到Windows剪映目录：
   复制整个 {draft_id} 文件夹到:
   {self.windows_draft_path}\\

3️⃣ 在剪映中打开：
   - 打开剪映PC版
   - 点击"导入项目"或在草稿列表中查找
   - ✅ 素材路径已经兼容，可以正常使用！

📁 文件夹结构应该是：
{self.windows_draft_path}\\
└── {draft_id}\\
    ├── draft_info.json
    ├── assets\\
    │   ├── video\\
    │   ├── audio\\
    │   └── image\\
    └── (其他文件...)
"""

# 使用示例
if __name__ == "__main__":
         # 配置
     SERVER_URL = "http://8.148.70.18:9000"
     # 注意：在Python字符串中，Windows路径需要使用双反斜杠或原始字符串
     WINDOWS_DRAFT_PATH = r"F:\jianyin\cgwz\JianyingPro Drafts"  # 原始字符串方式
     # 或者使用: WINDOWS_DRAFT_PATH = "F:\\jianyin\\cgwz\\JianyingPro Drafts"  # 转义方式
    
    # 创建下载器
    downloader = CapCutWindowsDownloader(SERVER_URL, WINDOWS_DRAFT_PATH)
    
    # 示例：创建一个包含视频和文本的草稿
    result = downloader.create_windows_compatible_draft(
        draft_id="my_windows_project",
        video_urls=[
            "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"
        ],
        image_urls=[
            "https://picsum.photos/800/600"
        ],
        texts=[
            {"text": "欢迎使用Windows兼容草稿！", "start": 1, "end": 5}
        ]
    )
    
    if result["success"]:
        print("\n" + downloader.download_instructions(result["draft_id"]))
    else:
        print(f"❌ 创建失败: {result['error']}") 