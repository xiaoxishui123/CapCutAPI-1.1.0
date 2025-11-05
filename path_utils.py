"""
路径处理工具模块
Path Utils Module

功能说明：
- 支持相对路径转换为绝对路径
- 支持Windows和Linux路径格式
- 自动识别路径类型
- 路径规范化和验证

作者：CapCutAPI Team
版本：1.0.0
"""

import os
import re
import logging
from typing import Union, Optional

logger = logging.getLogger('path_utils')


def is_windows_path(path: str) -> bool:
    """
    判断是否为Windows路径格式
    
    Args:
        path: 路径字符串
        
    Returns:
        bool: True表示是Windows路径，False表示不是
        
    示例：
        >>> is_windows_path("C:\\Users\\test")
        True
        >>> is_windows_path("/home/user/test")
        False
    """
    if not path:
        return False
    
    # 检查是否包含Windows盘符（如 C:, D:）
    if re.match(r'^[a-zA-Z]:', path):
        return True
    
    # 检查是否使用反斜杠作为分隔符
    if '\\' in path and '/' not in path:
        return True
    
    return False


def is_absolute_path(path: str) -> bool:
    """
    判断是否为绝对路径
    
    Args:
        path: 路径字符串
        
    Returns:
        bool: True表示是绝对路径，False表示是相对路径
        
    示例：
        >>> is_absolute_path("/home/user/test")
        True
        >>> is_absolute_path("./downloads/test")
        False
        >>> is_absolute_path("C:\\Users\\test")
        True
    """
    if not path:
        return False
    
    # Windows绝对路径：以盘符开头（如 C:）
    if is_windows_path(path):
        return re.match(r'^[a-zA-Z]:[/\\]', path) is not None
    
    # Linux/Unix绝对路径：以 / 开头
    return path.startswith('/')


def normalize_path(path: str, base_dir: Optional[str] = None) -> str:
    """
    规范化路径，支持相对路径转绝对路径
    
    功能说明：
    1. 如果是相对路径，转换为基于base_dir的绝对路径
    2. 如果是绝对路径，直接规范化
    3. 处理路径分隔符，统一格式
    4. 展开波浪号 (~) 为用户主目录
    
    Args:
        path: 需要规范化的路径
        base_dir: 基准目录，默认为当前工作目录
        
    Returns:
        str: 规范化后的绝对路径
        
    示例：
        >>> normalize_path("./downloads")
        '/home/CapCutAPI-1.1.0/downloads'
        >>> normalize_path("../data")
        '/home/data'
        >>> normalize_path("/absolute/path")
        '/absolute/path'
    """
    if not path:
        logger.warning("传入的路径为空，使用当前目录")
        return os.getcwd()
    
    # 去除首尾空格
    path = path.strip()
    
    # 展开用户主目录（~）
    if path.startswith('~'):
        path = os.path.expanduser(path)
        logger.info(f"展开用户主目录: {path}")
    
    # 如果没有提供基准目录，使用当前工作目录
    if base_dir is None:
        base_dir = os.getcwd()
        logger.debug(f"使用当前工作目录作为基准: {base_dir}")
    
    # 如果是绝对路径，直接规范化
    if is_absolute_path(path):
        normalized = os.path.abspath(path)
        logger.debug(f"绝对路径规范化: {path} -> {normalized}")
        return normalized
    
    # 相对路径：基于base_dir转换为绝对路径
    # 首先将路径与base_dir连接
    full_path = os.path.join(base_dir, path)
    
    # 然后规范化（处理 . 和 .. 等）
    normalized = os.path.abspath(full_path)
    
    logger.info(f"相对路径转换: {path} (基于 {base_dir}) -> {normalized}")
    
    return normalized


def ensure_directory_exists(path: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        bool: True表示目录存在或创建成功，False表示创建失败
        
    示例：
        >>> ensure_directory_exists("./downloads/drafts")
        True
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            logger.info(f"创建目录: {path}")
        return True
    except Exception as e:
        logger.error(f"创建目录失败: {path}, 错误: {e}")
        return False


def validate_path(path: str, must_exist: bool = False, must_be_dir: bool = False) -> tuple:
    """
    验证路径的有效性
    
    Args:
        path: 需要验证的路径
        must_exist: 是否必须存在
        must_be_dir: 是否必须是目录
        
    Returns:
        tuple: (is_valid, error_message)
        
    示例：
        >>> validate_path("/home/user/test", must_exist=True)
        (False, "路径不存在: /home/user/test")
    """
    if not path:
        return False, "路径为空"
    
    # 规范化路径
    try:
        normalized_path = normalize_path(path)
    except Exception as e:
        return False, f"路径格式错误: {e}"
    
    # 检查是否必须存在
    if must_exist and not os.path.exists(normalized_path):
        return False, f"路径不存在: {normalized_path}"
    
    # 检查是否必须是目录
    if must_be_dir and os.path.exists(normalized_path) and not os.path.isdir(normalized_path):
        return False, f"路径不是目录: {normalized_path}"
    
    return True, ""


def get_relative_path(target_path: str, base_path: str) -> str:
    """
    获取从base_path到target_path的相对路径
    
    Args:
        target_path: 目标路径
        base_path: 基准路径
        
    Returns:
        str: 相对路径
        
    示例：
        >>> get_relative_path("/home/user/data", "/home/user")
        'data'
    """
    try:
        return os.path.relpath(target_path, base_path)
    except Exception as e:
        logger.error(f"获取相对路径失败: target={target_path}, base={base_path}, 错误={e}")
        return target_path


def convert_to_windows_path(linux_path: str) -> str:
    """
    将Linux路径格式转换为Windows路径格式
    
    Args:
        linux_path: Linux格式路径
        
    Returns:
        str: Windows格式路径
        
    注意：此函数仅转换路径分隔符，不处理盘符映射
    
    示例：
        >>> convert_to_windows_path("/home/user/data")
        "\\home\\user\\data"
    """
    if not linux_path:
        return linux_path
    
    # 替换路径分隔符
    windows_path = linux_path.replace('/', '\\')
    
    logger.debug(f"路径格式转换 (Linux -> Windows): {linux_path} -> {windows_path}")
    
    return windows_path


def convert_to_linux_path(windows_path: str) -> str:
    """
    将Windows路径格式转换为Linux路径格式
    
    Args:
        windows_path: Windows格式路径
        
    Returns:
        str: Linux格式路径
        
    注意：此函数仅转换路径分隔符，不处理盘符映射
    
    示例：
        >>> convert_to_linux_path("C:\\Users\\test")
        "C:/Users/test"
    """
    if not windows_path:
        return windows_path
    
    # 替换路径分隔符
    linux_path = windows_path.replace('\\', '/')
    
    logger.debug(f"路径格式转换 (Windows -> Linux): {windows_path} -> {linux_path}")
    
    return linux_path


def safe_join(*paths) -> str:
    """
    安全地连接多个路径片段
    
    Args:
        *paths: 多个路径片段
        
    Returns:
        str: 连接后的完整路径
        
    示例：
        >>> safe_join("/home", "user", "data")
        '/home/user/data'
    """
    if not paths:
        return ""
    
    # 过滤空值
    valid_paths = [p for p in paths if p]
    
    if not valid_paths:
        return ""
    
    # 连接路径
    result = os.path.join(*valid_paths)
    
    # 规范化
    return os.path.normpath(result)


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("路径工具模块测试")
    print("=" * 60)
    
    # 测试相对路径转换
    print("\n1. 测试相对路径转换：")
    test_paths = [
        "./downloads",
        "../data",
        "~/documents",
        "/absolute/path",
        "relative/path/to/file"
    ]
    
    for test_path in test_paths:
        result = normalize_path(test_path)
        print(f"  {test_path:30s} -> {result}")
    
    # 测试路径验证
    print("\n2. 测试路径验证：")
    valid, msg = validate_path("./downloads", must_exist=False)
    print(f"  验证 './downloads': valid={valid}, msg={msg}")
    
    # 测试Windows路径判断
    print("\n3. 测试Windows路径判断：")
    windows_paths = [
        "C:\\Users\\test",
        "F:\\jianying\\cgwz",
        "/home/user/test",
        "./relative/path"
    ]
    
    for path in windows_paths:
        is_win = is_windows_path(path)
        print(f"  {path:30s} -> Windows路径: {is_win}")
    
    # 测试路径格式转换
    print("\n4. 测试路径格式转换：")
    print(f"  Linux -> Windows: /home/user/data -> {convert_to_windows_path('/home/user/data')}")
    windows_test_path = 'C:\\Users\\test'
    print(f"  Windows -> Linux: {windows_test_path} -> {convert_to_linux_path(windows_test_path)}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

