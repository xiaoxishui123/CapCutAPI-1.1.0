#!/usr/bin/env python3
import oss2
from settings.local import OSS_CONFIG
import requests

# 测试V2签名
print('=== 测试OSS V2签名 ===')
auth_v2 = oss2.Auth(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
endpoint = 'https://' + OSS_CONFIG['endpoint']
bucket_v2 = oss2.Bucket(auth_v2, endpoint, OSS_CONFIG['bucket_name'])

file_name = 'dfd_cat_1757127946_3514a3e1.zip'

try:
    # 生成V2签名URL
    signed_url_v2 = bucket_v2.sign_url('GET', file_name, 3600)
    print(f'V2签名URL: {signed_url_v2}')
    
    # 测试访问
    response = requests.head(signed_url_v2, timeout=10)
    print(f'V2签名访问结果: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ V2签名URL访问成功')
    else:
        print('❌ V2签名URL访问失败')
        
except Exception as e:
    print(f'V2签名错误: {e}')

print('\n=== 测试OSS V4签名 ===')
auth_v4 = oss2.AuthV4(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
bucket_v4 = oss2.Bucket(auth_v4, endpoint, OSS_CONFIG['bucket_name'], region=OSS_CONFIG['region'])

try:
    # 生成V4签名URL
    signed_url_v4 = bucket_v4.sign_url('GET', file_name, 3600)
    print(f'V4签名URL: {signed_url_v4}')
    
    # 测试访问
    response = requests.head(signed_url_v4, timeout=10)
    print(f'V4签名访问结果: {response.status_code}')
    
    if response.status_code == 200:
        print('✅ V4签名URL访问成功')
    else:
        print('❌ V4签名URL访问失败')
        
except Exception as e:
    print(f'V4签名错误: {e}')