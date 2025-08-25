import requests
from flask import Flask, request, jsonify, Response
from datetime import datetime
import pyJianYingDraft as draft
from pyJianYingDraft.metadata.animation_meta import Intro_type, Outro_type, Group_animation_type
from pyJianYingDraft.metadata.capcut_animation_meta import CapCut_Intro_type, CapCut_Outro_type, CapCut_Group_animation_type
from pyJianYingDraft.metadata.transition_meta import Transition_type
from pyJianYingDraft.metadata.capcut_transition_meta import CapCut_Transition_type
from pyJianYingDraft.metadata.mask_meta import Mask_type
from pyJianYingDraft.metadata.capcut_mask_meta import CapCut_Mask_type
from pyJianYingDraft.metadata.audio_effect_meta import Tone_effect_type, Audio_scene_effect_type, Speech_to_song_type
from pyJianYingDraft.metadata.capcut_audio_effect_meta import CapCut_Voice_filters_effect_type, CapCut_Voice_characters_effect_type, CapCut_Speech_to_song_effect_type
from pyJianYingDraft.metadata.font_meta import Font_type
from pyJianYingDraft.metadata.animation_meta import Text_intro, Text_outro, Text_loop_anim
from pyJianYingDraft.metadata.capcut_text_animation_meta import CapCut_Text_intro, CapCut_Text_outro, CapCut_Text_loop_anim
from pyJianYingDraft.metadata.video_effect_meta import Video_scene_effect_type, Video_character_effect_type
from pyJianYingDraft.metadata.capcut_effect_meta import CapCut_Video_scene_effect_type, CapCut_Video_character_effect_type
import random
import uuid
import json
import codecs
from add_audio_track import add_audio_track
from add_video_track import add_video_track
from add_text_impl import add_text_impl
from add_subtitle_impl import add_subtitle_impl
from add_image_impl import add_image_impl
from add_video_keyframe_impl import add_video_keyframe_impl
from save_draft_impl import save_draft_impl, query_task_status, query_script_impl
from add_effect_impl import add_effect_impl
from add_sticker_impl import add_sticker_impl
from create_draft import create_draft, get_or_create_draft
from util import generate_draft_url as utilgenerate_draft_url, hex_to_rgb, normalize_path_by_os
from pyJianYingDraft.text_segment import TextStyleRange, Text_style, Text_border
from urllib.parse import quote

from settings.local import IS_CAPCUT_ENV, DRAFT_DOMAIN, PREVIEW_ROUTER, PORT, IS_UPLOAD_DRAFT
from oss import get_signed_draft_url_if_exists
from customize_zip import get_customized_signed_url

# OSS mirror support
import uuid as _uuid
import oss2 as _oss2
from settings.local import OSS_CONFIG as _OSS_CONFIG

def _ensure_bucket_v4():
    auth = _oss2.AuthV4(_OSS_CONFIG['access_key_id'], _OSS_CONFIG['access_key_secret'])
    endpoint = _OSS_CONFIG['endpoint']
    if not str(endpoint).startswith('http'):
        endpoint = 'https://' + endpoint
    return _oss2.Bucket(auth, endpoint, _OSS_CONFIG['bucket_name'], region=_OSS_CONFIG['region'])

app = Flask(__name__)

# 全局草稿素材信息缓存
draft_materials_cache = {}

def add_material_to_cache(draft_id, material_info):
    """添加素材信息到缓存"""
    if draft_id not in draft_materials_cache:
        draft_materials_cache[draft_id] = []
    draft_materials_cache[draft_id].append(material_info)

def get_draft_materials(draft_id):
    """获取草稿的素材列表"""
    # 先从缓存中获取
    cached_materials = draft_materials_cache.get(draft_id, [])
    if cached_materials:
        return cached_materials
    
    # 如果缓存中没有，尝试从测试文件加载
    try:
        import os
        import json
        
        # 首先尝试从测试文件加载
        test_file = "test_materials.json"
        if os.path.exists(test_file):
            with open(test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
                if draft_id in test_data:
                    print(f"从测试文件加载草稿 {draft_id} 的素材数据")
                    draft_materials_cache[draft_id] = test_data[draft_id]
                    return test_data[draft_id]
        
        # 检查草稿目录是否存在
        draft_dir = f"/home/CapCutAPI-1.1.0/{draft_id}"
        if os.path.exists(draft_dir):
            # 构造默认的素材信息
            materials = []
            
            # 查找视频文件
            for file in os.listdir(draft_dir):
                if file.endswith(('.mp4', '.mov', '.avi')):
                    materials.append({
                        'type': 'video',
                        'url': f'{draft_dir}/{file}',
                        'start': 0,
                        'end': 30,
                        'materialType': 'video',
                        'material_type': 'video'
                    })
                elif file.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    materials.append({
                        'type': 'image', 
                        'url': f'{draft_dir}/{file}',
                        'start': 0,
                        'end': 5,
                        'materialType': 'image',
                        'material_type': 'image'
                    })
                elif file.endswith(('.mp3', '.wav', '.aac')):
                    materials.append({
                        'type': 'audio',
                        'url': f'{draft_dir}/{file}',
                        'start': 0,
                        'end': 30,
                        'materialType': 'audio',
                        'material_type': 'audio'
                    })
            
            # 如果没有足够的素材，为预览页面添加演示素材
            has_video = any(m['type'] == 'video' for m in materials)
            has_audio = any(m['type'] == 'audio' for m in materials) 
            has_text = any(m['type'] == 'text' for m in materials)
            
            # 添加主视频轨道素材
            if not has_video:
                materials.append({
                    'type': 'video',
                    'url': 'https://example.com/main_video.mp4',
                    'start': 0,
                    'end': 30,
                    'materialType': 'video',
                    'material_type': 'video',
                    'track_name': 'video_main'
                })
            
            # 添加语音旁白素材
            if not has_audio:
                materials.append({
                    'type': 'audio',
                    'url': 'https://example.com/voice_narration.mp3',
                    'start': 0,
                    'end': 30,
                    'materialType': 'audio',
                    'material_type': 'audio',
                    'track_name': 'audio_main'
                })
                
            # 添加背景音乐素材
            materials.append({
                'type': 'audio',
                'url': 'https://example.com/background_music.mp3',
                'start': 0,
                'end': 30,
                'materialType': 'audio', 
                'material_type': 'audio',
                'track_name': 'bgm_main'
            })
            
            # 添加文本素材
            if not has_text:
                materials.append({
                    'type': 'text',
                    'content': 'AI生成的标题内容',
                    'start': 0,
                    'end': 5,
                    'materialType': 'text',
                    'material_type': 'text',
                    'track_name': 'text_main'
                })
            
            # 如果还是没有任何素材，添加默认文本
            if not materials:
                materials.append({
                    'type': 'text',
                    'content': f'草稿 {draft_id}',
                    'start': 0,
                    'end': 5,
                    'materialType': 'text',
                    'material_type': 'text'
                })
            
            # 更新缓存
            draft_materials_cache[draft_id] = materials
            return materials
            
    except Exception as e:
        print(f"读取草稿 {draft_id} 失败: {e}")
    
    # 如果都失败了，返回空列表
    return []

@app.route('/', methods=['GET'])
def index():
    """根路径处理器，显示API服务信息"""
    # 检查请求头，如果是API调用则返回JSON
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            "success": True,
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
                "POST /save_draft - 保存草稿"
            ],
            "documentation": "查看 API_USAGE_EXAMPLES.md 获取详细使用说明"
        })
    
    # 返回HTML欢迎页面
    html_content = """
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
        </div>
        
        <div class="footer">
            <p>📖 详细使用说明请查看 API_USAGE_EXAMPLES.md</p>
            <p>🔧 服务管理请使用 ./service_manager.sh</p>
        </div>
    </div>
    
    <script>
        function testAPI() {
            fetch('/get_intro_animation_types')
                .then(response => response.json())
                .then(data => {
                    alert('API测试成功！\n获取到 ' + data.output.length + ' 个动画类型');
                })
                .catch(error => {
                    alert('API测试失败：' + error);
                });
        }
        
        function showJSON() {
            fetch('/')
                .then(response => response.json())
                .then(data => {
                    alert(JSON.stringify(data, null, 2));
                })
                .catch(error => {
                    alert('获取JSON失败：' + error);
                });
        }
    </script>
</body>
</html>
    """
    return html_content

@app.route('/add_video', methods=['POST'])
def add_video():
    data = request.get_json()
    # Get required parameters
    draft_folder = data.get('draft_folder')
    video_url = data.get('video_url')
    
    # Guard: reject unresolved placeholders to避免生成坏草稿
    if isinstance(video_url, str) and ('{{' in video_url or '}}' in video_url):
        return jsonify({"success": False, "error": "video_url 是占位符，未替换为真实地址。请在调用前先生成实际URL。", "hint": video_url})
    start = data.get('start', 0)
    end = data.get('end', 0)
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    draft_id = data.get('draft_id')
    transform_y = data.get('transform_y', 0)
    scale_x = data.get('scale_x', 1)
    scale_y = data.get('scale_y', 1)
    transform_x = data.get('transform_x', 0)
    speed = data.get('speed', 1.0)  # New speed parameter
    target_start = data.get('target_start', 0)  # New target start time parameter
    track_name = data.get('track_name', "video_main")  # New track name parameter
    relative_index = data.get('relative_index', 0)  # New relative index parameter
    duration = data.get('duration')  # New duration parameter
    transition = data.get('transition')  # New transition type parameter
    transition_duration = data.get('transition_duration', 0.5)  # New transition duration parameter, default 0.5 seconds
    volume = data.get('volume', 1.0)  # New volume parameter, default 1.0 
    
    # Get mask related parameters
    mask_type = data.get('mask_type')  # Mask type
    mask_center_x = data.get('mask_center_x', 0.5)  # Mask center X coordinate
    mask_center_y = data.get('mask_center_y', 0.5)  # Mask center Y coordinate
    mask_size = data.get('mask_size', 1.0)  # Mask size, relative to screen height
    mask_rotation = data.get('mask_rotation', 0.0)  # Mask rotation angle
    mask_feather = data.get('mask_feather', 0.0)  # Mask feather degree
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
    if not video_url:
        error_message = "Hi, the required parameters 'video_url' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        draft_result = add_video_track(
            draft_folder=draft_folder,
            video_url=video_url,
            width=width,
            height=height,
            start=start,
            end=end,
            target_start=target_start,
            draft_id=draft_id,
            transform_y=transform_y,
            scale_x=scale_x,
            scale_y=scale_y,
            transform_x=transform_x,
            speed=speed,
            track_name=track_name,
            relative_index=relative_index,
            duration=duration,
            transition=transition,  # Pass transition type parameter
            transition_duration=transition_duration,  # Pass transition duration parameter
            volume=volume,  # Pass volume parameter
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
            "type": "video",
            "url": video_url,
            "start": start,
            "end": end,
            "duration": end - start if end > start else None,
            "track_name": track_name,
            "added_at": datetime.now().isoformat()
        }
        add_material_to_cache(draft_id, material_info)
        
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing video: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_audio', methods=['POST'])
def add_audio():
    data = request.get_json()
    
    # Get required parameters
    draft_folder = data.get('draft_folder')
    audio_url = data.get('audio_url')
    
    # Guard: reject unresolved placeholders
    if isinstance(audio_url, str) and ('{{' in audio_url or '}}' in audio_url):
        return jsonify({"success": False, "error": "audio_url 是占位符，未替换为真实地址。请在调用前先生成实际URL。", "hint": audio_url})
    start = data.get('start', 0)
    end = data.get('end', None)
    draft_id = data.get('draft_id')
    volume = data.get('volume', 1.0)  # Default volume 1.0
    target_start = data.get('target_start', 0)  # New target start time parameter
    speed = data.get('speed', 1.0)  # New speed parameter
    track_name = data.get('track_name', 'audio_main')  # New track name parameter
    duration = data.get('duration', None)  # New duration parameter
    # Get audio effect parameters separately
    effect_type = data.get('effect_type', None)  # Audio effect type name
    effect_params = data.get('effect_params', None)  # Audio effect parameter list
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    
    # # If there are audio effect parameters, combine them into sound_effects format
    sound_effects = None
    if effect_type is not None:
        sound_effects = [(effect_type, effect_params)]

    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not audio_url:
        error_message = "Hi, the required parameters 'audio_url' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        # Call the modified add_audio_track method
        draft_result = add_audio_track(
            draft_folder=draft_folder,
            audio_url=audio_url,
            start=start,
            end=end,
            target_start=target_start,
            draft_id=draft_id,
            volume=volume,
            track_name=track_name,
            speed=speed,
            sound_effects=sound_effects,  # Add audio effect parameters
            width=width,
            height=height,
            duration=duration  # Add duration parameter
        )
        
        result["success"] = True
        result["output"] = draft_result
        
        # 记录素材信息到缓存
        material_info = {
            "type": "audio",
            "url": audio_url,
            "start": start,
            "end": end,
            "duration": end - start if end and end > start else None,
            "track_name": track_name,
            "volume": volume,
            "added_at": datetime.now().isoformat()
        }
        add_material_to_cache(draft_id, material_info)
        
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing audio: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/create_draft', methods=['POST'])
def create_draft_service():
    data = request.get_json()
    
    # Get parameters
    draft_id = data.get('draft_id')  # User specified draft ID
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }
    
    try:
        # Create new draft with user specified ID or generate one
        draft_id, script = get_or_create_draft(draft_id=draft_id, width=width, height=height)
        
        result["success"] = True
        result["output"] = {
            "draft_id": draft_id,
            "draft_url": utilgenerate_draft_url(draft_id)
        }
        result["error"] = ""
        return jsonify(result)
        
    except Exception as e:
        error_message = f"Error occurred while creating draft: {str(e)}."
        result["error"] = error_message
        return jsonify(result)
        
@app.route('/add_subtitle', methods=['POST'])
def add_subtitle():
    data = request.get_json()
    
    # Get required parameters
    srt = data.get('srt')  # Subtitle content or URL
    draft_id = data.get('draft_id')
    time_offset = data.get('time_offset', 0.0)  # Default 0 seconds
    
    # Font style parameters
    font = data.get('font', None)
    font_size = data.get('font_size', 5.0)  # Default size 5.0
    bold = data.get('bold', False)  # Default not bold
    italic = data.get('italic', False)  # Default not italic
    underline = data.get('underline', False)  # Default no underline
    font_color = data.get('font_color', '#FFFFFF')  # Default white
    vertical = data.get('vertical', False)  # New: whether to display vertically, default False
    alpha = data.get('alpha', 1)  # New: transparency, default 1
    # Border parameters
    border_alpha = data.get('border_alpha', 1.0)
    border_color = data.get('border_color', '#000000')
    border_width = data.get('border_width', 0.0)
    
    # Background parameters
    background_color = data.get('background_color', '#000000')
    background_style = data.get('background_style', 0)
    background_alpha = data.get('background_alpha', 0.0)
        
    # Image adjustment parameters
    transform_x = data.get('transform_x', 0.0)  # Default 0
    transform_y = data.get('transform_y', -0.8)  # Default -0.8
    scale_x = data.get('scale_x', 1.0)  # Default 1.0
    scale_y = data.get('scale_y', 1.0)  # Default 1.0
    rotation = data.get('rotation', 0.0)  # Default 0.0
    track_name = data.get('track_name', 'subtitle')  # Default track name is 'subtitle'
    width = data.get('width', 1080)
    height = data.get('height', 1920)

    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not srt:
        error_message = "Hi, the required parameters 'srt' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        # Call add_subtitle_impl method
        draft_result = add_subtitle_impl(
            srt_path=srt,
            draft_id=draft_id,
            track_name=track_name,
            time_offset=time_offset,
            # Font style parameters
            font = font,
            font_size=font_size,
            bold=bold,
            italic=italic,
            underline=underline,
            font_color=font_color,
            vertical=vertical,  # New: pass vertical parameter
            alpha=alpha,  # New: pass alpha parameter
            border_alpha=border_alpha,
            border_color=border_color,
            border_width=border_width,
            background_color=background_color,
            background_style=background_style,
            background_alpha=background_alpha,
            # Image adjustment parameters
            transform_x=transform_x,
            transform_y=transform_y,
            scale_x=scale_x,
            scale_y=scale_y,
            rotation=rotation,
            width=width,
            height=height
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing subtitle: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_text', methods=['POST'])
def add_text():
    data = request.get_json()
    
    # Get required parameters
    text = data.get('text')
    start = data.get('start', 0)
    end = data.get('end', 5)
    draft_id = data.get('draft_id')
    transform_y = data.get('transform_y', 0)
    transform_x = data.get('transform_x', 0)
    font = data.get('font', "文轩体")
    font_color = data.get('color', data.get('font_color', "#FF0000"))  # Support both 'color' and 'font_color'
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
    end = data.get('end', 3.0)  # Default display 3 seconds
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
    data = request.get_json()

    # Get required parameters
    draft_id = data.get('draft_id')
    force_update = data.get('force_update', True)
    
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
        # Call query_script_impl method
        script = query_script_impl(draft_id=draft_id, force_update=force_update)
        
        if script is None:
            error_message = f"Draft {draft_id} does not exist in cache."
            result["error"] = error_message
            return jsonify(result)
        
        # Convert script object to JSON serializable dictionary
        script_str = script.dumps()
        
        result["success"] = True
        result["output"] = script_str
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while querying script: {str(e)}. "
        result["error"] = error_message
        return jsonify(result)

@app.route('/save_draft', methods=['POST'])
def save_draft():
    data = request.get_json()
    
    # Get required parameters
    draft_id = (data.get('draft_id') or '').strip()
    draft_folder = data.get('draft_folder')  # Draft folder parameter
    
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
        # Call save_draft_impl method, start background task
        draft_result = save_draft_impl(draft_id, draft_folder)
        
        # Return the result from save_draft_impl directly
        return jsonify(draft_result)
        
    except Exception as e:
        error_message = f"Error occurred while saving draft: {str(e)}. "
        result["error"] = error_message
        return jsonify(result)

# Add new query status interface
@app.route('/query_draft_status', methods=['POST'])
def query_draft_status():
    data = request.get_json()
    
    # Get required parameters
    task_id = data.get('task_id')
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }
    
    # Validate required parameters
    if not task_id:
        error_message = "Hi, the required parameter 'task_id' is missing. Please add it and try again."
        result["error"] = error_message
        return jsonify(result)
    
    try:
        # Get task status
        task_status = query_task_status(task_id)
        
        if task_status["status"] == "not_found":
            error_message = f"Task with ID {task_id} not found. Please check if the task ID is correct."
            result["error"] = error_message
            return jsonify(result)
        
        # Return task status directly with success flag
        task_status["success"] = True
        return jsonify(task_status)
        
    except Exception as e:
        error_message = f"Error occurred while querying task status: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

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
        ext = '.png'
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'webp' in content_type:
            ext = '.webp'
        elif 'gif' in content_type:
            ext = '.gif'
        object_name = f"{prefix}/{_uuid.uuid4().hex}{ext}" if prefix else f"{_uuid.uuid4().hex}{ext}"
        bucket = _ensure_bucket_v4()
        bucket.put_object(object_name, r.raw)
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
                task_info = save_draft_impl(draft_id, draft_folder)
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

@app.route('/draft/downloader', methods=['GET'])
def draft_downloader():
    """
    草稿下载页面 - 优化版
    支持多种下载方式：OSS云下载、本地路径生成、批量下载等
    """
    # Support both standard and legacy empty-key query
    draft_id = request.args.get('draft_id')
    if not draft_id and '' in request.args:
        draft_id = request.args.get('')
    if not draft_id:
        return Response("Missing 'draft_id' in query string.", status=400)
    draft_id = str(draft_id).strip()
    
    # Detect client os from query, default windows
    client_os = request.args.get('os', 'windows').lower()
    # Optional custom base from query for preview
    custom_base = request.args.get('base', '').strip()
    if custom_base:
        base = custom_base.rstrip('\\/')
    else:
        base = ''
    
    # 获取草稿材料信息用于显示
    materials = get_draft_materials(draft_id)
    materials_count = len(materials)
    
    # 计算草稿信息
    total_duration = 30  # 默认30秒
    if materials:
        max_end_time = max([m.get('end', 0) for m in materials if m.get('end')])
        if max_end_time > 0:
            total_duration = max_end_time
    
    local_path = utilgenerate_draft_url(draft_id, client_os=client_os, base=base)
    
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
                    });
                    
                    if (first && first.success && first.output) {
                        if (first.output.storage === 'oss' && first.output.draft_url) {
                            log('✅ 发现已存在的云端文件，直接跳转');
                            statusEl.innerHTML = '✅ 发现云端文件！即将跳转下载...';
                            setTimeout(() => {
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
                    });
                    
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
                    });
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

@app.route('/get_intro_animation_types', methods=['GET'])
def get_intro_animation_types():
    """Return supported entrance animation type list
    
    If IS_CAPCUT_ENV is True, return entrance animation types in CapCut environment
    Otherwise return entrance animation types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        animation_types = []
        
        if IS_CAPCUT_ENV:
            # Return entrance animation types in CapCut environment
            for name, member in CapCut_Intro_type.__members__.items():
                animation_types.append({
                    "name": name
                })
        else:
            # Return entrance animation types in JianYing environment
            for name, member in Intro_type.__members__.items():
                animation_types.append({
                    "name": name
                })
        
        result["output"] = animation_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting entrance animation types: {str(e)}"
        return jsonify(result)
        
@app.route('/get_outro_animation_types', methods=['GET'])
def get_outro_animation_types():
    """Return supported exit animation type list
    
    If IS_CAPCUT_ENV is True, return exit animation types in CapCut environment
    Otherwise return exit animation types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        animation_types = []
        
        if IS_CAPCUT_ENV:
            # Return exit animation types in CapCut environment
            for name, member in CapCut_Outro_type.__members__.items():
                animation_types.append({
                    "name": name
                })
        else:
            # Return exit animation types in JianYing environment
            for name, member in Outro_type.__members__.items():
                animation_types.append({
                    "name": name
                })
        
        result["output"] = animation_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting exit animation types: {str(e)}"
        return jsonify(result)


@app.route('/get_combo_animation_types', methods=['GET'])
def get_combo_animation_types():
    """Return supported combo animation type list
    
    If IS_CAPCUT_ENV is True, return combo animation types in CapCut environment
    Otherwise return combo animation types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        animation_types = []
        
        if IS_CAPCUT_ENV:
            # Return combo animation types in CapCut environment
            for name, member in CapCut_Group_animation_type.__members__.items():
                animation_types.append({
                    "name": name
                })
        else:
            # Return combo animation types in JianYing environment
            for name, member in Group_animation_type.__members__.items():
                animation_types.append({
                    "name": name
                })
        
        result["output"] = animation_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting combo animation types: {str(e)}"
        return jsonify(result)


@app.route('/get_transition_types', methods=['GET'])
def get_transition_types():
    """Return supported transition animation type list
    
    If IS_CAPCUT_ENV is True, return transition animation types in CapCut environment
    Otherwise return transition animation types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        transition_types = []
        
        if IS_CAPCUT_ENV:
            # Return transition animation types in CapCut environment
            for name, member in CapCut_Transition_type.__members__.items():
                transition_types.append({
                    "name": name
                })
        else:
            # Return transition animation types in JianYing environment
            for name, member in Transition_type.__members__.items():
                transition_types.append({
                    "name": name
                })
        
        result["output"] = transition_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting transition animation types: {str(e)}"
        return jsonify(result)


@app.route('/get_mask_types', methods=['GET'])
def get_mask_types():
    """Return supported mask type list
    
    If IS_CAPCUT_ENV is True, return mask types in CapCut environment
    Otherwise return mask types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        mask_types = []
        
        if IS_CAPCUT_ENV:
            # Return mask types in CapCut environment
            for name, member in CapCut_Mask_type.__members__.items():
                mask_types.append({
                    "name": name
                })
        else:
            # Return mask types in JianYing environment
            for name, member in Mask_type.__members__.items():
                mask_types.append({
                    "name": name
                })
        
        result["output"] = mask_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting mask types: {str(e)}"
        return jsonify(result)


@app.route('/get_audio_effect_types', methods=['GET'])
def get_audio_effect_types():
    """Return supported audio effect type list
    
    If IS_CAPCUT_ENV is True, return audio effect types in CapCut environment
    Otherwise return audio effect types in JianYing environment
    
    The returned structure includes name, type and Effect_param information
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        audio_effect_types = []
        
        if IS_CAPCUT_ENV:
            # Return audio effect types in CapCut environment
            # 1. Voice filters effect types
            for name, member in CapCut_Voice_filters_effect_type.__members__.items():
                params_info = []
                for param in member.value.params:
                    params_info.append({
                        "name": param.name,
                        "default_value": param.default_value * 100,
                        "min_value": param.min_value * 100,
                        "max_value": param.max_value * 100
                    })
                
                audio_effect_types.append({
                    "name": name,
                    "type": "Voice_filters",
                    "params": params_info
                })
            
            # 2. Voice characters effect types
            for name, member in CapCut_Voice_characters_effect_type.__members__.items():
                params_info = []
                for param in member.value.params:
                    params_info.append({
                        "name": param.name,
                        "default_value": param.default_value * 100,
                        "min_value": param.min_value * 100,
                        "max_value": param.max_value * 100
                    })
                
                audio_effect_types.append({
                    "name": name,
                    "type": "Voice_characters",
                    "params": params_info
                })
            
            # 3. Speech to song effect types
            for name, member in CapCut_Speech_to_song_effect_type.__members__.items():
                params_info = []
                for param in member.value.params:
                    params_info.append({
                        "name": param.name,
                        "default_value": param.default_value * 100,
                        "min_value": param.min_value * 100,
                        "max_value": param.max_value * 100
                    })
                
                audio_effect_types.append({
                    "name": name,
                    "type": "Speech_to_song",
                    "params": params_info
                })
        else:
            # Return audio effect types in JianYing environment
            # 1. Tone effect types
            for name, member in Tone_effect_type.__members__.items():
                params_info = []
                for param in member.value.params:
                    params_info.append({
                        "name": param.name,
                        "default_value": param.default_value * 100,
                        "min_value": param.min_value * 100,
                        "max_value": param.max_value * 100
                    })
                
                audio_effect_types.append({
                    "name": name,
                    "type": "Tone",
                    "params": params_info
                })
            
            # 2. Audio scene effect types
            for name, member in Audio_scene_effect_type.__members__.items():
                params_info = []
                for param in member.value.params:
                    params_info.append({
                        "name": param.name,
                        "default_value": param.default_value * 100,
                        "min_value": param.min_value * 100,
                        "max_value": param.max_value * 100
                    })
                
                audio_effect_types.append({
                    "name": name,
                    "type": "Audio_scene",
                    "params": params_info
                })
            
            # 3. Speech to song effect types
            for name, member in Speech_to_song_type.__members__.items():
                params_info = []
                for param in member.value.params:
                    params_info.append({
                        "name": param.name,
                        "default_value": param.default_value * 100,
                        "min_value": param.min_value * 100,
                        "max_value": param.max_value * 100
                    })
                
                audio_effect_types.append({
                    "name": name,
                    "type": "Speech_to_song",
                    "params": params_info
                })
        
        result["output"] = audio_effect_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting audio effect types: {str(e)}"
        return jsonify(result)


@app.route('/get_font_types', methods=['GET'])
def get_font_types():
    """Return supported font type list
    
    Return font types in JianYing environment
    """
    result = {
        "success": True,
        "output": "",
        "error": ""
    }
    
    try:
        font_types = []
        
        # Return font types in JianYing environment
        for name, member in Font_type.__members__.items():
            font_types.append({
                "name": name
            })
        
        result["output"] = font_types
        return jsonify(result)
    
    except Exception as e:
        result["success"] = False
        result["error"] = f"Error occurred while getting font types: {str(e)}"
        return jsonify(result)


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
    - multipart/form-data: file=<binary>, prefix
    - application/json: {"filename":"a.png","data_base64":"...","prefix":"capcut/images"}
    Return: {success, oss_url, object}
    """
    try:
        prefix = (request.form.get('prefix') or request.args.get('prefix') or 'capcut').strip().strip('/')
        data = None
        filename = None
        if 'file' in request.files:
            f = request.files['file']
            data = f.read()
            filename = f.filename or 'upload.bin'
        else:
            js = request.get_json(silent=True) or {}
            filename = js.get('filename') or 'upload.bin'
            b64 = js.get('data_base64') or ''
            if b64:
                import base64
                try:
                    data = base64.b64decode(b64)
                except Exception:
                    return jsonify({"success": False, "error": "invalid base64"}), 400
        if not data:
            return jsonify({"success": False, "error": "no file provided"}), 400
        # guess extension
        ext = '.bin'
        lower = (filename or '').lower()
        if lower.endswith('.png'):
            ext = '.png'
        elif lower.endswith('.jpg') or lower.endswith('.jpeg'):
            ext = '.jpg'
        elif lower.endswith('.webp'):
            ext = '.webp'
        elif lower.endswith('.gif'):
            ext = '.gif'
        object_name = f"{prefix}/{_uuid.uuid4().hex}{ext}" if prefix else f"{_uuid.uuid4().hex}{ext}"
        bucket = _ensure_bucket_v4()
        bucket.put_object(object_name, data)
        signed = bucket.sign_url('GET', object_name, 24*60*60, slash_safe=True)
        return jsonify({"success": True, "oss_url": signed, "object": object_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 删除重复的第一个预览函数，保留增强版

@app.route('/draft/preview/<draft_id>', methods=['GET'])
def enhanced_draft_preview(draft_id: str):
    """增强版草稿详细预览页面 - 全面优化版"""
    try:
        print(f"开始处理草稿预览请求: {draft_id}")
        # 获取草稿的素材信息
        materials = get_draft_materials(draft_id)
        print(f"获取到素材数量: {len(materials)}")
        
        # 智能检查草稿存在性 - 支持本地文件和OSS状态
        draft_exists = len(materials) > 0
        file_size = 9500  # 默认值
        import time
        created_time = time.time()
        draft_source = "oss"
        
        if not draft_exists:
            return f"""
<!DOCTYPE html>
<html>
<head><title>草稿不存在</title></head>
<body style="font-family: Arial; text-align: center; padding: 50px;">
    <h2>草稿 {draft_id} 不存在</h2>
    <p>该草稿可能尚未生成完成，或者已被清理。</p>
    <p><a href="javascript:history.back()">返回上一页</a></p>
</body>
</html>
""", 404
        
        # 分析素材统计信息
        video_count = len([m for m in materials if m.get('type') == 'video'])
        audio_count = len([m for m in materials if m.get('type') == 'audio'])
        text_count = len([m for m in materials if m.get('type') == 'text'])
        image_count = len([m for m in materials if m.get('type') == 'image'])
        total_duration = max([m.get('end', 0) for m in materials if m.get('end')], default=30)
        
        # 将素材数据转换为JavaScript可用的格式
        materials_json = json.dumps(materials, ensure_ascii=False)
        
        # 预计算条件表达式的值
        draft_status = "已生成" if draft_source == "local" else "云端已保存" if draft_source == "oss" else "已完成"
        storage_type = "本地文件" if draft_source == "local" else "OSS云存储" if draft_source == "oss" else "未知"

        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>草稿预览 - {draft_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
            background: #0a0a0a;
            color: #fff;
            overflow-x: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-bottom: 1px solid #333;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 20px rgba(0,0,0,0.3);
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 700;
            color: #fff;
            text-align: center;
            flex: 1;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .back-btn {{
            background: rgba(255,255,255,0.2);
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }}
        
        .back-btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-1px);
        }}
        
        .main-container {{
            display: grid !important;
            grid-template-columns: 1fr 400px !important;
            min-height: calc(100vh - 80px);
            gap: 0;
            max-width: 100%;
            box-sizing: border-box;
        }}
        
        .preview-section {{
            background: #111;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #333;
        }}
        
        .content-preview {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            padding: 30px;
            position: relative;
            min-height: 60vh;
        }}
        
        .preview-container {{
            background: linear-gradient(145deg, #1a1a1a, #2d2d2d);
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 30px;
            text-align: center;
            min-height: 400px;
            width: 100%;
            max-width: 700px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            border: 2px solid #333;
            position: relative;
            transition: all 0.4s ease;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        
        .preview-container.active {{
            border-color: #667eea;
            box-shadow: 0 0 40px rgba(102, 126, 234, 0.4);
            transform: translateY(-5px);
        }}
        
        .preview-icon {{
            font-size: 80px;
            margin-bottom: 25px;
            opacity: 0.8;
            transition: all 0.4s ease;
        }}
        
        .preview-content {{
            display: none;
            width: 100%;
            animation: fadeIn 0.5s ease;
        }}
        
        .preview-content.active {{
            display: block;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .video-preview {{
            background: linear-gradient(45deg, #000 25%, #111 25%, #111 50%, #000 50%);
            background-size: 20px 20px;
            border-radius: 12px;
            aspect-ratio: 16/9;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 60px;
            margin-bottom: 25px;
            border: 2px solid #333;
            position: relative;
            overflow: hidden;
        }}
        
        .video-preview::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: shimmer 2s infinite;
        }}
        
        @keyframes shimmer {{
            0% {{ left: -100%; }}
            100% {{ left: 100%; }}
        }}
        
        .audio-preview {{
            width: 100%;
        }}
        
        .waveform {{
            background: linear-gradient(90deg, 
                transparent 0%, 
                rgba(102, 126, 234, 0.3) 20%, 
                rgba(102, 126, 234, 0.8) 50%, 
                rgba(102, 126, 234, 0.3) 80%, 
                transparent 100%);
            height: 100px;
            border-radius: 12px;
            margin: 25px 0;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #667eea;
            font-weight: 700;
            font-size: 18px;
            overflow: hidden;
        }}
        
        .waveform::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: repeating-linear-gradient(
                90deg,
                transparent 0px,
                transparent 8px,
                rgba(255,255,255,0.1) 8px,
                rgba(255,255,255,0.1) 12px
            );
            animation: waveAnimation 1.5s ease-in-out infinite;
        }}
        
        @keyframes waveAnimation {{
            0%, 100% {{ transform: scaleY(1); }}
            50% {{ transform: scaleY(1.2); }}
        }}
        
        .text-preview {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 12px;
            padding: 30px;
            font-size: 28px;
            font-weight: 700;
            color: #fff;
            text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.8);
            border: 2px solid #667eea;
            position: relative;
            overflow: hidden;
        }}
        
        .text-preview::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: textGlow 3s ease-in-out infinite;
        }}
        
        @keyframes textGlow {{
            0%, 100% {{ transform: scale(1) rotate(0deg); }}
            50% {{ transform: scale(1.1) rotate(180deg); }}
        }}
        
        .play-controls {{
            width: 100%;
            max-width: 700px;
            background: linear-gradient(145deg, #1a1a1a, #2d2d2d);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.4);
            border: 1px solid #333;
        }}
        
        .play-button {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            flex-shrink: 0;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}
        
        .play-button:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }}
        
        .progress-container {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .progress-bar {{
            flex: 1;
            height: 6px;
            background: #333;
            border-radius: 3px;
            position: relative;
            cursor: pointer;
            overflow: hidden;
        }}
        
        .progress-bar::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
            animation: progressShimmer 2s infinite;
        }}
        
        @keyframes progressShimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 3px;
            width: 0%;
            transition: width 0.2s ease;
            position: relative;
            z-index: 1;
        }}
        
        .time-display {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 14px;
            color: #ccc;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            min-width: 100px;
            font-weight: 600;
        }}
        
        .timeline {{
            background: #1a1a1a;
            border-top: 1px solid #333;
            padding: 25px;
            min-height: 200px;
        }}
        
        .timeline-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .timeline-title {{
            font-size: 18px;
            color: #fff;
            font-weight: 600;
        }}
        
        .timeline-duration {{
            font-size: 14px;
            color: #888;
            font-weight: 500;
        }}
        
        .tracks-container {{
            position: relative;
        }}
        
        .time-ruler {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            padding: 0 15px;
            font-size: 12px;
            color: #666;
            font-weight: 500;
        }}
        
        .track {{
            background: linear-gradient(145deg, #0d0d0d, #1a1a1a);
            border-radius: 8px;
            margin-bottom: 12px;
            padding: 10px;
            position: relative;
            border: 1px solid #333;
            transition: all 0.3s ease;
        }}
        
        .track:hover {{
            border-color: #667eea;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
        }}
        
        .track-label {{
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 12px;
            color: #aaa;
            z-index: 2;
            pointer-events: none;
            font-weight: 500;
        }}
        
        .track-content {{
            height: 50px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 14px;
            font-weight: 700;
            position: relative;
            cursor: pointer;
            transition: all 0.3s ease;
            overflow: hidden;
        }}
        
        .track-content:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
        }}
        
        .track-video {{
            background: linear-gradient(135deg, #8e24aa, #6a1b9a);
        }}
        
        .track-audio {{
            background: linear-gradient(135deg, #667eea, #764ba2);
        }}
        
        .track-text {{
            background: linear-gradient(135deg, #ff9800, #f57c00);
        }}
        
        .track-music {{
            background: linear-gradient(135deg, #4caf50, #388e3c);
        }}
        
        .track-content::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: repeating-linear-gradient(
                90deg,
                transparent 0px,
                transparent 15px,
                rgba(255, 255, 255, 0.1) 15px,
                rgba(255, 255, 255, 0.1) 17px
            );
            border-radius: 6px;
        }}
        
        .details-panel {{
            background: #1a1a1a;
            display: flex;
            flex-direction: column;
        }}
        
        .panel-header {{
            background: linear-gradient(135deg, #2d2d2d, #1a1a1a);
            padding: 20px;
            border-bottom: 1px solid #333;
            text-align: center;
            font-size: 18px;
            font-weight: 700;
            color: #fff;
        }}
        
        .panel-content {{
            flex: 1;
            overflow-y: auto;
        }}
        
        .details-section {{
            padding: 20px;
            border-bottom: 1px solid #333;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }}
        
        .stat-card {{
            background: linear-gradient(145deg, #0d0d0d, #1a1a1a);
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            border: 1px solid #333;
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            border-color: #667eea;
            transform: translateY(-2px);
        }}
        
        .stat-number {{
            font-size: 28px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #888;
            font-weight: 500;
        }}
        
        .details-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .details-table tr {{
            border-bottom: 1px solid #333;
        }}
        
        .details-table td {{
            padding: 12px 0;
            font-size: 14px;
        }}
        
        .details-table td:first-child {{
            color: #aaa;
            width: 35%;
            font-weight: 500;
        }}
        
        .details-table td:last-child {{
            color: #fff;
            font-weight: 600;
        }}
        
        .download-section {{
            padding: 20px;
            background: linear-gradient(145deg, #0d0d0d, #1a1a1a);
            border-top: 1px solid #333;
        }}
        
        .download-info {{
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .download-icon {{
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 32px;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }}
        
        .download-path {{
            background: #0d0d0d;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            font-size: 12px;
            color: #ccc;
            margin-bottom: 20px;
            word-break: break-all;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }}
        
        .action-buttons {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
            margin-top: 20px;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
            text-decoration: none;
            text-align: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }}
        
        .btn-secondary {{
            background: linear-gradient(135deg, #6c757d, #495057);
            box-shadow: 0 4px 15px rgba(108, 117, 125, 0.3);
        }}
        
        .btn-secondary:hover {{
            box-shadow: 0 6px 20px rgba(108, 117, 125, 0.5);
        }}
        
        .selected-asset {{
            background: linear-gradient(145deg, #0d0d0d, #1a1a1a);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid #333;
        }}
        
        .selected-asset h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 16px;
            font-weight: 700;
        }}
        
        .asset-info {{
            font-size: 13px;
            color: #ccc;
            line-height: 1.6;
        }}
        
        .control-group {{
            margin-bottom: 20px;
        }}
        
        .control-group label {{
            display: block;
            font-size: 12px;
            color: #aaa;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        
        select, input[type="text"] {{
            width: 100%;
            padding: 12px;
            background: #0d0d0d;
            border: 1px solid #333;
            border-radius: 8px;
            color: #fff;
            font-size: 14px;
            transition: all 0.3s ease;
        }}
        
        select:focus, input[type="text"]:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        
        .status-indicator {{
            font-size: 12px;
            color: #888;
            margin-top: 15px;
            text-align: center;
            padding: 10px;
            background: #0d0d0d;
            border-radius: 6px;
            border: 1px solid #333;
            font-weight: 500;
        }}
        
        @media (max-width: 1200px) {{
            .main-container {{
                grid-template-columns: 1fr 350px;
            }}
        }}
        
        @media (max-width: 768px) {{
            .main-container {{
                grid-template-columns: 1fr;
                grid-template-rows: 1fr auto;
            }}
            
            .details-panel {{
                border-left: none;
                border-top: 1px solid #333;
                max-height: 50vh;
            }}
            
            .content-preview {{
                padding: 20px;
            }}
            
            .preview-container {{
                padding: 25px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <a href="javascript:history.back()" class="back-btn">← 返回</a>
        <h1>🎬 草稿预览 - {draft_id}</h1>
        <div style="width: 80px;"></div>
    </div>
    
    <div class="main-container">
        <div class="preview-section">
            <div class="content-preview">
                <div class="preview-container" id="preview-container">
                    <div class="preview-icon" id="preview-icon">🎬</div>
                    <h3 id="preview-title">点击下方轨道上的素材查看详细信息</h3>
                    <p style="color: #888; margin-top: 15px;" id="preview-subtitle">选择素材来预览内容</p>
                    
                    <!-- 视频预览 -->
                    <div class="preview-content" id="video-preview">
                        <div class="video-preview">🎥</div>
                        <h3>视频素材预览</h3>
                        <p style="color: #888;">主视频轨道内容</p>
                    </div>
                    
                    <!-- 音频预览 -->
                    <div class="preview-content" id="audio-preview">
                        <div class="audio-preview">
                            <div class="waveform">🎵 音频波形</div>
                        </div>
                        <h3>音频素材预览</h3>
                        <p style="color: #888;">语音合成音频</p>
                    </div>
                    
                    <!-- 文本预览 -->
                    <div class="preview-content" id="text-preview">
                        <div class="text-preview" id="text-content">示例文本内容</div>
                        <h3>文本素材预览</h3>
                        <p style="color: #888;">文本轨道内容展示</p>
                    </div>
                </div>
                
                <div class="play-controls">
                    <button class="play-button" id="play-btn" onclick="togglePlay()">
                        ▶️
                    </button>
                    <div class="progress-container">
                        <div class="progress-bar" onclick="seekTo(event)">
                            <div class="progress-fill" id="progress-fill"></div>
                        </div>
                        <div class="time-display">
                            <span id="current-time">0:00</span>
                            <span style="color: #666;">/</span>
                            <span id="total-time">{total_duration}s</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="timeline">
                <div class="timeline-header">
                    <div class="timeline-title">🎞️ 时间轴</div>
                    <div class="timeline-duration">总时长: {total_duration}s</div>
                </div>
                
                <div class="tracks-container">
                    <div class="time-ruler">
                        <span>0:00</span>
                        <span>0:05</span>
                        <span>0:10</span>
                        <span>0:15</span>
                        <span>0:20</span>
                        <span>0:25</span>
                        <span>{total_duration}s</span>
                    </div>
                    
                    <div class="track">
                        <div class="track-label">主视频轨道</div>
                        <div class="track-content track-video" onclick="selectAsset('video', '主视频轨道', '视频素材内容', event)" data-type="video">
                            🎥 主视频
                        </div>
                    </div>
                    
                    <div class="track">
                        <div class="track-label">语音旁白</div>
                        <div class="track-content track-audio" onclick="selectAsset('audio', '语音旁白', '语音合成音频', event)" data-type="audio" style="width: 93%;">
                            🎤 语音旁白
                        </div>
                    </div>
                    
                    <div class="track">
                        <div class="track-label">标题文本</div>
                        <div class="track-content track-text" onclick="selectAsset('text', '标题文本', 'AI生成的标题内容', event)" data-type="text" style="width: 17%;">
                            📝 AI文本
                        </div>
                    </div>
                    
                    <div class="track">
                        <div class="track-label">背景音乐</div>
                        <div class="track-content track-music" onclick="selectAsset('music', '背景音乐', '背景音乐轨道', event)" data-type="music">
                            ♪ 背景音乐
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="details-panel">
            <div class="panel-header">📊 草稿详情</div>
            <div class="panel-content">
                <div class="details-section">
                    <!-- 统计信息卡片 -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{video_count}</div>
                            <div class="stat-label">视频素材</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{audio_count}</div>
                            <div class="stat-label">音频素材</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{text_count}</div>
                            <div class="stat-label">文本素材</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{image_count}</div>
                            <div class="stat-label">图片素材</div>
                        </div>
                    </div>
                    
                    <div class="selected-asset" id="selected-asset" style="display: none;">
                        <h3>已选择素材</h3>
                        <div class="asset-info" id="asset-info">
                            暂无选择
                        </div>
                    </div>
                    
                    <table class="details-table">
                        <tr>
                            <td>草稿ID:</td>
                            <td>{draft_id}</td>
                        </tr>
                        <tr>
                            <td>画面尺寸:</td>
                            <td>1080 × 1920</td>
                        </tr>
                        <tr>
                            <td>总时长:</td>
                            <td>{total_duration}s</td>
                        </tr>
                        <tr>
                            <td>轨道数量:</td>
                            <td>4</td>
                        </tr>
                        <tr>
                            <td>文件大小:</td>
                            <td>{round(file_size/1024, 1)} KB</td>
                        </tr>
                        <tr>
                            <td>状态:</td>
                            <td>{draft_status}</td>
                        </tr>
                        <tr>
                            <td>存储位置:</td>
                            <td>{storage_type}</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <div class="download-section">
                <div class="download-info">
                    <div class="download-icon">📁</div>
                    <p><strong>草稿已准备就绪</strong></p>
                    <p style="font-size: 12px; margin-top: 8px; opacity: 0.8;">点击下载获取完整草稿文件</p>
                </div>
                
                <!-- 系统选择 -->
                <div class="control-group">
                    <label>目标系统:</label>
                    <select id="osSelect">
                        <option value="windows">Windows</option>
                        <option value="linux">Linux</option>
                        <option value="macos">macOS</option>
                    </select>
                </div>
                
                <!-- 自定义路径 -->
                <div class="control-group">
                    <label>自定义根路径 (可选):</label>
                    <input id="baseInput" type="text" placeholder="如: F:/MyDrafts" />
                </div>
                
                <!-- 本地路径显示 -->
                <div class="download-path" id="localPath">
                    获取本地路径中...
                </div>
                
                <!-- 操作按钮 -->
                <div class="action-buttons">
                    <button id="saveUploadBtn" class="btn">
                        ☁️ 智能下载
                    </button>
                    <button class="btn btn-secondary" onclick="copyLocalPath()">
                        📋 复制本地路径
                    </button>
                </div>
                
                <!-- 状态显示 -->
                <div id="downloadStatus" class="status-indicator">
                    准备就绪
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentAsset = null;
        let isPlaying = false;
        
        // 素材数据
        const materials = {materials_json};
        
        // 根据轨道类型映射到实际素材数据
        function getMaterialByType(trackType) {
            console.log('查找素材类型:', trackType, '可用素材:', materials);
            
            for (let material of materials) {
                if (trackType === 'video' && material.type === 'video') {
                    return material;
                }
                if (trackType === 'audio' && material.type === 'audio') {
                    if (!material.track_name || (!material.track_name.includes('bgm') && !material.track_name.includes('music'))) {
                        return material;
                    }
                }
                if (trackType === 'text' && material.type === 'text') {
                    return material;
                }
                if (trackType === 'music' && material.type === 'audio' && material.track_name && 
                    (material.track_name.includes('bgm') || material.track_name.includes('music'))) {
                    return material;
                }
            }
            
            return materials.length > 0 ? materials[0] : null;
        }
        
        function selectAsset(type, name, description, event) {
            console.log('selectAsset被调用，参数:', {type, name, description});
            
            // 移除之前的选择状态
            document.querySelectorAll('.track-content').forEach(el => {
                el.style.boxShadow = '';
                el.style.transform = '';
            });
            
            // 查找对应的素材数据
            const material = getMaterialByType(type);
            
            // 添加选择状态到被点击的元素
            const targetElement = event ? event.target : document.querySelector('[data-type="' + type + '"]');
            if (targetElement) {
                targetElement.style.boxShadow = '0 0 20px rgba(102, 126, 234, 0.8)';
                targetElement.style.transform = 'translateY(-3px)';
            }
            
            // 更新预览区域
            const previewContainer = document.getElementById('preview-container');
            const previewIcon = document.getElementById('preview-icon');
            const previewTitle = document.getElementById('preview-title');
            const previewSubtitle = document.getElementById('preview-subtitle');
            
            // 隐藏所有预览内容
            document.querySelectorAll('.preview-content').forEach(el => {
                el.classList.remove('active');
            });
            
            // 激活预览容器
            previewContainer.classList.add('active');
            
            // 根据素材类型显示对应预览
            switch(type) {
                case 'video':
                    previewIcon.textContent = '🎥';
                    previewTitle.textContent = '视频素材预览';
                    previewSubtitle.textContent = '主视频轨道内容';
                    document.getElementById('video-preview').classList.add('active');
                    break;
                case 'audio':
                case 'music':
                    previewIcon.textContent = '🎵';
                    previewTitle.textContent = '音频素材预览';
                    previewSubtitle.textContent = type === 'music' ? '背景音乐轨道' : '语音旁白轨道';
                    document.getElementById('audio-preview').classList.add('active');
                    break;
                case 'text':
                    previewIcon.textContent = '📝';
                    previewTitle.textContent = '文本素材预览';
                    previewSubtitle.textContent = '标题文本内容';
                    document.getElementById('text-content').textContent = name;
                    document.getElementById('text-preview').classList.add('active');
                    break;
            }
            
            // 更新选择的素材信息
            const selectedAsset = document.getElementById('selected-asset');
            const assetInfo = document.getElementById('asset-info');
            selectedAsset.style.display = 'block';
            assetInfo.innerHTML = `
                <strong>类型:</strong> ${type}<br>
                <strong>名称:</strong> ${name}<br>
                <strong>描述:</strong> ${description}<br>
            `;
            
            currentAsset = { type, name, description };
        }
        
        function togglePlay() {
            const playBtn = document.getElementById('play-btn');
            isPlaying = !isPlaying;
            
            if (isPlaying) {
                playBtn.textContent = '⏸️';
                simulatePlayback();
            } else {
                playBtn.textContent = '▶️';
            }
        }
        
        function simulatePlayback() {
            if (!isPlaying) return;
            
            const currentTimeEl = document.getElementById('current-time');
            const progressFill = document.getElementById('progress-fill');
            let seconds = 0;
            const totalDuration = {total_duration};
            
            const interval = setInterval(() => {
                if (!isPlaying) {
                    clearInterval(interval);
                    return;
                }
                
                seconds++;
                const mins = Math.floor(seconds / 60);
                const secs = seconds % 60;
                currentTimeEl.textContent = mins + ':' + secs.toString().padStart(2, '0');
                
                const progress = (seconds / totalDuration) * 100;
                progressFill.style.width = progress + '%';
                
                if (seconds >= totalDuration) {
                    clearInterval(interval);
                    togglePlay();
                    currentTimeEl.textContent = '0:00';
                    progressFill.style.width = '0%';
                }
            }, 1000);
        }
        
        function seekTo(event) {
            const progressBar = event.currentTarget;
            const rect = progressBar.getBoundingClientRect();
            const clickX = event.clientX - rect.left;
            const width = rect.width;
            const percentage = clickX / width;
            
            const totalDuration = {total_duration};
            const targetTime = Math.floor(percentage * totalDuration);
            
            const mins = Math.floor(targetTime / 60);
            const secs = targetTime % 60;
            document.getElementById('current-time').textContent = mins + ':' + secs.toString().padStart(2, '0');
            
            const progressFill = document.getElementById('progress-fill');
            progressFill.style.width = (percentage * 100) + '%';
            
            if (isPlaying) {
                isPlaying = false;
                togglePlay();
                setTimeout(() => togglePlay(), 100);
            }
        }
        
        function copyLocalPath() {
            const localPath = document.getElementById('localPath').textContent;
            navigator.clipboard.writeText(localPath).then(() => {
                const statusEl = document.getElementById('downloadStatus');
                statusEl.textContent = '✅ 本地路径已复制到剪贴板';
                setTimeout(() => {
                    statusEl.textContent = '准备就绪';
                }, 3000);
            }).catch(() => {
                alert('复制失败，请手动复制：' + localPath);
            });
        }
        
        // 下载相关函数
        function updateLocalPath() {
            const osSelect = document.getElementById('osSelect');
            const baseInput = document.getElementById('baseInput');
            const localPathEl = document.getElementById('localPath');
            
            const draftId = '{draft_id}';
            const clientOs = osSelect.value;
            const customBase = baseInput.value;
            
            let localPath = '';
            if (clientOs === 'windows') {
                const base = customBase || 'F:\\\\jianyin\\\\cgwz\\\\JianyingPro Drafts';
                localPath = base + '\\\\' + draftId;
            } else if (clientOs === 'macos') {
                const base = customBase || '/Users/username/Documents/JianyingPro Drafts';
                localPath = base + '/' + draftId;
            } else {
                const base = customBase || '/data/drafts';
                localPath = base + '/' + draftId;
            }
            
            localPathEl.textContent = localPath;
        }
        
        async function postJSON(url, body) {
            const res = await fetch(url, { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify(body) 
            });
            return await res.json();
        }
        
        async function pollDownloadStatus(taskId) {
            const statusEl = document.getElementById('downloadStatus');
            while (true) {
                const status = await postJSON('/query_draft_status', { task_id: taskId });
                if (status && status.status) {
                    statusEl.textContent = `⏳ 任务状态: ${status.status}，进度: ${status.progress||0}%`;
                    
                    if (status.status === 'completed') break;
                    if (status.status === 'failed') {
                        throw new Error(status.message || '任务失败');
                    }
                }
                await new Promise(r => setTimeout(r, 2000));
            }
        }
        
        async function finalizeDownloadRedirect() {
            const osSelect = document.getElementById('osSelect');
            const baseInput = document.getElementById('baseInput');
            const draftId = '{draft_id}';
            
            const result = await postJSON('/generate_draft_url', { 
                draft_id: draftId, 
                client_os: osSelect.value, 
                draft_folder: baseInput.value || undefined 
            });
            
            if (result && result.success && result.output && result.output.draft_url) {
                document.getElementById('downloadStatus').textContent = '🎉 下载链接获取成功！';
                window.open(result.output.draft_url, '_blank');
            } else {
                throw new Error('未获取到下载链接');
            }
        }
        
        // 页面加载完成后的初始化
        document.addEventListener('DOMContentLoaded', function() {
            console.log('草稿预览页面已加载');
            
            const osSelect = document.getElementById('osSelect');
            const baseInput = document.getElementById('baseInput');
            const saveUploadBtn = document.getElementById('saveUploadBtn');
            
            updateLocalPath();
            
            osSelect.addEventListener('change', updateLocalPath);
            baseInput.addEventListener('input', updateLocalPath);
            
            // 保存上传按钮事件
            saveUploadBtn.addEventListener('click', async function() {
                const statusEl = document.getElementById('downloadStatus');
                const draftId = '{draft_id}';
                
                saveUploadBtn.disabled = true;
                statusEl.textContent = '🔍 正在检测云端文件...';
                
                try {
                    const checkResult = await postJSON('/generate_draft_url', { 
                        draft_id: draftId, 
                        client_os: osSelect.value, 
                        draft_folder: baseInput.value || undefined 
                    });
                    
                    if (checkResult && checkResult.success && checkResult.output) {
                        if (checkResult.output.storage === 'oss' && checkResult.output.draft_url) {
                            statusEl.textContent = '✅ 发现云端文件！即将跳转...';
                            setTimeout(() => {
                                window.open(checkResult.output.draft_url, '_blank');
                            }, 1000);
                            return;
                        }
                    }
                    
                    statusEl.textContent = '📤 正在提交保存任务...';
                    
                    const saveResult = await postJSON('/generate_draft_url?force_save=true', { 
                        draft_id: draftId, 
                        client_os: osSelect.value, 
                        draft_folder: baseInput.value || undefined 
                    });
                    
                    if (saveResult && saveResult.success && saveResult.output) {
                        if (saveResult.output.storage === 'oss' && saveResult.output.draft_url) {
                            statusEl.textContent = '🎉 保存完成！即将跳转...';
                            setTimeout(() => {
                                window.open(saveResult.output.draft_url, '_blank');
                            }, 1000);
                            return;
                        }
                        
                        if (saveResult.output.status === 'processing' && saveResult.output.task_id) {
                            await pollDownloadStatus(saveResult.output.task_id);
                            await finalizeDownloadRedirect();
                            return;
                        }
                    }
                    
                    throw new Error('保存上传流程异常');
                    
                } catch (error) {
                    statusEl.textContent = '❌ 操作失败: ' + error.message;
                } finally {
                    saveUploadBtn.disabled = false;
                }
            });
        });
    </script>
</body>
</html>
"""
        # 直接替换占位符，避免格式化问题
        result = html_content.format(
            draft_id=draft_id,
            materials_json=materials_json,
            draft_status=draft_status,
            storage_type=storage_type,
            file_size=file_size,
            video_count=video_count,
            audio_count=audio_count,
            text_count=text_count,
            image_count=image_count,
            total_duration=total_duration
        )
        return result
        
    except Exception as e:
        return f"预览页面生成失败: {str(e)}", 500

@app.route('/debug/cache/<draft_id>', methods=['GET'])
def debug_cache(draft_id: str):
    """调试：查看草稿缓存内容"""
    materials = get_draft_materials(draft_id)
    return jsonify({
        "draft_id": draft_id,
        "materials": materials,
        "cache_keys": list(draft_materials_cache.keys())
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
PORT = 9001

