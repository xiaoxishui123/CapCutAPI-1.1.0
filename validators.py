#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输入验证模块

提供各种输入验证函数，用于防止安全攻击（SSRF、SQL注入、路径遍历等）

功能：
- validate_draft_id: 验证草稿ID格式
- validate_url: 验证URL格式并防止SSRF攻击
- validate_file_path: 验证文件路径，防止路径遍历
- validate_text_content: 验证文本内容长度
- validate_numeric_range: 验证数值范围
- validate_color: 验证颜色格式（RGB、RGBA、HEX）
- validate_duration: 验证时长（用于视频、音频）
- validate_material_type: 验证素材类型

作者: CapCutAPI Team
创建时间: 2025-11-11
"""

import re
import os
from urllib.parse import urlparse
from typing import Tuple, Optional, List


def validate_draft_id(draft_id: str) -> Tuple[bool, str]:
    """
    验证草稿ID格式

    Args:
        draft_id: 草稿ID字符串

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_draft_id("dfd_cat_abc123")
        (True, "")
        >>> validate_draft_id("")
        (False, "草稿ID不能为空")
        >>> validate_draft_id("draft@#$")
        (False, "草稿ID只能包含字母、数字、下划线和连字符")
    """
    if not draft_id or not isinstance(draft_id, str):
        return False, "草稿ID不能为空"

    # 只允许字母、数字、下划线、连字符
    if not re.match(r'^[a-zA-Z0-9_-]+$', draft_id):
        return False, "草稿ID只能包含字母、数字、下划线和连字符"

    # 限制长度
    if len(draft_id) > 100:
        return False, "草稿ID长度不能超过100字符"

    if len(draft_id) < 3:
        return False, "草稿ID长度不能少于3字符"

    return True, ""


def validate_url(url: str, allow_internal: bool = False) -> Tuple[bool, str]:
    """
    验证URL格式并防止SSRF攻击

    Args:
        url: URL字符串
        allow_internal: 是否允许访问内网地址（默认False，用于安全防护）

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_url("https://example.com/video.mp4")
        (True, "")
        >>> validate_url("http://localhost:8080/video.mp4")
        (False, "禁止访问本地地址: localhost")
        >>> validate_url("http://192.168.1.100/video.mp4")
        (False, "禁止访问内网地址: 192.168.1.100")
    """
    if not url:
        return False, "URL不能为空"

    if not isinstance(url, str):
        return False, "URL必须是字符串"

    try:
        parsed = urlparse(url)

        # 只允许http和https协议
        if parsed.scheme not in ['http', 'https']:
            return False, f"不支持的协议: {parsed.scheme}，仅支持http和https"

        hostname = parsed.hostname
        if not hostname:
            return False, "无效的URL格式，缺少主机名"

        # 如果允许内网访问，跳过内网检查
        if allow_internal:
            return True, ""

        # 禁止访问本地地址
        forbidden_hosts = [
            'localhost', '127.0.0.1', '0.0.0.0', '::1',
            '169.254.169.254'  # AWS元数据服务
        ]

        if hostname.lower() in forbidden_hosts:
            return False, f"禁止访问本地地址: {hostname}"

        # 禁止访问常见内网地址段
        if hostname.startswith('192.168.') or hostname.startswith('10.'):
            return False, f"禁止访问内网地址: {hostname}"

        # 检查172.16.0.0 - 172.31.255.255 (内网B类地址)
        if hostname.startswith('172.'):
            try:
                second_octet = int(hostname.split('.')[1])
                if 16 <= second_octet <= 31:
                    return False, f"禁止访问内网地址: {hostname}"
            except (ValueError, IndexError):
                pass

        return True, ""

    except Exception as e:
        return False, f"URL解析错误: {str(e)}"


def validate_file_path(file_path: str, allow_absolute: bool = True) -> Tuple[bool, str]:
    """
    验证文件路径，防止路径遍历攻击

    Args:
        file_path: 文件路径字符串
        allow_absolute: 是否允许绝对路径（默认True）

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_file_path("/home/user/video.mp4")
        (True, "")
        >>> validate_file_path("../../etc/passwd")
        (False, "文件路径包含危险字符: ..")
        >>> validate_file_path("~/documents/video.mp4")
        (True, "")
    """
    if not file_path:
        return False, "文件路径不能为空"

    if not isinstance(file_path, str):
        return False, "文件路径必须是字符串"

    # 检查路径遍历攻击特征
    dangerous_patterns = ['..', '\x00', '\0']
    for pattern in dangerous_patterns:
        if pattern in file_path:
            return False, f"文件路径包含危险字符: {pattern}"

    # 检查是否为绝对路径
    is_absolute = os.path.isabs(file_path) or file_path.startswith('~')

    if not allow_absolute and is_absolute:
        return False, "不允许使用绝对路径"

    # 路径长度限制
    if len(file_path) > 4096:  # Unix系统路径最大长度
        return False, "文件路径长度超过限制(4096字符)"

    return True, ""


def validate_text_content(text: str, max_length: int = 10000, min_length: int = 0) -> Tuple[bool, str]:
    """
    验证文本内容

    Args:
        text: 文本内容
        max_length: 最大长度（默认10000字符）
        min_length: 最小长度（默认0字符）

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_text_content("Hello World")
        (True, "")
        >>> validate_text_content("", min_length=1)
        (False, "文本内容长度不能少于1字符")
    """
    if text is None:
        return False, "文本内容不能为None"

    if not isinstance(text, str):
        return False, "文本内容必须是字符串"

    text_len = len(text)

    if text_len < min_length:
        return False, f"文本内容长度不能少于{min_length}字符"

    if text_len > max_length:
        return False, f"文本内容长度不能超过{max_length}字符"

    return True, ""


def validate_numeric_range(
    value,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    field_name: str = "数值"
) -> Tuple[bool, str]:
    """
    验证数值范围

    Args:
        value: 数值（可以是int、float或字符串）
        min_val: 最小值（可选）
        max_val: 最大值（可选）
        field_name: 字段名称（用于错误信息）

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_numeric_range(50, 0, 100)
        (True, "")
        >>> validate_numeric_range(-10, 0, 100)
        (False, "数值不能小于0")
        >>> validate_numeric_range("abc", 0, 100)
        (False, "数值必须是有效的数字")
    """
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        return False, f"{field_name}必须是有效的数字"

    if min_val is not None and num_value < min_val:
        return False, f"{field_name}不能小于{min_val}"

    if max_val is not None and num_value > max_val:
        return False, f"{field_name}不能大于{max_val}"

    return True, ""


def validate_color(color: str) -> Tuple[bool, str]:
    """
    验证颜色格式（支持RGB、RGBA、HEX）

    Args:
        color: 颜色字符串

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_color("#FF5733")
        (True, "")
        >>> validate_color("rgb(255, 87, 51)")
        (True, "")
        >>> validate_color("rgba(255, 87, 51, 0.5)")
        (True, "")
        >>> validate_color("invalid_color")
        (False, "不支持的颜色格式")
    """
    if not color or not isinstance(color, str):
        return False, "颜色值不能为空"

    color = color.strip()

    # HEX格式: #RGB 或 #RRGGBB 或 #RRGGBBAA
    hex_pattern = r'^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$'
    if re.match(hex_pattern, color):
        return True, ""

    # RGB格式: rgb(r, g, b)
    rgb_pattern = r'^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$'
    rgb_match = re.match(rgb_pattern, color, re.IGNORECASE)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        if all(0 <= val <= 255 for val in [r, g, b]):
            return True, ""
        return False, "RGB值必须在0-255范围内"

    # RGBA格式: rgba(r, g, b, a)
    rgba_pattern = r'^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(0|1|0?\.\d+)\s*\)$'
    rgba_match = re.match(rgba_pattern, color, re.IGNORECASE)
    if rgba_match:
        r, g, b, a = rgba_match.groups()
        r, g, b = map(int, [r, g, b])
        a = float(a)
        if all(0 <= val <= 255 for val in [r, g, b]) and 0 <= a <= 1:
            return True, ""
        return False, "RGBA值必须在有效范围内(RGB: 0-255, A: 0-1)"

    return False, "不支持的颜色格式，支持: #HEX, rgb(r,g,b), rgba(r,g,b,a)"


def validate_duration(
    start: float,
    end: float,
    max_duration: Optional[float] = None
) -> Tuple[bool, str]:
    """
    验证时长（用于视频、音频片段）

    Args:
        start: 开始时间（秒）
        end: 结束时间（秒）
        max_duration: 最大时长（秒，可选）

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_duration(0, 10)
        (True, "")
        >>> validate_duration(10, 5)
        (False, "结束时间不能小于开始时间")
        >>> validate_duration(-1, 10)
        (False, "开始时间不能为负数")
    """
    # 验证开始时间
    is_valid, error = validate_numeric_range(start, min_val=0, field_name="开始时间")
    if not is_valid:
        return False, error

    # 验证结束时间
    is_valid, error = validate_numeric_range(end, min_val=0, field_name="结束时间")
    if not is_valid:
        return False, error

    # 验证结束时间必须大于开始时间
    if end <= start:
        return False, "结束时间必须大于开始时间"

    # 验证最大时长
    duration = end - start
    if max_duration is not None and duration > max_duration:
        return False, f"时长不能超过{max_duration}秒"

    return True, ""


def validate_material_type(material_type: str) -> Tuple[bool, str]:
    """
    验证素材类型

    Args:
        material_type: 素材类型字符串

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_material_type("video")
        (True, "")
        >>> validate_material_type("audio")
        (True, "")
        >>> validate_material_type("invalid_type")
        (False, "不支持的素材类型: invalid_type")
    """
    if not material_type or not isinstance(material_type, str):
        return False, "素材类型不能为空"

    valid_types = [
        'video',      # 视频
        'audio',      # 音频
        'image',      # 图片
        'text',       # 文本
        'sticker',    # 贴纸
        'effect',     # 特效
        'filter',     # 滤镜
        'transition', # 转场
        'subtitle',   # 字幕
    ]

    material_type = material_type.lower()

    if material_type not in valid_types:
        return False, f"不支持的素材类型: {material_type}，支持的类型: {', '.join(valid_types)}"

    return True, ""


def validate_resolution(width: int, height: int) -> Tuple[bool, str]:
    """
    验证分辨率

    Args:
        width: 宽度（像素）
        height: 高度（像素）

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_resolution(1920, 1080)
        (True, "")
        >>> validate_resolution(-1, 1080)
        (False, "宽度必须是正整数")
        >>> validate_resolution(10000, 10000)
        (False, "分辨率不能超过8K(7680x4320)")
    """
    # 验证宽度
    is_valid, error = validate_numeric_range(width, min_val=1, max_val=7680, field_name="宽度")
    if not is_valid:
        return False, error

    # 验证高度
    is_valid, error = validate_numeric_range(height, min_val=1, max_val=4320, field_name="高度")
    if not is_valid:
        return False, error

    # 常见分辨率验证（可选，用于警告）
    common_resolutions = [
        (1920, 1080),  # 1080p
        (1280, 720),   # 720p
        (3840, 2160),  # 4K
        (2560, 1440),  # 2K
        (1080, 1920),  # 竖屏1080p
        (720, 1280),   # 竖屏720p
    ]

    return True, ""


def validate_batch_limit(count: int, max_count: int = 100) -> Tuple[bool, str]:
    """
    验证批量操作数量限制

    Args:
        count: 操作数量
        max_count: 最大允许数量（默认100）

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_batch_limit(50)
        (True, "")
        >>> validate_batch_limit(150)
        (False, "批量操作数量不能超过100")
    """
    is_valid, error = validate_numeric_range(count, min_val=1, max_val=max_count, field_name="操作数量")
    if not is_valid:
        return False, error

    return True, ""


# ===== 批量验证辅助函数 =====

def validate_required_fields(data: dict, required_fields: List[str]) -> Tuple[bool, str]:
    """
    验证必填字段

    Args:
        data: 数据字典
        required_fields: 必填字段列表

    Returns:
        (是否有效, 错误信息)

    Examples:
        >>> validate_required_fields({"name": "test", "age": 18}, ["name", "age"])
        (True, "")
        >>> validate_required_fields({"name": "test"}, ["name", "age"])
        (False, "缺少必填字段: age")
    """
    if not isinstance(data, dict):
        return False, "数据必须是字典格式"

    missing_fields = [field for field in required_fields if field not in data or data[field] is None]

    if missing_fields:
        return False, f"缺少必填字段: {', '.join(missing_fields)}"

    return True, ""


# ===== 快捷验证装饰器（可选使用） =====

def validate_params(**validators):
    """
    参数验证装饰器

    使用示例:
        @validate_params(draft_id=validate_draft_id, video_url=validate_url)
        def add_video(draft_id, video_url):
            # 函数逻辑
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 这里可以实现参数自动验证逻辑
            # 暂时保留此接口，后续可扩展
            return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == '__main__':
    # 简单测试
    print("=== 验证器测试 ===")

    # 测试draft_id验证
    print("\n1. 测试draft_id验证:")
    test_cases = [
        ("dfd_cat_abc123", True),
        ("", False),
        ("draft@#$", False),
        ("ab", False),
    ]
    for draft_id, expected in test_cases:
        is_valid, error = validate_draft_id(draft_id)
        status = "✓" if is_valid == expected else "✗"
        print(f"  {status} validate_draft_id('{draft_id}'): {is_valid}, {error}")

    # 测试URL验证
    print("\n2. 测试URL验证:")
    test_urls = [
        ("https://example.com/video.mp4", True),
        ("http://localhost:8080/test", False),
        ("http://192.168.1.100/test", False),
        ("ftp://example.com/test", False),
    ]
    for url, expected in test_urls:
        is_valid, error = validate_url(url)
        status = "✓" if is_valid == expected else "✗"
        print(f"  {status} validate_url('{url}'): {is_valid}, {error}")

    # 测试颜色验证
    print("\n3. 测试颜色验证:")
    test_colors = [
        ("#FF5733", True),
        ("rgb(255, 87, 51)", True),
        ("rgba(255, 87, 51, 0.5)", True),
        ("invalid_color", False),
    ]
    for color, expected in test_colors:
        is_valid, error = validate_color(color)
        status = "✓" if is_valid == expected else "✗"
        print(f"  {status} validate_color('{color}'): {is_valid}, {error}")

    print("\n=== 测试完成 ===")
