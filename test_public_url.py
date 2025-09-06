#!/usr/bin/env python3
import requests
from settings.local import OSS_CONFIG

# 构建公开访问URL（不带签名）
file_name = 'dfd_cat_1757127946_3514a3e1.zip'
public_url = f"https://{OSS_CONFIG['bucket_name']}.{OSS_CONFIG['endpoint']}/{file_name}"

print(f'测试公开URL: {public_url}')

try:
    # 测试HEAD请求
    response = requests.head(public_url, timeout=10)
    print(f'HEAD请求结果: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ 公开URL访问成功')
        print(f'Content-Length: {response.headers.get("Content-Length")}')
        print(f'Content-Type: {response.headers.get("Content-Type")}')
        
        # 尝试下载前几个字节
        headers = {'Range': 'bytes=0-99'}
        response = requests.get(public_url, headers=headers, timeout=10)
        print(f'部分下载结果: {response.status_code}')
        print(f'下载内容长度: {len(response.content)} bytes')
        
    else:
        print('❌ 公开URL访问失败')
        print(f'响应头: {dict(response.headers)}')
        
except Exception as e:
    print(f'访问错误: {e}')
    import traceback
    traceback.print_exc()
