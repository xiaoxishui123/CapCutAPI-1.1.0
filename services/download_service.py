"""
草稿下载服务类 - 统一管理所有下载逻辑

职责：
1. 生成下载链接（OSS/本地）
2. 流式下载文件
3. 批量下载处理
4. 自动修复机制
5. 草稿状态检查

优化记录：
- 2025-12-01: 对大文件（>10MB）使用 OSS 直链重定向，避免代理下载超时
- 2025-12-01: 🔧 修复大文件定制化超时问题 - 对于>50MB的文件，异步处理定制化
"""

import logging
import time
import threading
from typing import Dict, List, Tuple, Optional, Union
from flask import Response, redirect, jsonify
import requests

logger = logging.getLogger(__name__)

# 大文件阈值：超过此大小使用 OSS 直链而非代理下载（10MB）
LARGE_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB

# 🆕 定制化超时阈值：超过此大小的文件使用异步定制化处理（50MB）
CUSTOMIZATION_SIZE_THRESHOLD = 50 * 1024 * 1024  # 50MB

# 🆕 定制化任务状态缓存
_customization_tasks = {}


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

        🔧 2025-12-01 优化：
        - 对于大文件（>50MB），先返回基础版本URL，后台异步生成定制化版本
        - 避免定制化处理超时导致 HTTP 502 错误

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
            from customize_zip import get_customized_signed_url, ensure_customized_zip, _hash_str, REWRITE_VERSION
            from oss import get_signed_draft_url_if_exists, _ensure_bucket
            from settings.local import IS_UPLOAD_DRAFT

            logger.info(f"生成下载链接: draft_id={draft_id}, client_os={client_os}")

            # 如果启用了OSS上传
            if IS_UPLOAD_DRAFT:
                # 尝试获取已签名的URL
                signed_url, exists = get_signed_draft_url_if_exists(draft_id)

                if exists and signed_url:
                    # 🆕 检查文件大小
                    file_size = 0
                    try:
                        bucket = _ensure_bucket()
                        base_key = f"{draft_id}.zip"
                        if bucket.object_exists(base_key):
                            meta = bucket.head_object(base_key)
                            file_size = meta.content_length
                            logger.info(f"草稿文件大小: {file_size/1024/1024:.2f} MB")
                    except Exception as e:
                        logger.warning(f"获取文件大小失败: {e}")

                    # 如果需要定制化
                    if draft_folder or client_os != 'windows':
                        # 🆕 先检查定制化版本是否已存在
                        try:
                            key_suffix = _hash_str(f"{REWRITE_VERSION}|{client_os}|{draft_folder}")
                            custom_key = f"{draft_id}__{client_os}__{key_suffix}.zip"
                            bucket = _ensure_bucket()
                            
                            if bucket.object_exists(custom_key):
                                # 定制化版本已存在，直接返回
                                logger.info(f"定制化版本已存在: {custom_key}")
                                custom_url = bucket.sign_url('GET', custom_key, 24*60*60, slash_safe=True)
                                return {
                                    'success': True,
                                    'data': {
                                        'download_url': custom_url,
                                        'storage': 'oss',
                                        'client_os': client_os,
                                        'draft_folder': draft_folder,
                                        'customized': True
                                    }
                                }
                        except Exception as e:
                            logger.warning(f"检查定制化版本失败: {e}")

                        # 🆕 对于大文件，使用异步定制化
                        if file_size > CUSTOMIZATION_SIZE_THRESHOLD:
                            file_size_mb = file_size / 1024 / 1024
                            # 预估时间：基础10秒 + 每MB约1秒
                            estimated_time = int(10 + file_size_mb * 1.0)
                            logger.warning(f"文件较大 ({file_size_mb:.2f}MB)，使用异步定制化，预计需要 {estimated_time} 秒")
                            
                            # 启动后台定制化任务
                            task_key = f"{draft_id}_{client_os}_{draft_folder}"
                            task_status = _customization_tasks.get(task_key)
                            
                            # 检查任务状态
                            if isinstance(task_status, dict) and task_status.get('status') == 'completed':
                                # 任务已完成，尝试获取定制化URL
                                try:
                                    custom_url = get_customized_signed_url(draft_id, client_os, draft_folder)
                                    return {
                                        'success': True,
                                        'data': {
                                            'download_url': custom_url,
                                            'storage': 'oss',
                                            'client_os': client_os,
                                            'draft_folder': draft_folder,
                                            'customized': True,
                                            'message': '✅ 定制化版本已就绪'
                                        }
                                    }
                                except Exception:
                                    pass
                            
                            if not task_status or (isinstance(task_status, dict) and task_status.get('status') == 'failed'):
                                # 新任务或重试失败的任务
                                _customization_tasks[task_key] = {
                                    'status': 'processing',
                                    'start_time': time.time(),
                                    'file_size_mb': file_size_mb,
                                    'estimated_time': estimated_time
                                }
                                
                                def async_customize():
                                    try:
                                        logger.info(f"[异步定制化] 开始处理: {draft_id}")
                                        ensure_customized_zip(draft_id, client_os, draft_folder)
                                        _customization_tasks[task_key] = {
                                            'status': 'completed',
                                            'start_time': _customization_tasks[task_key]['start_time'],
                                            'file_size_mb': file_size_mb
                                        }
                                        logger.info(f"[异步定制化] 完成: {draft_id}")
                                    except Exception as e:
                                        _customization_tasks[task_key] = {
                                            'status': 'failed',
                                            'error': str(e),
                                            'start_time': _customization_tasks[task_key]['start_time'],
                                            'file_size_mb': file_size_mb
                                        }
                                        logger.error(f"[异步定制化] 失败: {e}")
                                
                                thread = threading.Thread(target=async_customize, daemon=True)
                                thread.start()
                            
                            # 计算当前进度
                            progress = 0
                            remaining = estimated_time
                            if isinstance(task_status, dict) and task_status.get('start_time'):
                                elapsed = int(time.time() - task_status['start_time'])
                                progress = min(95, int((elapsed / max(1, estimated_time)) * 100))
                                remaining = max(0, estimated_time - elapsed)
                            
                            # 返回友好的提示信息
                            return {
                                'success': True,
                                'data': {
                                    'download_url': signed_url,
                                    'storage': 'oss',
                                    'client_os': client_os,
                                    'draft_folder': draft_folder,
                                    'customized': False,
                                    'large_file': True,
                                    'async_processing': True,
                                    'file_size': file_size,
                                    'file_size_mb': round(file_size_mb, 2),
                                    'estimated_time': estimated_time,
                                    'progress': progress,
                                    'remaining_time': remaining,
                                    'message': f'📦 文件较大 ({file_size_mb:.1f}MB)，正在后台生成定制化版本...\n⏳ 预计需要 {estimated_time} 秒，当前进度 {progress}%\n💡 请等待 {remaining} 秒后重新点击下载'
                                }
                            }
                        
                        # 正常大小的文件，同步生成定制化版本
                        try:
                            custom_url = get_customized_signed_url(draft_id, client_os, draft_folder)
                            return {
                                'success': True,
                                'data': {
                                    'download_url': custom_url,
                                    'storage': 'oss',
                                    'client_os': client_os,
                                    'draft_folder': draft_folder,
                                    'customized': True
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
            from urllib.parse import quote, urlencode
            safe_id = quote(draft_id, safe='-_.')

            # 🔧 修复：本地模式也需要传递 client_os 和 draft_folder 参数
            params = {
                'draft_id': safe_id,
                'client_os': client_os
            }
            if draft_folder:
                params['draft_folder'] = draft_folder
            
            download_url = f"{DRAFT_DOMAIN}{PREVIEW_ROUTER}?{urlencode(params)}"
            logger.info(f"[本地模式] 生成下载URL: {download_url[:100]}...")

            return {
                'success': True,
                'data': {
                    'download_url': download_url,
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
                       draft_folder: str = '', auto_regenerate: bool = True,
                       force_proxy: bool = False) -> Union[Tuple[Response, int], Response]:
        """
        流式下载草稿文件
        
        🔧 优化：支持本地模式和 OSS 模式
        - 本地模式：直接从本地文件系统读取并转换路径
        - OSS 模式：从 OSS 获取定制化版本

        Args:
            draft_id: 草稿ID
            client_os: 客户端操作系统
            draft_folder: 草稿文件夹路径
            auto_regenerate: 是否自动重新生成
            force_proxy: 是否强制使用代理下载（忽略文件大小）

        Returns:
            Union[Tuple[Response, int], Response]: Flask响应对象
        """
        try:
            from urllib.parse import quote
            from settings.local import IS_UPLOAD_DRAFT
            import os

            logger.info(f"下载请求: draft_id={draft_id}, client_os={client_os}, force_proxy={force_proxy}, IS_UPLOAD_DRAFT={IS_UPLOAD_DRAFT}")

            # 🆕 本地模式：直接从本地文件系统提供下载
            if not IS_UPLOAD_DRAFT:
                return self._stream_download_local(draft_id, client_os, draft_folder, auto_regenerate)

            # OSS 模式：原有逻辑
            from customize_zip import get_customized_signed_url

            # 生成定制化URL
            draft_url = get_customized_signed_url(draft_id, client_os, draft_folder)

            # 🔧 优化：先用 GET + stream=True 获取响应头，检查文件大小
            logger.info(f"开始检查文件大小: {draft_id}")
            file_response = requests.get(draft_url, stream=True, timeout=300)

            if file_response.status_code == 200:
                # 获取文件大小
                content_length = int(file_response.headers.get('content-length', 0))
                
                # 🔧 优化：如果文件大于阈值，关闭连接并返回重定向
                if not force_proxy and content_length > LARGE_FILE_THRESHOLD:
                    file_size_mb = content_length / 1024 / 1024
                    logger.info(f"🔄 检测到大文件: {file_size_mb:.2f}MB > {LARGE_FILE_THRESHOLD/1024/1024}MB")
                    logger.info(f"🔗 返回 OSS 直链重定向，避免代理下载超时")
                    
                    # 关闭流式连接，释放资源
                    file_response.close()
                    
                    return jsonify({
                        'success': True,
                        'redirect': True,
                        'download_url': draft_url,
                        'file_size': content_length,
                        'file_size_mb': round(file_size_mb, 2),
                        'message': '文件较大，使用 OSS 直接下载以提高稳定性',
                        'draft_id': draft_id
                    }), 200
                
                # 小文件：继续代理下载
                logger.info(f"小文件 ({content_length} bytes)，使用代理下载")
                
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

                if content_length:
                    response.headers['Content-Length'] = str(content_length)
                    response.headers['X-File-Size'] = str(content_length)

                logger.info(f"代理下载成功: {filename} ({content_length} bytes)")
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

    def _stream_download_local(self, draft_id: str, client_os: str = 'windows',
                               draft_folder: str = '', auto_regenerate: bool = True) -> Union[Tuple[Response, int], Response]:
        """
        🆕 本地模式下载：直接从本地文件系统读取并转换路径
        
        流程：
        1. 查找本地草稿文件夹或 zip 文件
        2. 转换 draft_info.json 中的路径
        3. 打包并提供下载
        """
        import os
        import zipfile
        import tempfile
        import json
        from urllib.parse import quote
        
        logger.info(f"[本地模式] 开始处理: {draft_id}")
        
        # 查找草稿目录
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        draft_dir = os.path.join(current_dir, draft_id)
        zip_path = os.path.join(current_dir, f"{draft_id}.zip")
        
        logger.info(f"[本地模式] 草稿目录: {draft_dir}")
        logger.info(f"[本地模式] ZIP路径: {zip_path}")
        
        # 检查草稿是否存在
        if not os.path.exists(draft_dir) and not os.path.exists(zip_path):
            logger.warning(f"[本地模式] 草稿不存在: {draft_id}")
            
            # 尝试自动修复
            if auto_regenerate:
                logger.info(f"[本地模式] 尝试自动重新生成...")
                return self._handle_auto_regenerate_local(draft_id, client_os, draft_folder)
            
            return self._create_error_response(f'草稿不存在: {draft_id}'), 404
        
        try:
            # 创建临时目录（不使用 with，手动管理）
            import shutil
            temp_dir = tempfile.mkdtemp()
            output_zip = os.path.join(temp_dir, f"{draft_id}.zip")
            
            try:
                # 如果已有 zip 文件，使用它作为基础
                if os.path.exists(zip_path):
                    logger.info(f"[本地模式] 使用现有 ZIP 文件: {zip_path}")
                    base_zip = zip_path
                else:
                    # 从目录创建 zip
                    logger.info(f"[本地模式] 从目录创建 ZIP")
                    base_zip = os.path.join(temp_dir, "base.zip")
                    self._zip_directory(draft_dir, base_zip)
                
                # 转换路径并创建新 zip
                logger.info(f"[本地模式] 开始路径转换: client_os={client_os}, draft_folder='{draft_folder}'")
                self._customize_local_zip(base_zip, output_zip, draft_id, client_os, draft_folder)
                
                file_size = os.path.getsize(output_zip)
                file_size_mb = file_size / 1024 / 1024
                logger.info(f"[本地模式] 文件大小: {file_size_mb:.2f} MB")
                
                # 🔧 优化：对于大文件使用流式响应
                if file_size > 10 * 1024 * 1024:  # > 10MB
                    logger.info(f"[本地模式] 大文件 ({file_size_mb:.2f} MB)，使用流式传输")
                    
                    # 使用流式响应
                    def generate():
                        chunk_size = 64 * 1024  # 64KB chunks
                        bytes_sent = 0
                        with open(output_zip, 'rb') as f:
                            while True:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                bytes_sent += len(chunk)
                                yield chunk
                        logger.info(f"[本地模式] 流式传输完成: {bytes_sent / 1024 / 1024:.2f} MB")
                        # 传输完成后清理临时目录
                        try:
                            shutil.rmtree(temp_dir)
                        except Exception:
                            pass
                    
                    filename = f"{draft_id}.zip"
                    encoded_filename = quote(filename, safe='')
                    
                    response = Response(generate(), mimetype='application/zip')
                    response.headers['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
                    response.headers['Content-Type'] = 'application/zip'
                    response.headers['Content-Length'] = str(file_size)
                    response.headers['X-Content-Type-Options'] = 'nosniff'
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    response.headers['X-Download-Mode'] = 'local-stream'
                    response.headers['X-File-Size-MB'] = f'{file_size_mb:.2f}'
                    
                    logger.info(f"[本地模式] ✅ 开始流式下载: {filename} ({file_size_mb:.2f} MB)")
                    return response, 200
                else:
                    # 小文件：读入内存一次性返回
                    logger.info(f"[本地模式] 小文件 ({file_size_mb:.2f} MB)，直接返回")
                    with open(output_zip, 'rb') as f:
                        file_data = f.read()
                
            except Exception as inner_e:
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                raise inner_e
            
            filename = f"{draft_id}.zip"
            encoded_filename = quote(filename, safe='')
            
            # 直接返回内存中的数据（小文件）
            response = Response(file_data, mimetype='application/zip')
            response.headers['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Length'] = str(file_size)
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['X-Download-Mode'] = 'local'
            
            logger.info(f"[本地模式] ✅ 下载成功: {filename}")
            return response, 200
                
        except Exception as e:
            logger.error(f"[本地模式] 下载失败: {e}", exc_info=True)
            return self._create_error_response(f'本地下载失败: {str(e)}'), 500

    def _zip_directory(self, source_dir: str, output_zip: str):
        """将目录打包成 zip"""
        import zipfile
        import os
        
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, source_dir)
                    zf.write(file_path, arc_name)

    def _customize_local_zip(self, input_zip: str, output_zip: str, draft_id: str, 
                            client_os: str, draft_folder: str):
        """
        本地模式下转换 zip 中的路径
        复用 customize_zip.py 中的路径重写逻辑
        """
        import zipfile
        import json
        
        logger.info(f"[本地模式] 开始路径转换: client_os={client_os}, draft_folder='{draft_folder}'")
        
        with zipfile.ZipFile(input_zip, 'r') as zin, \
             zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zout:
            
            for item in zin.infolist():
                filename = item.filename.replace("\\", "/")
                filename_lower = filename.lower()
                basename = filename.split("/")[-1].lower()
                
                if basename == "draft_info.json":
                    # 重写 draft_info.json 中的路径
                    raw = zin.read(item)
                    try:
                        info = json.loads(raw.decode("utf-8"))
                        info = self._rewrite_paths(info, draft_id, client_os, draft_folder)
                        data = json.dumps(info, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                        logger.info(f"[本地模式] ✅ draft_info.json 路径已转换")
                    except Exception as e:
                        logger.warning(f"[本地模式] draft_info.json 解析失败: {e}")
                        data = raw
                    
                    zi = zipfile.ZipInfo(filename)
                    zi.date_time = item.date_time
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zout.writestr(zi, data)
                    
                elif basename == "draft_meta_info.json":
                    # 重写 draft_meta_info.json
                    raw = zin.read(item)
                    try:
                        meta = json.loads(raw.decode("utf-8"))
                        meta = self._rewrite_meta(meta, draft_id, client_os, draft_folder)
                        data = json.dumps(meta, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                        logger.info(f"[本地模式] ✅ draft_meta_info.json 路径已转换")
                    except Exception as e:
                        logger.warning(f"[本地模式] draft_meta_info.json 解析失败: {e}")
                        data = raw
                    
                    zi = zipfile.ZipInfo(filename)
                    zi.date_time = item.date_time
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zout.writestr(zi, data)
                else:
                    # 其他文件直接复制
                    data = zin.read(item)
                    zi = zipfile.ZipInfo(filename)
                    zi.date_time = item.date_time
                    zi.compress_type = item.compress_type
                    zout.writestr(zi, data)

    def _rewrite_paths(self, info: dict, draft_id: str, client_os: str, draft_folder: str) -> dict:
        """重写 draft_info.json 中的素材路径"""
        import copy
        info = copy.deepcopy(info)
        
        # 确定路径分隔符和基础路径
        if client_os == 'windows':
            sep = '\\'
            if draft_folder:
                base_path = f"{draft_folder}\\{draft_id}"
            else:
                base_path = ""  # 使用相对路径
        else:
            sep = '/'
            if draft_folder:
                base_path = f"{draft_folder}/{draft_id}"
            else:
                base_path = ""
        
        def rewrite_path(path: str, asset_type: str = '') -> str:
            """转换单个路径"""
            if not path:
                return path
            
            # 提取文件名
            filename = path.replace('\\', '/').split('/')[-1]
            
            # 确定资产类型
            if not asset_type:
                if 'video' in path.lower() or filename.endswith('.mp4'):
                    asset_type = 'video'
                elif 'audio' in path.lower() or filename.endswith('.mp3'):
                    asset_type = 'audio'
                elif 'image' in path.lower() or filename.endswith(('.png', '.jpg', '.jpeg')):
                    asset_type = 'image'
                else:
                    asset_type = 'video'
            
            if base_path:
                # 绝对路径模式
                new_path = f"{base_path}{sep}assets{sep}{asset_type}{sep}{filename}"
            else:
                # 相对路径模式
                new_path = f"assets{sep}{asset_type}{sep}{filename}"
            
            return new_path
        
        # 遍历所有素材并重写路径
        materials = info.get('materials', {})
        
        # 处理视频
        for video in materials.get('videos', []):
            if video.get('path'):
                video['path'] = rewrite_path(video['path'], 'video')
        
        # 处理音频
        for audio in materials.get('audios', []):
            if audio.get('path'):
                audio['path'] = rewrite_path(audio['path'], 'audio')
        
        # 处理图片
        for image in materials.get('images', []) + materials.get('stickers', []):
            if image.get('path'):
                image['path'] = rewrite_path(image['path'], 'image')
        
        # 处理轨道中的素材引用
        for track in info.get('tracks', []):
            for segment in track.get('segments', []):
                if segment.get('material_id'):
                    # 查找对应的素材并更新路径（如果需要）
                    pass
        
        return info

    def _rewrite_meta(self, meta: dict, draft_id: str, client_os: str, draft_folder: str) -> dict:
        """重写 draft_meta_info.json"""
        import copy
        import uuid
        
        meta = copy.deepcopy(meta)
        
        if draft_folder:
            if client_os == 'windows':
                meta['draft_root_path'] = draft_folder
                meta['draft_fold_path'] = f"{draft_folder}\\{draft_id}"
            else:
                meta['draft_root_path'] = draft_folder
                meta['draft_fold_path'] = f"{draft_folder}/{draft_id}"
        else:
            # 相对路径模式：清空路径
            meta['draft_root_path'] = ''
            meta['draft_fold_path'] = ''
        
        # 刷新 draft_id（避免剪映认为是重复草稿）
        meta['draft_id'] = str(uuid.uuid4()).upper()
        meta['draft_name'] = draft_id
        
        return meta

    def _handle_auto_regenerate_local(self, draft_id: str, client_os: str,
                                      draft_folder: str) -> Tuple[Response, int]:
        """本地模式下的自动重新生成"""
        try:
            logger.warning(f"[本地模式-自动修复] 尝试重新生成: {draft_id}")
            
            from database import get_draft_materials
            materials = get_draft_materials(draft_id)
            
            if not materials:
                return self._create_error_response('草稿材料不存在，无法重新生成'), 404
            
            # 重新生成草稿（本地模式）
            from save_draft_impl import save_draft_impl
            result = save_draft_impl(draft_id, draft_folder, client_os)
            
            if result.get('success'):
                logger.info(f"[本地模式-自动修复] 草稿重新生成成功")
                # 递归调用本地下载
                return self._stream_download_local(draft_id, client_os, draft_folder, auto_regenerate=False)
            else:
                return self._create_error_response(f"重新生成失败: {result.get('error', '未知错误')}"), 500
                
        except Exception as e:
            logger.error(f"[本地模式-自动修复] 失败: {e}", exc_info=True)
            return self._create_error_response(f'自动修复失败: {str(e)}'), 500

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
