
import os
import re
import pyJianYingDraft as draft
import shutil
from util import zip_draft, is_windows_path
from oss import upload_to_oss
from typing import Dict, Literal
from draft_cache import DRAFT_CACHE, get_draft
from downloader import download_file
from concurrent.futures import ThreadPoolExecutor, as_completed
import imageio.v2 as imageio
import subprocess
import json
from get_duration_impl import get_video_duration
import uuid
import threading
import logging
import time
import sqlite3

from database import update_draft_status
from settings import IS_CAPCUT_ENV, IS_UPLOAD_DRAFT
from os_path_config import get_os_path_config, get_default_draft_path

logger = logging.getLogger('flask_video_generator')

TaskStatus = Literal["initialized", "processing", "completed", "failed", "not_found"]
# 使用新的操作系统路径配置
DEFAULT_WINDOWS_DRAFT_FOLDER = "F:\\jianyin\\cgwz\\JianyingPro Drafts"

def build_asset_path(draft_folder: str, draft_id: str, asset_type: str, material_name: str) -> str:
    if is_windows_path(draft_folder):
        if os.name == 'nt':
            draft_real_path = os.path.join(draft_folder, draft_id, "assets", asset_type, material_name)
        else:
            windows_drive, windows_path = re.match(r'([a-zA-Z]:)(.*)', draft_folder).groups()
            parts = [p for p in windows_path.split('\\') if p]
            draft_real_path = os.path.join(windows_drive, *parts, draft_id, "assets", asset_type, material_name)
            draft_real_path = draft_real_path.replace('/', '\\')
    else:
        draft_real_path = os.path.join(draft_folder, draft_id, "assets", asset_type, material_name)
    return draft_real_path

def save_draft_background(draft_id: str, draft_folder: str, task_id: str):
    try:
        update_draft_status(draft_id, 'processing', 0, '开始保存草稿')
        
        script = get_draft(draft_id)
        if script is None:
            raise Exception(f"Draft {draft_id} does not exist in cache or database")
        logger.info(f"Task {task_id}: Successfully retrieved draft {draft_id} from cache.")
        update_draft_status(draft_id, 'processing', 5, '正在更新媒体元数据')
        update_media_metadata(script, draft_id)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        draft_path = os.path.join(current_dir, draft_id)
        if os.path.exists(draft_path):
            shutil.rmtree(draft_path)

        template_dir = "template" if IS_CAPCUT_ENV else "template_jianying"
        draft_folder_for_duplicate = draft.Draft_folder(current_dir)
        draft_folder_for_duplicate.duplicate_as_template(template_dir, draft_id)

        # 使用操作系统路径配置获取默认路径
        if not draft_folder:
            os_config = get_os_path_config()
            draft_folder = os_config.get_current_os_draft_path()
            logger.info(f"使用默认草稿路径: {draft_folder} (操作系统: {os_config.os_type})")
        else:
            logger.info(f"使用自定义草稿路径: {draft_folder}")
        
        download_tasks = []
        materials_to_download = []
        if script.materials.audios:
            materials_to_download.extend(script.materials.audios)
        if script.materials.videos:
            materials_to_download.extend(script.materials.videos)

        update_draft_status(draft_id, 'processing', 10, f"收集到 {len(materials_to_download)} 个下载任务")

        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_material = {}
            for material in materials_to_download:
                remote_url = material.remote_url
                if not remote_url:
                    logger.warning(f"Material {material.material_name} has no remote_url, skipping.")
                    continue

                asset_type = 'audio'
                if isinstance(material, draft.Video_material):
                    asset_type = 'image' if material.material_type == 'photo' else 'video'
                
                material.replace_path = build_asset_path(draft_folder, draft_id, asset_type, material.material_name)
                local_path = os.path.join(draft_path, "assets", asset_type, material.material_name)
                
                future = executor.submit(download_file, remote_url, local_path)
                future_to_material[future] = material

            completed_count = 0
            total_count = len(future_to_material)
            for future in as_completed(future_to_material):
                completed_count += 1
                progress = 10 + int((completed_count / total_count) * 60)
                update_draft_status(draft_id, 'processing', progress, f"正在下载素材 ({completed_count}/{total_count})")
                try:
                    future.result()
                except Exception as e:
                    material = future_to_material[future]
                    logger.error(f"Task {task_id}: Failed to download {material.material_name}: {e}")

        update_draft_status(draft_id, 'processing', 70, '正在保存草稿信息')
        
        # Force local consumption
        for material in materials_to_download:
            material.remote_url = None

        script.dump(os.path.join(draft_path, "draft_info.json"))

        update_draft_status(draft_id, 'processing', 80, '正在压缩草稿文件')
        zip_filename = f"{draft_id}.zip"
        zip_file_path = os.path.join(current_dir, zip_filename)
        if not zip_draft(draft_path, zip_file_path):
            raise Exception("Failed to compress draft folder")

        draft_url = zip_file_path
        
        # 检查是否是自定义下载路径（任何临时目录或自定义路径）
        is_custom_download = draft_folder and (draft_folder.startswith('/tmp/') or 'custom' in draft_folder.lower())
        
        if IS_UPLOAD_DRAFT and not is_custom_download:
            # 正常OSS上传模式
            update_draft_status(draft_id, 'processing', 90, '正在上传至云存储')
            draft_url = upload_to_oss(zip_file_path)
            # 删除本地文件
            if os.path.exists(draft_path):
                shutil.rmtree(draft_path)
        else:
            # 本地保存模式或自定义下载模式
            if is_custom_download:
                # 自定义下载：将文件复制到指定的临时目录
                update_draft_status(draft_id, 'processing', 90, '正在复制文件到临时目录')
                temp_target_path = os.path.join(draft_folder, draft_id)
                if os.path.exists(temp_target_path):
                    shutil.rmtree(temp_target_path)
                shutil.copytree(draft_path, temp_target_path)
                logger.info(f"Task {task_id}: 已将草稿文件复制到临时目录: {temp_target_path}")
                # 保留原始draft_path，不删除
            else:
                # 普通本地保存模式，保留文件
                logger.info(f"Task {task_id}: 本地保存模式，文件保存在: {draft_path}")
                logger.info(f"草稿文件已复制到临时目录: {temp_target_path}")
        
        update_draft_status(draft_id, 'completed', 100, draft_url)
        logger.info(f"Task {task_id} completed, draft URL: {draft_url}")

    except Exception as e:
        logger.error(f"Saving draft {draft_id} task {task_id} failed: {e}", exc_info=True)
        update_draft_status(draft_id, 'failed', message=str(e))

def save_draft_impl(draft_id: str, draft_folder: str = None) -> Dict[str, str]:
    logger.info(f"Received save draft request: draft_id={draft_id}, draft_folder={draft_folder}")
    try:
        task_id = draft_id # Use draft_id as task_id for simplicity
        update_draft_status(draft_id, 'initialized', 0, '任务已创建')
        
        thread = threading.Thread(target=save_draft_background, args=(draft_id, draft_folder, task_id))
        thread.start()
        
        return {"success": True, "task_id": task_id, "message": "Draft save task started successfully"}
    except Exception as e:
        logger.error(f"Failed to start save draft task {draft_id}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

def query_task_status(task_id: str):
    # This function can be simplified or removed if long polling is directly on drafts table
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("SELECT status, progress, message FROM drafts WHERE id = ?", (task_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {"status": result[0], "progress": result[1], "message": result[2]}
    return {"status": "not_found"}

def query_script_impl(draft_id: str, force_update: bool = True):
    if draft_id not in DRAFT_CACHE:
        logger.warning(f"Draft {draft_id} does not exist in cache.")
        return None
    script = DRAFT_CACHE[draft_id]
    if force_update:
        update_media_metadata(script, draft_id)
    return script

def update_media_metadata(script, draft_id=None):
    # This function remains largely the same, but we can pass draft_id to update status
    audios = script.materials.audios or []
    videos = script.materials.videos or []

    for audio in audios:
        if not audio.remote_url: continue
        try:
            # Simplified metadata update logic
            duration_result = get_video_duration(audio.remote_url)
            if duration_result["success"]:
                audio.duration = int(duration_result["output"] * 1000000)
        except Exception as e:
            logger.error(f"Error getting audio duration for {audio.material_name}: {e}")

    for video in videos:
        if not video.remote_url: continue
        try:
            if video.material_type == 'photo':
                img = imageio.imread(video.remote_url)
                video.height, video.width = img.shape[:2]
            elif video.material_type == 'video':
                # Simplified ffprobe logic
                command = ['/usr/bin/ffprobe', '-v', 'error', '-show_entries', 'stream=width,height,duration', '-of', 'json', video.remote_url]
                result = subprocess.check_output(command, stderr=subprocess.STDOUT)
                info = json.loads(result.decode('utf-8'))
                if 'streams' in info and info['streams']:
                    stream = info['streams'][0]
                    video.width = int(stream.get('width', 0))
                    video.height = int(stream.get('height', 0))
                    video.duration = int(float(stream.get('duration', '0')) * 1000000)
        except Exception as e:
            logger.error(f"Error updating metadata for {video.material_name}: {e}")

    # Simplified conflict resolution and duration update
    for track in script.tracks.values():
        track.segments.sort(key=lambda s: s.start)
        valid_segments = []
        last_end = -1
        for seg in track.segments:
            if seg.start >= last_end:
                valid_segments.append(seg)
                last_end = seg.end
        track.segments = valid_segments
    
    # script.recalculate_duration()  # 该方法在pyJianYingDraft库中不存在，已注释

if __name__ == "__main__":
    # Example usage for testing
    pass
