#!/usr/bin/env python3
import oss2
from settings.local import OSS_CONFIG

# 创建OSS客户端
auth = oss2.AuthV4(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
endpoint = 'https://' + OSS_CONFIG['endpoint']
bucket = oss2.Bucket(auth, endpoint, OSS_CONFIG['bucket_name'], region=OSS_CONFIG['region'])

# 检查文件是否存在
file_name = 'dfd_cat_1757127946_3514a3e1.zip'
print(f'检查文件: {file_name}')

try:
    exists = bucket.object_exists(file_name)
    print(f'文件存在: {exists}')
    
    if exists:
        meta = bucket.get_object_meta(file_name)
        print(f'文件大小: {meta.content_length} bytes')
        print(f'最后修改时间: {meta.last_modified}')
    else:
        print('文件不存在，列出最近的文件:')
        objects = list(bucket.list_objects().object_list)
        for obj in objects[-10:]:
            print(f'  {obj.key} ({obj.size} bytes)')
except Exception as e:
    print(f'错误: {e}')
