"""
草稿下载服务类 - 统一管理所有下载逻辑

职责：
1. 生成下载链接（OSS/本地）
2. 流式下载文件
3. 批量下载处理
4. 自动修复机制
5. 草稿状态检查
"""

import logging
import time
from typing import Dict, List, Tuple, Optional
from flask import Response
import requests

logger = logging.getLogger(__name__)


class DraftDownloadService:
    """草稿下载服务 - 统一管理所有下载逻辑"""

    def __init__(self, oss_client=None, cache_manager=None):
        """
        初始化下载服务

        Args:
            oss_client: OSS客户端（可选）
            cache_manager: 缓存管理器（可选）
        """
        self.oss_client = oss_client
        self.cache = cache_manager
        logger.info("DraftDownloadService 初始化完成")

    def check_draft_exists(self, draft_id: str, client_os: str = 'windows',
                          draft_folder: str = '') -> Dict:
        """
        检查草稿是否存在

        Args:
            draft_id: 草稿ID
            client_os: 客户端操作系统
            draft_folder: 草稿文件夹路径

        Returns:
            Dict: {
                'draft_id': str,
                'exists_in_oss': bool,
                'exists_in_database': bool,
                'exists_in_cache': bool,
                'base_key': str,
                'customized_version': {...}
            }
        """
        try:
            from oss import _ensure_bucket
            from draft_cache import DRAFT_CACHE
            import sqlite3

            bucket = _ensure_bucket()
            base_key = f"{draft_id}.zip"

            # 检查OSS
            base_exists = False
            try:
                base_exists = bucket.object_exists(base_key)
            except Exception as e:
                logger.warning(f"检查OSS文件失败: {e}")

            # 检查数据库
            draft_record = None
            try:
                conn = sqlite3.connect('capcut.db')
                c = conn.cursor()
                c.execute("SELECT id, status, created_at FROM drafts WHERE id = ?", (draft_id,))
                draft_record = c.fetchone()
                conn.close()
            except Exception as e:
                logger.error(f"查询数据库失败: {e}")

            # 检查缓存
            in_cache = draft_id in DRAFT_CACHE

            result = {
                'draft_id': draft_id,
                'exists_in_oss': base_exists,
                'exists_in_database': draft_record is not None,
                'exists_in_cache': in_cache,
                'base_key': base_key
            }

            if draft_record:
                result['draft_info'] = {
                    'status': draft_record[1],
                    'created_at': draft_record[2]
                }

            # 检查定制化版本
            if client_os:
                from customize_zip import _hash_str, REWRITE_VERSION
                key_suffix = _hash_str(f"{REWRITE_VERSION}|{client_os}|{draft_folder}")
                custom_key = f"{draft_id}__{client_os}__{key_suffix}.zip"

                custom_exists = False
                try:
                    custom_exists = bucket.object_exists(custom_key)
                except Exception:
                    pass

                result['customized_version'] = {
                    'key': custom_key,
                    'exists': custom_exists
                }

            return result

        except Exception as e:
            logger.error(f"检查草稿存在性失败: {e}", exc_info=True)
            return {
                'draft_id': draft_id,
                'error': str(e),
                'exists_in_oss': False,
                'exists_in_database': False,
                'exists_in_cache': False
            }

    def get_download_url(self, draft_id: str, client_os: str = 'windows',
                        draft_folder: str = '', force_save: bool = False) -> Dict:
        """
        生成草稿下载链接

        Args:
            draft_id: 草稿ID
            client_os: 客户端操作系统
            draft_folder: 草稿文件夹路径
            force_save: 是否强制保存

        Returns:
            Dict: {
                'success': bool,
                'data': {
                    'download_url': str,
                    'storage': str,  # 'oss' or 'local'
                    'client_os': str,
                    'draft_folder': str
                }
            }
        """
        try:
            from customize_zip import get_customized_signed_url
            from oss import get_signed_draft_url_if_exists
            from settings.local import IS_UPLOAD_DRAFT

            logger.info(f"生成下载链接: draft_id={draft_id}, client_os={client_os}")

            # 如果启用了OSS上传
            if IS_UPLOAD_DRAFT:
                # 尝试获取已签名的URL
                signed_url, exists = get_signed_draft_url_if_exists(draft_id)

                if exists and signed_url:
                    # 如果需要定制化
                    if draft_folder or client_os != 'windows':
                        try:
                            custom_url = get_customized_signed_url(draft_id, client_os, draft_folder)
                            return {
                                'success': True,
                                'data': {
                                    'download_url': custom_url,
                                    'storage': 'oss',
                                    'client_os': client_os,
                                    'draft_folder': draft_folder
                                }
                            }
                        except FileNotFoundError as e:
                            # 🔧 修复：基础文件不存在，不应该返回基础URL（因为它也是无效的）
                            logger.error(f"基础草稿文件不存在: {e}")
                            return {
                                'success': False,
                                'error': f'基础草稿文件不存在: {draft_id}',
                                'error_type': 'FILE_NOT_FOUND',
                                'suggestion': '请尝试重新保存草稿'
                            }
                        except Exception as e:
                            # 其他错误：降级使用基础URL
                            logger.warning(f"生成定制化URL失败，使用基础URL: {e}")

                    # 返回基础签名URL
                    return {
                        'success': True,
                        'data': {
                            'download_url': signed_url,
                            'storage': 'oss',
                            'client_os': client_os,
                            'draft_folder': draft_folder
                        }
                    }

                # 文件不存在，如果需要强制保存
                if force_save:
                    from save_draft_impl import save_draft_impl
                    task_info = save_draft_impl(draft_id, draft_folder, client_os)
                    return {
                        'success': True,
                        'data': {
                            'status': 'processing',
                            'task_id': task_info.get('task_id', draft_id),
                            'message': '保存任务已启动，请轮询状态'
                        }
                    }

            # 返回本地路径
            from settings.local import DRAFT_DOMAIN, PREVIEW_ROUTER
            from urllib.parse import quote
            safe_id = quote(draft_id, safe='-_.')

            return {
                'success': True,
                'data': {
                    'download_url': f"{DRAFT_DOMAIN}{PREVIEW_ROUTER}?draft_id={safe_id}",
                    'storage': 'local',
                    'client_os': client_os,
                    'draft_folder': draft_folder
                }
            }

        except Exception as e:
            logger.error(f"生成下载链接失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def stream_download(self, draft_id: str, client_os: str = 'windows',
                       draft_folder: str = '', auto_regenerate: bool = True) -> Tuple[Response, int]:
        """
        流式下载草稿文件

        Args:
            draft_id: 草稿ID
            client_os: 客户端操作系统
            draft_folder: 草稿文件夹路径
            auto_regenerate: 是否自动重新生成

        Returns:
            Tuple[Response, int]: (Flask响应对象, 状态码)
        """
        try:
            from customize_zip import get_customized_signed_url
            from urllib.parse import quote

            logger.info(f"代理下载: draft_id={draft_id}, client_os={client_os}")

            # 生成定制化URL
            draft_url = get_customized_signed_url(draft_id, client_os, draft_folder)

            # 从OSS获取文件
            file_response = requests.get(draft_url, stream=True)

            if file_response.status_code == 200:
                # 使用草稿ID作为文件名
                filename = f"{draft_id}.zip"
                encoded_filename = quote(filename, safe='')

                def generate():
                    for chunk in file_response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk

                response = Response(generate(), mimetype='application/zip')
                response.headers['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
                response.headers['Content-Type'] = 'application/zip'
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['Access-Control-Allow-Origin'] = '*'

                if 'content-length' in file_response.headers:
                    response.headers['Content-Length'] = file_response.headers['content-length']

                logger.info(f"代理下载成功: {filename}")
                return response, 200
            else:
                logger.warning(f"OSS文件不存在或无法访问: {file_response.status_code}")
                return self._create_error_response(
                    f'无法从OSS获取文件，状态码: {file_response.status_code}'
                ), 404

        except Exception as e:
            logger.error(f"代理下载失败: {e}", exc_info=True)

            # 如果启用自动修复且是文件不存在错误
            if auto_regenerate and self._is_file_not_found_error(e):
                return self._handle_auto_regenerate(draft_id, client_os, draft_folder)

            return self._create_error_response(f'代理下载失败: {str(e)}'), 500

    def batch_download(self, draft_ids: List[str], client_os: str = 'windows',
                      draft_folder: str = '') -> List[Dict]:
        """
        批量下载草稿

        Args:
            draft_ids: 草稿ID列表
            client_os: 客户端操作系统
            draft_folder: 草稿文件夹路径

        Returns:
            List[Dict]: 每个草稿的下载结果
        """
        results = []

        for draft_id in draft_ids:
            try:
                result = self.get_download_url(draft_id, client_os, draft_folder)
                result['draft_id'] = draft_id
                results.append(result)
            except FileNotFoundError as e:
                # 🔧 修复：文件不存在错误，返回明确的错误信息
                logger.error(f"批量下载失败 {draft_id}: 基础文件不存在 - {e}")
                results.append({
                    'draft_id': draft_id,
                    'success': False,
                    'error': f'基础草稿文件不存在: {draft_id}',
                    'error_type': 'FILE_NOT_FOUND',
                    'suggestion': '请尝试重新保存草稿'
                })
            except Exception as e:
                logger.error(f"批量下载失败 {draft_id}: {e}")
                results.append({
                    'draft_id': draft_id,
                    'success': False,
                    'error': str(e)
                })

        return results

    def _is_file_not_found_error(self, error: Exception) -> bool:
        """判断是否是文件不存在的错误"""
        error_str = str(error)
        return any(keyword in error_str for keyword in [
            '基础草稿文件不存在',
            'NoSuchKey',
            'FileNotFoundError'
        ])

    def _handle_auto_regenerate(self, draft_id: str, client_os: str,
                                draft_folder: str) -> Tuple[Response, int]:
        """处理自动重新生成"""
        try:
            logger.warning(f"[自动修复] 文件不存在，尝试重新生成: {draft_id}")

            # 获取草稿材料
            from database import get_draft_materials
            materials = get_draft_materials(draft_id)

            if not materials:
                return self._create_error_response('草稿材料不存在，无法重新生成'), 404

            # 重新生成草稿
            from save_draft_impl import regenerate_and_upload_draft
            regenerate_result = regenerate_and_upload_draft(draft_id, materials)

            if regenerate_result['success']:
                logger.info(f"[自动修复] 草稿重新生成成功: {draft_id}")

                # 等待上传完成
                time.sleep(3)

                # 重新下载
                from customize_zip import get_customized_signed_url
                draft_url = get_customized_signed_url(draft_id, client_os, draft_folder)

                file_response = requests.get(draft_url, stream=True)

                if file_response.status_code == 200:
                    from urllib.parse import quote

                    # 使用草稿ID作为文件名
                    filename = f"{draft_id}.zip"
                    encoded_filename = quote(filename, safe='')

                    def generate():
                        for chunk in file_response.iter_content(chunk_size=8192):
                            if chunk:
                                yield chunk

                    response = Response(generate(), mimetype='application/zip')
                    response.headers['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
                    response.headers['Content-Type'] = 'application/zip'
                    response.headers['X-Auto-Regenerated'] = 'true'

                    logger.info(f"[自动修复] 重新生成后下载成功: {filename}")
                    return response, 200

            return self._create_error_response('自动修复失败'), 500

        except Exception as regen_error:
            logger.error(f"[自动修复] 重新生成失败: {regen_error}", exc_info=True)
            return self._create_error_response(f'自动修复失败: {str(regen_error)}'), 500

    def _create_error_response(self, error_message: str) -> Response:
        """创建统一的错误响应"""
        from flask import jsonify
        return jsonify({
            'success': False,
            'error': error_message,
            'error_type': 'DOWNLOAD_FAILED'
        })


# 创建全局单例
_download_service_instance = None


def get_download_service() -> DraftDownloadService:
    """获取下载服务单例"""
    global _download_service_instance
    if _download_service_instance is None:
        _download_service_instance = DraftDownloadService()
    return _download_service_instance
