"""
工具模块包

包含：
- decorators: Flask装饰器
- error_handlers: 统一错误处理
"""

from .decorators import (
    require_draft_exists,
    auto_regenerate_on_missing,
    rate_limit,
    log_download,
    validate_draft_id,
    download_decorators,
    deprecated_endpoint
)

from .error_handlers import (
    APIError,
    ErrorCode,
    create_error_response,
    create_success_response,
    register_error_handlers,
    # 便捷函数
    draft_not_found_error,
    file_not_found_error,
    invalid_parameter_error,
    missing_parameter_error,
    rate_limit_error,
    oss_error,
    database_error
)

__all__ = [
    # 装饰器
    'require_draft_exists',
    'auto_regenerate_on_missing',
    'rate_limit',
    'log_download',
    'validate_draft_id',
    'download_decorators',
    'deprecated_endpoint',

    # 错误处理
    'APIError',
    'ErrorCode',
    'create_error_response',
    'create_success_response',
    'register_error_handlers',

    # 便捷错误函数
    'draft_not_found_error',
    'file_not_found_error',
    'invalid_parameter_error',
    'missing_parameter_error',
    'rate_limit_error',
    'oss_error',
    'database_error',
]
