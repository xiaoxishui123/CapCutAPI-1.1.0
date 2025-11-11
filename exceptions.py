#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义异常类模块

提供统一的异常处理机制,用于规范API错误响应格式

作者: CapCutAPI Team
创建时间: 2025-11-11
"""

from typing import Optional, Dict, Any


class CapCutAPIException(Exception):
    """
    CapCut API基础异常类

    所有自定义异常的基类,提供统一的错误处理接口
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            status_code: HTTP状态码
            details: 额外的错误详情
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典格式(用于JSON响应)

        Returns:
            包含错误信息的字典
        """
        return {
            'success': False,
            'error': self.message,
            'error_type': self.__class__.__name__,
            'status_code': self.status_code,
            'details': self.details
        }


# ===== 资源相关异常 =====

class ResourceNotFoundException(CapCutAPIException):
    """资源未找到异常"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type}未找到: {resource_id}",
            status_code=404,
            details={
                'resource_type': resource_type,
                'resource_id': resource_id
            }
        )


class DraftNotFoundException(ResourceNotFoundException):
    """草稿未找到异常"""

    def __init__(self, draft_id: str):
        super().__init__(
            resource_type='草稿',
            resource_id=draft_id
        )


class MaterialNotFoundException(ResourceNotFoundException):
    """素材未找到异常"""

    def __init__(self, material_id: str):
        super().__init__(
            resource_type='素材',
            resource_id=material_id
        )


# ===== 验证相关异常 =====

class ValidationException(CapCutAPIException):
    """验证异常基类"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=400,
            details={'field': field} if field else {}
        )


class InvalidInputException(ValidationException):
    """无效输入异常"""
    pass


class MissingRequiredFieldException(ValidationException):
    """缺少必填字段异常"""

    def __init__(self, field_name: str):
        super().__init__(
            message=f"缺少必填字段: {field_name}",
            field=field_name
        )


class InvalidURLException(ValidationException):
    """无效URL异常"""

    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"无效的URL: {reason}",
            field='url'
        )
        self.details['url'] = url
        self.details['reason'] = reason


class InvalidDraftIDException(ValidationException):
    """无效草稿ID异常"""

    def __init__(self, draft_id: str, reason: str):
        super().__init__(
            message=f"无效的草稿ID: {reason}",
            field='draft_id'
        )
        self.details['draft_id'] = draft_id


# ===== 存储相关异常 =====

class StorageException(CapCutAPIException):
    """存储异常基类"""

    def __init__(self, message: str, storage_type: str = 'unknown'):
        super().__init__(
            message=message,
            status_code=500,
            details={'storage_type': storage_type}
        )


class OSSUploadException(StorageException):
    """OSS上传异常"""

    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(
            message=f"OSS上传失败: {message}",
            storage_type='oss'
        )
        if file_path:
            self.details['file_path'] = file_path


class OSSDownloadException(StorageException):
    """OSS下载异常"""

    def __init__(self, message: str, file_url: Optional[str] = None):
        super().__init__(
            message=f"OSS下载失败: {message}",
            storage_type='oss'
        )
        if file_url:
            self.details['file_url'] = file_url


class DatabaseException(StorageException):
    """数据库异常"""

    def __init__(self, message: str, query: Optional[str] = None):
        super().__init__(
            message=f"数据库操作失败: {message}",
            storage_type='database'
        )
        if query:
            self.details['query'] = query


# ===== 业务逻辑异常 =====

class BusinessLogicException(CapCutAPIException):
    """业务逻辑异常基类"""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=422  # Unprocessable Entity
        )


class DraftAlreadyExistsException(BusinessLogicException):
    """草稿已存在异常"""

    def __init__(self, draft_id: str):
        super().__init__(
            message=f"草稿已存在: {draft_id}"
        )
        self.details['draft_id'] = draft_id


class InvalidOperationException(BusinessLogicException):
    """无效操作异常"""
    pass


class MaterialProcessingException(BusinessLogicException):
    """素材处理异常"""

    def __init__(self, message: str, material_type: Optional[str] = None):
        super().__init__(message=message)
        if material_type:
            self.details['material_type'] = material_type


# ===== 外部服务异常 =====

class ExternalServiceException(CapCutAPIException):
    """外部服务异常"""

    def __init__(self, service_name: str, message: str):
        super().__init__(
            message=f"{service_name}服务错误: {message}",
            status_code=502  # Bad Gateway
        )
        self.details['service_name'] = service_name


class DownloadException(ExternalServiceException):
    """下载异常"""

    def __init__(self, url: str, reason: str):
        super().__init__(
            service_name='下载服务',
            message=reason
        )
        self.details['url'] = url


class NetworkException(ExternalServiceException):
    """网络异常"""

    def __init__(self, message: str):
        super().__init__(
            service_name='网络',
            message=message
        )


# ===== 配置相关异常 =====

class ConfigurationException(CapCutAPIException):
    """配置异常"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=f"配置错误: {message}",
            status_code=500
        )
        if config_key:
            self.details['config_key'] = config_key


class MissingConfigException(ConfigurationException):
    """缺少配置异常"""

    def __init__(self, config_key: str):
        super().__init__(
            message=f"缺少必需的配置项",
            config_key=config_key
        )


# ===== 权限相关异常 =====

class PermissionException(CapCutAPIException):
    """权限异常"""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=403  # Forbidden
        )


class UnauthorizedException(CapCutAPIException):
    """未授权异常"""

    def __init__(self, message: str = "未授权访问"):
        super().__init__(
            message=message,
            status_code=401  # Unauthorized
        )


# ===== 速率限制异常 =====

class RateLimitException(CapCutAPIException):
    """速率限制异常"""

    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(
            message=message,
            status_code=429  # Too Many Requests
        )


# ===== 超时异常 =====

class TimeoutException(CapCutAPIException):
    """超时异常"""

    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            message=f"{operation}超时 ({timeout_seconds}秒)",
            status_code=504  # Gateway Timeout
        )
        self.details['operation'] = operation
        self.details['timeout_seconds'] = timeout_seconds


# ===== 辅助函数 =====

def handle_exception(exception: Exception) -> Dict[str, Any]:
    """
    统一的异常处理函数

    Args:
        exception: 异常对象

    Returns:
        标准化的错误响应字典
    """
    if isinstance(exception, CapCutAPIException):
        return exception.to_dict()

    # 处理其他Python标准异常
    return {
        'success': False,
        'error': str(exception),
        'error_type': exception.__class__.__name__,
        'status_code': 500
    }


def get_status_code(exception: Exception) -> int:
    """
    获取异常对应的HTTP状态码

    Args:
        exception: 异常对象

    Returns:
        HTTP状态码
    """
    if isinstance(exception, CapCutAPIException):
        return exception.status_code
    return 500


if __name__ == '__main__':
    # 简单测试
    print("=== 异常类测试 ===\n")

    # 测试各种异常
    exceptions = [
        DraftNotFoundException('draft_123'),
        InvalidInputException('无效的输入', field='draft_id'),
        OSSUploadException('网络错误', file_path='/path/to/file'),
        BusinessLogicException('业务规则违反'),
        TimeoutException('上传操作', 30),
    ]

    for exc in exceptions:
        print(f"异常类型: {exc.__class__.__name__}")
        print(f"错误消息: {exc.message}")
        print(f"HTTP状态码: {exc.status_code}")
        print(f"JSON格式: {exc.to_dict()}")
        print("-" * 60)

    print("\n=== 测试完成 ===")
