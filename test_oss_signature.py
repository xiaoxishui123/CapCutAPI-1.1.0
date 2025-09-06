#!/usr/bin/env python3
import oss2
from settings.local import OSS_CONFIG
import requests

# 创建OSS客户端
auth = oss2.AuthV4(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
endpoint = 'https://' + OSS_CONFIG['endpoint']
bucket = oss2.Bucket(auth, endpoint, OSS_CONFIG['bucket_name'], region=OSS_CONFIG['region'])

# 文件名
file_name = 'dfd_cat_1757127946_3514a3e1.zip'

print(f'测试文件: {file_name}')
print(f'Bucket: {OSS_CONFIG["bucket_name"]}')
print(f'Endpoint: {endpoint}')
print(f'Region: {OSS_CONFIG["region"]}')

try:
    # 生成新的签名URL
    signed_url = bucket.sign_url('GET', file_name, 3600)  # 1小时有效期
    print(f'\n新生成的签名URL:')
    print(signed_url)
    
    # 测试访问
    print('\n测试访问签名URL...')
    response = requests.head(signed_url, timeout=10)
    print(f'HTTP状态码: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ 签名URL访问成功')
        print(f'Content-Length: {response.headers.get("Content-Length")}')
        print(f'Content-Type: {response.headers.get("Content-Type")}')
    else:
        print('❌ 签名URL访问失败')
        print(f'响应头: {dict(response.headers)}')
        
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()