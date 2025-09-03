#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作系统路径配置模块
用于检测操作系统类型并提供相应的默认草稿路径配置
"""

import os
import platform
import json
from typing import Dict, Optional


class OSPathConfig:
    """
    操作系统路径配置类
    负责检测操作系统类型并管理不同平台的默认草稿路径
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        初始化操作系统路径配置
        
        Args:
            config_file (str): 配置文件路径，默认为 config.json
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.os_type = self._detect_os_type()
    
    def _load_config(self) -> Dict:
        """
        加载配置文件
        
        Returns:
            Dict: 配置字典
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，返回默认配置
            return self._get_default_config()
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    def _get_default_config(self) -> Dict:
        """
        获取默认配置
        
        Returns:
            Dict: 默认配置字典
        """
        return {
            "draft_paths": {
                "windows": "F:/jianyin/cgwz/JianyingPro Drafts",
                "linux": "/data/jianying/drafts",
                "darwin": "/Users/Shared/JianyingPro Drafts"
            }
        }
    
    def _detect_os_type(self) -> str:
        """
        检测当前操作系统类型
        
        Returns:
            str: 操作系统类型 ('windows', 'linux', 'darwin')
        """
        system = platform.system().lower()
        
        # 标准化操作系统名称
        if system == 'windows':
            return 'windows'
        elif system == 'linux':
            return 'linux'
        elif system == 'darwin':  # macOS
            return 'darwin'
        else:
            # 对于未知系统，默认使用 linux 配置
            return 'linux'
    
    def get_default_draft_path(self, os_type: Optional[str] = None) -> str:
        """
        获取指定操作系统的默认草稿路径
        
        Args:
            os_type (Optional[str]): 操作系统类型，如果为 None 则使用当前系统
        
        Returns:
            str: 默认草稿路径
        """
        if os_type is None:
            os_type = self.os_type
        
        # 从配置中获取路径
        draft_paths = self.config.get('draft_paths', {})
        
        # 如果指定的操作系统类型存在配置，则返回对应路径
        if os_type in draft_paths:
            return draft_paths[os_type]
        
        # 如果没有找到对应配置，返回默认路径
        default_paths = self._get_default_config()['draft_paths']
        return default_paths.get(os_type, default_paths['linux'])
    
    def get_current_os_draft_path(self) -> str:
        """
        获取当前操作系统的默认草稿路径
        
        Returns:
            str: 当前操作系统的默认草稿路径
        """
        return self.get_default_draft_path()
    
    def set_draft_path(self, os_type: str, path: str) -> bool:
        """
        设置指定操作系统的草稿路径
        
        Args:
            os_type (str): 操作系统类型
            path (str): 草稿路径
        
        Returns:
            bool: 设置是否成功
        """
        try:
            # 确保 draft_paths 配置存在
            if 'draft_paths' not in self.config:
                self.config['draft_paths'] = {}
            
            # 设置路径
            self.config['draft_paths'][os_type] = path
            
            # 保存配置到文件
            return self._save_config()
        except Exception as e:
            print(f"设置草稿路径失败: {e}")
            return False
    
    def _save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_all_draft_paths(self) -> Dict[str, str]:
        """
        获取所有操作系统的草稿路径配置
        
        Returns:
            Dict[str, str]: 所有操作系统的草稿路径字典
        """
        return self.config.get('draft_paths', self._get_default_config()['draft_paths'])
    
    def get_os_info(self) -> Dict[str, str]:
        """
        获取当前操作系统信息
        
        Returns:
            Dict[str, str]: 操作系统信息字典
        """
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'detected_type': self.os_type,
            'default_draft_path': self.get_current_os_draft_path()
        }
    
    def validate_path(self, path: str) -> bool:
        """
        验证路径是否有效
        
        Args:
            path (str): 要验证的路径
        
        Returns:
            bool: 路径是否有效
        """
        try:
            # 检查路径格式是否正确
            if not path or not isinstance(path, str):
                return False
            
            # 对于 Windows 路径，检查是否包含盘符
            if self.os_type == 'windows' and ':' not in path:
                return False
            
            # 尝试创建目录（如果不存在）
            os.makedirs(path, exist_ok=True)
            
            # 检查是否可写
            return os.access(path, os.W_OK)
        except Exception:
            return False


# 全局实例
_os_path_config = None


def get_os_path_config() -> OSPathConfig:
    """
    获取全局操作系统路径配置实例
    
    Returns:
        OSPathConfig: 操作系统路径配置实例
    """
    global _os_path_config
    if _os_path_config is None:
        _os_path_config = OSPathConfig()
    return _os_path_config


def get_default_draft_path(os_type: Optional[str] = None) -> str:
    """
    快捷函数：获取默认草稿路径
    
    Args:
        os_type (Optional[str]): 操作系统类型
    
    Returns:
        str: 默认草稿路径
    """
    return get_os_path_config().get_default_draft_path(os_type)


def get_current_os_type() -> str:
    """
    快捷函数：获取当前操作系统类型
    
    Returns:
        str: 当前操作系统类型
    """
    return get_os_path_config().os_type


if __name__ == "__main__":
    # 测试代码
    config = OSPathConfig()
    print(f"当前操作系统: {config.os_type}")
    print(f"默认草稿路径: {config.get_current_os_draft_path()}")
    print(f"所有路径配置: {config.get_all_draft_paths()}")
    print(f"系统信息: {config.get_os_info()}")