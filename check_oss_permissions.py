#!/usr/bin/env python3
import oss2
from settings.local import OSS_CONFIG

# 创建OSS客户端
auth = oss2.Auth(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
endpoint = 'https://' + OSS_CONFIG['endpoint']
bucket = oss2.Bucket(auth, endpoint, OSS_CONFIG['bucket_name'])

print(f'检查Bucket权限: {OSS_CONFIG["bucket_name"]}')

try:
    # 检查bucket ACL
    acl = bucket.get_bucket_acl()
    print(f'Bucket ACL: {acl.acl}')
    
    # 检查bucket信息
    info = bucket.get_bucket_info()
    print(f'Bucket创建时间: {info.creation_date}')
    print(f'Bucket位置: {info.location}')
    print(f'Bucket存储类型: {info.storage_class}')
    
    # 检查文件ACL
    file_name = 'dfd_cat_1757127946_3514a3e1.zip'
    try:
        file_acl = bucket.get_object_acl(file_name)
        print(f'文件ACL: {file_acl.acl}')
    except Exception as e:
        print(f'获取文件ACL失败: {e}')
    
    # 尝试直接下载文件（不使用签名URL）
    try:
        result = bucket.get_object(file_name)
        print(f'直接下载成功，文件大小: {len(result.read())} bytes')
    except Exception as e:
        print(f'直接下载失败: {e}')
        
except Exception as e:
    print(f'检查权限失败: {e}')
    import traceback
    traceback.print_exc()
