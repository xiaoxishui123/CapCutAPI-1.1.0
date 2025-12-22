#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云渲染（最小可用版）：把草稿主视频轨道合成为 MP4

设计目标：
- 低风险：不改动现有草稿/下载/预览/保存逻辑，只新增独立渲染链路
- 可追踪：submit_render 返回 task_id；get_render_status 可查询进度
- 可交付：最终产出 mp4，上传到 MP4 OSS（使用现有 upload_mp4_to_oss）

当前版本能力（MVP）：
- 仅渲染“视频轨道”的片段，按 target_timerange.start 排序拼接
- 忽略转场/特效/文本/贴纸（后续可迭代）
- 每个片段会被转码为统一分辨率与编码（H.264 + AAC），再 concat
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pyJianYingDraft as draft

from draft_cache import get_draft
from downloader import download_video, download_image, download_audio
from oss import upload_mp4_to_oss
from settings.local import MP4_OSS_CONFIG
from sticker_assets import get_sticker_image_url


logger = logging.getLogger("flask_video_generator")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capcut.db")


def _ensure_render_table() -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS render_tasks (
            task_id TEXT PRIMARY KEY,
            draft_id TEXT,
            status TEXT,
            progress INTEGER,
            message TEXT,
            video_url TEXT,
            file_path TEXT,
            file_size INTEGER,
            duration_seconds REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_render_tasks_draft_id ON render_tasks(draft_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_render_tasks_updated_at ON render_tasks(updated_at DESC)")
    conn.commit()
    conn.close()


def _update_task(task_id: str, **fields: Any) -> None:
    _ensure_render_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 先确保任务存在
    c.execute(
        "INSERT OR IGNORE INTO render_tasks(task_id, draft_id, status, progress, message) VALUES(?, ?, ?, ?, ?)",
        (task_id, fields.get("draft_id"), fields.get("status", "queued"), fields.get("progress", 0), fields.get("message", "")),
    )

    sets = []
    vals = []
    for k, v in fields.items():
        if k in {
            "draft_id",
            "status",
            "progress",
            "message",
            "video_url",
            "file_path",
            "file_size",
            "duration_seconds",
        }:
            sets.append(f"{k} = ?")
            vals.append(v)
    sets.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE render_tasks SET {', '.join(sets)} WHERE task_id = ?"
    vals.append(task_id)
    c.execute(sql, tuple(vals))
    conn.commit()
    conn.close()


def get_render_status(task_id: str) -> Dict[str, Any]:
    _ensure_render_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT task_id, draft_id, status, progress, message, video_url, file_path, file_size, duration_seconds, updated_at
        FROM render_tasks
        WHERE task_id = ?
        """,
        (task_id,),
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return {"success": False, "status": "not_found", "error": "task not found", "task_id": task_id}
    return {
        "success": True,
        "task_id": row[0],
        "draft_id": row[1],
        "status": row[2],
        "progress": row[3] or 0,
        "message": row[4] or "",
        "video_url": row[5] or "",
        "file_path": row[6] or "",
        "file_size": row[7] or 0,
        "duration": row[8] or 0,
        "updated_at": row[9],
    }


@dataclass
class RenderOptions:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    preset: str = "veryfast"
    crf: int = 23
    # 是否上传到 MP4 OSS；为 False 时，将保留本地文件并通过 /render/download 提供下载
    upload_to_oss: bool = True
    # 是否强制使用草稿分辨率（True 时会用 script.width/script.height 覆盖 width/height）
    use_draft_resolution: bool = False


def submit_render(draft_id: str, options: Optional[RenderOptions] = None) -> Dict[str, Any]:
    """提交渲染任务（后台线程执行）"""
    options = options or RenderOptions()
    task_id = f"rnd_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    _update_task(task_id, draft_id=draft_id, status="queued", progress=0, message="任务已创建")

    t = threading.Thread(target=_render_background, args=(task_id, draft_id, options), daemon=True)
    t.start()

    return {
        "success": True,
        "task_id": task_id,
        "estimated_time": 120,
        "method": "submit_render",
        "message": "render task submitted",
    }


def _collect_video_segments(script: "draft.Script_file") -> List[Tuple[int, "draft.Video_segment"]]:
    """从草稿中提取所有 video 轨道片段，按开始时间排序"""
    segments: List[Tuple[int, "draft.Video_segment"]] = []
    for track in script.tracks.values():
        if getattr(track, "track_type", None) and track.track_type.name != "video":
            continue
        for seg in getattr(track, "segments", []) or []:
            if isinstance(seg, draft.Video_segment):
                segments.append((seg.start, seg))
    segments.sort(key=lambda x: x[0])
    return segments


def _video_material_by_id(script: "draft.Script_file") -> Dict[str, "draft.Video_material"]:
    m: Dict[str, "draft.Video_material"] = {}
    for v in script.materials.videos or []:
        m[v.material_id] = v
    return m


def _collect_audio_segments(script: "draft.Script_file") -> List[Tuple[int, "draft.Audio_segment"]]:
    """从草稿中提取所有 audio 轨道片段，按开始时间排序"""
    segments: List[Tuple[int, "draft.Audio_segment"]] = []
    for track in script.tracks.values():
        if getattr(track, "track_type", None) and track.track_type.name != "audio":
            continue
        for seg in getattr(track, "segments", []) or []:
            if isinstance(seg, draft.Audio_segment):
                segments.append((seg.start, seg))
    segments.sort(key=lambda x: x[0])
    return segments


def _audio_material_by_id(script: "draft.Script_file") -> Dict[str, "draft.Audio_material"]:
    m: Dict[str, "draft.Audio_material"] = {}
    for a in script.materials.audios or []:
        m[a.material_id] = a
    return m


def _collect_text_segments(script: "draft.Script_file") -> List[Tuple[int, "draft.Text_segment"]]:
    """从草稿中提取所有 text 轨道片段，按开始时间排序"""
    segments: List[Tuple[int, "draft.Text_segment"]] = []
    for track in script.tracks.values():
        if getattr(track, "track_type", None) and track.track_type.name != "text":
            continue
        for seg in getattr(track, "segments", []) or []:
            if isinstance(seg, draft.Text_segment):
                segments.append((seg.start, seg))
    segments.sort(key=lambda x: x[0])
    return segments


def _collect_sticker_segments(script: "draft.Script_file") -> List[Tuple[int, "draft.Sticker_segment"]]:
    """从草稿中提取所有 sticker 轨道片段，按开始时间排序"""
    segments: List[Tuple[int, "draft.Sticker_segment"]] = []
    for track in script.tracks.values():
        if getattr(track, "track_type", None) and track.track_type.name != "sticker":
            continue
        for seg in getattr(track, "segments", []) or []:
            if isinstance(seg, draft.Sticker_segment):
                segments.append((seg.start, seg))
    segments.sort(key=lambda x: x[0])
    return segments


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def _ffmpeg_exists() -> bool:
    return os.path.exists("/usr/bin/ffmpeg")


def _mp4_oss_ready() -> bool:
    """检查 MP4 OSS 配置是否完整。"""
    required = ["bucket_name", "access_key_id", "access_key_secret", "endpoint", "region"]
    try:
        return all((MP4_OSS_CONFIG or {}).get(k) for k in required)
    except Exception:
        return False


def _find_font_file() -> Optional[str]:
    """尽量找到一个支持中文的字体文件，用于 ffmpeg drawtext。

    优先级：
    1) 环境变量 RENDER_FONT_FILE
    2) 常见系统路径候选
    """
    env_font = (os.getenv("RENDER_FONT_FILE") or "").strip()
    if env_font and os.path.exists(env_font):
        return env_font

    candidates = [
        # Noto CJK (常见)
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/google-noto-cjk/NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        # DejaVu (基本拉丁)
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
        "/usr/share/fonts/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _rgb01_to_hex(rgb: Tuple[float, float, float]) -> str:
    r = max(0, min(255, int(round(rgb[0] * 255))))
    g = max(0, min(255, int(round(rgb[1] * 255))))
    b = max(0, min(255, int(round(rgb[2] * 255))))
    return f"#{r:02X}{g:02X}{b:02X}"


def _build_drawtext_filter(base_dir: str, text_segs: List[Tuple[int, "draft.Text_segment"]], options: RenderOptions) -> Optional[str]:
    """把多个 Text_segment 转成一个 drawtext 链式滤镜字符串。

    约束（MVP）：
    - 只渲染基础文本：内容 + 颜色 + 透明度 + 简单位置
    - 不支持：气泡/花字/描边/背景/动画/多样式范围（后续可迭代）
    """
    if not text_segs:
        return None

    font_file = _find_font_file()
    size_scale = float(os.getenv("RENDER_TEXT_SIZE_SCALE", "6"))
    size_scale = max(0.1, min(50.0, size_scale))

    parts: List[str] = []
    for idx, (_s, seg) in enumerate(text_segs):
        # 1) 文本内容写入文件，避免 ffmpeg drawtext 的复杂转义问题
        textfile = os.path.join(base_dir, f"text_{idx:04d}.txt")
        try:
            with open(textfile, "w", encoding="utf-8") as f:
                f.write(seg.text or "")
        except Exception:
            # 如果写失败，跳过该段
            continue

        start_s = seg.target_timerange.start / 1_000_000.0
        end_s = seg.target_timerange.end / 1_000_000.0

        # 2) 位置：Clip_settings 的 transform_x/y 单位为“半画布宽/高”
        tx = float(getattr(seg.clip_settings, "transform_x", 0.0) or 0.0)
        ty = float(getattr(seg.clip_settings, "transform_y", 0.0) or 0.0)
        base_x = f"(W/2)+({tx})*W/2"
        base_y = f"(H/2)+({ty})*H/2"

        align = int(getattr(seg.style, "align", 1) or 1)
        if align == 2:
            x_expr = f"{base_x}-text_w"
        elif align == 0:
            x_expr = base_x
        else:
            x_expr = f"{base_x}-text_w/2"
        y_expr = f"{base_y}-text_h/2"

        # 3) 字号：草稿 size 不是像素，这里做一个保守映射
        raw_size = float(getattr(seg.style, "size", 8.0) or 8.0)
        fontsize = max(12, int(round(raw_size * size_scale * (options.height / 1920.0))))

        # 4) 颜色与透明度
        rgb = getattr(seg.style, "color", (1.0, 1.0, 1.0)) or (1.0, 1.0, 1.0)
        color_hex = _rgb01_to_hex(rgb)
        alpha = float(getattr(seg.style, "alpha", 1.0) or 1.0)
        alpha = max(0.0, min(1.0, alpha))
        fontcolor = f"{color_hex}@{alpha:.3f}"

        # 5) 组装 drawtext
        # 注意：textfile 路径要用单引号包裹；enable 也要用单引号包裹
        draw = (
            "drawtext="
            f"textfile='{textfile}':"
            f"x={x_expr}:y={y_expr}:"
            f"fontsize={fontsize}:"
            f"fontcolor={fontcolor}:"
            f"enable='between(t,{start_s:.3f},{end_s:.3f})'"
        )
        if font_file:
            draw = draw.replace("drawtext=", f"drawtext=fontfile='{font_file}':", 1)

        parts.append(draw)

    if not parts:
        return None
    return ",".join(parts)


def _apply_stickers_overlay(base_dir: str, input_video: str, sticker_segs: List[Tuple[int, "draft.Sticker_segment"]], options: RenderOptions) -> str:
    """把贴纸叠加到视频上（基础版：位置/缩放/透明度；不做旋转/翻转）"""
    # 先把能渲染的贴纸收集起来
    renderable: List[Dict[str, Any]] = []
    for idx, (_s, seg) in enumerate(sticker_segs):
        url = get_sticker_image_url(getattr(seg, "resource_id", ""))
        if not url:
            continue
        renderable.append({"idx": idx, "seg": seg, "url": url})

    if not renderable:
        return input_video

    # 需要多输入，用 filter_complex 做 overlay 链
    inputs: List[str] = ["-i", input_video]
    filter_parts: List[str] = []

    # 贴纸输入索引从 1 开始（0 是视频）
    for i, item in enumerate(renderable, start=1):
        seg = item["seg"]
        url = item["url"]
        # 下载贴纸图片到本地（统一用 png）
        local_img = download_image(url, base_dir, f"sticker_{i}.png")
        inputs.extend(["-i", local_img])

        start_s = seg.target_timerange.start / 1_000_000.0
        end_s = seg.target_timerange.end / 1_000_000.0

        tx = float(getattr(seg.clip_settings, "transform_x", 0.0) or 0.0)
        ty = float(getattr(seg.clip_settings, "transform_y", 0.0) or 0.0)
        sx = float(getattr(seg.clip_settings, "scale_x", 1.0) or 1.0)
        sy = float(getattr(seg.clip_settings, "scale_y", 1.0) or 1.0)
        alpha = float(getattr(seg.clip_settings, "alpha", 1.0) or 1.0)
        alpha = max(0.0, min(1.0, alpha))

        flip_h = bool(getattr(seg.clip_settings, "flip_horizontal", False))
        flip_v = bool(getattr(seg.clip_settings, "flip_vertical", False))
        rotation_deg = float(getattr(seg.clip_settings, "rotation", 0.0) or 0.0)

        # 将 transform_x/y（半画布单位）映射到像素坐标，并让贴纸以中心对齐
        base_x = f"(W/2)+({tx})*W/2"
        base_y = f"(H/2)+({ty})*H/2"
        x_expr = f"{base_x}-overlay_w/2"
        y_expr = f"{base_y}-overlay_h/2"

        # 处理贴纸输入：
        # format rgba -> (optional) flip -> (optional) rotate -> alpha -> scale
        chain = f"[{i}:v]format=rgba"
        if flip_h:
            chain += ",hflip"
        if flip_v:
            chain += ",vflip"
        if abs(rotation_deg) > 1e-6:
            # rotate 需要弧度；c=none 保持透明背景；rotw/roth 让画布自适应旋转后尺寸
            theta = rotation_deg * 3.141592653589793 / 180.0
            chain += f",rotate={theta}:ow=rotw(iw):oh=roth(ih):c=none"
        chain += f",colorchannelmixer=aa={alpha:.3f}"
        chain += f",scale=iw*{sx}:ih*{sy}[stk{i}]"
        filter_parts.append(chain)

    # overlay 链
    current = "[0:v]"
    for i, item in enumerate(renderable, start=1):
        seg = item["seg"]
        start_s = seg.target_timerange.start / 1_000_000.0
        end_s = seg.target_timerange.end / 1_000_000.0

        tx = float(getattr(seg.clip_settings, "transform_x", 0.0) or 0.0)
        ty = float(getattr(seg.clip_settings, "transform_y", 0.0) or 0.0)
        base_x = f"(W/2)+({tx})*W/2"
        base_y = f"(H/2)+({ty})*H/2"
        x_expr = f"{base_x}-overlay_w/2"
        y_expr = f"{base_y}-overlay_h/2"

        out_label = f"[v{i}]"
        filter_parts.append(
            f"{current}[stk{i}]overlay=x={x_expr}:y={y_expr}:enable='between(t,{start_s:.3f},{end_s:.3f})'{out_label}"
        )
        current = out_label

    filter_complex = ";".join(filter_parts)
    out_path = os.path.join(base_dir, "video_with_stickers.mp4")
    cmd = [
        "/usr/bin/ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        current,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        options.preset,
        "-crf",
        str(options.crf),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        out_path,
    ]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out_path


def _make_black_gap_clip(base_dir: str, idx: int, duration: float, options: RenderOptions) -> str:
    """生成黑色视频占位片段（用于补齐时间轴空隙）"""
    out_clip = os.path.join(base_dir, f"gap_{idx:04d}.mp4")
    cmd = [
        "/usr/bin/ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-t",
        str(duration),
        "-i",
        f"color=c=black:s={options.width}x{options.height}:r={options.fps}",
        "-f",
        "lavfi",
        "-t",
        str(duration),
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-shortest",
        "-c:v",
        "libx264",
        "-preset",
        options.preset,
        "-crf",
        str(options.crf),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        out_clip,
    ]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out_clip


def _make_image_clip(base_dir: str, idx: int, image_url: str, duration: float, options: RenderOptions) -> str:
    """把图片转成固定时长的视频片段"""
    local_img = download_image(image_url, base_dir, f"img_{idx}.png")
    out_clip = os.path.join(base_dir, f"clip_{idx:04d}.mp4")
    vf = (
        f"scale={options.width}:{options.height}:force_original_aspect_ratio=decrease,"
        f"pad={options.width}:{options.height}:(ow-iw)/2:(oh-ih)/2,"
        f"fps={options.fps}"
    )
    cmd = [
        "/usr/bin/ffmpeg",
        "-y",
        "-loop",
        "1",
        "-t",
        str(duration),
        "-i",
        local_img,
        "-f",
        "lavfi",
        "-t",
        str(duration),
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf",
        vf,
        "-shortest",
        "-c:v",
        "libx264",
        "-preset",
        options.preset,
        "-crf",
        str(options.crf),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        out_clip,
    ]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out_clip


def _build_audio_mix(base_dir: str, audio_segs: List[Tuple[int, "draft.Audio_segment"]], script: "draft.Script_file", total_duration: float) -> Optional[str]:
    """按时间轴混音生成 aac（m4a）。没有音频则返回 None。"""
    if not audio_segs:
        return None

    mat_map = _audio_material_by_id(script)

    inputs: List[str] = []
    filter_parts: List[str] = []
    labels: List[str] = []

    for idx, (_start, seg) in enumerate(audio_segs):
        mat = mat_map.get(seg.material_id)
        if not mat:
            raise RuntimeError(f"audio material not found for segment: {seg.material_id}")
        src_url = (getattr(mat, "remote_url", None) or "").strip()
        if not src_url:
            raise RuntimeError("audio material has no remote_url (cannot render)")

        # 下载音频
        local_audio = download_audio(src_url, base_dir, f"aud_{idx}.mp3")
        inputs.extend(["-i", local_audio])

        # 计算截取范围（秒）
        ss = 0.0
        dur = max(0.001, seg.target_timerange.duration / 1_000_000.0)
        if seg.source_timerange is not None:
            ss = max(0.0, seg.source_timerange.start / 1_000_000.0)
            dur = max(0.001, seg.source_timerange.duration / 1_000_000.0)

        delay_ms = max(0, int(seg.target_timerange.start / 1000))
        vol = float(getattr(seg, "volume", 1.0) or 1.0)

        # atrim + asetpts + volume + adelay
        label = f"a{idx}"
        labels.append(f"[{label}]")
        filter_parts.append(
            f"[{idx}:a]atrim=start={ss}:duration={dur},asetpts=PTS-STARTPTS,volume={vol},adelay={delay_ms}|{delay_ms}[{label}]"
        )

    if len(labels) == 1:
        # 单路：也做 apad + atrim 到视频时长
        filter_parts.append(f"{labels[0]}apad,atrim=0:{total_duration}[amix]")
    else:
        filter_parts.append(f"{''.join(labels)}amix=inputs={len(labels)}:dropout_transition=0,apad,atrim=0:{total_duration}[amix]")

    filter_complex = ";".join(filter_parts)
    out_audio = os.path.join(base_dir, "audio_mix.m4a")
    cmd = [
        "/usr/bin/ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[amix]",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        out_audio,
    ]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out_audio


def _render_background(task_id: str, draft_id: str, options: RenderOptions) -> None:
    try:
        if not _ffmpeg_exists():
            raise RuntimeError("ffmpeg not found at /usr/bin/ffmpeg")

        _update_task(task_id, status="processing", progress=1, message="正在读取草稿")

        script = get_draft(draft_id)
        if script is None:
            raise RuntimeError(f"draft not found in cache: {draft_id}")

        # 使用草稿原始分辨率（如果存在）
        try:
            if getattr(options, "use_draft_resolution", False):
                options.width = int(getattr(script, "width", options.width) or options.width)
                options.height = int(getattr(script, "height", options.height) or options.height)
            options.fps = int(getattr(script, "fps", options.fps) or options.fps)
        except Exception:
            pass

        segs = _collect_video_segments(script)
        audio_segs = _collect_audio_segments(script)
        text_segs = _collect_text_segments(script)
        sticker_segs = _collect_sticker_segments(script)
        if not segs:
            raise RuntimeError("no video segments found to render")

        material_map = _video_material_by_id(script)

        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "render_tmp", task_id)
        _ensure_dir(base_dir)

        # 计算“时间轴总时长”（尽量对齐剪辑时间轴，而不是简单求和）
        timeline_end_us = 0
        for _s, seg in segs:
            timeline_end_us = max(timeline_end_us, seg.end)
        for _s, seg in audio_segs:
            timeline_end_us = max(timeline_end_us, seg.end)
        total_duration = max(0.001, timeline_end_us / 1_000_000.0)

        _update_task(task_id, progress=5, message=f"发现 {len(segs)} 个视频/图片片段，{len(audio_segs)} 个音频片段，{len(text_segs)} 个文本/字幕片段，{len(sticker_segs)} 个贴纸片段，准备渲染")

        # 1) 按时间轴生成“片段列表”（包含补黑）
        clip_paths: List[str] = []
        cursor_us = 0
        clip_index = 0
        for idx, (_start, seg) in enumerate(segs):
            progress = 5 + int((idx / max(1, len(segs))) * 55)
            _update_task(task_id, progress=progress, message=f"处理视觉片段 {idx+1}/{len(segs)}")

            mat = material_map.get(seg.material_id)
            if not mat:
                raise RuntimeError(f"material not found for segment: {seg.material_id}")

            src_url = (getattr(mat, "remote_url", None) or "").strip()
            if not src_url:
                raise RuntimeError("video material has no remote_url (cannot render)")

            # 先补齐空白（黑场），让时间轴对齐
            if seg.target_timerange.start > cursor_us:
                gap_dur = (seg.target_timerange.start - cursor_us) / 1_000_000.0
                gap_clip = _make_black_gap_clip(base_dir, clip_index, gap_dur, options)
                clip_paths.append(gap_clip)
                clip_index += 1
                cursor_us = seg.target_timerange.start
            elif seg.target_timerange.start < cursor_us:
                # 重叠：MVP 先不做叠加，直接顺序拼接（记录警告）
                logger.warning(f"[render] overlap detected, will serialize: seg_start={seg.target_timerange.start} cursor={cursor_us}")

            # 当前片段时长（秒）
            dur = max(0.001, seg.target_timerange.duration / 1_000_000.0)

            # 图片片段
            if getattr(mat, "material_type", "").lower() == "photo":
                out_clip = _make_image_clip(base_dir, clip_index, src_url, dur, options)
                clip_paths.append(out_clip)
                clip_index += 1
                cursor_us = max(cursor_us, seg.target_timerange.end)
                continue

            # 视频片段：下载到 base_dir/assets/video/...
            local_src = download_video(src_url, base_dir, f"seg_{idx}.mp4")

            # 计算截取范围（秒）
            ss = 0.0
            if seg.source_timerange is not None:
                ss = max(0.0, seg.source_timerange.start / 1_000_000.0)
                dur = max(0.001, seg.source_timerange.duration / 1_000_000.0)

            out_clip = os.path.join(base_dir, f"clip_{clip_index:04d}.mp4")
            clip_index += 1

            # 为确保 concat 稳定：统一分辨率+fps+编码，并补静音音轨
            vf = (
                f"scale={options.width}:{options.height}:force_original_aspect_ratio=decrease,"
                f"pad={options.width}:{options.height}:(ow-iw)/2:(oh-ih)/2,"
                f"fps={options.fps}"
            )
            cmd = [
                "/usr/bin/ffmpeg",
                "-y",
                "-ss",
                str(ss),
                "-t",
                str(dur),
                "-i",
                local_src,
                "-f",
                "lavfi",
                "-t",
                str(dur),
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-vf",
                vf,
                "-shortest",
                "-c:v",
                "libx264",
                "-preset",
                options.preset,
                "-crf",
                str(options.crf),
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                out_clip,
            ]
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            clip_paths.append(out_clip)
            cursor_us = max(cursor_us, seg.target_timerange.end)

        # 如果时间轴末尾还有空白，补到总时长
        if timeline_end_us > cursor_us:
            gap_dur = (timeline_end_us - cursor_us) / 1_000_000.0
            gap_clip = _make_black_gap_clip(base_dir, clip_index, gap_dur, options)
            clip_paths.append(gap_clip)

        _update_task(task_id, progress=60, message="正在拼接视频/图片片段")

        # 2) concat demuxer 拼接
        list_path = os.path.join(base_dir, "concat_list.txt")
        with open(list_path, "w", encoding="utf-8") as f:
            for p in clip_paths:
                f.write(f"file '{p}'\n")

        final_video_path = os.path.join(base_dir, f"{draft_id}_video.mp4")
        cmd_concat = [
            "/usr/bin/ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_path,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            final_video_path,
        ]
        subprocess.check_output(cmd_concat, stderr=subprocess.STDOUT)

        # 3) 文本/字幕叠加（如果存在）
        if text_segs:
            _update_task(task_id, progress=72, message="正在渲染文本/字幕（叠加到视频）")
            draw_filter = _build_drawtext_filter(base_dir, text_segs, options)
            if draw_filter:
                video_text_path = os.path.join(base_dir, f"{draft_id}_video_text.mp4")
                cmd_text = [
                    "/usr/bin/ffmpeg",
                    "-y",
                    "-i",
                    final_video_path,
                    "-vf",
                    draw_filter,
                    "-an",
                    "-c:v",
                    "libx264",
                    "-preset",
                    options.preset,
                    "-crf",
                    str(options.crf),
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    video_text_path,
                ]
                subprocess.check_output(cmd_text, stderr=subprocess.STDOUT)
                final_video_path = video_text_path

        # 4) 贴纸叠加（如果存在且能解析到图片URL）
        if sticker_segs:
            _update_task(task_id, progress=74, message="正在渲染贴纸（叠加到视频）")
            final_video_path = _apply_stickers_overlay(base_dir, final_video_path, sticker_segs, options)

        _update_task(task_id, progress=75, message="正在混音音频")

        audio_mix_path = _build_audio_mix(base_dir, audio_segs, script, total_duration)

        _update_task(task_id, progress=80, message="正在封装最终 MP4")

        final_path = os.path.join(base_dir, f"{draft_id}_final.mp4")
        if audio_mix_path:
            # 用混音结果替换视频中的静音
            cmd_mux = [
                "/usr/bin/ffmpeg",
                "-y",
                "-i",
                final_video_path,
                "-i",
                audio_mix_path,
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-movflags",
                "+faststart",
                final_path,
            ]
            subprocess.check_output(cmd_mux, stderr=subprocess.STDOUT)
        else:
            # 没有音频：直接用视频文件
            shutil.copy2(final_video_path, final_path)

        file_size = os.path.getsize(final_path) if os.path.exists(final_path) else 0

        # 5) 上传（如果 MP4 OSS 未配置，则提供本地下载）
        if options.upload_to_oss and _mp4_oss_ready():
            _update_task(task_id, progress=85, message="正在上传 mp4 到 OSS")
            video_url = upload_mp4_to_oss(final_path)
            # 上传成功后可以清理临时目录
            try:
                shutil.rmtree(base_dir, ignore_errors=True)
            except Exception:
                pass
            file_path_for_query = ""
        else:
            # 没有配置 MP4 OSS：不失败，直接提供本地下载接口
            if options.upload_to_oss and (not _mp4_oss_ready()):
                tip = "未配置MP4_OSS，已生成本地mp4，可通过 /render/download 下载"
            else:
                tip = "已按请求生成本地mp4（未上传OSS），可通过 /render/download 下载"
            _update_task(task_id, progress=85, message=tip)
            video_url = f"/render/download?task_id={task_id}"
            file_path_for_query = final_path

        _update_task(
            task_id,
            status="completed",
            progress=100,
            message="渲染完成",
            video_url=video_url,
            file_path=file_path_for_query,
            file_size=file_size,
            duration_seconds=total_duration,
        )
    except Exception as e:
        logger.error(f"[render] task {task_id} failed: {e}", exc_info=True)
        _update_task(task_id, status="failed", progress=0, message=str(e))


