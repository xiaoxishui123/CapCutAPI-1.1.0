"""
统一错误处理模块

提供：
1. 标准化的错误响应格式
2. 错误码定义
3. Flask全局错误处理器
"""

import logging
from flask import jsonify, request
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# ==================== 错误码定义 ====================

class ErrorCode:
    """错误码枚举类"""

    # 4xxx - 客户端错误
    INVALID_DRAFT_ID = 4000
    DRAFT_NOT_FOUND = 4001
    INVALID_PARAMETER = 4002
    MISSING_PARAMETER = 4003
    FILE_NOT_FOUND = 4004
    PERMISSION_DENIED = 4005
    RATE_LIMIT_EXCEEDED = 4029

    # 5xxx - 服务器错误
    INTERNAL_ERROR = 5000
    OSS_ERROR = 5001
    DATABASE_ERROR = 5002
    AUTO_REGENERATE_FAILED = 5003
    DOWNLOAD_FAILED = 5004


# ==================== 错误类型与消息映射 ====================

ERROR_MESSAGES = {
    # 客户端错误
    ErrorCode.INVALID_DRAFT_ID: {
        'message': '无效的草稿ID',
        'suggestion': '请检查草稿ID格式是否正确'
    },
    ErrorCode.DRAFT_NOT_FOUND: {
        'message': '草稿不存在',
        'suggestion': '请确认草稿ID是否正确，或尝试重新创建草稿'
    },
    ErrorCode.INVALID_PARAMETER: {
        'message': '参数格式错误',
        'suggestion': '请检查请求参数是否符合API规范'
    },
    ErrorCode.MISSING_PARAMETER: {
        'message': '缺少必需参数',
        'suggestion': '请查阅API文档，补充必需参数'
    },
    ErrorCode.FILE_NOT_FOUND: {
        'message': '文件不存在',
        'suggestion': '文件可能已被删除，请尝试重新保存草稿'
    },
    ErrorCode.PERMISSION_DENIED: {
        'message': '权限不足',
        'suggestion': '请联系管理员获取访问权限'
    },
    ErrorCode.RATE_LIMIT_EXCEEDED: {
        'message': '请求过于频繁',
        'suggestion': '请稍后再试，或联系管理员提高限额'
    },

    # 服务器错误
    ErrorCode.INTERNAL_ERROR: {
        'message': '服务器内部错误',
        'suggestion': '请稍后重试，如果问题持续请联系技术支持'
    },
    ErrorCode.OSS_ERROR: {
        'message': 'OSS存储服务错误',
        'suggestion': '云存储服务暂时不可用，请稍后重试'
    },
    ErrorCode.DATABASE_ERROR: {
        'message': '数据库错误',
        'suggestion': '数据服务暂时不可用，请稍后重试'
    },
    ErrorCode.AUTO_REGENERATE_FAILED: {
        'message': '自动修复失败',
        'suggestion': '请尝试手动重新保存草稿'
    },
    ErrorCode.DOWNLOAD_FAILED: {
        'message': '下载失败',
        'suggestion': '请检查网络连接，或稍后重试'
    }
}


# ==================== 标准化错误响应 ====================

class APIError(Exception):
    """API错误基类"""

    def __init__(self, error_code: int, message: str = None,
                 details: Dict = None, http_status: int = None):
        """
        初始化API错误

        Args:
            error_code: 错误码
            message: 自定义错误消息（可选）
            details: 额外的错误详情（可选）
            http_status: HTTP状态码（可选，默认根据error_code推断）
        """
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.http_status = http_status or self._infer_http_status(error_code)

        super().__init__(self.message or self._get_default_message())

    def _infer_http_status(self, error_code: int) -> int:
        """根据错误码推断HTTP状态码"""
        if 4000 <= error_code < 5000:
            # 客户端错误
            if error_code == ErrorCode.DRAFT_NOT_FOUND or error_code == ErrorCode.FILE_NOT_FOUND:
                return 404
            elif error_code == ErrorCode.RATE_LIMIT_EXCEEDED:
                return 429
            elif error_code == ErrorCode.PERMISSION_DENIED:
                return 403
            else:
                return 400
        else:
            # 服务器错误
            return 500

    def _get_default_message(self) -> str:
        """获取默认错误消息"""
        error_info = ERROR_MESSAGES.get(self.error_code)
        return error_info['message'] if error_info else '未知错误'

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        error_info = ERROR_MESSAGES.get(self.error_code, {})

        response = {
            'success': False,
            'error': self.message or error_info.get('message', '未知错误'),
            'error_type': self._get_error_type(),
            'error_code': self.error_code
        }

        # 添加建议
        if 'suggestion' in error_info:
            response['suggestion'] = error_info['suggestion']

        # 添加额外详情
        if self.details:
            response['details'] = self.details

        # 添加请求追踪ID（便于排查问题）
        if hasattr(request, 'id'):
            response['request_id'] = request.id

        return response

    def _get_error_type(self) -> str:
        """获取错误类型名称"""
        for name, code in vars(ErrorCode).items():
            if not name.startswith('_') and code == self.error_code:
                return name
        return 'UNKNOWN_ERROR'


def create_error_response(error_code: int, message: str = None,
                          details: Dict = None, http_status: int = None) -> Tuple[Dict, int]:
    """
    创建标准化错误响应

    Args:
        error_code: 错误码
        message: 自定义错误消息
        details: 错误详情
        http_status: HTTP状态码

    Returns:
        (response_dict, http_status_code)
    """
    error = APIError(error_code, message, details, http_status)
    return jsonify(error.to_dict()), error.http_status


def create_success_response(data: Dict = None, message: str = None) -> Dict:
    """
    创建标准化成功响应

    Args:
        data: 响应数据
        message: 成功消息

    Returns:
        响应字典
    """
    response = {
        'success': True
    }

    if message:
        response['message'] = message

    if data:
        response['data'] = data

    return jsonify(response)


# ==================== Flask全局错误处理器 ====================

def register_error_handlers(app):
    """
    注册Flask全局错误处理器

    使用方法：
        from flask import Flask
        from utils.error_handlers import register_error_handlers

        app = Flask(__name__)
        register_error_handlers(app)

    Args:
        app: Flask应用实例
    """

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        """处理APIError异常"""
        logger.error(f"API错误: {error.error_code} - {error.message}")
        return jsonify(error.to_dict()), error.http_status

    @app.errorhandler(404)
    def handle_not_found(error):
        """处理404错误"""
        logger.warning(f"资源未找到: {request.url}")
        return create_error_response(
            ErrorCode.FILE_NOT_FOUND,
            message='请求的资源不存在',
            details={'path': request.path}
        )

    @app.errorhandler(400)
    def handle_bad_request(error):
        """处理400错误"""
        logger.warning(f"错误的请求: {request.url} - {error}")
        return create_error_response(
            ErrorCode.INVALID_PARAMETER,
            message='请求参数错误',
            details={'error': str(error)}
        )

    @app.errorhandler(403)
    def handle_forbidden(error):
        """处理403错误"""
        logger.warning(f"权限不足: {request.url}")
        return create_error_response(
            ErrorCode.PERMISSION_DENIED,
            message='您没有权限访问此资源'
        )

    @app.errorhandler(429)
    def handle_rate_limit(error):
        """处理429错误"""
        logger.warning(f"限流: {request.remote_addr} - {request.url}")
        return create_error_response(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            message='请求过于频繁，请稍后再试'
        )

    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理500错误"""
        logger.error(f"服务器错误: {error}", exc_info=True)
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            message='服务器内部错误',
            details={'error': str(error)} if app.debug else None
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """处理未捕获的异常"""
        logger.error(f"未捕获的异常: {error}", exc_info=True)

        # 生产环境不暴露详细错误信息
        if app.debug:
            return create_error_response(
                ErrorCode.INTERNAL_ERROR,
                message='发生未预期的错误',
                details={
                    'error': str(error),
                    'type': type(error).__name__
                }
            )
        else:
            return create_error_response(
                ErrorCode.INTERNAL_ERROR,
                message='服务暂时不可用，请稍后重试'
            )

    logger.info("✅ 全局错误处理器已注册")


# ==================== 便捷函数 ====================

def draft_not_found_error(draft_id: str) -> Tuple[Dict, int]:
    """草稿不存在错误"""
    return create_error_response(
        ErrorCode.DRAFT_NOT_FOUND,
        details={'draft_id': draft_id}
    )


def file_not_found_error(filename: str = None) -> Tuple[Dict, int]:
    """文件不存在错误"""
    return create_error_response(
        ErrorCode.FILE_NOT_FOUND,
        details={'filename': filename} if filename else None
    )


def invalid_parameter_error(param_name: str, reason: str = None) -> Tuple[Dict, int]:
    """参数错误"""
    details = {'parameter': param_name}
    if reason:
        details['reason'] = reason

    return create_error_response(
        ErrorCode.INVALID_PARAMETER,
        details=details
    )


def missing_parameter_error(param_name: str) -> Tuple[Dict, int]:
    """缺少参数错误"""
    return create_error_response(
        ErrorCode.MISSING_PARAMETER,
        message=f'缺少必需参数: {param_name}',
        details={'parameter': param_name}
    )


def rate_limit_error(retry_after: int = None) -> Tuple[Dict, int]:
    """限流错误"""
    details = {}
    if retry_after:
        details['retry_after'] = retry_after

    return create_error_response(
        ErrorCode.RATE_LIMIT_EXCEEDED,
        details=details
    )


def oss_error(operation: str, error_details: str = None) -> Tuple[Dict, int]:
    """OSS错误"""
    return create_error_response(
        ErrorCode.OSS_ERROR,
        message=f'OSS {operation} 操作失败',
        details={'error': error_details} if error_details else None
    )


def database_error(operation: str, error_details: str = None) -> Tuple[Dict, int]:
    """数据库错误"""
    return create_error_response(
        ErrorCode.DATABASE_ERROR,
        message=f'数据库 {operation} 操作失败',
        details={'error': error_details} if error_details else None
    )


# ==================== 使用示例 ====================

if __name__ == '__main__':
    """
    错误处理使用示例
    """

    # 示例1：抛出API错误
    try:
        raise APIError(ErrorCode.DRAFT_NOT_FOUND, details={'draft_id': 'test_123'})
    except APIError as e:
        print(e.to_dict())

    # 示例2：使用便捷函数
    response, status_code = draft_not_found_error('test_123')
    print(f"状态码: {status_code}, 响应: {response}")

    # 示例3：创建成功响应
    success_response = create_success_response(
        data={'draft_url': 'https://example.com/draft.zip'},
        message='下载链接生成成功'
    )
    print(success_response)
