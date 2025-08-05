#!/usr/bin/env python3
import requests
import time

# 测试创建草稿
print("=== 测试创建草稿 ===")
draft_id = f"test_draft_{int(time.time())}"
data = {
    "draft_id": draft_id,
    "width": 1080,
    "height": 1920
}

try:
    response = requests.post("http://localhost:9000/create_draft", json=data)
    result = response.json()
    print(f"创建草稿结果: {result}")
    
    if result.get("success"):
        print("✅ 草稿创建成功")
        
        # 测试添加文本
        print("\n=== 测试添加文本 ===")
        text_data = {
            "draft_id": draft_id,
            "text": "测试文本",
            "start": 0,
            "end": 5,
            "font": "ZY_Courage",
            "font_color": "#FF0000",
            "font_size": 40.0
        }
        
        response = requests.post("http://localhost:9000/add_text", json=text_data)
        result = response.json()
        print(f"添加文本结果: {result}")
        
        if result.get("success"):
            print("✅ 文本添加成功")
            
            # 测试保存草稿
            print("\n=== 测试保存草稿 ===")
            save_data = {"draft_id": draft_id}
            
            response = requests.post("http://localhost:9000/save_draft", json=save_data)
            result = response.json()
            print(f"保存草稿结果: {result}")
            
            if result.get("success"):
                print("✅ 草稿保存成功")
                
                # 检查本地文件
                import os
                draft_folder = f"dfd_{draft_id}"
                if os.path.exists(draft_folder):
                    print(f"✅ 本地草稿文件夹已创建: {draft_folder}")
                    files = os.listdir(draft_folder)
                    print(f"文件夹内容: {files}")
                else:
                    print(f"❌ 本地草稿文件夹未找到: {draft_folder}")
            else:
                print(f"❌ 草稿保存失败: {result.get('error')}")
        else:
            print(f"❌ 文本添加失败: {result.get('error')}")
    else:
        print(f"❌ 草稿创建失败: {result.get('error')}")
        
except Exception as e:
    print(f"❌ 测试过程中发生错误: {str(e)}") 