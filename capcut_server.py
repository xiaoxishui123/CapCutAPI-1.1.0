#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCutAPI Server - 剪映草稿生成和管理API服务

功能描述:
- 提供剪映草稿创建、编辑和管理API
- 支持视频、音频、文本、图片等多种素材添加
- 在线预览草稿功能
- 云端存储和下载管理
- 多平台兼容（Windows、Linux、macOS）

版本: v1.1.0
作者: CapCutAPI Team
创建时间: 2024-01-01
最后更新: 2025-01-03
"""

# ===== 标准库导入 =====
import codecs
import html
import json
import logging
import os
import random
import sqlite3
import time
import uuid
from datetime import datetime
from urllib.parse import quote

# ===== 第三方库导入 =====
import oss2
import requests
from flask import Flask, request, jsonify, Response, render_template, redirect

# ===== pyJianYingDraft 相关导入 =====
import pyJianYingDraft as draft
from pyJianYingDraft.metadata.animation_meta import (
    Intro_type, Outro_type, Group_animation_type,
    Text_intro, Text_outro, Text_loop_anim
)
from pyJianYingDraft.metadata.capcut_animation_meta import (
    CapCut_Intro_type, CapCut_Outro_type, CapCut_Group_animation_type
)
from pyJianYingDraft.metadata.transition_meta import Transition_type
from pyJianYingDraft.metadata.capcut_transition_meta import CapCut_Transition_type
from pyJianYingDraft.metadata.mask_meta import Mask_type
from pyJianYingDraft.metadata.capcut_mask_meta import CapCut_Mask_type
from pyJianYingDraft.metadata.audio_effect_meta import (
    Tone_effect_type, Audio_scene_effect_type, Speech_to_song_type
)
from pyJianYingDraft.metadata.capcut_audio_effect_meta import (
    CapCut_Voice_filters_effect_type, CapCut_Voice_characters_effect_type,
    CapCut_Speech_to_song_effect_type
)
from pyJianYingDraft.metadata.font_meta import Font_type
from pyJianYingDraft.metadata.capcut_text_animation_meta import (
    CapCut_Text_intro, CapCut_Text_outro, CapCut_Text_loop_anim
)
from pyJianYingDraft.metadata.video_effect_meta import (
    Video_scene_effect_type, Video_character_effect_type
)
from pyJianYingDraft.metadata.capcut_effect_meta import (
    CapCut_Video_scene_effect_type, CapCut_Video_character_effect_type
)
from pyJianYingDraft.text_segment import TextStyleRange, Text_style, Text_border

# ===== 本地模块导入 =====
from add_audio_track import add_audio_track
from add_video_track import add_video_track
from add_text_impl import add_text_impl
from add_subtitle_impl import add_subtitle_impl
from add_image_impl import add_image_impl
from add_video_keyframe_impl import add_video_keyframe_impl
from save_draft_impl import save_draft_impl, query_task_status, query_script_impl
from os_path_config import get_os_path_config
from add_effect_impl import add_effect_impl
from add_sticker_impl import add_sticker_impl
from create_draft import create_draft, get_or_create_draft
from util import generate_draft_url as utilgenerate_draft_url, hex_to_rgb, normalize_path_by_os
from database import (
    init_db,
    get_draft_materials as get_draft_materials_from_db,
    add_material_to_db,
    get_all_drafts,
    update_draft_status
)
from oss import get_signed_draft_url_if_exists
from customize_zip import get_customized_signed_url
from settings.local import IS_CAPCUT_ENV, DRAFT_DOMAIN, PREVIEW_ROUTER, PORT, IS_UPLOAD_DRAFT, OSS_CONFIG
from validators import (
    validate_draft_id,
    validate_url,
    validate_text_content,
    validate_numeric_range,
    validate_color,
    validate_duration,
    validate_material_type,
    validate_resolution,
    validate_file_path,
    validate_required_fields
)
from exceptions import (
    CapCutAPIException,
    DraftNotFoundException,
    ValidationException,
    StorageException,
    handle_exception,
    get_status_code
)
from log_config import setup_logging, setup_access_logger, PerformanceLogger, log_api_request, log_api_response

def _ensure_bucket_v4():
    """创建OSS Bucket实例（使用V4签名）"""
    auth = oss2.AuthV4(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
    endpoint = OSS_CONFIG['endpoint']
    if not str(endpoint).startswith('http'):
        endpoint = 'https://' + endpoint
    return oss2.Bucket(auth, endpoint, OSS_CONFIG['bucket_name'], region=OSS_CONFIG['region'])

app = Flask(__name__, template_folder='templates')

# ===== 日志配置 =====
# 使用增强的日志配置
logger = setup_logging(log_level='INFO', log_to_console=True, log_to_file=True)
access_logger = setup_access_logger()

# 记录服务启动
logger.info("=" * 60)
logger.info("CapCutAPI 服务启动")
logger.info(f"版本: v1.1.0")
logger.info(f"端口: {PORT}")
logger.info(f"环境: {'CapCut' if IS_CAPCUT_ENV else '剪映'}")
logger.info(f"草稿上传: {'启用' if IS_UPLOAD_DRAFT else '禁用'}")
logger.info("=" * 60)

# ===== 全局异常处理器 =====

@app.errorhandler(CapCutAPIException)
def handle_capcut_api_exception(error):
    """处理自定义API异常"""
    logger.error(f"API异常: {error.message}", exc_info=True, extra=error.details)
    response_data = error.to_dict()
    return jsonify(response_data), error.status_code

@app.errorhandler(404)
def handle_not_found(error):
    """处理404错误"""
    logger.warning(f"资源未找到: {request.url}")
    return jsonify({
        'success': False,
        'error': '资源未找到',
        'error_type': 'NotFound',
        'status_code': 404,
        'path': request.path
    }), 404

@app.errorhandler(500)
def handle_internal_error(error):
    """处理500错误"""
    logger.error(f"服务器内部错误: {error}", exc_info=True)
    return jsonify({
        'success': False,
        'error': '服务器内部错误，请联系管理员',
        'error_type': 'InternalServerError',
        'status_code': 500
    }), 500

@app.errorhandler(Exception)
def handle_unexpected_exception(error):
    """处理所有未捕获的异常"""
    logger.error(f"未预期的异常: {error}", exc_info=True)
    error_dict = handle_exception(error)
    status_code = get_status_code(error)
    return jsonify(error_dict), status_code

init_db()

# ===== 请求/响应日志中间件 =====

@app.before_request
def log_request():
    """在每个请求前记录访问日志"""
    request.start_time = datetime.now()

    # 记录请求信息
    log_api_request(
        access_logger,
        endpoint=request.path,
        method=request.method,
        remote_addr=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )

@app.after_request
def log_response(response):
    """在每个请求后记录响应日志"""
    if hasattr(request, 'start_time'):
        duration = (datetime.now() - request.start_time).total_seconds()

        # 记录响应信息
        log_api_response(
            access_logger,
            endpoint=request.path,
            status_code=response.status_code,
            duration=duration,
            response_size=response.content_length
        )

    return response

# ===== 全局变量和配置 =====
draft_materials_cache = {}
custom_download_path = ""  # 自定义下载路径

# ===== 工具函数 =====

def create_standard_response(success=False, output="", error=""):
    """创建标准API响应格式"""
    return {
        "success": success,
        "output": output,
        "error": error
    }

def handle_api_error(error_message, exception=None):
    """统一错误处理"""
    if exception:
        logger.error(f"API错误: {error_message}", exc_info=exception)
    else:
        logger.warning(f"API错误: {error_message}")
    return jsonify(create_standard_response(success=False, error=error_message))

def get_material_type_by_extension(file_ext):
    """根据文件扩展名确定素材类型"""
    file_ext = file_ext.lower()
    if file_ext in ['mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm']:
        return 'video'
    elif file_ext in ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a']:
        return 'audio'
    elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']:
        return 'image'
    elif file_ext in ['txt', 'srt', 'vtt', 'ass']:
        return 'text'
    return 'unknown'

def validate_required_params(params, required_fields):
    """验证必需参数"""
    missing = [field for field in required_fields if not params.get(field)]
    if missing:
        return f"缺少必需参数: {', '.join(missing)}"
    return None

def add_material_to_cache(draft_id, material_info):
    """添加素材信息到缓存和数据库"""
    try:
        material_id = str(uuid.uuid4())
        add_material_to_db(draft_id, material_id, material_info)
        
        # 更新内存缓存
        if draft_id not in draft_materials_cache:
            draft_materials_cache[draft_id] = []
        material_info['id'] = material_id
        draft_materials_cache[draft_id].append(material_info)
    except Exception as e:
        logger.error(f'持久化素材到数据库失败: {e}', exc_info=True)

def get_draft_materials(draft_id):
    """获取草稿素材信息 - 优先从缓存获取，然后从数据库获取，最后扫描文件系统"""
    # 首先检查内存缓存
    if draft_id in draft_materials_cache:
        return draft_materials_cache[draft_id]
    
    # 如果缓存中没有，从数据库获取
    db_materials = get_draft_materials_from_db(draft_id)
    if db_materials:
        draft_materials_cache[draft_id] = db_materials
        return db_materials
    
    # 如果数据库中也没有，扫描草稿目录中的实际文件
    return _scan_draft_directory(draft_id)

def _scan_draft_directory(draft_id):
    """扫描草稿目录中的文件"""
    draft_path = f"drafts/{draft_id}"
    if not os.path.exists(draft_path):
        return []
        
    materials = []
    for filename in os.listdir(draft_path):
        file_path = os.path.join(draft_path, filename)
        if os.path.isfile(file_path) and filename != 'draft_info.json':
            material_info = _create_material_info(draft_id, filename, file_path)
            if material_info:
                materials.append(material_info)
    
    # 缓存素材信息
    if materials:
        draft_materials_cache[draft_id] = materials
        _save_materials_to_db(draft_id, materials)
    
    return materials

def _create_material_info(draft_id, filename, file_path):
    """创建素材信息对象"""
    try:
        file_ext = filename.lower().split('.')[-1]
        material_type = get_material_type_by_extension(file_ext)
        
        return {
            'id': f"{draft_id}_{filename}",
            'name': filename,
            'type': material_type,
            'path': file_path,
            'size': os.path.getsize(file_path),
            'duration': '未知',
            'created_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"创建素材信息失败: {e}", exc_info=True)
        return None

def _save_materials_to_db(draft_id, materials):
    """将素材信息保存到数据库"""
    for material in materials:
        try:
            add_material_to_db(draft_id, material)
        except Exception as e:
            logger.error(f"保存素材到数据库失败: {e}", exc_info=True)

# ===== HTML模板生成函数 =====

def generate_index_html():
    """生成首页HTML内容"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CapCutAPI 服务</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 800px;
            width: 90%;
            text-align: center;
        }
        .logo {
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 20px;
        }
        .status {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 1.1em;
        }
        .endpoints {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: left;
        }
        .endpoint {
            margin: 8px 0;
            padding: 8px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
        .method {
            font-weight: bold;
            color: #667eea;
        }
        .url {
            color: #495057;
            font-family: monospace;
        }
        .description {
            color: #6c757d;
            font-size: 0.9em;
        }
        .info {
            background: #e7f3ff;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }
        .test-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            margin: 10px;
            transition: background 0.3s;
        }
        .test-button:hover {
            background: #5a6fd8;
        }
        .footer {
            margin-top: 30px;
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🎬 CapCutAPI</div>
        <div class="status">✅ 服务运行正常</div>
        
        <div class="info">
            <h3>服务器信息</h3>
            <p><strong>地址:</strong> http://8.148.70.18:9000</p>
            <p><strong>版本:</strong> 1.1.0</p>
            <p><strong>状态:</strong> 在线</p>
        </div>
        
        <div class="endpoints">
            <h3>可用的API端点</h3>
            <div class="endpoint">
                <span class="method">GET</span> <span class="url">/get_intro_animation_types</span>
                <div class="description">获取入场动画类型</div>
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <span class="url">/get_outro_animation_types</span>
                <div class="description">获取出场动画类型</div>
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <span class="url">/get_transition_types</span>
                <div class="description">获取转场类型</div>
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <span class="url">/get_mask_types</span>
                <div class="description">获取遮罩类型</div>
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <span class="url">/get_font_types</span>
                <div class="description">获取字体类型</div>
            </div>
            <div class="endpoint">
                <span class="method">POST</span> <span class="url">/create_draft</span>
                <div class="description">创建草稿</div>
            </div>
            <div class="endpoint">
                <span class="method">POST</span> <span class="url">/add_video</span>
                <div class="description">添加视频</div>
            </div>
            <div class="endpoint">
                <span class="method">POST</span> <span class="url">/add_text</span>
                <div class="description">添加文本</div>
            </div>
            <div class="endpoint">
                <span class="method">POST</span> <span class="url">/add_subtitle</span>
                <div class="description">添加字幕</div>
            </div>
            <div class="endpoint">
                <span class="method">POST</span> <span class="url">/save_draft</span>
                <div class="description">保存草稿</div>
            </div>
        </div>
        
        <div>
            <button class="test-button" onclick="testAPI()">测试API</button>
            <button class="test-button" onclick="showJSON()">显示JSON</button>
            <button class="test-button" onclick="openDashboard()">📊 草稿管理</button>
            <button class="test-button" onclick="openPreview()">🎬 预览演示</button>
        </div>
        
        <div class="footer">
            <p>📖 详细使用说明请查看 API_USAGE_EXAMPLES.md</p>
            <p>🔧 服务管理请使用 ./service_manager.sh</p>
            <p style="color: #4CAF50; font-weight: bold;">🆕 新功能：支持相对路径下载 - draft_folder参数现在可使用相对路径(如: ./downloads, ../output)</p>
        </div>
    </div>
    
    <script>
        function testAPI() {
            fetch('/get_intro_animation_types')
                .then(response => response.json())
                .then(data => {
                    alert('API测试成功！\\n获取到 ' + data.output.length + ' 个动画类型');
                })
                .catch(error => {
                    alert('API测试失败：' + error);
                });
        }
        
        function showJSON() {
            fetch('/', {
                headers: {
                    'Accept': 'application/json'
                }
            })
                .then(response => response.json())
                .then(data => {
                    alert(JSON.stringify(data, null, 2));
                })
                .catch(error => {
                    alert('获取JSON失败：' + error);
                });
        }
        
        function openDashboard() {
            window.open('/api/drafts/dashboard', '_blank');
        }
        
        function openPreview() {
            window.open('/draft/preview/sample_draft', '_blank');
        }
    </script>
</body>
</html>
    """

# ===== 路由处理函数 =====

@app.route('/', methods=['GET'])
def index():
    """根路径处理器，显示API服务信息"""
    # 检查请求头，如果是API调用则返回JSON
    if request.headers.get('Accept') == 'application/json':
        return jsonify(create_standard_response(
            success=True,
            output={
                "message": "CapCutAPI 服务运行正常",
                "version": "1.1.0",
                "server": "http://8.148.70.18:9000",
                "available_endpoints": [
                    "GET / - 服务信息",
                    "GET /get_intro_animation_types - 获取入场动画类型",
                    "GET /get_outro_animation_types - 获取出场动画类型", 
                    "GET /get_transition_types - 获取转场类型",
                    "GET /get_mask_types - 获取遮罩类型",
                    "GET /get_font_types - 获取字体类型",
                    "POST /create_draft - 创建草稿",
                    "POST /add_video - 添加视频",
                    "POST /add_audio - 添加音频",
                    "POST /add_text - 添加文本",
                    "POST /add_subtitle - 添加字幕",
                    "POST /add_image - 添加图片",
                    "POST /add_effect - 添加特效",
                    "POST /add_sticker - 添加贴纸",
                    "POST /save_draft - 保存草稿 (🆕 支持相对路径)"
                ],
                "documentation": "查看 API_USAGE_EXAMPLES.md 获取详细使用说明",
                "new_features": "🆕 支持相对路径下载 - draft_folder参数现在可以使用相对路径(如: ./downloads, ../output)或绝对路径，相对路径将自动转换为基于项目根目录的绝对路径"
            }
        ))
    
    # 返回HTML欢迎页面
    return generate_index_html()

@app.route('/add_video', methods=['POST'])
def add_video():
    """添加视频素材到草稿"""
    try:
        data = request.get_json()

        # 验证必需参数
        video_url = data.get('video_url')
        if not video_url:
            return handle_api_error("缺少必需参数 'video_url'")

        # 拒绝未解析的占位符
        if isinstance(video_url, str) and ('{{' in video_url or '}}' in video_url):
            return handle_api_error(f"video_url 是占位符，未替换为真实地址。请在调用前先生成实际URL。", video_url)

        # ===== 输入验证 =====
        # 验证draft_id
        draft_id = data.get('draft_id')
        if draft_id:
            is_valid, error_msg = validate_draft_id(draft_id)
            if not is_valid:
                return jsonify({'success': False, 'error': f'draft_id验证失败: {error_msg}'}), 400

        # 验证video_url（允许内网地址，因为可能使用本地文件服务器）
        is_valid, error_msg = validate_url(video_url, allow_internal=True)
        if not is_valid:
            return jsonify({'success': False, 'error': f'video_url验证失败: {error_msg}'}), 400

        # 验证时长参数
        start = data.get('start', 0)
        end = data.get('end', 0)
        if end > 0:  # 如果指定了end，验证start和end的有效性
            is_valid, error_msg = validate_duration(start, end)
            if not is_valid:
                return jsonify({'success': False, 'error': f'时长验证失败: {error_msg}'}), 400

        # 验证分辨率
        width = data.get('width', 1080)
        height = data.get('height', 1920)
        is_valid, error_msg = validate_resolution(int(width), int(height))
        if not is_valid:
            return jsonify({'success': False, 'error': f'分辨率验证失败: {error_msg}'}), 400

        # 获取参数
        params = {
            'draft_folder': data.get('draft_folder'),
            'video_url': video_url,
            'start': data.get('start', 0),
            'end': data.get('end', 0),
            'width': data.get('width', 1080),
            'height': data.get('height', 1920),
            'draft_id': data.get('draft_id'),
            'transform_y': data.get('transform_y', 0),
            'scale_x': data.get('scale_x', 1),
            'scale_y': data.get('scale_y', 1),
            'transform_x': data.get('transform_x', 0),
            'speed': data.get('speed', 1.0),
            'target_start': data.get('target_start', 0),
            'track_name': data.get('track_name', "video_main"),
            'relative_index': data.get('relative_index', 0),
            'duration': data.get('duration'),
            'transition': data.get('transition'),
            'transition_duration': data.get('transition_duration', 0.5),
            'volume': data.get('volume', 1.0),
            # 遮罩相关参数
            'mask_type': data.get('mask_type'),
            'mask_center_x': data.get('mask_center_x', 0.5),
            'mask_center_y': data.get('mask_center_y', 0.5),
            'mask_size': data.get('mask_size', 1.0),
            'mask_rotation': data.get('mask_rotation', 0.0),
            'mask_feather': data.get('mask_feather', 0.0),
            'mask_invert': data.get('mask_invert', False),
            'mask_rect_width': data.get('mask_rect_width'),
            'mask_round_corner': data.get('mask_round_corner'),
            'background_blur': data.get('background_blur')
        }
        
        # 调用业务逻辑
        draft_result = add_video_track(**params)
        
        # 记录素材信息到缓存
        material_info = {
            "type": "video",
            "url": video_url,
            "start": params['start'],
            "end": params['end'],
            "duration": params['end'] - params['start'] if params['end'] > params['start'] else None,
            "track_name": params['track_name'],
            "added_at": datetime.now().isoformat()
        }
        add_material_to_cache(params['draft_id'], material_info)
        
        return jsonify(create_standard_response(success=True, output=draft_result))
        
    except Exception as e:
        return handle_api_error(f"处理视频时发生错误: {str(e)}", e)

@app.route('/add_audio', methods=['POST'])
def add_audio():
    """添加音频素材到草稿"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        audio_url = data.get('audio_url')
        if not audio_url:
            return handle_api_error("缺少必需参数 'audio_url'")
        
        # 拒绝未解析的占位符
        if isinstance(audio_url, str) and ('{{' in audio_url or '}}' in audio_url):
            return handle_api_error(f"audio_url 是占位符，未替换为真实地址。请在调用前先生成实际URL。", audio_url)
        
        # 获取参数
        params = {
            'draft_folder': data.get('draft_folder'),
            'audio_url': audio_url,
            'start': data.get('start', 0),
            'end': data.get('end', None),
            'target_start': data.get('target_start', 0),
            'draft_id': data.get('draft_id'),
            'volume': data.get('volume', 1.0),
            'track_name': data.get('track_name', 'audio_main'),
            'speed': data.get('speed', 1.0),
            'width': data.get('width', 1080),
            'height': data.get('height', 1920),
            'duration': data.get('duration', None),
            'client_os': data.get('client_os', 'windows')  # 添加客户端操作系统参数，默认为windows
        }
        
        # 处理音频效果参数
        sound_effects = None
        effect_type = data.get('effect_type')
        if effect_type:
            effect_params = data.get('effect_params')
            sound_effects = [(effect_type, effect_params)]
            params['sound_effects'] = sound_effects
        
        # 调用业务逻辑
        draft_result = add_audio_track(**params)
        
        # 记录素材信息到缓存
        material_info = {
            "type": "audio",
            "url": audio_url,
            "start": params['start'],
            "end": params['end'],
            "duration": (params['end'] - params['start']) if params['end'] and params['end'] > params['start'] else None,
            "track_name": params['track_name'],
            "volume": params['volume'],
            "added_at": datetime.now().isoformat()
        }
        add_material_to_cache(params['draft_id'], material_info)
        
        return jsonify(create_standard_response(success=True, output=draft_result))
        
    except Exception as e:
        return handle_api_error(f"处理音频时发生错误: {str(e)}", e)

@app.route('/create_draft', methods=['POST'])
def create_draft_service():
    """创建新的草稿项目"""
    try:
        data = request.get_json()

        # 获取参数
        draft_id = data.get('draft_id')  # 用户指定的草稿ID
        width = data.get('width', 1080)
        height = data.get('height', 1920)

        # ===== 输入验证 =====
        # 验证draft_id（如果用户指定了）
        if draft_id:
            is_valid, error_msg = validate_draft_id(draft_id)
            if not is_valid:
                return jsonify({'success': False, 'error': f'draft_id验证失败: {error_msg}'}), 400

        # 验证分辨率
        is_valid, error_msg = validate_resolution(int(width), int(height))
        if not is_valid:
            return jsonify({'success': False, 'error': f'分辨率验证失败: {error_msg}'}), 400

        # 创建新草稿
        draft_id, script = get_or_create_draft(draft_id=draft_id, width=width, height=height)
        
        # 初始化草稿缓存，确保预览功能能够识别草稿存在
        if draft_id not in draft_materials_cache:
            draft_materials_cache[draft_id] = []
            # 添加基本草稿信息到缓存
            basic_info = {
                "type": "draft_info",
                "name": data.get('name', '未命名草稿'),
                "width": width,
                "height": height,
                "created_at": datetime.now().isoformat(),
                "status": "created"
            }
            draft_materials_cache[draft_id].append(basic_info)
        
        return jsonify(create_standard_response(
            success=True,
            output={
                "draft_id": draft_id,
                "draft_url": utilgenerate_draft_url(draft_id)
            }
        ))
        
    except Exception as e:
        return handle_api_error(f"创建草稿时发生错误: {str(e)}", e)
        
@app.route('/add_subtitle', methods=['POST'])
def add_subtitle():
    """添加字幕到草稿"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        srt = data.get('srt')
        if not srt:
            return handle_api_error("缺少必需参数 'srt'")
        
        # 获取参数
        params = {
            'srt_path': srt,
            'draft_id': data.get('draft_id'),
            'track_name': data.get('track_name', 'subtitle'),
            'time_offset': data.get('time_offset', 0.0),
            # 字体样式参数
            'font': data.get('font'),
            'font_size': data.get('font_size', 5.0),
            'bold': data.get('bold', False),
            'italic': data.get('italic', False),
            'underline': data.get('underline', False),
            'font_color': data.get('font_color', '#FFFFFF'),
            'vertical': data.get('vertical', False),
            'alpha': data.get('alpha', 1),
            # 边框参数
            'border_alpha': data.get('border_alpha', 1.0),
            'border_color': data.get('border_color', '#000000'),
            'border_width': data.get('border_width', 0.0),
            # 背景参数
            'background_color': data.get('background_color', '#000000'),
            'background_style': data.get('background_style', 0),
            'background_alpha': data.get('background_alpha', 0.0),
            # 位置调整参数
            'transform_x': data.get('transform_x', 0.0),
            'transform_y': data.get('transform_y', -0.8),
            'scale_x': data.get('scale_x', 1.0),
            'scale_y': data.get('scale_y', 1.0),
            'rotation': data.get('rotation', 0.0),
            'width': data.get('width', 1080),
            'height': data.get('height', 1920)
        }
        
        # 调用业务逻辑
        draft_result = add_subtitle_impl(**params)
        
        return jsonify(create_standard_response(success=True, output=draft_result))
        
    except Exception as e:
        return handle_api_error(f"处理字幕时发生错误: {str(e)}", e)

@app.route('/add_text', methods=['POST'])
def add_text():
    data = request.get_json()

    # Get required parameters
    text = data.get('text')
    start = data.get('start', 0)
    end = data.get('end', 5)
    draft_id = data.get('draft_id')

    # ===== 输入验证 =====
    # 验证必填参数
    is_valid, error_msg = validate_required_fields(data, ['text'])
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    # 验证文本内容
    is_valid, error_msg = validate_text_content(text, max_length=10000)
    if not is_valid:
        return jsonify({'success': False, 'error': f'文本内容验证失败: {error_msg}'}), 400

    # 验证draft_id
    if draft_id:
        is_valid, error_msg = validate_draft_id(draft_id)
        if not is_valid:
            return jsonify({'success': False, 'error': f'draft_id验证失败: {error_msg}'}), 400

    # 验证时长
    is_valid, error_msg = validate_duration(start, end)
    if not is_valid:
        return jsonify({'success': False, 'error': f'时长验证失败: {error_msg}'}), 400

    # 验证颜色格式
    font_color = data.get('color', data.get('font_color', "#FF0000"))
    is_valid, error_msg = validate_color(font_color)
    if not is_valid:
        return jsonify({'success': False, 'error': f'字体颜色验证失败: {error_msg}'}), 400

    transform_y = data.get('transform_y', 0)
    transform_x = data.get('transform_x', 0)
    font = data.get('font', "文轩体")
    font_size = data.get('size', data.get('font_size', 8.0))  # Support both 'size' and 'font_size'
    track_name = data.get('track_name', "text_main")
    vertical = data.get('vertical', False)
    font_alpha = data.get('alpha', data.get('font_alpha', 1.0))  # Support both 'alpha' and 'font_alpha'  
    outro_animation = data.get('outro_animation', None)
    outro_duration = data.get('outro_duration', 0.5)
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    
    # New fixed width and height parameters 
    fixed_width = data.get('fixed_width', -1)
    fixed_height = data.get('fixed_height', -1)
    
    # Border parameters
    border_alpha = data.get('border_alpha', 1.0)
    border_color = data.get('border_color', "#000000")
    border_width = data.get('border_width', 0.0)
    
    # Background parameters
    background_color = data.get('background_color', "#000000")
    background_style = data.get('background_style', 0)
    background_alpha = data.get('background_alpha', 0.0)
    background_round_radius = data.get('background_round_radius', 0.0)
    background_height = data.get('background_height', 0.14)  # Background height, range 0.0-1.0
    background_width = data.get('background_width', 0.14)  # Background width, range 0.0-1.0
    background_horizontal_offset = data.get('background_horizontal_offset', 0.5)  # Background horizontal offset, range 0.0-1.0
    background_vertical_offset = data.get('background_vertical_offset', 0.5)  # Background vertical offset, range 0.0-1.0

    # Shadow parameters
    shadow_enabled = data.get('shadow_enabled', False)  # Whether to enable shadow
    shadow_alpha = data.get('shadow_alpha', 0.9)  # Shadow transparency, range 0.0-1.0
    shadow_angle = data.get('shadow_angle', -45.0)  # Shadow angle, range -180.0-180.0
    shadow_color = data.get('shadow_color', "#000000")  # Shadow color
    shadow_distance = data.get('shadow_distance', 5.0)  # Shadow distance
    shadow_smoothing = data.get('shadow_smoothing', 0.15)  # Shadow smoothing, range 0.0-1.0
    
    # Bubble and decorative text effects
    bubble_effect_id = data.get('bubble_effect_id')
    bubble_resource_id = data.get('bubble_resource_id')
    effect_effect_id = data.get('effect_effect_id')
    
    # Entrance animation
    intro_animation = data.get('intro_animation')
    intro_duration = data.get('intro_duration', 0.5)
    
    # Exit animation
    outro_animation = data.get('outro_animation')
    outro_duration = data.get('outro_duration', 0.5)

    # Multi-style text parameters
    text_styles_data = data.get('text_styles', [])
    text_styles = None
    if text_styles_data:
        text_styles = []
        for style_data in text_styles_data:
            # Get style range
            start_pos = style_data.get('start', 0)
            end_pos = style_data.get('end', 0)
            
            # Create text style
            style = Text_style(
                size=style_data.get('style',{}).get('size', font_size),
                bold=style_data.get('style',{}).get('bold', False),
                italic=style_data.get('style',{}).get('italic', False),
                underline=style_data.get('style',{}).get('underline', False),
                color=hex_to_rgb(style_data.get('style',{}).get('color', font_color)),
                alpha=style_data.get('style',{}).get('alpha', font_alpha),
                align=style_data.get('style',{}).get('align', 1),
                vertical=style_data.get('style',{}).get('vertical', vertical),
                letter_spacing=style_data.get('style',{}).get('letter_spacing', 0),
                line_spacing=style_data.get('style',{}).get('line_spacing', 0)
            )
            
            # Create border (if any)
            border = None
            if style_data.get('border',{}).get('width', 0) > 0:
                border = Text_border(
                    alpha=style_data.get('border',{}).get('alpha', border_alpha),
                    color=hex_to_rgb(style_data.get('border',{}).get('color', border_color)),
                    width=style_data.get('border',{}).get('width', border_width)
                )
            
            # Create style range object
            style_range = TextStyleRange(
                start=start_pos,
                end=end_pos,
                style=style,
                border=border,
                font_str=style_data.get('font', font)
            )
            
            text_styles.append(style_range)

    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not text or start is None or end is None:
        error_message = "Hi, the required parameters 'text', 'start' or 'end' are missing. "
        result["error"] = error_message
        return jsonify(result)

    try:
        
        # Call add_text_impl method
        draft_result = add_text_impl(
            text=text,
            start=start,
            end=end,
            draft_id=draft_id,
            transform_y=transform_y,
            transform_x=transform_x,
            font=font,
            font_color=font_color,
            font_size=font_size,
            track_name=track_name,
            vertical=vertical,
            font_alpha=font_alpha,
            border_alpha=border_alpha,
            border_color=border_color,
            border_width=border_width,
            background_color=background_color,
            background_style=background_style,
            background_alpha=background_alpha,
            background_round_radius=background_round_radius,
            background_height=background_height,
            background_width=background_width,
            background_horizontal_offset=background_horizontal_offset,
            background_vertical_offset=background_vertical_offset,
            shadow_enabled=shadow_enabled,
            shadow_alpha=shadow_alpha,
            shadow_angle=shadow_angle,
            shadow_color=shadow_color,
            shadow_distance=shadow_distance,
            shadow_smoothing=shadow_smoothing,
            bubble_effect_id=bubble_effect_id,
            bubble_resource_id=bubble_resource_id,
            effect_effect_id=effect_effect_id,
            intro_animation=intro_animation,
            intro_duration=intro_duration,
            outro_animation=outro_animation,
            outro_duration=outro_duration,
            width=width,
            height=height,
            fixed_width=fixed_width,
            fixed_height=fixed_height,
            text_styles=text_styles
        )
        
        result["success"] = True
        result["output"] = draft_result
        
        # 记录素材信息到缓存
        material_info = {
            "type": "text",
            "content": text,
            "start": start,
            "end": end,
            "duration": end - start if end > start else None,
            "track_name": track_name,
            "font": font,
            "font_size": font_size,
            "added_at": datetime.now().isoformat()
        }
        add_material_to_cache(draft_id, material_info)
        
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing text: {str(e)}. You can click the link below for help: "
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_image', methods=['POST'])
def add_image():
    data = request.get_json()
    
    # Get required parameters
    draft_folder = data.get('draft_folder')
    image_url = data.get('image_url')
    
    # Guard: reject unresolved placeholders
    if isinstance(image_url, str) and ('{{' in image_url or '}}' in image_url):
        return jsonify({"success": False, "error": "image_url 是占位符，未替换为真实地址。请在调用前先生成实际URL。", "hint": image_url})
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    start = data.get('start', 0)
    
    # 🔧 修复：支持 duration 参数（工作流使用）或 end 参数（直接调用）
    duration = data.get('duration')
    if duration is not None:
        # 如果传递了 duration，计算 end = start + duration
        end = start + duration
    else:
        # 否则使用 end 参数（向后兼容）
        end = data.get('end', start + 3.0)  # 默认持续3秒
    
    draft_id = data.get('draft_id')
    transform_y = data.get('transform_y', 0)
    scale_x = data.get('scale_x', 1)
    scale_y = data.get('scale_y', 1)
    transform_x = data.get('transform_x', 0)
    track_name = data.get('track_name', "image_main")  # Default track name
    relative_index = data.get('relative_index', 0)  # New track rendering order index parameter 
    animation = data.get('animation')  # Entrance animation parameter (backward compatibility)
    animation_duration = data.get('animation_duration', 0.5)  # Entrance animation duration
    intro_animation = data.get('intro_animation')  # New entrance animation parameter, higher priority than animation
    intro_animation_duration = data.get('intro_animation_duration', 0.5)
    outro_animation = data.get('outro_animation')  # New exit animation parameter
    outro_animation_duration = data.get('outro_animation_duration', 0.5)  # New exit animation duration
    combo_animation = data.get('combo_animation')  # New combo animation parameter
    combo_animation_duration = data.get('combo_animation_duration', 0.5)  # New combo animation duration
    transition = data.get('transition')  # Transition type parameter
    transition_duration = data.get('transition_duration', 0.5)  # Transition duration parameter, default 0.5 seconds
    
    # New mask related parameters 
    mask_type = data.get('mask_type')  # Mask type
    mask_center_x = data.get('mask_center_x', 0.0)  # Mask center X coordinate
    mask_center_y = data.get('mask_center_y', 0.0)  # Mask center Y coordinate
    mask_size = data.get('mask_size', 0.5)  # Mask main size, relative to canvas height
    mask_rotation = data.get('mask_rotation', 0.0)  # Mask rotation angle
    mask_feather = data.get('mask_feather', 0.0)  # Mask feather parameter
    mask_invert = data.get('mask_invert', False)  # Whether to invert mask
    mask_rect_width = data.get('mask_rect_width')  # Rectangle mask width
    mask_round_corner = data.get('mask_round_corner')  # Rectangle mask rounded corner

    background_blur = data.get('background_blur')  # Background blur level, optional values: 1 (light), 2 (medium), 3 (strong), 4 (maximum), default None (no background blur)

    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not image_url:
        error_message = "Hi, the required parameters 'image_url' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        draft_result = add_image_impl(
            draft_folder=draft_folder,
            image_url=image_url,
            width=width,
            height=height,
            start=start,
            end=end,
            draft_id=draft_id,
            transform_y=transform_y,
            scale_x=scale_x,
            scale_y=scale_y,
            transform_x=transform_x,
            track_name=track_name,
            relative_index=relative_index,  # Pass track rendering order index parameter
            animation=animation,  # Pass entrance animation parameter (backward compatibility)
            animation_duration=animation_duration,  # Pass entrance animation duration
            intro_animation=intro_animation,  # Pass new entrance animation parameter
            intro_animation_duration=intro_animation_duration,
            outro_animation=outro_animation,  # Pass exit animation parameter
            outro_animation_duration=outro_animation_duration,  # Pass exit animation duration
            combo_animation=combo_animation,  # Pass combo animation parameter
            combo_animation_duration=combo_animation_duration,  # Pass combo animation duration
            transition=transition,  # Pass transition type parameter
            transition_duration=transition_duration,  # Pass transition duration parameter (seconds)
            # Pass mask related parameters
            mask_type=mask_type,
            mask_center_x=mask_center_x,
            mask_center_y=mask_center_y,
            mask_size=mask_size,
            mask_rotation=mask_rotation,
            mask_feather=mask_feather,
            mask_invert=mask_invert,
            mask_rect_width=mask_rect_width,
            mask_round_corner=mask_round_corner,
            background_blur=background_blur
        )
        
        result["success"] = True
        result["output"] = draft_result
        
        # 记录素材信息到缓存
        material_info = {
            "type": "image",
            "url": image_url,
            "start": start,
            "end": end,
            "duration": end - start if end > start else None,
            "track_name": track_name,
            "added_at": datetime.now().isoformat()
        }
        add_material_to_cache(draft_id, material_info)
        
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing image: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_video_keyframe', methods=['POST'])
def add_video_keyframe():
    data = request.get_json()
    
    # Get required parameters
    draft_id = data.get('draft_id')
    track_name = data.get('track_name', 'video_main')  # Default main track
    
    # Single keyframe parameters (backward compatibility)
    property_type = data.get('property_type', 'alpha')  # Default opacity
    time = data.get('time', 0.0)  # Default 0 seconds
    value = data.get('value', '1.0')  # Default value 1.0
    
    # Batch keyframe parameters (new)
    property_types = data.get('property_types')  # Property type list
    times = data.get('times')  # Time list
    values = data.get('values')  # Value list

    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    try:
        # Call add_video_keyframe_impl method
        draft_result = add_video_keyframe_impl(
            draft_id=draft_id,
            track_name=track_name,
            property_type=property_type,
            time=time,
            value=value,
            property_types=property_types,
            times=times,
            values=values
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while adding keyframe: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_effect', methods=['POST'])
def add_effect():
    data = request.get_json()
    
    # Get required parameters
    effect_type = data.get('effect_type')  # Effect type name, will match from Video_scene_effect_type or Video_character_effect_type
    start = data.get('start', 0)  # Start time (seconds), default 0
    end = data.get('end', 3.0)  # End time (seconds), default 3 seconds
    draft_id = data.get('draft_id')  # Draft ID, if None or corresponding zip file not found, create new draft
    track_name = data.get('track_name', "effect_01")  # Track name, can be omitted when there is only one effect track
    params = data.get('params')  # Effect parameter list, items not provided or None in parameter list use default values
    width = data.get('width', 1080)
    height = data.get('height', 1920)

    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not effect_type:
        error_message = "Hi, the required parameters 'effect_type' are missing. Please add them and try again."
        result["error"] = error_message
        return jsonify(result)

    try:
        # Call add_effect_impl method
        draft_result = add_effect_impl(
            effect_type=effect_type,
            start=start,
            end=end,
            draft_id=draft_id,
            track_name=track_name,
            params=params,
            width=width,
            height=height
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while adding effect: {str(e)}. "
        result["error"] = error_message
        return jsonify(result)

@app.route('/query_script', methods=['POST'])
def query_script():
    """查询草稿脚本内容"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        draft_id = data.get('draft_id')
        if not draft_id:
            return handle_api_error("缺少必需参数 'draft_id'")
        
        force_update = data.get('force_update', True)
        
        # 调用查询实现方法
        script = query_script_impl(draft_id=draft_id, force_update=force_update)
        
        if script is None:
            return handle_api_error(f"草稿 {draft_id} 在缓存中不存在")
        
        # 将脚本对象转换为JSON可序列化字典
        script_str = script.dumps()
        
        return jsonify(create_standard_response(success=True, output=script_str))
        
    except Exception as e:
        return handle_api_error(f"查询脚本时发生错误: {str(e)}", e)

@app.route('/save_draft', methods=['POST'])
def save_draft():
    """保存草稿到文件系统"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        draft_id = (data.get('draft_id') or '').strip()
        if not draft_id:
            return handle_api_error("缺少必需参数 'draft_id'")
        
        # 获取草稿文件夹参数
        draft_folder = data.get('draft_folder')
        # 获取客户端操作系统信息，默认为windows
        client_os = data.get('client_os', 'windows')
        
        # 调用保存实现方法，启动后台任务
        draft_result = save_draft_impl(draft_id, draft_folder, client_os)
        
        # 直接返回 save_draft_impl 的结果
        return jsonify(draft_result)
        
    except Exception as e:
        return handle_api_error(f"保存草稿时发生错误: {str(e)}", e)

@app.route('/query_draft_status', methods=['POST'])
def query_draft_status():
    """查询草稿任务状态"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        task_id = data.get('task_id')
        if not task_id:
            return handle_api_error("缺少必需参数 'task_id'")
        
        # 获取任务状态
        task_status = query_task_status(task_id)
        
        if task_status["status"] == "not_found":
            return handle_api_error(f"未找到ID为 {task_id} 的任务。请检查任务ID是否正确")
        
        # 直接返回任务状态并添加成功标识
        task_status["success"] = True
        return jsonify(task_status)
        
    except Exception as e:
        return handle_api_error(f"查询任务状态时发生错误: {str(e)}", e)

@app.route('/mirror_to_oss', methods=['POST'])
def mirror_to_oss():
    """Download an external URL (e.g., Dify file URL) and mirror it to our OSS bucket.
    Body: {"url": "http://...", "prefix": "capcut/images"}
    Return: {success, oss_url, object}
    """
    data = request.get_json(force=True, silent=True) or {}
    src_url = (data.get('url') or '').strip()
    prefix = (data.get('prefix') or 'capcut').strip().strip('/')
    if not src_url:
        return jsonify({"success": False, "error": "url required"}), 400
    try:
        # stream download
        r = requests.get(src_url, timeout=20, stream=True)
        r.raise_for_status()
        content_type = r.headers.get('Content-Type', '')
        
        # 🔧 修复：标准化 MIME 类型和扩展名映射
        mime_to_ext = {
            # 图片
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            # 音频
            'audio/mpeg': '.mp3',
            'audio/mp3': '.mp3',  # 非标准但需支持
            'audio/wav': '.wav',
            'audio/ogg': '.ogg',
            'audio/flac': '.flac',
            'audio/mp4': '.m4a',
        }
        
        # 优先使用映射表
        ext = mime_to_ext.get(content_type.lower())
        if not ext:
            # 降级为关键词匹配
            ct_lower = content_type.lower()
            if 'jpeg' in ct_lower or 'jpg' in ct_lower:
                ext = '.jpg'
            elif 'png' in ct_lower:
                ext = '.png'
            elif 'webp' in ct_lower:
                ext = '.webp'
            elif 'gif' in ct_lower:
                ext = '.gif'
            elif 'mpeg' in ct_lower or 'mp3' in ct_lower:
                ext = '.mp3'
            elif 'wav' in ct_lower:
                ext = '.wav'
            else:
                ext = '.bin'  # 默认
        
        # 标准化 Content-Type
        if content_type.lower() == 'audio/mp3':
            content_type = 'audio/mpeg'
        
        object_name = f"{prefix}/{uuid.uuid4().hex}{ext}" if prefix else f"{uuid.uuid4().hex}{ext}"
        bucket = _ensure_bucket_v4()
        
        # 🔧 修复：上传时设置 Content-Type 头部
        headers = {'Content-Type': content_type} if content_type else {}
        logger.info(f"📦 镜像到OSS - 对象名: {object_name}, MIME: {content_type}")
        
        bucket.put_object(object_name, r.raw, headers=headers)
        signed = bucket.sign_url('GET', object_name, 24*60*60, slash_safe=True)
        return jsonify({"success": True, "oss_url": signed, "object": object_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/generate_draft_url', methods=['POST'])
def generate_draft_url():
    data = request.get_json(silent=True) or {}
    
    # Get required parameters
    draft_id = data.get('draft_id')
    draft_folder = data.get('draft_folder')  # Custom client base folder for local save use or display
    force_save = data.get('force_save')
    client_os = (data.get('client_os') or 'windows').lower()
    # Also accept query flag as compatibility
    if force_save is None:
        force_save = request.args.get('force_save', 'false').lower() in ['1', 'true', 'yes']
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }
    
    # Validate required parameters
    if not draft_id:
        error_message = "Hi, the required parameter 'draft_id' is missing. Please add it and try again."
        result["error"] = error_message
        return jsonify(result)
    
    try:
        # Sanitize and encode draft_id to avoid newline/space issues
        if isinstance(draft_id, str):
            draft_id = draft_id.strip()
        else:
            draft_id = str(draft_id).strip()
        safe_id = quote(draft_id, safe='-_.')

        # If upload-to-OSS mode is enabled and the draft zip already exists, return signed URL directly
        if IS_UPLOAD_DRAFT:
            signed_url, exists = get_signed_draft_url_if_exists(draft_id)
            if exists and signed_url:
                # If client provided customization info (os or draft_folder), generate derived zip
                if draft_folder or (client_os and client_os != 'windows'):
                    try:
                        if not draft_folder:
                            # If no explicit draft_folder, keep as-is but return base URL
                            pass
                        else:
                            custom_url = get_customized_signed_url(draft_id, client_os, draft_folder)
                            draft_result = {"draft_url": custom_url, "storage": "oss", "client_os": client_os, "draft_folder": draft_folder or ""}
                            result["success"] = True
                            result["output"] = draft_result
                            return jsonify(result)
                    except Exception as _:
                        # Fall back to base signed url on any failure
                        pass
                draft_result = {"draft_url": signed_url, "storage": "oss", "client_os": client_os, "draft_folder": draft_folder or ""}
                result["success"] = True
                result["output"] = draft_result
                return jsonify(result)

            # Not exists: if force_save requested, kick off background save now
            if force_save:
                task_info = save_draft_impl(draft_id, draft_folder, client_os)
                out = {
                    "status": "processing",
                    "task_id": task_info.get("task_id", draft_id),
                    "message": "Save task started. Please poll /query_draft_status until completed, then call /generate_draft_url again.",
                    "next": {
                        "query": "/query_draft_status",
                        "generate": "/generate_draft_url"
                    },
                    "client_os": client_os,
                    "draft_folder": draft_folder or ""
                }
                result["success"] = True
                result["output"] = out
                return jsonify(result)

        # Fallback to local preview router page
        draft_result = { "draft_url" : f"{DRAFT_DOMAIN}{PREVIEW_ROUTER}?draft_id={safe_id}", "storage": "local", "client_os": client_os, "draft_folder": draft_folder or ""}
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)
        
    except Exception as e:
        error_message = f"Error occurred while saving draft: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

    
    import json as _json
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>草稿下载 - {draft_id}</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif; 
                padding: 0; 
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .header {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 15px 20px;
                color: white;
                text-align: center;
                font-size: 20px;
                font-weight: 600;
            }
            .container { 
                max-width: 900px; 
                margin: 20px auto; 
                background: #fff; 
                border-radius: 15px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
                overflow: hidden;
            }
            .card-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                text-align: center;
            }
            .card-body {
                padding: 30px;
            }
            .draft-info {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 25px;
                border-left: 4px solid #667eea;
            }
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            .info-item {
                background: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .info-item .label {
                font-size: 12px;
                color: #6c757d;
                margin-bottom: 5px;
            }
            .info-item .value {
                font-size: 18px;
                font-weight: 600;
                color: #495057;
            }
            .controls-section {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 25px;
            }
            .section-title {
                font-size: 16px;
                font-weight: 600;
                color: #495057;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .row { 
                display: flex; 
                align-items: center; 
                gap: 15px; 
                flex-wrap: wrap; 
                margin-bottom: 15px;
            }
            .form-group {
                flex: 1;
                min-width: 200px;
            }
            .form-group label {
                display: block;
                font-size: 14px;
                color: #495057;
                margin-bottom: 5px;
                font-weight: 500;
            }
            .id { 
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; 
                color: #667eea; 
                background: rgba(102, 126, 234, 0.1);
                padding: 3px 8px;
                border-radius: 4px;
                font-weight: 600;
            }
            .path { 
                background: #e9ecef; 
                padding: 12px; 
                border-radius: 8px; 
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; 
                font-size: 13px;
                overflow-x: auto;
                border: 1px solid #dee2e6;
                word-break: break-all;
            }
            .alert { 
                color: #155724;
                background: #d1ecf1;
                border: 1px solid #bee5eb;
                border-radius: 8px;
                padding: 15px;
                margin: 15px 0;
                font-size: 14px;
            }
            .alert-info {
                color: #0c5460;
                background: #d1ecf1;
                border-color: #bee5eb;
            }
            .alert-warning {
                color: #856404;
                background: #fff3cd;
                border-color: #ffeaa7;
            }
            .btn { 
                background: #667eea; 
                color: #fff; 
                border: none; 
                padding: 12px 20px; 
                border-radius: 8px; 
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                min-width: 120px;
                justify-content: center;
            }
            .btn:hover { 
                background: #5a6fd8;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }
            .btn:disabled { 
                opacity: 0.6; 
                cursor: not-allowed; 
                transform: none;
                box-shadow: none;
            }
            .btn-secondary {
                background: #6c757d;
            }
            .btn-secondary:hover {
                background: #5a6268;
            }
            .btn-success {
                background: #28a745;
            }
            .btn-success:hover {
                background: #218838;
            }
            .log { 
                margin-top: 15px; 
                background: #f8f9fa; 
                border-radius: 8px; 
                padding: 15px; 
                height: 200px; 
                overflow-y: auto; 
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; 
                font-size: 12px;
                border: 1px solid #dee2e6;
                line-height: 1.5;
            }
            select, input[type="text"] { 
                padding: 10px 12px; 
                border-radius: 8px; 
                border: 1px solid #ced4da; 
                font-size: 14px;
                transition: border-color 0.3s ease, box-shadow 0.3s ease;
                width: 100%;
                box-sizing: border-box;
            }
            select:focus, input[type="text"]:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .action-buttons {
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                justify-content: center;
                margin-top: 20px;
            }
            .status-display {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin-top: 15px;
                border: 1px solid #dee2e6;
                text-align: center;
                font-weight: 500;
            }
            .loading {
                display: inline-block;
                width: 12px;
                height: 12px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 8px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .feature-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border: 1px solid #e9ecef;
            }
            .feature-icon {
                font-size: 24px;
                margin-bottom: 10px;
            }
            .feature-title {
                font-weight: 600;
                margin-bottom: 8px;
            }
            .feature-desc {
                font-size: 13px;
                color: #6c757d;
                line-height: 1.4;
            }
            @media (max-width: 768px) {
                .container {
                    margin: 10px;
                    border-radius: 10px;
                }
                .card-body {
                    padding: 20px;
                }
                .row {
                    flex-direction: column;
                    align-items: stretch;
                }
                .action-buttons {
                    flex-direction: column;
                }
                .btn {
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            🎬 CapCutAPI - 草稿下载中心
        </div>
        
        <div class="container">
            <div class="card-header">
                <h2 style="margin: 0;">草稿下载管理</h2>
                <p style="margin: 10px 0 0; opacity: 0.9;">智能下载 · 多平台支持 · 云端同步</p>
            </div>
            
            <div class="card-body">
                <!-- 草稿信息展示 -->
                <div class="draft-info">
                    <div class="section-title">
                        📋 草稿信息
                    </div>
                    <p><strong>草稿 ID：</strong><span class="id">{draft_id}</span></p>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="label">素材数量</div>
                            <div class="value">{materials_count}</div>
                        </div>
                        <div class="info-item">
                            <div class="label">预计时长</div>
                            <div class="value">{total_duration}s</div>
                        </div>
                        <div class="info-item">
                            <div class="label">存储状态</div>
                            <div class="value">云端已保存</div>
                        </div>
                        <div class="info-item">
                            <div class="label">画面尺寸</div>
                            <div class="value">1080×1920</div>
                        </div>
                    </div>
                </div>
                
                <!-- 下载配置 -->
                <div class="controls-section">
                    <div class="section-title">
                        ⚙️ 下载配置
                    </div>
                    <div class="row">
                        <div class="form-group">
                            <label>目标系统:</label>
                            <select id="osSelect">
                                <option value="windows">Windows</option>
                                <option value="linux">Linux</option>
                                <option value="macos">macOS</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>自定义根路径 (可选):</label>
                            <input id="baseInput" type="text" placeholder="如: F:/MyDrafts 或 /data/drafts" />
                        </div>
                    </div>
                    
                    <div class="alert alert-info">
                        <strong>💡 提示：</strong>系统会根据你的选择自动生成适合的本地路径格式。OSS云下载模式下，文件会自动下载到指定位置。
                    </div>
                </div>
                
                <!-- 路径预览 -->
                <div class="controls-section">
                    <div class="section-title">
                        📁 本地路径预览
                    </div>
                    <div class="path" id="localPath">获取本地路径中...</div>
                </div>
                
                <!-- 功能特性展示 -->
                <div class="controls-section">
                    <div class="section-title">
                        ✨ 功能特性
                    </div>
                    <div class="feature-grid">
                        <div class="feature-card">
                            <div class="feature-icon">☁️</div>
                            <div class="feature-title">智能云下载</div>
                            <div class="feature-desc">自动检测云端文件，提供高速下载链接，支持断点续传</div>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🔄</div>
                            <div class="feature-title">实时同步</div>
                            <div class="feature-desc">草稿状态实时更新，支持后台处理进度监控</div>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🎯</div>
                            <div class="feature-title">精准适配</div>
                            <div class="feature-desc">根据系统类型自动调整路径格式，无缝集成到剪映</div>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">📱</div>
                            <div class="feature-title">多平台支持</div>
                            <div class="feature-desc">支持Windows、Linux、macOS等多种操作系统</div>
                        </div>
                    </div>
                </div>
                
                <!-- 操作按钮 -->
                <div class="action-buttons">
                    <button id="previewBtn" class="btn btn-secondary" onclick="openPreview()">
                        🔍 预览草稿
                    </button>
                    <button id="saveUploadBtn" class="btn">
                        ☁️ 智能下载
                    </button>
                    <button id="copyPathBtn" class="btn btn-success" onclick="copyLocalPath()">
                        📋 复制路径
                    </button>
                </div>
                
                <!-- 状态显示 -->
                <div id="status" class="status-display">准备就绪</div>
                
                <!-- 日志显示 -->
                <div id="log" class="log" style="display: none;"></div>
            </div>
        </div>
        
        <script>
            const draftId = "{draft_id}";
            const btn = document.getElementById('saveUploadBtn');
            const statusEl = document.getElementById('status');
            const logEl = document.getElementById('log');
            const osSelect = document.getElementById('osSelect');
            const baseInput = document.getElementById('baseInput');
            
            // 设置初始系统类型
            osSelect.value = "{client_os}";
            try { 
                baseInput.value = new URL(window.location.href).searchParams.get('base') || ''; 
            } catch(e) {}
            
            // 监听系统选择变化
            osSelect.addEventListener('change', () => {
                updateLocalPath();
                updateURL();
            });
            
            // 监听路径输入变化
            baseInput.addEventListener('input', () => {
                updateLocalPath();
                updateURL();
            });
            
            // 更新URL参数
            function updateURL() {
                const url = new URL(window.location.href);
                url.searchParams.set('draft_id', draftId);
                url.searchParams.set('os', osSelect.value);
                if (baseInput.value) {
                    url.searchParams.set('base', baseInput.value);
                } else {
                    url.searchParams.delete('base');
                }
                window.history.replaceState({}, '', url.toString());
            }
            
            // 更新本地路径显示
            function updateLocalPath() {
                const localPathEl = document.getElementById('localPath');
                const clientOs = osSelect.value;
                const customBase = baseInput.value;
                
                let localPath = '';
                if (clientOs === 'windows') {
                    const base = customBase || 'F:\\\\jianyin\\\\cgwz\\\\JianyingPro Drafts';
                    localPath = base + '\\\\' + draftId;
                } else if (clientOs === 'macos') {
                    const base = customBase || '/Users/' + (window.navigator.userAgent.includes('Mac') ? 'YourUsername' : 'username') + '/Documents/JianyingPro Drafts';
                    localPath = base + '/' + draftId;
                } else {
                    const base = customBase || '/data/drafts';
                    localPath = base + '/' + draftId;
                }
                
                localPathEl.textContent = localPath;
            }
            
            // 日志记录函数
            function log(msg) {
                const t = new Date().toLocaleTimeString();
                logEl.textContent += `[${t}] ${msg}\\n`;
                logEl.scrollTop = logEl.scrollHeight;
                logEl.style.display = 'block';
            }
            
            // 复制本地路径
            function copyLocalPath() {
                const localPath = document.getElementById('localPath').textContent;
                navigator.clipboard.writeText(localPath).then(() => {
                    statusEl.innerHTML = '✅ 本地路径已复制到剪贴板';
                    setTimeout(() => {
                        statusEl.textContent = '准备就绪';
                    }, 3000);
                }).catch(() => {
                    statusEl.innerHTML = '❌ 复制失败，请手动复制：' + localPath;
                });
            }
            
            // 打开预览页面
            function openPreview() {
                const previewUrl = `/draft/preview/${draftId}`;
                window.open(previewUrl, '_blank');
            }
            
            // 发送JSON请求
            async function postJSON(url, body) {
                const res = await fetch(url, { 
                    method: 'POST', 
                    headers: {'Content-Type':'application/json'}, 
                    body: JSON.stringify(body) 
                });
                return await res.json();
            }
            
            // 轮询状态
            async function pollStatus(taskId) {
                while (true) {
                    const s = await postJSON('/query_draft_status', { task_id: taskId });
                    if (s && s.status) {
                        statusEl.innerHTML = `<div class="loading"></div>任务状态: ${s.status}，进度: ${s.progress||0}% ${s.message||''}`;
                        log(`status=${s.status}, progress=${s.progress}`);
                        if (s.status === 'completed') break;
                        if (s.status === 'failed') throw new Error(s.message || '任务失败');
                    }
                    await new Promise(r => setTimeout(r, 2000));
                }
            }
            
            // 最终跳转
            async function finalizeRedirect() {
                const r = await postJSON('/generate_draft_url', { 
                    draft_id: draftId, 
                    client_os: osSelect.value, 
                    draft_folder: baseInput.value || undefined 
                });
                if (r && r.success && r.output && r.output.draft_url) {
                    log('🎉 获取下载链接成功，即将跳转');
                    statusEl.innerHTML = '🎉 下载链接获取成功！即将跳转...';
                    setTimeout(() => {
                        window.open(r.output.draft_url, '_blank');
                    }, 1000);
                } else {
                    throw new Error('未获取到下载链接');
                }
            }
            
            // 自动运行
            async function autoRun() {
                try {
                    btn.disabled = true;
                    statusEl.innerHTML = '<div class="loading"></div>正在检测云端文件...';
                    log('🔍 检测是否已存在 OSS 直链');
                    
                    const first = await postJSON('/generate_draft_url', { 
                        draft_id: draftId, 
                        client_os: osSelect.value, 
                        draft_folder: baseInput.value || undefined 
                    }});
                    
                    if (first && first.success && first.output) {
                        if (first.output.storage === 'oss' && first.output.draft_url) {
                            log('✅ 发现已存在的云端文件，直接跳转');
                            statusEl.innerHTML = '✅ 发现云端文件！即将跳转下载...';
                            setTimeout(() => {{
                                window.open(first.output.draft_url, '_blank');
                            }, 1000);
                            return;
                        }
                    }
                    
                    log('📤 未发现直链，自动触发保存并上传');
                    statusEl.innerHTML = '<div class="loading"></div>正在提交保存任务...';
                    
                    const start = await postJSON('/generate_draft_url?force_save=true', { 
                        draft_id: draftId, 
                        client_os: osSelect.value, 
                        draft_folder: baseInput.value || undefined 
                    }});
                    
                    if (start && start.success && start.output) {
                        if (start.output.storage === 'oss' && start.output.draft_url) {
                            log('⚡ 快速保存完成，直接跳转');
                            window.open(start.output.draft_url, '_blank');
                            return;
                        }
                        if (start.output.status === 'processing' && start.output.task_id) {
                            log('⏳ 任务已提交，等待处理完成...');
                            await pollStatus(start.output.task_id);
                            await finalizeRedirect();
                            return;
                        }
                    }
                    throw new Error('自动流程接口返回异常');
                } catch (e) {
                    log('❌ 自动流程失败: ' + e.message);
                    statusEl.innerHTML = '❌ 自动下载失败，请点击按钮重试';
                } finally {
                    btn.disabled = false;
                }
            }
            
            // 页面加载完成后初始化
            document.addEventListener('DOMContentLoaded', () => {
                updateLocalPath();
                // 延迟启动自动下载，给用户时间看到页面
                setTimeout(autoRun, 1000);
            });
            
            // 手动下载按钮事件
            btn.addEventListener('click', async () => {
                btn.disabled = true; 
                statusEl.innerHTML = '<div class="loading"></div>正在提交任务...'; 
                log('🚀 手动触发 force_save 请求');
                try {
                    const r = await postJSON('/generate_draft_url?force_save=true', { 
                        draft_id: draftId, 
                        client_os: osSelect.value, 
                        draft_folder: baseInput.value || undefined 
                    }});
                    if (r && r.success && r.output) {
                        if (r.output.storage === 'oss' && r.output.draft_url) {
                            window.open(r.output.draft_url, '_blank');
                            return;
                        }
                        if (r.output.status === 'processing' && r.output.task_id) {
                            await pollStatus(r.output.task_id);
                            await finalizeRedirect();
                            return;
                        }
                    }
                    throw new Error('接口返回异常');
                } catch (e) {
                    statusEl.innerHTML = '❌ 操作失败: ' + e.message;
                    log('❌ 失败: ' + e.message);
                } finally {
                    btn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """.format(
        draft_id=draft_id,
        client_os=client_os,
        materials_count=materials_count,
        total_duration=total_duration
    )
    
    return html_template

@app.route('/add_sticker', methods=['POST'])
def add_sticker():
    data = request.get_json()
    # Get required parameters
    resource_id = data.get('sticker_id')
    start = data.get('start', 0)
    end = data.get('end', 5.0)  # Default display 5 seconds
    draft_id = data.get('draft_id')
    transform_y = data.get('transform_y', 0)
    transform_x = data.get('transform_x', 0)
    alpha = data.get('alpha', 1.0)
    flip_horizontal = data.get('flip_horizontal', False)
    flip_vertical = data.get('flip_vertical', False)
    rotation = data.get('rotation', 0.0)
    scale_x = data.get('scale_x', 1.0)
    scale_y = data.get('scale_y', 1.0)
    track_name = data.get('track_name', 'sticker_main')
    relative_index = data.get('relative_index', 0)
    width = data.get('width', 1080)
    height = data.get('height', 1920)

    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not resource_id:
        error_message = "Hi, the required parameter 'sticker_id' is missing. Please add it and try again. "
        result["error"] = error_message
        return jsonify(result)

    try:
        # Call add_sticker_impl method
        draft_result = add_sticker_impl(
            resource_id=resource_id,
            start=start,
            end=end,
            draft_id=draft_id,
            transform_y=transform_y,
            transform_x=transform_x,
            alpha=alpha,
            flip_horizontal=flip_horizontal,
            flip_vertical=flip_vertical,
            rotation=rotation,
            scale_x=scale_x,
            scale_y=scale_y,
            track_name=track_name,
            relative_index=relative_index,
            width=width,
            height=height
        )

        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while adding sticker: {str(e)}. "
        result["error"] = error_message
        return jsonify(result)

# ===== 元数据获取API =====

@app.route('/get_intro_animation_types', methods=['GET'])
def get_intro_animation_types():
    """获取支持的入场动画类型列表"""
    try:
        animation_types = []
        
        if IS_CAPCUT_ENV:
            # 返回CapCut环境下的入场动画类型
            for name in CapCut_Intro_type.__members__:
                animation_types.append({"name": name})
        else:
            # 返回剪映环境下的入场动画类型
            for name in Intro_type.__members__:
                animation_types.append({"name": name})
        
        return jsonify(create_standard_response(success=True, output=animation_types))
    
    except Exception as e:
        return handle_api_error(f"获取入场动画类型时发生错误: {str(e)}", e)

@app.route('/get_outro_animation_types', methods=['GET'])
def get_outro_animation_types():
    """获取支持的出场动画类型列表"""
    try:
        animation_types = []
        
        if IS_CAPCUT_ENV:
            # 返回CapCut环境下的出场动画类型
            for name in CapCut_Outro_type.__members__:
                animation_types.append({"name": name})
        else:
            # 返回剪映环境下的出场动画类型
            for name in Outro_type.__members__:
                animation_types.append({"name": name})
        
        return jsonify(create_standard_response(success=True, output=animation_types))
    
    except Exception as e:
        return handle_api_error(f"获取出场动画类型时发生错误: {str(e)}", e)

@app.route('/get_transition_types', methods=['GET'])
def get_transition_types():
    """获取支持的转场动画类型列表"""
    try:
        transition_types = []
        
        if IS_CAPCUT_ENV:
            # 返回CapCut环境下的转场动画类型
            for name in CapCut_Transition_type.__members__:
                transition_types.append({"name": name})
        else:
            # 返回剪映环境下的转场动画类型
            for name in Transition_type.__members__:
                transition_types.append({"name": name})
        
        return jsonify(create_standard_response(success=True, output=transition_types))
    
    except Exception as e:
        return handle_api_error(f"获取转场动画类型时发生错误: {str(e)}", e)


@app.route('/get_mask_types', methods=['GET'])
def get_mask_types():
    """获取支持的遮罩类型列表"""
    try:
        mask_types = []
        
        if IS_CAPCUT_ENV:
            for name in CapCut_Mask_type.__members__:
                mask_types.append({"name": name})
        else:
            for name in Mask_type.__members__:
                mask_types.append({"name": name})
        
        return jsonify(create_standard_response(success=True, output=mask_types))
    
    except Exception as e:
        return handle_api_error(f"获取遮罩类型时发生错误: {str(e)}", e)

@app.route('/get_font_types', methods=['GET'])
def get_font_types():
    """获取支持的字体类型列表"""
    try:
        font_types = []
        
        # 返回剪映环境下的字体类型
        for name in Font_type.__members__:
            font_types.append({"name": name})
        
        return jsonify(create_standard_response(success=True, output=font_types))
    
    except Exception as e:
        return handle_api_error(f"获取字体类型时发生错误: {str(e)}", e)


@app.route('/get_text_intro_types', methods=['GET'])
def get_text_intro_types():
    """Return supported text entrance animation type list
    
    If IS_CAPCUT_ENV is True, return text entrance animation types in CapCut environment
    Otherwise return text entrance animation types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        text_intro_types = []
        
        if IS_CAPCUT_ENV:
            # Return text entrance animation types in CapCut environment
            for name, member in CapCut_Text_intro.__members__.items():
                text_intro_types.append({
                    "name": name
                })
        else:
            # Return text entrance animation types in JianYing environment
            for name, member in Text_intro.__members__.items():
                text_intro_types.append({
                    "name": name
                })
        
        result["output"] = text_intro_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting text entrance animation types: {str(e)}"
        return jsonify(result)

@app.route('/get_text_outro_types', methods=['GET'])
def get_text_outro_types():
    """Return supported text exit animation type list
    
    If IS_CAPCUT_ENV is True, return text exit animation types in CapCut environment
    Otherwise return text exit animation types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        text_outro_types = []
        
        if IS_CAPCUT_ENV:
            # Return text exit animation types in CapCut environment
            for name, member in CapCut_Text_outro.__members__.items():
                text_outro_types.append({
                    "name": name
                })
        else:
            # Return text exit animation types in JianYing environment
            for name, member in Text_outro.__members__.items():
                text_outro_types.append({
                    "name": name
                })
        
        result["output"] = text_outro_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting text exit animation types: {str(e)}"
        return jsonify(result)

@app.route('/get_text_loop_anim_types', methods=['GET'])
def get_text_loop_anim_types():
    """Return supported text loop animation type list
    
    If IS_CAPCUT_ENV is True, return text loop animation types in CapCut environment
    Otherwise return text loop animation types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        text_loop_anim_types = []
        
        if IS_CAPCUT_ENV:
            # Return text loop animation types in CapCut environment
            for name, member in CapCut_Text_loop_anim.__members__.items():
                text_loop_anim_types.append({
                    "name": name
                })
        else:
            # Return text loop animation types in JianYing environment
            for name, member in Text_loop_anim.__members__.items():
                text_loop_anim_types.append({
                    "name": name
                })
        
        result["output"] = text_loop_anim_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting text loop animation types: {str(e)}"
        return jsonify(result)


@app.route('/get_video_scene_effect_types', methods=['GET'])
def get_video_scene_effect_types():
    """Return supported scene effect type list
    
    If IS_CAPCUT_ENV is True, return scene effect types in CapCut environment
    Otherwise return scene effect types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        effect_types = []
        
        if IS_CAPCUT_ENV:
            # Return scene effect types in CapCut environment
            for name, member in CapCut_Video_scene_effect_type.__members__.items():
                effect_types.append({
                    "name": name
                })
        else:
            # Return scene effect types in JianYing environment
            for name, member in Video_scene_effect_type.__members__.items():
                effect_types.append({
                    "name": name
                })
        
        result["output"] = effect_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting scene effect types: {str(e)}"
        return jsonify(result)


@app.route('/get_video_character_effect_types', methods=['GET'])
def get_video_character_effect_types():
    """Return supported character effect type list
    
    If IS_CAPCUT_ENV is True, return character effect types in CapCut environment
    Otherwise return character effect types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        effect_types = []
        
        if IS_CAPCUT_ENV:
            # Return character effect types in CapCut environment
            for name, member in CapCut_Video_character_effect_type.__members__.items():
                effect_types.append({
                    "name": name
                })
        else:
            # Return character effect types in JianYing environment
            for name, member in Video_character_effect_type.__members__.items():
                effect_types.append({
                    "name": name
                })
        
        result["output"] = effect_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting character effect types: {str(e)}"
        return jsonify(result)

@app.route('/upload_to_oss', methods=['POST'])
def upload_to_oss_route():
    """Upload binary content to OSS and return signed url.
    Accepts:
    - multipart/form-data: file=<binary>, prefix, content_type (optional)
    - application/json: {"filename":"a.png","data_base64":"...","prefix":"capcut/images"}
    Return: {success, oss_url, object}
    """
    try:
        prefix = (request.form.get('prefix') or request.args.get('prefix') or 'capcut').strip().strip('/')
        data = None
        filename = None
        content_type = None
        
        if 'file' in request.files:
            f = request.files['file']
            data = f.read()
            filename = f.filename or 'upload.bin'
            # 获取 Content-Type（优先使用表单字段，其次使用文件对象）
            content_type = request.form.get('content_type') or f.content_type
        else:
            js = request.get_json(silent=True) or {}
            filename = js.get('filename') or 'upload.bin'
            content_type = js.get('content_type')
            b64 = js.get('data_base64') or ''
            if b64:
                import base64
                try:
                    data = base64.b64decode(b64)
                except Exception:
                    return jsonify({"success": False, "error": "invalid base64"}), 400
        
        if not data:
            return jsonify({"success": False, "error": "no file provided"}), 400
        
        # 🔧 修复：智能推断扩展名和 MIME 类型
        ext = '.bin'
        lower = (filename or '').lower()
        
        # 扩展名到 MIME 类型映射
        ext_to_mime = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac',
        }
        
        # 从文件名推断扩展名
        for file_ext, mime in ext_to_mime.items():
            if lower.endswith(file_ext):
                ext = file_ext
                if not content_type:  # 如果没有提供 Content-Type，使用映射
                    content_type = mime
                break
        
        # 标准化 Content-Type
        if content_type and content_type.lower() == 'audio/mp3':
            content_type = 'audio/mpeg'
        
        # 如果还没有 Content-Type，设置默认值
        if not content_type:
            content_type = 'application/octet-stream'
        
        object_name = f"{prefix}/{uuid.uuid4().hex}{ext}" if prefix else f"{uuid.uuid4().hex}{ext}"
        bucket = _ensure_bucket_v4()
        
        # 🔧 修复：上传时设置 Content-Type 头部
        headers = {'Content-Type': content_type}
        logger.info(f"📦 上传到OSS - 文件名: {filename}, 对象名: {object_name}, MIME: {content_type}")
        
        bucket.put_object(object_name, data, headers=headers)
        signed = bucket.sign_url('GET', object_name, 24*60*60, slash_safe=True)
        return jsonify({"success": True, "oss_url": signed, "object": object_name})
    except Exception as e:
        logger.error(f"上传到OSS失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# 草稿管理相关路由
@app.route('/api/drafts/dashboard', methods=['GET'])
def drafts_dashboard():
    """草稿管理仪表板页面"""
    try:
        from flask import render_template
        return render_template('dashboard.html')
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>仪表板错误</title>
            <style>body{{font-family:Arial;margin:40px;text-align:center;}}</style>
        </head>
        <body>
            <h1>❌ 仪表板加载失败</h1>
            <p>错误信息: {str(e)}</p>
            <p><a href="/">返回首页</a></p>
        </body>
        </html>
        """

# 草稿预览路由
@app.route('/api/drafts/preview/<draft_id>', methods=['GET'])
def preview_draft(draft_id):
    """
    预览特定草稿，显示草稿信息和素材
    """
    try:
        # 获取草稿信息
        draft_info = get_draft_info(draft_id)
        if not draft_info:
            return f"<h1>草稿不存在</h1><p>草稿ID: {draft_id}</p>", 404
        
        # 获取草稿素材
        materials = get_draft_materials(draft_id)
        
        # 计算总时长
        total_duration = 0
        for material in materials:
            if material.get('duration', 0) > 0:
                total_duration = max(total_duration, material.get('start_time', 0) + material.get('duration', 0))
        
        # 渲染预览页面
        return render_template_with_official_style(draft_id, materials, total_duration)
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>错误</title>
        </head>
        <body>
            <h1>加载草稿时出错</h1>
            <p>错误信息: {str(e)}</p>
            <a href="/api/drafts/dashboard">返回仪表板</a>
        </body>
        </html>
        """
        # 使用简单的字符串替换，避免格式化问题
        # 生成SSR内容
        def html_escape(text: str) -> str:
                        return html.escape(text) if isinstance(text, str) else str(text)

        # Details 首屏渲染：展示第一个素材
        first = materials[0] if materials else {}
        startTime = float(first.get('start_time') or first.get('start') or 0)
        duration = float(first.get('duration') or ((first.get('end') or 0) - (first.get('start') or 0)) or 0)
        endTime = startTime + duration
        ssr_rows = [
            ('Type:', first.get('type') or 'video'),
            ('Source URL:', first.get('source_url') or first.get('url') or 'N/A'),
            ('Start Time:', f"{startTime:.2f}s"),
            ('End Time:', f"{endTime:.2f}s"),
            ('Duration:', f"{duration:.2f}s"),
            ('Track Name:', first.get('track_name') or 'N/A'),
        ]
        ssr_details_rows = ''.join([
            f"<tr><td>{html_escape(k)}</td><td>" + (f"<a class='url-link' target='_blank' href='{html_escape(v)}'>{html_escape(v)}</a>" if k=='Source URL:' and v!='N/A' else html_escape(v)) + "</td></tr>"
            for k, v in ssr_rows
        ])

        # Timeline 首屏渲染
        lane_order = {'video':0, 'image':1, 'text':2, 'audio_voice':3, 'audio_bgm':4, 'audio':4}
        def classify_audio(m):
            tn = (m.get('track_name') or '')
            if any(x in tn.lower() for x in ['voice', 'narrat']):
                return 'audio_voice'
            if any(x in tn.lower() for x in ['bgm', 'music']):
                return 'audio_bgm'
            return 'audio'
        lane_height, gap = 28, 4
        tl_width_pct = 100  # SSR 用百分比，前端接管后会重算像素
        ssr_blocks = []
        for idx, m in enumerate(materials):
            mtype = m.get('type') or 'video'
            if mtype == 'audio':
                mtype = classify_audio(m)
            s = float(m.get('start_time') or m.get('start') or 0)
            d = float(m.get('duration') or ((m.get('end') or 0) - (m.get('start') or 0)) or 0)
            left_pct = (s / max(total_duration, 1)) * tl_width_pct
            width_pct = max((d / max(total_duration, 1)) * tl_width_pct, 3)
            lane_idx = lane_order.get(mtype, 0)
            top_px = lane_idx * (lane_height + gap)
            name = m.get('name') or (m.get('source_url') or m.get('url') or '').split('/')[-1] or 'Material'
            short = (name[:22] + '...') if len(name) > 25 else name
            icon = '🎥' if m.get('type')=='video' else '🎵' if m.get('type')=='audio' else '📝' if m.get('type')=='text' else '🖼️' if m.get('type')=='image' else '📄'
            ssr_blocks.append(
                f"<div class='material-block {m.get('type','video')} lane-height' style='left:{left_pct}%;width:{width_pct}%;top:{top_px}px'><span class='material-icon'>{icon}</span><span style='font-size:11px'>{html_escape(short)}</span><span style='font-size:10px;opacity:.9;margin-left:6px'>{d:.1f}s</span></div>"
            )
        lanes_used = 0
        for m in materials:
            mt = m.get('type') or 'video'
            if mt == 'audio':
                mt = classify_audio(m)
            lanes_used = max(lanes_used, lane_order.get(mt, 0))
        ssr_timeline_blocks = ''.join(ssr_blocks)
        ssr_timeline_height = (lanes_used + 1) * (lane_height + gap)
        result = html_template.replace('{draft_id}', draft_id) \
                              .replace('{materials_json}', materials_json) \
                              .replace('{total_duration}', str(total_duration)) \
                              .replace('{ssr_details_rows}', ssr_details_rows) \
                                                             .replace('{ssr_timeline_blocks}', ssr_timeline_blocks) \
                              .replace('{ssr_timeline_height}', str(ssr_timeline_height))
        resp = Response(result)
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
        
    except Exception as e:
        return f"预览页面生成失败: {str(e)}", 500
        
@app.route('/debug/cache/<draft_id>', methods=['GET'])
def debug_cache(draft_id: str):
    """调试：查看草稿缓存内容"""
    materials = get_draft_materials(draft_id)
    return jsonify({
        "success": True,
        "draft_id": draft_id,
        "materials_count": len(materials),
        "materials": materials,
        "cache_source": "test_materials.json" if draft_id in draft_materials_cache else "cache"
    })

@app.route('/api/drafts/list', methods=['GET'])
def list_drafts():
    """获取所有可用草稿列表 - 新增功能"""
    try:
        from datetime import datetime
        import os
        
        db_drafts = get_all_drafts()
        
        drafts_list = []
        for draft in db_drafts:
            # 获取草稿的详细信息
            materials = get_draft_materials(draft['id'])
            material_count = len(materials) if materials else 0
            
            # 计算文件大小(估算)
            total_size = material_count * 1024 * 1024  # 每个素材估算1MB
            
            # 处理时间格式 - 使用正确的字段名
            try:
                if draft.get('modified_time') and draft['modified_time'] != '未知':
                    # 尝试解析时间字符串
                    from datetime import datetime
                    if isinstance(draft['modified_time'], str):
                        # 如果是字符串格式，转换为时间戳
                        dt = datetime.strptime(draft['modified_time'], '%Y-%m-%d %H:%M:%S')
                        timestamp = int(dt.timestamp())
                    else:
                        timestamp = int(draft['modified_time'])
                else:
                    timestamp = int(datetime.now().timestamp())
            except:
                timestamp = int(datetime.now().timestamp())
            
            # 创建时间处理
            try:
                if draft.get('created_time') and draft['created_time'] != '未知':
                    if isinstance(draft['created_time'], str):
                        dt = datetime.strptime(draft['created_time'], '%Y-%m-%d %H:%M:%S')
                        create_timestamp = int(dt.timestamp())
                    else:
                        create_timestamp = int(draft['created_time'])
                else:
                    create_timestamp = timestamp
            except:
                create_timestamp = timestamp
                
            # 状态映射函数 - 正确处理所有草稿状态
            def map_draft_status(db_status):
                """
                将数据库中的草稿状态映射为前端显示状态
                
                Args:
                    db_status (str): 数据库中的状态值
                    
                Returns:
                    str: 前端显示的状态值
                """
                status_mapping = {
                    'initialized': 'draft',      # 已初始化 -> 草稿
                    'draft': 'draft',            # 草稿 -> 草稿
                    'processing': 'processing',   # 处理中 -> 处理中
                    'rendering': 'processing',    # 渲染中 -> 处理中
                    'uploading': 'processing',    # 上传中 -> 处理中
                    'saved': 'active',           # 已保存 -> 活跃
                    'completed': 'active',       # 已完成 -> 活跃
                    'published': 'active',       # 已发布 -> 活跃
                    'error': 'error',            # 错误 -> 错误
                    'failed': 'error',           # 失败 -> 错误
                    'cancelled': 'draft',        # 已取消 -> 草稿
                    'paused': 'processing'       # 已暂停 -> 处理中
                }
                return status_mapping.get(db_status, 'draft')  # 默认返回draft
            
            drafts_list.append({
                "id": draft['id'],
                "name": f"草稿_{draft['id'][:8]}",  # 缩短显示
                "status": map_draft_status(draft.get('status')),
                "material_count": material_count,
                "create_time": create_timestamp,
                "update_time": timestamp,
                "total_size": total_size,
                "source": "database"
            })

        return jsonify({
            "success": True,
            "drafts": drafts_list,
            "total": len(drafts_list),
            "message": "获取成功"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "drafts": [],
            "total": 0,
            "error": f"获取草稿列表失败: {str(e)}"
        })

# 新增缺失的API端点
@app.route('/api/draft/preview/<draft_id>', methods=['GET'])
def preview_draft_api(draft_id):
    """草稿预览API - 重定向到预览页面"""
    return redirect(f'/draft/preview/{draft_id}', code=302)

@app.route('/api/drafts/edit/<draft_id>', methods=['GET'])
def edit_draft_api(draft_id):
    """编辑草稿API - 重定向到预览页面"""
    return redirect(f'/draft/preview/{draft_id}', code=302)

@app.route('/api/drafts/delete/<draft_id>', methods=['DELETE'])
def delete_draft_api(draft_id):
    """删除草稿API"""
    try:
        logger.info(f"开始删除草稿: {draft_id}")

        # 检查草稿是否存在
        from database import get_draft_by_id
        draft_info = get_draft_by_id(draft_id)
        logger.debug(f"草稿信息: {draft_info}")

        # 从数据库删除草稿和相关素材
        conn = sqlite3.connect('capcut.db')
        c = conn.cursor()
        c.execute("DELETE FROM materials WHERE draft_id = ?", (draft_id,))
        c.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
        conn.commit()
        conn.close()

        # 从缓存中删除
        if draft_id in draft_materials_cache:
            del draft_materials_cache[draft_id]

        # 删除本地文件夹（如果存在）
        import shutil
        draft_path = f"drafts/{draft_id}"
        if os.path.exists(draft_path):
            shutil.rmtree(draft_path)

        logger.info(f"草稿删除成功: {draft_id}")
        return jsonify({
            'success': True,
            'message': '草稿删除成功',
            'draft_id': draft_id
        })

    except Exception as e:
        logger.error(f"删除草稿失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'删除草稿失败: {str(e)}'
        }), 500

@app.route('/api/drafts/download/<draft_id>', methods=['GET'])
def download_draft_file(draft_id):
    """下载草稿文件 - 修复版本"""
    try:
        # 检查草稿是否存在
        materials = get_draft_materials(draft_id)
        if not materials:
            return jsonify({
                'success': False,
                'error': f'草稿 {draft_id} 不存在'
            }), 404
        
        # 生成下载链接
        try:
            # 直接调用本地的generate_draft_url_api函数
            from flask import request as flask_request
            
            # 模拟请求数据
            mock_data = {
                'draft_id': draft_id,
                'force_save': True,
                'client_os': flask_request.args.get('client_os', 'windows')
            }
            
            # 创建模拟请求上下文
            with app.test_request_context('/generate_draft_url', 
                                        method='POST', 
                                        json=mock_data):
                response = generate_draft_url_api()
                
                if hasattr(response, 'get_json'):
                    result = response.get_json()
                    if result and result.get('success'):
                        draft_url = result.get('output', {}).get('draft_url')
                        if draft_url:
                            return jsonify({
                                'success': True,
                                'download_url': draft_url,
                                'draft_id': draft_id,
                                'source': result.get('output', {}).get('source', 'unknown')
                            })
                
        except Exception as url_error:
            logger.error(f"生成下载链接失败: {url_error}")
        
        # 降级处理：返回草稿信息和手动导入指引
        return jsonify({
            'success': True,
            'message': '草稿存在，请手动导入',
            'draft_id': draft_id,
            'materials_count': len(materials),
            'instructions': {
                'message': f'请在剪映中手动导入草稿ID: {draft_id}',
                'steps': [
                    '1. 打开剪映应用',
                    '2. 进入草稿管理',
                    f'3. 查找草稿ID: {draft_id}',
                    '4. 或从本地文件夹导入'
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"下载草稿失败: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'下载失败: {str(e)}'
        }), 500

def get_draft_title(draft_id):
    """获取草稿的真实标题名称 - 按官方格式命名"""
    try:
        # 1. 优先从缓存中获取草稿名称
        if draft_id in draft_materials_cache:
            for material in draft_materials_cache[draft_id]:
                if material.get('type') == 'draft_info':
                    name = material.get('name', '') or material.get('title', '')
                    if name and name != '未命名草稿':
                        return name
        
        # 2. 尝试从本地草稿文件夹读取
        draft_info_path = os.path.join(draft_id, 'draft_info.json')
        if os.path.exists(draft_info_path):
            with open(draft_info_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
                title = draft_data.get('title', '')
                if title:
                    return title
        
        # 3. 尝试从downloads目录读取
        downloads_path = os.path.join('downloads', draft_id, 'draft_info.json')
        if os.path.exists(downloads_path):
            with open(downloads_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
                title = draft_data.get('title', '')
                if title:
                    return title
        
        # 4. 尝试从数据库读取
        from database import get_draft_by_id
        draft_info = get_draft_by_id(draft_id)
        if draft_info and 'script_data' in draft_info and draft_info['script_data']:
            script_data = draft_info['script_data']
            if isinstance(script_data, dict):
                title = script_data.get('title', '')
                if title:
                    return title
        
        # 5. 按照官方格式生成草稿名称
        if draft_id.startswith('dfd_cat_'):
            try:
                # 从 draft_id 中提取时间戳 (如: dfd_cat_1756104121_cb774809)
                parts = draft_id.split('_')
                if len(parts) >= 3:
                    timestamp = int(parts[2])
                    from datetime import datetime
                    dt = datetime.fromtimestamp(timestamp)
                    # 按照官方格式：月日格式 (如: 1月15日)
                    return f"{dt.month}月{dt.day}日"
            except:
                pass
        
        # 6. 最后的默认格式 - 使用当前日期
        from datetime import datetime
        now = datetime.now()
        return f"{now.month}月{now.day}日"
        
    except Exception as e:
        logger.error(f"获取草稿标题失败: {e}", exc_info=True)
        from datetime import datetime
        now = datetime.now()
        return f"{now.month}月{now.day}日"

@app.route('/api/drafts/download/proxy/<draft_id>', methods=['GET'])
def download_draft_proxy(draft_id):
    """代理下载草稿文件 - 解决跨域问题"""
    try:
        # 🔧 最终修复：使用customize_zip生成定制化版本
        # 从请求参数获取client_os和draft_folder
        client_os = request.args.get('client_os', 'windows')
        draft_folder = request.args.get('draft_folder', '')
        
        logger.info(f"代理下载草稿: {draft_id}, client_os={client_os}, draft_folder='{draft_folder}'")
        
        # 调用customize_zip生成定制化URL
        from customize_zip import get_customized_signed_url
        draft_url = get_customized_signed_url(draft_id, client_os, draft_folder)
        
        logger.info(f"[代理下载] 使用定制化OSS链接: {draft_url[:120]}...")
        logger.info(f"[代理下载] 参数 - client_os={client_os}, draft_folder='{draft_folder}'")
        
        # 从OSS获取文件内容
        import requests
        
        # 获取文件
        file_response = requests.get(draft_url, stream=True)
        if file_response.status_code == 200:
            # 直接使用draft_id作为文件名，保持原始格式
            filename = f"{draft_id}.zip"
            
            # 对中文文件名进行URL编码处理，确保HTTP头兼容性
            from urllib.parse import quote
            encoded_filename = quote(filename, safe='')
            
            # 如果响应头中有文件名，优先使用草稿标题
            if 'content-disposition' in file_response.headers:
                content_disp = file_response.headers['content-disposition']
                logger.debug(f"原始content-disposition: {content_disp}")
            
            logger.debug(f"使用草稿标题作为文件名: {filename}")
            logger.info(f"URL编码后的文件名: {encoded_filename}")
            
            # 创建响应
            def generate():
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            # 设置响应头（增强版 - 防止浏览器阻止下载）
            response = Response(generate(), mimetype='application/zip')
            response.headers['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
            response.headers['Content-Type'] = 'application/zip'
            
            # 添加安全相关响应头，防止浏览器阻止下载
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['Content-Security-Policy'] = "default-src 'none'"
            
            # 允许跨域访问（如果需要）
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            
            # 如果有内容长度，设置它
            if 'content-length' in file_response.headers:
                response.headers['Content-Length'] = file_response.headers['content-length']
            
            logger.info(f"代理下载成功: {filename}")
            return response
        else:
            logger.info(f"OSS文件不存在或无法访问: {file_response.status_code}")
            return jsonify({
                'success': False,
                'error': f'无法从OSS获取文件，状态码: {file_response.status_code}'
            }), 404
        
    except Exception as e:
        logger.error(f"代理下载失败: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'代理下载失败: {str(e)}'
        }), 500

@app.route('/api/drafts/download/custom/<draft_id>', methods=['POST'])
def download_draft_to_custom_path(draft_id):
    """自定义路径下载草稿文件 - 实际下载到指定路径"""
    try:
        data = request.get_json() or {}
        use_custom_path = data.get('use_custom_path', False)
        custom_path = data.get('custom_path', '')
        client_os = data.get('client_os', 'windows')
        
        # 检查草稿是否存在
        materials = get_draft_materials(draft_id)
        if not materials:
            return jsonify({
                'success': False,
                'error': f'草稿 {draft_id} 不存在'
            }), 404
        
        # 获取配置的下载路径
        if not custom_path:
            # 从全局配置中获取路径
            global custom_download_path
            if not custom_download_path:
                # 尝试从文件加载配置
                try:
                    config_file = 'path_config.json'
                    if os.path.exists(config_file):
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            custom_download_path = config.get('custom_download_path', '')
                except Exception as e:
                    logger.error(f"加载配置文件失败: {e}", exc_info=True)
            
            custom_path = custom_download_path
        
        if not custom_path:
            return jsonify({
                'success': False,
                'error': '请先配置下载路径'
            }), 400
        
        # 如果使用自定义路径，生成自定义格式的压缩包
        if use_custom_path:
            try:
                # 使用customize_zip模块生成自定义路径的压缩包
                from customize_zip import get_customized_signed_url
                
                # 生成自定义压缩包的下载链接
                download_url = get_customized_signed_url(
                    draft_id=draft_id,
                    client_os=client_os,
                    draft_folder=custom_path
                )
                
                if download_url:
                    return jsonify({
                        'success': True,
                        'download_url': download_url,
                        'draft_id': draft_id,
                        'custom_path': custom_path,
                        'client_os': client_os,
                        'message': f'草稿已生成自定义路径版本，下载后解压到: {custom_path}',
                        'source': 'customized_zip',
                        'instructions': {
                            'message': '下载完成后请按以下步骤操作：',
                            'steps': [
                                f'1. 下载完成后，将压缩包解压到: {custom_path}',
                                '2. 确保解压后的文件夹结构正确',
                                '3. 打开剪映应用',
                                '4. 从草稿管理中导入或直接打开项目文件'
                            ]
                        }
                    })
                else:
                    raise Exception("无法生成自定义压缩包下载链接")
                    
            except Exception as custom_error:
                logger.error(f"生成自定义压缩包失败: {custom_error}")
                import traceback
                traceback.print_exc()
        
        # 降级处理：生成普通下载链接
        try:
            # 直接调用本地的generate_draft_url_api函数
            from flask import request as flask_request
            
            # 模拟请求数据
            mock_data = {
                'draft_id': draft_id,
                'force_save': True,
                'client_os': client_os
            }
            
            # 创建模拟请求上下文
            with app.test_request_context('/generate_draft_url', 
                                        method='POST', 
                                        json=mock_data):
                response = generate_draft_url_api()
                
                if hasattr(response, 'get_json'):
                    result = response.get_json()
                    if result and result.get('success'):
                        draft_url = result.get('output', {}).get('draft_url')
                        if draft_url:
                            return jsonify({
                                'success': True,
                                'download_url': draft_url,
                                'draft_id': draft_id,
                                'custom_path': custom_path,
                                'client_os': client_os,
                                'message': f'请手动下载并解压到: {custom_path}',
                                'source': result.get('output', {}).get('source', 'unknown'),
                                'instructions': {
                                    'message': '下载完成后请按以下步骤操作：',
                                    'steps': [
                                        '1. 点击下载链接下载压缩包',
                                        f'2. 将压缩包解压到: {custom_path}',
                                        '3. 打开剪映应用',
                                        '4. 从草稿管理中导入项目'
                                    ]
                                }
                            })
                
        except Exception as url_error:
            logger.error(f"生成下载链接失败: {url_error}")
        
        # 最终降级处理：返回草稿信息和手动导入指引
        return jsonify({
            'success': True,
            'message': f'草稿存在，请手动导入到路径: {custom_path}',
            'draft_id': draft_id,
            'custom_path': custom_path,
            'client_os': client_os,
            'materials_count': len(materials),
            'instructions': {
                'message': f'请在剪映中手动导入草稿ID: {draft_id}',
                'steps': [
                    '1. 打开剪映应用',
                    '2. 进入草稿管理',
                    f'3. 查找草稿ID: {draft_id}',
                    f'4. 或从路径导入: {custom_path}'
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"自定义路径下载草稿失败: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'自定义路径下载失败: {str(e)}'
        }), 500

@app.route('/api/drafts/batch-download', methods=['POST'])
def batch_download_drafts():
    """批量下载草稿"""
    try:
        data = request.get_json()
        draft_ids = data.get('draft_ids', [])
        client_os = data.get('client_os', 'unknown')
        draft_folder = data.get('draft_folder', '')
        
        if not draft_ids:
            return jsonify({
                'success': False,
                'error': '请提供草稿ID列表'
            }), 400
        
        results = []
        for draft_id in draft_ids:
            try:
                # 检查草稿是否存在
                materials = get_draft_materials(draft_id)
                if materials:
                    results.append({
                        'draft_id': draft_id,
                        'status': 'queued',
                        'message': '已加入下载队列'
                    })
                else:
                    results.append({
                        'draft_id': draft_id,
                        'status': 'error',
                        'message': '草稿不存在'
                    })
            except Exception as e:
                results.append({
                    'draft_id': draft_id,
                    'status': 'error',
                    'message': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': f'已处理 {len(draft_ids)} 个草稿',
            'results': results,
            'download_info': {
                'client_os': client_os,
                'draft_folder': draft_folder,
                'total_count': len(draft_ids)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'批量下载失败: {str(e)}'
        }), 500

@app.route('/api/draft/long_poll_status', methods=['GET'])
def long_poll_draft_status():
    draft_id = request.args.get('draft_id')
    last_status = request.args.get('last_status')
    timeout = int(request.args.get('timeout', 30))

    if not draft_id:
        return jsonify({"success": False, "error": "'draft_id' is required"}), 400

    start_time = time.time()
    while time.time() - start_time < timeout:
        conn = sqlite3.connect('capcut.db')
        c = conn.cursor()
        c.execute("SELECT status, progress, message FROM drafts WHERE id = ?", (draft_id,))
        result = c.fetchone()
        conn.close()
        
        current_status = result[0] if result else None

        if current_status and current_status != last_status:
            return jsonify({
                "success": True,
                "draft_id": draft_id,
                "status": current_status,
                "progress": result[1],
                "message": result[2]
            })
        
        time.sleep(1) # 1秒轮询一次

    return jsonify({"success": True, "status": "timeout", "message": "No status change"})

# 操作系统检测API
@app.route('/api/os/info', methods=['GET'])
def get_os_info():
    """获取操作系统信息和默认路径配置"""
    try:
        os_config = get_os_path_config()
        # 使用get_os_info()方法获取可序列化的字典数据
        os_info = os_config.get_os_info()
        return jsonify({
            'success': True,
            'data': os_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 草稿路径配置API

@app.route('/api/draft/path/config', methods=['GET', 'POST'])
def draft_path_config():
    """获取或更新草稿路径配置"""
    global custom_download_path
    
    if request.method == 'GET':
        # 获取当前路径配置
        try:
            # 从文件读取配置
            config_file = 'path_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    current_path = config.get('custom_download_path', '')
            else:
                current_path = custom_download_path or ''
            
            return jsonify({
                'success': True,
                'custom_path': current_path
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        # 更新路径配置
        try:
            data = request.get_json()
            custom_path = data.get('custom_path', '')
            client_os = data.get('client_os', 'unknown')
            
            # 路径验证逻辑
            if custom_path:
                # 检查是否为跨平台路径（例如：在Linux服务器上配置Windows路径）
                import re
                is_cross_platform = False
                
                # 检测Windows路径特征（盘符开头，如 C:\, D:\, F:\）
                if client_os == 'windows' and re.match(r'^[A-Za-z]:\\', custom_path):
                    is_cross_platform = True
                    logger.debug(f"检测到跨平台路径配置: Windows路径 '{custom_path}' 在 Linux 服务器上")
                
                # 如果不是跨平台路径，才进行物理验证
                if not is_cross_platform:
                    try:
                        os.makedirs(custom_path, exist_ok=True)
                    except Exception as e:
                        return jsonify({
                            'success': False,
                            'error': f'无法创建或访问路径: {str(e)}'
                        }), 400
                else:
                    # 跨平台路径只做格式验证，不进行物理验证
                    logger.debug(f"跳过跨平台路径的物理验证: {custom_path}")
            
            # 保存配置到全局变量
            custom_download_path = custom_path
            
            # 保存配置到文件
            try:
                config_file = 'path_config.json'
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump({'custom_download_path': custom_path}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"保存配置文件失败: {e}", exc_info=True)
                
            return jsonify({
                'success': True,
                'message': '路径配置已更新',
                'custom_path': custom_path
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500



# 草稿下载进度API
@app.route('/api/draft/download/progress/<task_id>', methods=['GET'])
def get_download_progress(task_id):
    """获取草稿下载进度"""
    try:
        # 这里应该从实际的下载任务管理器中获取进度
        # 目前返回模拟数据
        progress_data = {
            'task_id': task_id,
            'progress': 75,  # 0-100
            'status': 'downloading',  # downloading, completed, failed
            'message': '正在下载草稿文件...',
            'downloaded_size': '15.2MB',
            'total_size': '20.3MB'
        }
        
        return jsonify({
            'success': True,
            'data': progress_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 新增草稿下载API端点
@app.route('/api/draft/download', methods=['POST'])
def draft_download_api():
    """草稿下载API - 处理下载请求"""
    try:
        data = request.get_json()
        draft_id = data.get('draft_id')
        draft_folder = data.get('draft_folder', '')
        client_os = data.get('client_os', 'unknown')
        use_custom_path = data.get('use_custom_path', False)
        
        if not draft_id:
            return jsonify({
                'success': False,
                'error': '缺少草稿ID'
            }), 400
        
        # 检查草稿是否存在
        materials = get_draft_materials(draft_id)
        if not materials:
            return jsonify({
                'success': False,
                'error': '草稿不存在或无素材'
            }), 404
        
        # 🔧 最终修复：智能下载总是使用customize_zip来处理路径
        # 不管use_custom_path是true还是false，都调用customize_zip
        # draft_folder为空时，customize_zip会清空路径；不为空时，会设置为指定路径
        try:
            from customize_zip import get_customized_signed_url
            # 调用customize_zip生成定制化下载链接
            # draft_folder为空 → 清空路径（相对路径模式）
            # draft_folder不为空 → 设置为指定路径
            custom_download_url = get_customized_signed_url(draft_id, client_os, draft_folder)
            if custom_download_url:
                # 使用代理下载URL，这样可以控制文件名
                from urllib.parse import urlencode
                params = urlencode({
                    'client_os': client_os,
                    'draft_folder': draft_folder
                })
                proxy_download_url = f"/api/draft/download/proxy/{draft_id}?{params}"
                
                # 根据draft_folder是否为空，返回不同的提示信息
                if draft_folder:
                    message = f'已生成自定义下载链接，包含{client_os}路径配置'
                    instructions = {
                        'message': '下载完成后请按以下步骤操作：',
                        'steps': [
                            f'1. 下载完成后，将压缩包解压到: {draft_folder}',
                            '2. 确保解压后的文件夹结构正确',
                            '3. 打开剪映应用',
                            '4. 从草稿管理中导入或直接打开项目文件'
                        ]
                    }
                else:
                    message = f'已生成智能下载链接（相对路径模式）'
                    instructions = {
                        'message': '下载完成后请按以下步骤操作：',
                        'steps': [
                            '1. 下载完成后，解压ZIP文件',
                            '2. 将草稿文件夹复制到剪映草稿目录（任意位置）',
                            '3. 打开剪映应用',
                            '4. 草稿会自动出现在草稿列表中'
                        ]
                    }
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'download_url': proxy_download_url,
                    'original_url': custom_download_url,
                    'client_os': client_os,
                    'custom_path': draft_folder if draft_folder else '(相对路径)',
                    'instructions': instructions
                })
        except Exception as custom_error:
            logger.error(f"生成定制化下载链接失败: {custom_error}")
            import traceback
            traceback.print_exc()
            
            # customize_zip失败，降级到返回配置信息
            return jsonify({
                'success': False,
                'error': f'下载失败: {str(custom_error)}',
                'draft_id': draft_id,
                'materials_count': len(materials)
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _download_draft_to_custom_path_impl(draft_id, custom_path, materials):
    """将草稿文件下载到自定义路径的内部实现"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        import shutil
        
        logger.info(f"开始自定义下载: draft_id={draft_id}, custom_path={custom_path}")
        
        # 确保自定义路径存在
        if not os.path.exists(custom_path):
            os.makedirs(custom_path, exist_ok=True)
            logger.info(f"创建自定义路径: {custom_path}")
        
        # 创建草稿目录
        draft_target_path = os.path.join(custom_path, draft_id)
        if not os.path.exists(draft_target_path):
            os.makedirs(draft_target_path, exist_ok=True)
            logger.info(f"创建草稿目标目录: {draft_target_path}")
        
        # 查找草稿源目录
        draft_source_path = None
        possible_paths = [
            f'/home/CapCutAPI-1.1.0/drafts/{draft_id}',
            f'/home/CapCutAPI-1.1.0/output/{draft_id}',
            f'/tmp/{draft_id}'
        ]
        
        logger.info(f"查找草稿源目录，可能的路径: {possible_paths}")
        
        for path in possible_paths:
            if os.path.exists(path):
                draft_source_path = path
                logger.info(f"找到草稿源目录: {draft_source_path}")
                break
        
        if not draft_source_path:
            # 如果找不到源目录，说明草稿只存在于缓存中，需要先保存
            logger.info(f"草稿源目录不存在，尝试先保存草稿到临时目录")
            
            # 先保存草稿到临时目录
            temp_draft_folder = '/tmp/capcut_temp_drafts'
            if not os.path.exists(temp_draft_folder):
                os.makedirs(temp_draft_folder, exist_ok=True)
            
            try:
                # 调用save_draft_impl来保存草稿
                from save_draft_impl import save_draft_impl
                from database import get_draft_status
                import time
                
                save_result = save_draft_impl(draft_id, temp_draft_folder, "windows")
                
                if save_result.get('success'):
                    task_id = save_result.get('task_id')
                    logger.info(f"草稿保存任务已启动，任务ID: {task_id}")
                    
                    # 等待保存完成
                    max_wait_time = 300  # 最大等待5分钟
                    wait_interval = 2    # 每2秒检查一次
                    waited_time = 0
                    
                    while waited_time < max_wait_time:
                        status_info = get_draft_status(draft_id)
                        if status_info:
                            status = status_info.get('status', '')
                            logger.info(f"草稿状态: {status}")
                            
                            if status == 'completed':
                                # 保存完成，更新源路径
                                draft_source_path = os.path.join(temp_draft_folder, draft_id)
                                logger.info(f"草稿保存完成，源路径: {draft_source_path}")
                                break
                            elif status == 'failed':
                                error_msg = f'草稿保存失败: {status_info.get("message", "未知错误")}'
                                logger.error(error_msg)
                                return {
                                    'success': False,
                                    'error': error_msg
                                }
                        
                        time.sleep(wait_interval)
                        waited_time += wait_interval
                    
                    if waited_time >= max_wait_time:
                        error_msg = '草稿保存超时'
                        logger.error(error_msg)
                        return {
                            'success': False,
                            'error': error_msg
                        }
                else:
                    error_msg = f'启动草稿保存失败: {save_result.get("error", "未知错误")}'
                    logger.error(error_msg)
                    return {
                        'success': False,
                        'error': error_msg
                    }
            except Exception as save_error:
                error_msg = f'保存草稿时发生异常: {str(save_error)}'
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
        
        # 检查源目录内容
        source_files = []
        for root, dirs, files in os.walk(draft_source_path):
            for file in files:
                source_files.append(os.path.join(root, file))
        
        logger.info(f"源目录文件列表: {source_files}")
        
        if not source_files:
            # 如果源目录没有文件，尝试从素材列表复制文件
            logger.info("源目录为空，尝试从素材列表复制文件")
            files_copied = []
            
            # 复制draft_info.json（如果存在）
            draft_info_file = os.path.join(draft_source_path, 'draft_info.json')
            if os.path.exists(draft_info_file):
                target_info_file = os.path.join(draft_target_path, 'draft_info.json')
                shutil.copy2(draft_info_file, target_info_file)
                files_copied.append('draft_info.json')
                logger.info("复制了 draft_info.json")
            
            # 从素材列表复制文件
            if materials:
                assets_dir = os.path.join(draft_target_path, 'assets')
                os.makedirs(assets_dir, exist_ok=True)
                
                for material in materials:
                    if 'file_path' in material and os.path.exists(material['file_path']):
                        filename = os.path.basename(material['file_path'])
                        target_file = os.path.join(assets_dir, filename)
                        shutil.copy2(material['file_path'], target_file)
                        files_copied.append(f'assets/{filename}')
                        logger.info(f"复制素材文件: {filename}")
            
            return {
                'success': True,
                'download_path': draft_target_path,
                'files_copied': files_copied,
                'note': '从素材列表复制文件'
            }
        
        # 复制草稿文件
        files_copied = []
        for root, dirs, files in os.walk(draft_source_path):
            for file in files:
                source_file = os.path.join(root, file)
                # 计算相对路径
                rel_path = os.path.relpath(source_file, draft_source_path)
                target_file = os.path.join(draft_target_path, rel_path)
                
                # 确保目标目录存在
                target_dir = os.path.dirname(target_file)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir, exist_ok=True)
                
                # 复制文件
                shutil.copy2(source_file, target_file)
                files_copied.append(rel_path)
                logger.info(f"复制文件: {rel_path}")
        
        logger.info(f"下载完成，共复制 {len(files_copied)} 个文件")
        
        return {
            'success': True,
            'download_path': draft_target_path,
            'files_copied': files_copied
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# 添加缺失的 generate_draft_url 路由
@app.route('/generate_draft_url', methods=['POST'])
def generate_draft_url_api():
    """生成草稿下载URL的API接口"""
    try:
        data = request.get_json()
        draft_id = data.get('draft_id')
        client_os = data.get('client_os', 'windows')
        draft_folder = data.get('draft_folder', '')
        force_save = data.get('force_save', False)
        
        if not draft_id:
            return jsonify({
                'success': False,
                'error': '缺少草稿ID参数'
            }), 400
        
        # 检查草稿是否存在
        materials = get_draft_materials(draft_id)
        if not materials:
            return jsonify({
                'success': False,
                'error': f'草稿 {draft_id} 不存在'
            }), 404
        
        # 如果需要强制保存，先保存草稿
        if force_save:
            try:
                # 调用保存草稿功能
                save_result = save_draft_impl(draft_id, None, "windows")
                if not save_result.get('success', False):
                    return jsonify({
                        'success': False,
                        'error': f'保存草稿失败: {save_result.get("error", "未知错误")}'
                    }), 500
            except Exception as save_error:
                logger.info(f"保存草稿时出错: {save_error}")
                # 继续尝试生成URL，即使保存失败
        
        # 尝试从OSS获取已签名的URL
        try:
            signed_url = get_signed_draft_url_if_exists(draft_id)
            if signed_url:
                return jsonify({
                    'success': True,
                    'output': {
                        'draft_url': signed_url,
                        'source': 'oss'
                    },
                    'message': '从OSS获取下载链接成功'
                })
        except Exception as oss_error:
            logger.info(f"从OSS获取URL失败: {oss_error}")
        
        # 尝试获取自定义签名URL
        try:
            custom_url = get_customized_signed_url(draft_id)
            if custom_url:
                return jsonify({
                    'success': True,
                    'output': {
                        'draft_url': custom_url,
                        'source': 'custom'
                    },
                    'message': '获取自定义下载链接成功'
                })
        except Exception as custom_error:
            logger.info(f"获取自定义URL失败: {custom_error}")
        
        # 检查是否有自定义下载路径配置
        global custom_download_path
        if custom_download_path and draft_folder:
            try:
                # 使用自定义路径进行文件复制
                import shutil
                source_path = f"Drafts/{draft_id}"
                target_path = os.path.join(custom_download_path, draft_id)
                
                # 确保源路径存在
                if os.path.exists(source_path):
                    # 如果目标路径已存在，先删除
                    if os.path.exists(target_path):
                        shutil.rmtree(target_path)
                    
                    # 复制整个草稿文件夹到自定义路径
                    shutil.copytree(source_path, target_path)
                    
                    return jsonify({
                        'success': True,
                        'output': {
                            'draft_url': target_path,
                            'source': 'custom_path'
                        },
                        'message': f'草稿已成功复制到: {target_path}',
                        'custom_path': target_path
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'源草稿路径不存在: {source_path}'
                    }), 404
                    
            except Exception as copy_error:
                logger.info(f"复制草稿到自定义路径失败: {copy_error}")
                # 继续使用默认路径作为备选
        
        # 生成本地路径作为备选方案
        try:
            local_path = utilgenerate_draft_url(draft_id, client_os, draft_folder)
            return jsonify({
                'success': True,
                'output': {
                    'draft_url': local_path,
                    'source': 'local_path'
                },
                'message': f'请在剪映中导入路径: {local_path}',
                'instructions': {
                    'step1': '打开剪映应用',
                    'step2': f'在草稿目录中查找: {draft_id}',
                    'step3': '或手动导入草稿文件夹',
                    'local_path': local_path
                }
            })
        except Exception as path_error:
            logger.error(f"生成本地路径失败: {path_error}")
            return jsonify({
                'success': False,
                'error': f'生成草稿路径失败: {str(path_error)}'
            }), 500
        
    except Exception as e:
        logger.error(f"generate_draft_url API错误: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'生成草稿URL时发生错误: {str(e)}'
        }), 500

# 草稿预览辅助函数
def get_draft_info(draft_id):
    """获取草稿基本信息"""
    try:
        from database import get_draft_by_id
        draft_info = get_draft_by_id(draft_id)
        if draft_info:
            return draft_info
        
        # 如果数据库中没有，返回默认信息
        return {
            'id': draft_id,
            'name': f'草稿_{draft_id}',
            'status': 'unknown',
            'create_time': '未知',
            'update_time': '未知'
        }
    except Exception as e:
        logger.error(f"获取草稿信息失败: {e}", exc_info=True)
        return {
            'id': draft_id,
            'name': f'草稿_{draft_id}',
            'status': 'error',
            'create_time': '未知',
            'update_time': '未知'
        }

# 代理下载路由 - 控制文件名
@app.route('/api/draft/download/proxy/<draft_id>', methods=['GET'])
def download_proxy(draft_id):
    """代理下载 - 控制文件名"""
    try:
        # 获取存储的下载URL（这里需要一个临时存储机制）
        # 为了简化，我们重新生成下载URL
        from customize_zip import get_customized_signed_url
        
        # 从请求参数获取配置，或使用默认值
        client_os = request.args.get('client_os', 'windows')
        draft_folder = request.args.get('draft_folder', '')
        
        # 🔧 修复：智能下载不应该读取path_config.json
        # 只有用户明确传递draft_folder时才使用，否则保持为空（相对路径模式）
        logger.info(f"[单数代理] client_os={client_os}, draft_folder='{draft_folder}'")
        
        # 生成下载URL
        download_url = get_customized_signed_url(draft_id, client_os, draft_folder)
        logger.info(f"[单数代理] 生成URL: {download_url[:100]}...")
        
        if download_url:
            # 使用requests获取文件并返回
            import requests
            response = requests.get(download_url, stream=True)
            
            if response.status_code == 200:
                from flask import Response
                
                # 设置正确的文件名
                filename = f"{draft_id}.zip"
                
                def generate():
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
                
                # 创建响应并添加安全相关响应头，防止浏览器阻止下载
                flask_response = Response(generate())
                flask_response.headers['Content-Type'] = 'application/zip'
                flask_response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                # 添加安全相关响应头
                flask_response.headers['X-Content-Type-Options'] = 'nosniff'
                flask_response.headers['Content-Security-Policy'] = "default-src 'none'"
                
                # 允许跨域访问
                flask_response.headers['Access-Control-Allow-Origin'] = '*'
                flask_response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                flask_response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
                
                # 设置内容长度
                if response.headers.get('Content-Length'):
                    flask_response.headers['Content-Length'] = response.headers.get('Content-Length')
                
                return flask_response
            else:
                return "下载文件失败", 404
        else:
            return "无法生成下载链接", 404
            
    except Exception as e:
        return f"下载代理失败: {str(e)}", 500

# 草稿预览页面 - 完全按照官方文档风格设计
@app.route('/debug/download', methods=['GET'])
def debug_download():
    """调试下载页面"""
    return render_template('debug_download.html')

@app.route('/download_guide', methods=['GET'])
def download_guide():
    """提供下载指导页面"""
    try:
        return render_template('download_guide.html')
    except Exception as e:
        return f"""
        <html>
        <head><title>下载指南</title></head>
        <body>
            <h1>📥 自定义下载指南</h1>
            <h2>🔒 浏览器安全限制说明</h2>
            <p>由于浏览器安全机制，无法直接下载到您指定的路径。</p>
            
            <h2>💡 解决方案</h2>
            <h3>方案一：设置浏览器默认下载路径</h3>
            <ol>
                <li>打开浏览器设置</li>
                <li>找到"下载"或"下载内容"设置</li>
                <li>设置下载路径为：<code>F:\\jianying\\cgwz\\JianyingPro Drafts</code></li>
                <li>点击"自定义下载"，文件会下载到设置的路径</li>
            </ol>
            
            <h3>方案二：手动移动文件</h3>
            <ol>
                <li>下载文件到默认位置（通常是Downloads文件夹）</li>
                <li>将ZIP文件移动到剪映目录</li>
                <li>解压使用</li>
            </ol>
            
            <h2>✅ 核心优势</h2>
            <p>无论使用哪种方案，下载的草稿都包含正确的Windows路径格式，剪映可以自动识别所有素材！</p>
            
            <p><a href="javascript:history.back()">🔙 返回草稿预览</a></p>
        </body>
        </html>
        """

@app.route('/static/download_helper.bat', methods=['GET'])
def download_helper_script():
    """提供Windows自动移动脚本"""
    try:
        script_path = '/home/CapCutAPI-1.1.0/static/download_helper.bat'
        if os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            from flask import Response
            response = Response(content, mimetype='application/octet-stream')
            response.headers['Content-Disposition'] = 'attachment; filename=download_helper.bat'
            return response
        else:
            return "脚本文件不存在", 404
    except Exception as e:
        return f"下载脚本失败: {str(e)}", 500

@app.route('/draft/preview/<draft_id>', methods=['GET'])
def enhanced_draft_preview(draft_id):
    """草稿预览页面 - 符合官方文档设计风格"""
    try:
        # 获取草稿素材
        materials = get_draft_materials(draft_id)
        if not materials:
            materials = []
        
        # 获取草稿基础信息
        draft_info = get_draft_info(draft_id)
        
        # 计算总时长，处理非数字值
        total_duration = 0
        for m in materials:
            duration = m.get('duration', 0)
            if isinstance(duration, (int, float)):
                total_duration += duration
            elif isinstance(duration, str) and duration.replace('.', '').isdigit():
                total_duration += float(duration)
            # 忽略非数字值如 '未知'
        
        # 生成官方风格的HTML预览页面
        return render_template_with_official_style(draft_id, materials, total_duration, draft_info)
        
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>预览错误</title>
            <style>body{{font-family:Arial;margin:40px;text-align:center;background:#1a1a1a;color:#fff;}}</style>
        </head>
        <body>
            <h1>❌ 预览加载失败</h1>
            <p>草稿ID: {draft_id}</p>
            <p>错误信息: {str(e)}</p>
            <p><a href="javascript:history.back()" style="color:#4a9eff;">返回上一页</a></p>
        </body>
        </html>
        """
        
        # 生成素材详情表格
        material_rows = ""
        for i, material in enumerate(materials):
            material_type = material.get("type", "unknown")
            video_url = material.get("url", "-")
            start_time = material.get("start", 0)
            if isinstance(start_time, str) and start_time.replace('.', '').replace('-', '').isdigit():
                start_time = float(start_time)
            elif not isinstance(start_time, (int, float)):
                start_time = 0
            
            material_duration = material.get("duration", 30)
            if isinstance(material_duration, str) and material_duration.replace('.', '').isdigit():
                material_duration = float(material_duration)
            elif not isinstance(material_duration, (int, float)):
                material_duration = 30
            
            end_time = material.get("end", start_time + material_duration)
            if isinstance(end_time, str) and end_time.replace('.', '').replace('-', '').isdigit():
                end_time = float(end_time)
            elif not isinstance(end_time, (int, float)):
                end_time = start_time + material_duration
            
            duration = end_time - start_time
            
            # 为每个素材添加下载按钮
            download_btn = f'<a href="{video_url}" target="_blank" class="download-btn">下载</a>' if video_url != "-" else "无下载链接"
            
            material_rows += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{material_type.upper()}</td>
                    <td title="{video_url}">{video_url[:40]}{'...' if len(video_url) > 40 else ''}</td>
                    <td>{start_time:.2f}s</td>
                    <td>{end_time:.2f}s</td>
                    <td>{duration:.2f}s</td>
                    <td>{download_btn}</td>
                </tr>
            """
        
        # 生成轨道信息
        tracks_info = ""
        if materials:
            tracks = {}
            for material in materials:
                track_name = material.get('track_name', '默认轨道')
                if track_name not in tracks:
                    tracks[track_name] = {'count': 0, 'type': material.get('type', 'unknown')}
                tracks[track_name]['count'] += 1
            
            for track_name, info in tracks.items():
                tracks_info += f"""
                    <tr>
                        <td>{track_name}</td>
                        <td>{info['type'].upper()}</td>
                        <td>{info['count']}</td>
                    </tr>
                """
        
        # 生成完整的HTML预览页面
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>草稿预览 - {draft_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 6px;
            padding: 15px;
            margin: 20px;
            color: #856404;
            text-align: center;
            font-weight: 500;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
            display: block;
        }}
        .stat-label {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: 500;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .download-btn {{
            background: #28a745;
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 12px;
            transition: background 0.3s;
        }}
        .download-btn:hover {{
            background: #218838;
        }}
        .no-data {{
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 40px;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 草稿预览</h1>
            <p>草稿ID: {draft_id}</p>
        </div>
        
        <div class="warning">
            ⚠️ 重要提示：草稿在后台仅保留10分钟，长时间不操作就会释放
        </div>
        
        <div class="content">
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-number">{len(materials)}</span>
                    <div class="stat-label">素材数量</div>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{total_duration:.1f}s</span>
                    <div class="stat-label">总时长</div>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{draft_info.get('status', 'unknown')}</span>
                    <div class="stat-label">草稿状态</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📋 素材详情与下载选项</h2>
                {f'''
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>类型</th>
                            <th>素材URL</th>
                            <th>开始时间</th>
                            <th>结束时间</th>
                            <th>时长</th>
                            <th>下载</th>
                        </tr>
                    </thead>
                    <tbody>
                        {material_rows}
                    </tbody>
                </table>
                ''' if materials else '<div class="no-data">暂无素材数据</div>'}
            </div>
            
            <div class="section">
                <h2>🎵 轨道信息</h2>
                {f'''
                <table>
                    <thead>
                        <tr>
                            <th>轨道名称</th>
                            <th>轨道类型</th>
                            <th>素材数量</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tracks_info}
                    </tbody>
                </table>
                ''' if tracks_info else '<div class="no-data">暂无轨道信息</div>'}
            </div>
            
            <div class="section">
                <h2>💾 草稿下载</h2>
                <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; text-align: center;">
                    <p>请在剪映中输入草稿目录路径来下载此草稿</p>
                    <p><strong>草稿ID:</strong> <code>{draft_id}</code></p>
                    <p><em>注意：请在10分钟内完成下载，超时后草稿将被自动释放</em></p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>CapCutAPI - 草稿预览系统 | 更新时间: {draft_info.get('update_time', '未知')}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
        
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>预览错误</title>
            <style>body{{font-family:Arial;margin:40px;text-align:center;}}</style>
        </head>
        <body>
            <h1>❌ 预览加载失败</h1>
            <p>草稿ID: {draft_id}</p>
            <p>错误信息: {str(e)}</p>
            <p><a href="javascript:history.back()">返回上一页</a></p>
        </body>
        </html>
        """


# 重复路由定义已删除，使用上面的 enhanced_draft_preview 函数

def render_template_with_official_style(draft_id, materials, total_duration, draft_info=None):
    """使用现有模板渲染预览页面，但应用官方风格"""
    try:
        # 如果没有提供 draft_info，创建一个默认的
        if draft_info is None:
            draft_info = {
                'create_time': '未知',
                'update_time': '未知'
            }
        
        # 使用现有的预览模板
        return render_template('preview.html', 
                             draft_id=draft_id,
                             materials=materials,
                             total_duration=total_duration,
                             draft_info=draft_info,
                             timeline_html=generate_timeline_html_for_template(materials, total_duration, draft_id))
    except Exception as e:
        logger.error(f"模板渲染失败: {e}", exc_info=True)
        # 如果模板不存在，返回简单的HTML
        return f"""
        <html>
        <head>
            <title>草稿预览 - {draft_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .materials {{ background: #2d2d2d; padding: 20px; border-radius: 8px; }}
                .material {{ padding: 10px; border-bottom: 1px solid #404040; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>草稿预览 - {draft_id}</h1>
                    <p>总时长: {total_duration:.2f}秒</p>
                </div>
                <div class="materials">
                    <h2>素材列表 ({len(materials)} 个)</h2>
                    {''.join([f'<div class="material">{m.get("type", "unknown").upper()}: {m.get("url", "N/A")}</div>' for m in materials])}
                </div>
            </div>
        </body>
        </html>
        """

def generate_timeline_html_for_template(materials, total_duration, draft_id=None):
    """生成适用于官方模板的时间轴HTML - 按类型分层显示（官方模式）"""
    
    # 【增强】text类型素材也作为字幕显示
    # 在materials中，type为text的素材实际上是文本/字幕
    logger.info(f"\n=== 处理素材，查找字幕 ===")
    logger.debug(f"原始素材数量: {len(materials)}")
    
    text_materials_count = 0
    for material in materials:
        mat_type = material.get('type', 'unknown')
        if mat_type == 'text':
            # text类型实际上是字幕/文本，标记为subtitle以便正确显示
            material['original_type'] = 'text'
            material['type'] = 'subtitle'  # 改为subtitle类型在时间轴上显示
            content = material.get('content', '字幕')
            start = material.get('start', 0)
            logger.info(f"  ✓ 发现文本素材(作为字幕): {content[:30]}... start={start}s")
            text_materials_count += 1
    
    logger.info(f"文本/字幕素材数量: {text_materials_count}")
    logger.info(f"处理后素材总数: {len(materials)}")
    
    if not materials:
        return '<div class="empty-timeline">暂无素材数据</div>'
    
    # 定义轨道类型和对应的图标，按官方显示顺序排列
    track_types = {
        'video': {'label': '视频', 'icon': '🎥', 'order': 1, 'color': '#4CAF50'},
        'image': {'label': '图片', 'icon': '🖼️', 'order': 2, 'color': '#FF9800'},
        'text': {'label': '文本', 'icon': '📝', 'order': 3, 'color': '#2196F3'},
        'subtitle': {'label': '字幕', 'icon': '💬', 'order': 4, 'color': '#9C27B0'},
        'effect': {'label': '特效', 'icon': '✨', 'order': 5, 'color': '#E91E63'},
        'sticker': {'label': '贴纸', 'icon': '🏷️', 'order': 6, 'color': '#FF5722'},
        'audio': {'label': '音频', 'icon': '🎵', 'order': 7, 'color': '#607D8B'},
        'unknown': {'label': '其他', 'icon': '📄', 'order': 8, 'color': '#9E9E9E'}
    }
    
    # 标准化素材类型名称
    def normalize_material_type(material_type):
        """标准化素材类型名称"""
        if not material_type:
            return 'unknown'
        
        material_type = str(material_type).lower().strip()
        
        # 类型映射表
        type_mapping = {
            'video': 'video',
            'videos': 'video',
            'mp4': 'video',
            'mov': 'video',
            'avi': 'video',
            'audio': 'audio',
            'audios': 'audio',
            'mp3': 'audio',
            'wav': 'audio',
            'aac': 'audio',
            'image': 'image',
            'images': 'image',
            'img': 'image',
            'jpg': 'image',
            'jpeg': 'image',
            'png': 'image',
            'gif': 'image',
            'text': 'text',
            'texts': 'text',
            'txt': 'text',
            'subtitle': 'subtitle',
            'subtitles': 'subtitle',
            'srt': 'subtitle',
            'effect': 'effect',
            'effects': 'effect',
            'sticker': 'sticker',
            'stickers': 'sticker'
        }
        
        return type_mapping.get(material_type, 'unknown')
    
    # 【智能处理】修正音频素材的start时间
    # 如果同track_name的音频start都是0，自动计算累加时间
    audio_materials = [m for m in materials if normalize_material_type(m.get('type', 'unknown')) == 'audio']
    
    # 按track_name分组音频
    audio_by_track = {}
    for audio in audio_materials:
        track_name = audio.get('track_name', 'audio')
        if track_name not in audio_by_track:
            audio_by_track[track_name] = []
        audio_by_track[track_name].append(audio)
    
    # 对audio_voice类型的音频，如果start都是0，自动累加时间
    for track_name, track_audios in audio_by_track.items():
        if track_name == 'audio_voice' and len(track_audios) > 1:
            # 检查是否所有音频start都是0
            all_start_zero = all(float(a.get('start', 0)) == 0 for a in track_audios)
            if all_start_zero:
                logger.info(f"🔧 检测到{len(track_audios)}个语音音频start都是0，自动计算时间顺序...")
                # 按added_at排序（保持添加顺序）
                track_audios.sort(key=lambda x: x.get('added_at', ''))
                # 累加计算start时间
                cumulative_time = 0
                for audio in track_audios:
                    audio['start'] = cumulative_time
                    duration = float(audio.get('duration', 0))
                    audio['end'] = cumulative_time + duration
                    cumulative_time += duration
                    logger.info(f"  ✓ 音频 start={audio['start']:.2f}s, duration={duration:.2f}s")
    
    # 按类型分组素材
    materials_by_type = {}
    for material in materials:
        # 获取并标准化素材类型
        raw_type = material.get('type', material.get('material_type', 'unknown'))
        material_type = normalize_material_type(raw_type)
        
        if material_type not in materials_by_type:
            materials_by_type[material_type] = []
        materials_by_type[material_type].append(material)
    
    # 按时间顺序排序每个类型的素材
    for material_type in materials_by_type:
        materials_by_type[material_type].sort(key=lambda x: float(x.get('start', x.get('start_time', 0)) or 0))
    
    # 调试日志：打印素材分组情况
    logger.info(f"\n===== 时间轴生成调试信息 =====")
    logger.info(f"总素材数量: {len(materials)}")
    logger.info(f"总时长: {total_duration}秒")
    for mat_type, mats in materials_by_type.items():
        logger.info(f"\n【{mat_type}】类型素材: {len(mats)}个")
        for i, m in enumerate(mats):
            start = m.get('start', m.get('start_time', 0))
            duration = m.get('duration', m.get('length', '未知'))
            name = m.get('name', m.get('filename', f'{mat_type}_{i+1}'))
            logger.info(f"  {i+1}. {name} - 开始:{start}s, 时长:{duration}s")
    logger.info(f"================================\n")
    
    def assign_to_subtracks(materials_list):
        """
        将素材分配到不重叠的子轨道上（剪映逻辑）
        - 素材已按时间排序
        - 只检查轨道的最后一个素材，如果新素材在最后素材结束后开始，就放在同一轨道
        - 这样时间连续的素材会自然地排列在同一轨道
        """
        if not materials_list:
            return []
        
        subtracks = []  # 每个子轨道是一个素材列表
        
        for material in materials_list:
            start = float(material.get('start', material.get('start_time', 0)) or 0)
            duration = float(material.get('duration', material.get('length', 30)) or 30)
            if duration <= 0:
                duration = 30
            end = start + duration
            
            # 尝试将素材放入已有的子轨道
            placed = False
            for subtrack in subtracks:
                # 【剪映逻辑】只检查该轨道的最后一个素材
                if subtrack:
                    last_material = subtrack[-1]
                    last_start = float(last_material.get('start', last_material.get('start_time', 0)) or 0)
                    last_duration = float(last_material.get('duration', last_material.get('length', 30)) or 30)
                    if last_duration <= 0:
                        last_duration = 30
                    last_end = last_start + last_duration
                    
                    # 如果新素材在最后素材结束后开始（或有一点容差），就放在同一轨道
                    if start >= last_end - 0.01:  # 0.01秒容差
                        subtrack.append(material)
                        placed = True
                        break
            
            # 如果没有合适的子轨道，创建新的子轨道
            if not placed:
                subtracks.append([material])
        
        return subtracks
    
    # 生成多轨道HTML（官方风格）- 按类型分层，支持子轨道
    timeline_html = []
    
    # 按官方顺序显示轨道（视频在上，音频在下）
    sorted_types = sorted(materials_by_type.keys(), key=lambda x: track_types.get(x, {'order': 999})['order'])
    
    for material_type in sorted_types:
        type_materials = materials_by_type[material_type]
        track_info = track_types.get(material_type, track_types['unknown'])
        
        # 将该类型的素材分配到子轨道
        subtracks = assign_to_subtracks(type_materials)
        
        # 调试日志：打印子轨道分配情况
        logger.info(f"【{material_type}】类型分配到 {len(subtracks)} 个子轨道")
        for idx, subtrack in enumerate(subtracks):
            logger.info(f"  子轨道 #{idx+1}: {len(subtrack)} 个素材")
        
        # 为每个子轨道生成HTML
        for subtrack_idx, subtrack_materials in enumerate(subtracks):
            # 轨道容器开始
            subtrack_label = f"{track_info['label']}"
            if len(subtracks) > 1:
                subtrack_label += f" #{subtrack_idx + 1}"
            
            timeline_html.append(f'''
        <div class="timeline-track official-track" data-track-type="{material_type}" data-subtrack="{subtrack_idx}">
            <div class="track-label official-label">
                <span class="track-icon">{track_info['icon']}</span>
                <span class="track-name">{subtrack_label}</span>
                <span class="track-count">({len(subtrack_materials)})</span>
            </div>
            <div class="track-items official-items">''')
            
            # 为该子轨道的所有素材生成时间块
            for i, material in enumerate(subtrack_materials):
                # 获取时间信息，支持多种字段名
                start = float(material.get('start', material.get('start_time', 0)) or 0)
                duration = float(material.get('duration', material.get('length', 30)) or 30)
                
                # 确保时长不为0
                if duration <= 0:
                    duration = 30
                
                # 计算位置和宽度（百分比）
                if total_duration > 0:
                    left_percent = (start / total_duration) * 100
                    width_percent = (duration / total_duration) * 100
                else:
                    # 如果没有总时长，使用固定布局
                    left_percent = i * 25
                    width_percent = 20
                
                # 限制最小宽度和最大宽度
                width_percent = max(3, min(width_percent, 100 - left_percent))
                left_percent = max(0, min(left_percent, 97))
                
                # 生成素材名称
                material_name = material.get('name', material.get('filename', material.get('title', f'{track_info["label"]}_{i+1}')))
                if len(material_name) > 15:
                    display_name = material_name[:12] + '...'
                else:
                    display_name = material_name
                
                # 将素材数据转换为JSON字符串，并进行HTML转义
                try:
                    material_json = html.escape(json.dumps(material, ensure_ascii=False))
                except Exception:
                    material_json = html.escape(json.dumps({'id': material.get('id', f'material_{i}'), 'type': material_type}, ensure_ascii=False))
                
                material_id = material.get('id', f'material_{material_type}_{subtrack_idx}_{i}')
                
                # 根据素材类型设置不同的样式和内容
                block_color = track_info.get('color', '#9E9E9E')
                
                if material_type == 'video':
                    block_class = 'timeline-block official-block video-block'
                    block_content = f'<div class="material-icon">🎬</div><span class="material-name">{display_name}</span>'
                elif material_type == 'audio':
                    block_class = 'timeline-block official-block audio-block'
                    block_content = f'<div class="material-icon">🎵</div><span class="material-name">{display_name}</span>'
                elif material_type == 'image':
                    block_class = 'timeline-block official-block image-block'
                    block_content = f'<div class="material-icon">🖼️</div><span class="material-name">{display_name}</span>'
                elif material_type == 'text':
                    block_class = 'timeline-block official-block text-block'
                    block_content = f'<div class="material-icon">📝</div><span class="material-name">{display_name}</span>'
                elif material_type == 'subtitle':
                    block_class = 'timeline-block official-block subtitle-block'
                    block_content = f'<div class="material-icon">💬</div><span class="material-name">{display_name}</span>'
                else:
                    block_class = f'timeline-block official-block {material_type}-block'
                    block_content = f'<div class="material-icon">{track_info["icon"]}</div><span class="material-name">{display_name}</span>'
                
                # 生成时间块HTML
                timeline_html.append(f'''
                <div class="{block_class}" 
                     style="left: {left_percent:.2f}%; width: {width_percent:.2f}%; background-color: {block_color}; border-left: 3px solid {block_color};"
                     onclick="onTimelineMaterialClick('{material_id}', this)"
                     title="{track_info['label']}: {material_name}\n时间: {start:.2f}s - {start + duration:.2f}s\n时长: {duration:.2f}s"
                     data-start="{start}"
                     data-duration="{duration}"
                     data-type="{material_type}"
                     data-material='{material_json}'>
                    {block_content}
                    <div class="material-time">{start:.1f}s</div>
                </div>''')
            
            # 子轨道容器结束
            timeline_html.append('</div></div>')
    
    return ''.join(timeline_html)


@app.route('/draft/downloader', methods=['GET'])
def draft_downloader():
    """草稿下载路由 - 处理/draft/downloader请求"""
    try:
        draft_id = request.args.get('draft_id')
        if not draft_id:
            return jsonify({
                'success': False,
                'error': '缺少draft_id参数'
            }), 400
        
        # 重定向到正确的下载API
        return redirect(f'/api/drafts/download/{draft_id}')
        
    except Exception as e:
        logger.error(f"草稿下载路由错误: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'下载失败: {str(e)}'
        }), 500


# ===== 健康检查和监控端点 =====

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点 - 返回服务状态和基本信息"""
    try:
        # 检查数据库连接
        db_status = "healthy"
        try:
            conn = sqlite3.connect('capcut.db')
            conn.execute("SELECT 1")
            conn.close()
        except Exception as db_error:
            db_status = f"unhealthy: {str(db_error)}"
            logger.error(f"数据库健康检查失败: {db_error}", exc_info=True)

        # 检查OSS连接（如果启用）
        oss_status = "disabled"
        if IS_UPLOAD_DRAFT:
            try:
                bucket = _ensure_bucket_v4()
                # 简单的存在性检查,不实际上传
                oss_status = "healthy"
            except Exception as oss_error:
                oss_status = f"unhealthy: {str(oss_error)}"
                logger.error(f"OSS健康检查失败: {oss_error}", exc_info=True)

        # 检查缓存状态
        cache_size = len(draft_materials_cache)

        # 整体健康状态
        overall_status = "healthy" if db_status == "healthy" and (oss_status in ["healthy", "disabled"]) else "unhealthy"

        return jsonify({
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'version': 'v1.1.0',
            'environment': 'CapCut' if IS_CAPCUT_ENV else '剪映',
            'components': {
                'database': db_status,
                'oss': oss_status,
                'cache': {
                    'status': 'healthy',
                    'size': cache_size,
                    'max_size': 10000
                }
            },
            'uptime': 'N/A'  # 可以添加启动时间跟踪
        }), 200 if overall_status == "healthy" else 503

    except Exception as e:
        logger.error(f"健康检查失败: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/health/ready', methods=['GET'])
def readiness_check():
    """就绪检查端点 - 检查服务是否准备好接收请求"""
    try:
        # 检查关键组件是否就绪
        conn = sqlite3.connect('capcut.db')
        conn.execute("SELECT COUNT(*) FROM drafts")
        conn.close()

        return jsonify({
            'ready': True,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"就绪检查失败: {e}", exc_info=True)
        return jsonify({
            'ready': False,
            'reason': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


@app.route('/health/live', methods=['GET'])
def liveness_check():
    """存活检查端点 - 简单的ping检查"""
    return jsonify({
        'alive': True,
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/metrics', methods=['GET'])
def metrics():
    """性能指标端点 - 返回服务运行指标"""
    try:
        # 数据库统计
        conn = sqlite3.connect('capcut.db')
        c = conn.cursor()

        # 草稿总数
        c.execute("SELECT COUNT(*) FROM drafts")
        total_drafts = c.fetchone()[0]

        # 素材总数
        c.execute("SELECT COUNT(*) FROM materials")
        total_materials = c.fetchone()[0]

        # 按状态统计草稿
        c.execute("SELECT status, COUNT(*) FROM drafts GROUP BY status")
        draft_by_status = {row[0] or 'unknown': row[1] for row in c.fetchall()}

        conn.close()

        # 缓存统计
        cache_stats = {
            'size': len(draft_materials_cache),
            'max_size': 10000,
            'usage_percent': round(len(draft_materials_cache) / 10000 * 100, 2)
        }

        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'database': {
                'total_drafts': total_drafts,
                'total_materials': total_materials,
                'drafts_by_status': draft_by_status
            },
            'cache': cache_stats,
            'system': {
                'environment': 'CapCut' if IS_CAPCUT_ENV else '剪映',
                'upload_enabled': IS_UPLOAD_DRAFT,
                'port': PORT
            }
        }), 200

    except Exception as e:
        logger.error(f"获取性能指标失败: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


if __name__ == "__main__":
    try:
        logger.info("🚀 启动 CapCutAPI 服务...")
        logger.info(f"🔗 访问地址: http://localhost:{PORT}")
        app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("🚫 服务已停止")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}", exc_info=True)
