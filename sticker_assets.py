#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贴纸资源映射（resource_id -> 可渲染图片URL）

原因（通俗解释）：
- 草稿里的贴纸 `Sticker_segment` 只有一个 `resource_id`，这是剪映/CapCut 内置素材的编号
- 在服务器上，我们拿不到剪映客户端内部的贴纸图片文件
- 所以云渲染要“看得见贴纸”，必须有一张真实可下载的贴纸图片（PNG/WebP/JPG）

做法：
- 提供一个很简单的映射表（JSON文件）：
  { "resource_id_1": "https://.../sticker.png", "resource_id_2": "..." }
- 渲染时根据 resource_id 找到对应图片 URL 来叠加到视频上
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict, Optional


_LOCK = threading.Lock()


def _map_path() -> str:
    # 放在项目根目录（与 capcut_server.py 同级）
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "sticker_resource_map.json")


def _load_map() -> Dict[str, Any]:
    path = _map_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _save_map(data: Dict[str, Any]) -> None:
    path = _map_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def set_sticker_resource(resource_id: str, image_url: str) -> Dict[str, Any]:
    """注册/更新贴纸资源映射"""
    rid = (resource_id or "").strip()
    url = (image_url or "").strip()
    if not rid or not url:
        raise ValueError("resource_id and image_url required")
    with _LOCK:
        data = _load_map()
        data[rid] = url
        _save_map(data)
    return {"resource_id": rid, "image_url": url}


def get_sticker_image_url(resource_id: str) -> Optional[str]:
    rid = (resource_id or "").strip()
    if not rid:
        return None
    with _LOCK:
        data = _load_map()
        v = data.get(rid)
        return v if isinstance(v, str) and v.strip() else None


def list_sticker_resources(limit: int = 200) -> Dict[str, str]:
    with _LOCK:
        data = _load_map()
    # 只返回字符串
    items = [(k, v) for k, v in data.items() if isinstance(k, str) and isinstance(v, str)]
    items = items[: max(0, int(limit or 0))] if limit else items
    return {k: v for k, v in items}


