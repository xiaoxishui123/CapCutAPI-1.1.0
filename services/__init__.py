"""
服务层模块 - 业务逻辑封装

将业务逻辑从Flask路由中分离，提高可测试性和可维护性
"""

from .download_service import DraftDownloadService, get_download_service

__all__ = ['DraftDownloadService', 'get_download_service']
