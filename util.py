#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCutAPI 工具函数模块
包含项目中用到的各种工具函数
"""

import os
import json
import hashlib
import zipfile
import time
import functools
from typing import Tuple


def generate_draft_url(draft_id=None):
    """生成草稿本地路径"""
    default_folder = "F:/jianyin/cgwz/JianyingPro Drafts"  # 使用正斜杠
    
    if draft_id:
        return f"{default_folder}/{draft_id}".replace('/', '\\')
    return default_folder.replace('/', '\\')


def is_windows_path(path: str) -> bool:
    """判断是否为Windows路径格式"""
    if not path:
        return False
    
    # 检查是否包含Windows驱动器号 (如 C:, D: 等)
    if len(path) >= 2 and path[1] == ':' and path[0].isalpha():
        return True
    
    # 检查是否包含反斜杠
    if '\\' in path:
        return True
    
    return False


def url_to_hash(url: str) -> str:
    """将URL转换为哈希值，用于生成唯一的文件名"""
    return hashlib.md5(url.encode('utf-8')).hexdigest()


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """将十六进制颜色转换为RGB值 (0-1范围)"""
    # 移除 # 符号
    hex_color = hex_color.lstrip('#')
    
    # 确保是6位十六进制
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color format: {hex_color}")
    
    try:
        # 转换为RGB值 (0-255)
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # 转换为0-1范围
        return (r / 255.0, g / 255.0, b / 255.0)
    except ValueError:
        raise ValueError(f"Invalid hex color format: {hex_color}")


def zip_draft(draft_folder: str, zip_path: str) -> bool:
    """将草稿文件夹打包为zip文件"""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(draft_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, draft_folder)
                    zipf.write(file_path, arcname)
        return True
    except Exception as e:
        print(f"压缩草稿失败: {e}")
        return False


def timing_decorator(func):
    """计时装饰器，用于性能监控"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"函数 {func.__name__} 执行时间: {execution_time:.4f} 秒")
        return result
    return wrapper


def format_path_for_platform(path: str, target_platform: str = "windows") -> str:
    """将路径格式化为目标平台格式"""
    if not path:
        return path
        
    if target_platform.lower() == "windows":
        # 转换为Windows路径格式
        return path.replace('/', '\\')
    else:
        # 转换为Unix/Linux路径格式
        return path.replace('\\', '/')


def ensure_directory_exists(directory_path: str) -> bool:
    """确保目录存在，如果不存在则创建"""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败: {e}")
        return False


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0


def safe_json_loads(json_str: str, default=None):
    """安全的JSON解析，如果失败返回默认值"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj, default=None) -> str:
    """安全的JSON序列化，如果失败返回默认值"""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return default or "{}"


def validate_draft_id(draft_id: str) -> bool:
    """验证草稿ID格式是否有效"""
    if not draft_id:
        return False
    
    # 只允许字母、数字、下划线和连字符
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
    return all(c in allowed_chars for c in draft_id)


def normalize_time_range(start: float, end: float) -> Tuple[float, float]:
    """标准化时间范围，确保start <= end"""
    if start > end:
        start, end = end, start
    return (max(0, start), max(0, end))


def format_duration(seconds: float) -> str:
    """将秒数格式化为时:分:秒格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将值限制在指定范围内"""
    return max(min_val, min(value, max_val)) 