"""
Flask装饰器模块 - 提供通用的装饰器功能

包含：
1. @require_draft_exists - 确保草稿存在
2. @auto_regenerate_on_missing - 自动修复缺失文件
3. @rate_limit - 下载限流
4. @log_download - 下载日志记录
"""

import logging
import time
from functools import wraps
from flask import request, jsonify, make_response
from typing import Callable

logger = logging.getLogger(__name__)

# 简单的内存限流器（生产环境建议使用Redis）
_rate_limiter = {}
_rate_limit_window = 60  # 秒


def require_draft_exists(f: Callable) -> Callable:
    """
    装饰器：确保草稿存在

    使用方法：
        @app.route('/api/drafts/<draft_id>')
        @require_draft_exists
        def download_draft(draft_id):
            # draft_id对应的草稿肯定存在
            ...

    Args:
        f: 被装饰的函数

    Returns:
        包装后的函数
    """
    @wraps(f)
    def wrapper(draft_id, *args, **kwargs):
        try:
            from database import get_draft_materials

            # 检查草稿是否存在
            materials = get_draft_materials(draft_id)
            if not materials:
                logger.warning(f"草稿不存在: {draft_id}")
                return jsonify({
                    'success': False,
                    'error': '草稿不存在',
                    'error_type': 'DRAFT_NOT_FOUND',
                    'error_code': 1001,
                    'draft_id': draft_id,
                    'suggestion': '请检查草稿ID是否正确'
                }), 404

            # 草稿存在，将materials作为关键字参数传递
            kwargs['materials'] = materials
            return f(draft_id, *args, **kwargs)

        except Exception as e:
            logger.error(f"检查草稿存在性失败: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': '检查草稿状态失败',
                'error_type': 'INTERNAL_ERROR',
                'error_code': 5000,
                'details': str(e)
            }), 500

    return wrapper


def auto_regenerate_on_missing(f: Callable) -> Callable:
    """
    装饰器：文件缺失时自动重新生成

    使用方法：
        @app.route('/api/drafts/download/<draft_id>')
        @auto_regenerate_on_missing
        def download_draft(draft_id):
            ...

    当检测到OSS文件不存在时，自动触发重新生成并重试

    Args:
        f: 被装饰的函数

    Returns:
        包装后的函数
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            # 第一次尝试
            return f(*args, **kwargs)
        except Exception as e:
            error_str = str(e)

            # 检查是否是文件不存在错误
            is_file_missing = any(keyword in error_str for keyword in [
                '基础草稿文件不存在',
                'NoSuchKey',
                'FileNotFoundError',
                'does not exist'
            ])

            if not is_file_missing:
                # 不是文件缺失错误，直接抛出
                raise

            # 尝试自动修复
            logger.warning(f"[自动修复] 检测到文件缺失，尝试重新生成")

            try:
                # 提取draft_id（可能在args或kwargs中）
                draft_id = None
                if args and len(args) > 0:
                    draft_id = args[0]
                elif 'draft_id' in kwargs:
                    draft_id = kwargs['draft_id']

                if not draft_id:
                    logger.error("[自动修复] 无法提取draft_id")
                    raise

                # 获取草稿材料
                from database import get_draft_materials
                materials = get_draft_materials(draft_id)

                if not materials:
                    logger.error(f"[自动修复] 草稿材料不存在: {draft_id}")
                    raise

                # 重新生成草稿
                from save_draft_impl import regenerate_and_upload_draft
                logger.info(f"[自动修复] 开始重新生成草稿: {draft_id}")

                result = regenerate_and_upload_draft(draft_id, materials)

                if not result.get('success'):
                    logger.error(f"[自动修复] 重新生成失败: {result.get('error')}")
                    raise

                logger.info(f"[自动修复] 草稿重新生成成功: {draft_id}")

                # 等待上传完成
                time.sleep(3)

                # 重试原函数
                return f(*args, **kwargs)

            except Exception as regen_error:
                logger.error(f"[自动修复] 修复失败: {regen_error}", exc_info=True)
                # 修复失败，返回友好错误
                return jsonify({
                    'success': False,
                    'error': '草稿文件不存在且自动修复失败',
                    'error_type': 'AUTO_REGENERATE_FAILED',
                    'error_code': 4001,
                    'suggestion': '请尝试重新保存草稿，或联系管理员'
                }), 500

    return wrapper


def rate_limit(max_requests: int = 10, window_seconds: int = 60) -> Callable:
    """
    装饰器：限制下载频率

    使用方法：
        @app.route('/api/drafts/download/<draft_id>')
        @rate_limit(max_requests=10, window_seconds=60)
        def download_draft(draft_id):
            ...

    Args:
        max_requests: 时间窗口内最大请求数
        window_seconds: 时间窗口大小（秒）

    Returns:
        装饰器函数
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 获取客户端标识（IP地址）
            client_id = request.remote_addr

            # 获取当前时间
            current_time = time.time()

            # 清理过期记录
            if client_id in _rate_limiter:
                _rate_limiter[client_id] = [
                    t for t in _rate_limiter[client_id]
                    if current_time - t < window_seconds
                ]
            else:
                _rate_limiter[client_id] = []

            # 检查是否超过限制
            if len(_rate_limiter[client_id]) >= max_requests:
                logger.warning(f"[限流] 客户端 {client_id} 超过限制: {max_requests}/{window_seconds}s")
                return jsonify({
                    'success': False,
                    'error': '请求过于频繁，请稍后再试',
                    'error_type': 'RATE_LIMIT_EXCEEDED',
                    'error_code': 4029,
                    'max_requests': max_requests,
                    'window_seconds': window_seconds,
                    'retry_after': int(window_seconds - (current_time - _rate_limiter[client_id][0]))
                }), 429

            # 记录本次请求
            _rate_limiter[client_id].append(current_time)

            # 执行原函数
            return f(*args, **kwargs)

        return wrapper

    return decorator


def log_download(f: Callable) -> Callable:
    """
    装饰器：记录下载操作日志

    使用方法：
        @app.route('/api/drafts/download/<draft_id>')
        @log_download
        def download_draft(draft_id):
            ...

    记录内容：
    - 草稿ID
    - 客户端IP
    - 下载时间
    - 客户端OS
    - 是否成功
    - 响应时间

    Args:
        f: 被装饰的函数

    Returns:
        包装后的函数
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        # 提取draft_id
        draft_id = None
        if args and len(args) > 0:
            draft_id = args[0]
        elif 'draft_id' in kwargs:
            draft_id = kwargs['draft_id']

        # 提取请求信息
        client_ip = request.remote_addr
        client_os = request.args.get('client_os', 'unknown')
        user_agent = request.headers.get('User-Agent', 'unknown')

        # 记录开始日志
        logger.info(f"[下载开始] draft_id={draft_id}, client_ip={client_ip}, client_os={client_os}")

        try:
            # 执行原函数
            response = f(*args, **kwargs)

            # 计算响应时间
            elapsed_time = time.time() - start_time

            # 判断是否成功
            success = True
            status_code = 200

            if isinstance(response, tuple):
                _, status_code = response
                success = status_code < 400

            # 记录成功日志
            logger.info(
                f"[下载完成] draft_id={draft_id}, "
                f"status={status_code}, "
                f"elapsed={elapsed_time:.2f}s, "
                f"success={success}"
            )

            # TODO: 将下载记录保存到数据库
            # _save_download_record(draft_id, client_ip, client_os, success, elapsed_time)

            return response

        except Exception as e:
            # 计算响应时间
            elapsed_time = time.time() - start_time

            # 记录失败日志
            logger.error(
                f"[下载失败] draft_id={draft_id}, "
                f"elapsed={elapsed_time:.2f}s, "
                f"error={str(e)}"
            )

            # TODO: 保存失败记录
            # _save_download_record(draft_id, client_ip, client_os, False, elapsed_time, str(e))

            # 重新抛出异常
            raise

    return wrapper


def validate_draft_id(f: Callable) -> Callable:
    """
    装饰器：验证draft_id格式

    使用方法：
        @app.route('/api/drafts/<draft_id>')
        @validate_draft_id
        def get_draft(draft_id):
            ...

    Args:
        f: 被装饰的函数

    Returns:
        包装后的函数
    """
    @wraps(f)
    def wrapper(draft_id, *args, **kwargs):
        # 验证draft_id不为空
        if not draft_id or not draft_id.strip():
            return jsonify({
                'success': False,
                'error': '草稿ID不能为空',
                'error_type': 'INVALID_DRAFT_ID',
                'error_code': 4000
            }), 400

        # 验证draft_id格式（可根据实际需求调整）
        # 例如：dfd_cat_1763382269_293b5e69
        if len(draft_id) > 100:
            return jsonify({
                'success': False,
                'error': '草稿ID长度超过限制',
                'error_type': 'INVALID_DRAFT_ID',
                'error_code': 4000
            }), 400

        # 执行原函数
        return f(draft_id, *args, **kwargs)

    return wrapper


# 可以组合使用装饰器
def download_decorators(
    require_exists: bool = True,
    auto_regenerate: bool = True,
    enable_rate_limit: bool = True,
    enable_logging: bool = True
) -> Callable:
    """
    组合装饰器：一次性应用多个装饰器

    使用方法：
        @app.route('/api/drafts/download/<draft_id>')
        @download_decorators(require_exists=True, auto_regenerate=True)
        def download_draft(draft_id, materials=None):
            ...

    Args:
        require_exists: 是否检查草稿存在
        auto_regenerate: 是否自动修复
        enable_rate_limit: 是否启用限流
        enable_logging: 是否记录日志

    Returns:
        装饰器函数
    """
    def decorator(f: Callable) -> Callable:
        # 从内到外应用装饰器
        decorated_func = f

        if enable_logging:
            decorated_func = log_download(decorated_func)

        if enable_rate_limit:
            decorated_func = rate_limit()(decorated_func)

        if auto_regenerate:
            decorated_func = auto_regenerate_on_missing(decorated_func)

        if require_exists:
            decorated_func = require_draft_exists(decorated_func)

        decorated_func = validate_draft_id(decorated_func)

        return decorated_func

    return decorator


def deprecated_endpoint(new_endpoint: str = None, sunset_date: str = None) -> Callable:
    """
    装饰器：标记端点已废弃

    使用方法：
        @app.route('/old/endpoint')
        @deprecated_endpoint(
            new_endpoint='/api/v2/new/endpoint',
            sunset_date='2025-02-15'
        )
        def old_endpoint():
            ...

    功能：
    - 在响应头中添加废弃警告
    - 记录废弃警告日志
    - 提示迁移到新端点

    Args:
        new_endpoint: 新的替代端点路径
        sunset_date: 端点下线日期（YYYY-MM-DD）

    Returns:
        装饰器函数
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 记录废弃警告
            endpoint_name = f.__name__
            warning_msg = f"[DEPRECATED] 端点 {endpoint_name} 已废弃"

            if new_endpoint:
                warning_msg += f"，请迁移到 {new_endpoint}"
            if sunset_date:
                warning_msg += f"，将于 {sunset_date} 下线"

            logger.warning(warning_msg)

            # 执行原函数
            response = f(*args, **kwargs)

            # 如果响应是 tuple (通常是 jsonify 返回的)
            if isinstance(response, tuple):
                json_response, status_code = response
                flask_response = make_response(json_response, status_code)
            else:
                flask_response = make_response(response)

            # 添加废弃警告头
            flask_response.headers['X-API-Deprecated'] = 'true'
            flask_response.headers['X-API-Deprecation-Info'] = warning_msg

            if new_endpoint:
                flask_response.headers['X-API-Alternative'] = new_endpoint
            if sunset_date:
                flask_response.headers['X-API-Sunset'] = sunset_date

            # 在响应体中也添加警告（如果是 JSON 响应）
            if flask_response.is_json:
                data = flask_response.get_json()
                if isinstance(data, dict):
                    data['_deprecation_warning'] = {
                        'message': warning_msg,
                        'deprecated': True,
                        'alternative': new_endpoint,
                        'sunset_date': sunset_date
                    }
                    flask_response.set_data(flask_response.get_json().__class__.__name__)
                    import json
                    flask_response.data = json.dumps(data, ensure_ascii=False)

            return flask_response

        return wrapper

    return decorator


# 示例使用
if __name__ == '__main__':
    """
    装饰器使用示例
    """

    # 示例1：单个装饰器
    @require_draft_exists
    def example1(draft_id, materials=None):
        print(f"处理草稿: {draft_id}, 材料数: {len(materials)}")

    # 示例2：组合装饰器
    @download_decorators(
        require_exists=True,
        auto_regenerate=True,
        enable_rate_limit=True,
        enable_logging=True
    )
    def example2(draft_id, materials=None):
        print(f"下载草稿: {draft_id}")

    # 示例3：自定义组合
    @log_download
    @rate_limit(max_requests=5, window_seconds=30)
    @require_draft_exists
    def example3(draft_id, materials=None):
        print(f"高频下载: {draft_id}")
