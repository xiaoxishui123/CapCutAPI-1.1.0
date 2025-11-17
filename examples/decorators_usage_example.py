"""
装饰器和错误处理使用示例

演示如何在Flask路由中使用新的装饰器和错误处理机制
"""

from flask import Flask, request
from utils import (
    download_decorators,
    require_draft_exists,
    auto_regenerate_on_missing,
    rate_limit,
    log_download,
    create_success_response,
    draft_not_found_error,
    register_error_handlers
)

app = Flask(__name__)

# 注册全局错误处理器
register_error_handlers(app)


# ==================== 示例1：使用单个装饰器 ====================

@app.route('/api/v2/drafts/<draft_id>/info', methods=['GET'])
@require_draft_exists
def get_draft_info(draft_id, materials=None):
    """
    获取草稿信息

    装饰器功能：
    - @require_draft_exists 自动检查草稿是否存在
    - 如果存在，materials会自动注入到函数参数中
    - 如果不存在，自动返回404错误
    """
    return create_success_response(
        data={
            'draft_id': draft_id,
            'materials_count': len(materials),
            'materials': [
                {
                    'type': m.get('type'),
                    'url': m.get('url')
                } for m in materials[:5]  # 只返回前5个
            ]
        },
        message='草稿信息获取成功'
    )


# ==================== 示例2：使用多个装饰器 ====================

@app.route('/api/v2/drafts/<draft_id>/download', methods=['GET'])
@log_download  # 外层：记录下载日志
@rate_limit(max_requests=10, window_seconds=60)  # 中层：限流
@require_draft_exists  # 内层：检查存在性
def download_draft_v2(draft_id, materials=None):
    """
    下载草稿（手动组合装饰器）

    装饰器执行顺序（从外到内）：
    1. log_download - 记录开始时间
    2. rate_limit - 检查是否超过限流
    3. require_draft_exists - 检查草稿是否存在
    4. 执行函数体
    5. rate_limit - 记录本次请求
    6. log_download - 记录结束时间和结果
    """
    from services import get_download_service

    service = get_download_service()
    client_os = request.args.get('client_os', 'windows')
    draft_folder = request.args.get('draft_folder', '')

    return service.stream_download(draft_id, client_os, draft_folder)


# ==================== 示例3：使用组合装饰器 ====================

@app.route('/api/v2/drafts/<draft_id>/download/quick', methods=['GET'])
@download_decorators(
    require_exists=True,     # 检查存在性
    auto_regenerate=True,    # 自动修复
    enable_rate_limit=True,  # 启用限流
    enable_logging=True      # 记录日志
)
def quick_download(draft_id, materials=None):
    """
    快速下载（使用组合装饰器）

    一次性应用所有装饰器，代码更简洁
    """
    from services import get_download_service

    service = get_download_service()
    client_os = request.args.get('client_os', 'windows')
    draft_folder = request.args.get('draft_folder', '')

    return service.stream_download(draft_id, client_os, draft_folder)


# ==================== 示例4：手动使用错误处理 ====================

@app.route('/api/v2/drafts/<draft_id>/delete', methods=['DELETE'])
def delete_draft(draft_id):
    """
    删除草稿（手动错误处理）

    演示如何手动使用错误处理函数
    """
    try:
        from database import get_draft_materials, delete_draft as db_delete_draft

        # 检查草稿是否存在
        materials = get_draft_materials(draft_id)
        if not materials:
            # 使用便捷函数返回错误
            return draft_not_found_error(draft_id)

        # 删除草稿
        success = db_delete_draft(draft_id)

        if not success:
            from utils import create_error_response, ErrorCode
            return create_error_response(
                ErrorCode.DATABASE_ERROR,
                message='删除草稿失败'
            )

        # 返回成功响应
        return create_success_response(
            message=f'草稿 {draft_id} 已删除'
        )

    except Exception as e:
        from utils import create_error_response, ErrorCode
        return create_error_response(
            ErrorCode.INTERNAL_ERROR,
            details={'error': str(e)}
        )


# ==================== 示例5：自定义限流参数 ====================

@app.route('/api/v2/drafts/batch/download', methods=['POST'])
@log_download
@rate_limit(max_requests=3, window_seconds=300)  # 5分钟只能3次
def batch_download():
    """
    批量下载（自定义限流）

    批量操作使用更严格的限流：5分钟3次
    """
    from services import get_download_service
    import json

    data = request.get_json()
    draft_ids = data.get('draft_ids', [])

    if not draft_ids:
        from utils import missing_parameter_error
        return missing_parameter_error('draft_ids')

    if len(draft_ids) > 10:
        from utils import invalid_parameter_error
        return invalid_parameter_error(
            'draft_ids',
            '批量下载最多支持10个草稿'
        )

    service = get_download_service()
    client_os = data.get('client_os', 'windows')
    draft_folder = data.get('draft_folder', '')

    results = service.batch_download(draft_ids, client_os, draft_folder)

    return create_success_response(
        data={'results': results},
        message=f'批量下载完成，成功{len(results)}个'
    )


# ==================== 示例6：无装饰器对比 ====================

@app.route('/api/v2/drafts/<draft_id>/status/legacy', methods=['GET'])
def get_draft_status_legacy(draft_id):
    """
    获取草稿状态（旧方式 - 无装饰器）

    对比：代码冗长，错误处理分散
    """
    try:
        from database import get_draft_materials
        from flask import jsonify

        # 手动验证draft_id
        if not draft_id or not draft_id.strip():
            return jsonify({
                'success': False,
                'error': '草稿ID不能为空'
            }), 400

        # 手动检查草稿存在性
        materials = get_draft_materials(draft_id)
        if not materials:
            return jsonify({
                'success': False,
                'error': '草稿不存在',
                'draft_id': draft_id
            }), 404

        # 手动记录日志
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"获取草稿状态: {draft_id}")

        # 业务逻辑
        return jsonify({
            'success': True,
            'data': {
                'draft_id': draft_id,
                'status': 'completed',
                'materials_count': len(materials)
            }
        })

    except Exception as e:
        # 手动错误处理
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"获取草稿状态失败: {e}", exc_info=True)

        return jsonify({
            'success': False,
            'error': '服务器内部错误'
        }), 500


@app.route('/api/v2/drafts/<draft_id>/status/new', methods=['GET'])
@download_decorators(
    require_exists=True,
    enable_logging=True,
    auto_regenerate=False,  # 状态查询不需要自动修复
    enable_rate_limit=False  # 状态查询不需要限流
)
def get_draft_status_new(draft_id, materials=None):
    """
    获取草稿状态（新方式 - 使用装饰器）

    对比：代码简洁，自动处理常见情况
    """
    return create_success_response(
        data={
            'draft_id': draft_id,
            'status': 'completed',
            'materials_count': len(materials)
        }
    )


# ==================== 对比总结 ====================

"""
代码对比：

旧方式 (get_draft_status_legacy):
- 38行代码
- 手动验证、检查、日志、错误处理
- 代码冗长，重复逻辑多
- 容易遗漏某些检查

新方式 (get_draft_status_new):
- 11行代码 (-71%)
- 装饰器自动处理
- 代码简洁，逻辑清晰
- 标准化，不易出错

性能影响：
- 装饰器开销：< 1ms
- 可忽略不计
"""


if __name__ == '__main__':
    print("=" * 60)
    print("装饰器和错误处理使用示例")
    print("=" * 60)
    print()
    print("运行示例服务器：")
    print("  python examples/decorators_usage_example.py")
    print()
    print("测试端点：")
    print("  curl http://localhost:5000/api/v2/drafts/{draft_id}/info")
    print("  curl http://localhost:5000/api/v2/drafts/{draft_id}/download")
    print("  curl http://localhost:5000/api/v2/drafts/{draft_id}/status/new")
    print()
    print("对比新旧方式：")
    print("  旧: curl http://localhost:5000/api/v2/drafts/{draft_id}/status/legacy")
    print("  新: curl http://localhost:5000/api/v2/drafts/{draft_id}/status/new")
    print("=" * 60)

    # 启动测试服务器
    # app.run(debug=True, port=5000)
