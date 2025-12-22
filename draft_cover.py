#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
草稿封面（Draft Cover）支持

目标（最小风险实现）：
1) 提供一个 API 让用户“声明”想用哪张图片/哪段视频的哪一帧作为封面
2) 在 `save_draft` 导出时，把封面写入草稿根目录的 `draft_cover.jpg`
3) 更新 `draft_meta_info.json` / `draft_info.json` 的封面相关字段

说明：
- 剪映/CapCut 草稿结构里已有 `draft_cover` / `static_cover_image_path` 等字段，但本项目此前未实现“写封面文件”。
- 为避免影响已有流程，我们不修改 pyJianYingDraft 的内部结构，只在导出阶段做文件级补丁。
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests


logger = logging.getLogger("flask_video_generator")

_STORE_LOCK = threading.Lock()


@dataclass
class DraftCoverConfig:
    """封面配置（会暂存到本地 JSON 文件，等待 save_draft 时应用）"""

    draft_id: str
    cover_image_url: Optional[str] = None
    video_url: Optional[str] = None
    time_point: float = 0.0
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # 保持字段最小化
        return {k: v for k, v in d.items() if v is not None}


def _store_path() -> str:
    # 放在项目根目录（与 capcut_server.py 同级）
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "draft_cover_store.json")


def _load_store() -> Dict[str, Any]:
    path = _store_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception as e:
        logger.warning(f"读取 draft_cover_store.json 失败，将视为无配置: {e}")
        return {}


def _save_store(store: Dict[str, Any]) -> None:
    path = _store_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def set_draft_cover_config(draft_id: str, cover_image_url: Optional[str], video_url: Optional[str], time_point: float) -> Dict[str, Any]:
    """保存封面配置（不会立即生成封面文件，生成发生在 save_draft 导出阶段）"""
    cfg = DraftCoverConfig(
        draft_id=draft_id,
        cover_image_url=cover_image_url,
        video_url=video_url,
        time_point=float(time_point or 0.0),
        updated_at=datetime.now().isoformat(),
    )
    with _STORE_LOCK:
        store = _load_store()
        store[draft_id] = cfg.to_dict()
        _save_store(store)
    return cfg.to_dict()


def pop_draft_cover_config(draft_id: str) -> Optional[Dict[str, Any]]:
    """取出并删除封面配置（用于 save_draft 导出时一次性应用）"""
    with _STORE_LOCK:
        store = _load_store()
        cfg = store.pop(draft_id, None)
        _save_store(store)
        return cfg


def _run_ffmpeg_extract_frame(input_url: str, output_jpg: str, time_point: float = 0.0) -> Tuple[bool, str]:
    """用 ffmpeg 抽帧/转码到 jpg。成功返回 (True, '')，失败返回 (False, 错误信息)。"""
    ffmpeg_bin = "/usr/bin/ffmpeg"
    if not os.path.exists(ffmpeg_bin):
        return False, "ffmpeg not found at /usr/bin/ffmpeg"

    # -ss 放在 -i 前面更快；对图片也兼容（忽略 -ss）
    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss",
        str(max(0.0, float(time_point or 0.0))),
        "-i",
        input_url,
        "-frames:v",
        "1",
        "-q:v",
        "2",
        output_jpg,
    ]
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return True, ""
    except subprocess.CalledProcessError as e:
        out = (e.output or b"").decode("utf-8", errors="ignore")
        return False, out[-1200:]  # 截断日志，避免太长
    except Exception as e:
        return False, str(e)


def _download_bytes(url: str, timeout: int = 60) -> bytes:
    r = requests.get(url, timeout=timeout, stream=True)
    r.raise_for_status()
    return r.content


def update_draft_cover_metadata(draft_path: str, cover_filename: str = "draft_cover.jpg") -> None:
    """只更新 JSON 元数据（不负责生成封面文件）"""
    meta_path = os.path.join(draft_path, "draft_meta_info.json")
    info_path = os.path.join(draft_path, "draft_info.json")

    # 1) draft_meta_info.json：设置 draft_cover
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["draft_cover"] = cover_filename
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, separators=(",", ":"))
        except Exception as e:
            logger.warning(f"更新 draft_meta_info.json 封面字段失败: {e}")

    # 2) draft_info.json：设置 static_cover_image_path（如果字段存在）
    if os.path.exists(info_path):
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                info = json.load(f)
            if isinstance(info, dict):
                # 不强行构造复杂 cover 对象，保持最小改动
                if "static_cover_image_path" in info:
                    info["static_cover_image_path"] = cover_filename
                if "cover" in info and info.get("cover") is None:
                    # 保持 cover 为 null（兼容不同版本剪映/CapCut）
                    pass
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, separators=(",", ":"))
        except Exception as e:
            logger.warning(f"更新 draft_info.json 封面字段失败: {e}")


def apply_draft_cover_if_configured(draft_id: str, draft_path: str) -> None:
    """在导出阶段应用封面配置：生成 draft_cover.jpg + 更新 JSON 元数据"""
    cfg = pop_draft_cover_config(draft_id)
    if not cfg:
        return

    cover_image_url = (cfg.get("cover_image_url") or "").strip()
    video_url = (cfg.get("video_url") or "").strip()
    time_point = float(cfg.get("time_point") or 0.0)

    cover_path = os.path.join(draft_path, "draft_cover.jpg")

    # 1) 优先使用 ffmpeg：不管输入是图片还是视频，都输出 jpg
    if cover_image_url:
        ok, err = _run_ffmpeg_extract_frame(cover_image_url, cover_path, 0.0)
        if not ok:
            # fallback：直接下载（可能不是 jpg，但至少不阻塞主流程）
            logger.warning(f"[{draft_id}] ffmpeg 生成封面失败，尝试直接下载: {err}")
            try:
                data = _download_bytes(cover_image_url, timeout=60)
                with open(cover_path, "wb") as f:
                    f.write(data)
            except Exception as e:
                logger.warning(f"[{draft_id}] 直接下载封面也失败，跳过封面: {e}")
                return
    elif video_url:
        ok, err = _run_ffmpeg_extract_frame(video_url, cover_path, time_point)
        if not ok:
            logger.warning(f"[{draft_id}] 从视频抽帧生成封面失败，跳过封面: {err}")
            return
    else:
        # 没有任何输入
        logger.warning(f"[{draft_id}] 未提供 cover_image_url 或 video_url，无法生成封面")
        return

    # 2) 更新元数据
    update_draft_cover_metadata(draft_path, "draft_cover.jpg")


