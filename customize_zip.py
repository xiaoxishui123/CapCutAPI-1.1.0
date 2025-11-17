import io
import os
import hashlib
import json
import tempfile
import zipfile
import uuid
import time
from typing import Tuple
from oss import _ensure_bucket
from util import normalize_path_by_os

ASSET_DIRS = ("assets/audio/", "assets/image/", "assets/video/")

# 版本号：修改路径重写逻辑后需要更新此版本号，以使OSS缓存失效
# v6: 新增自动刷新draft_id和时间戳功能，彻底解决剪映重命名问题
REWRITE_VERSION = "v6_refresh_draft_id"


def _hash_str(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:12]


def _rewrite_paths_in_json(data, draft_id: str, client_os: str, draft_folder: str) -> dict:
    """
    Recursively rewrite any paths that contain assets/*
    🔧 修复：当draft_folder为空时，转换为相对路径（assets/audio/xxx.mp3）
    """
    def rewrite_path_if_needed(value: str) -> str:
        lower = value.replace("\\", "/").lower()
        if "assets/" not in lower:
            return value
        # try to find the segment from assets/... onwards
        idx = lower.find("assets/")
        rel = value[idx:]  # keep original filename case (e.g., assets/audio/xxx.mp3)
        
        # 🆕 相对路径模式：当draft_folder为空时，只返回相对路径部分
        if not draft_folder:
            # 返回相对路径（根据client_os调整分隔符）
            result = normalize_path_by_os(rel, client_os)
            print(f"[路径重写] 原路径: {value[:60]}... → 相对路径: {result}")
            return result
        
        # 原有逻辑：拼接完整路径
        base = draft_folder.rstrip("/\\")
        # join base + draft_id + rel
        joined = f"{base}/{draft_id}/" + rel
        result = normalize_path_by_os(joined, client_os)
        print(f"[路径重写] 原路径: {value[:40]}... → 自定义路径: {result[:40]}...")
        return result

    if isinstance(data, dict):
        new_obj = {}
        for k, v in data.items():
            if isinstance(v, str):
                # common fields: replace_path or any path-like value including assets/
                new_obj[k] = rewrite_path_if_needed(v)
            else:
                new_obj[k] = _rewrite_paths_in_json(v, draft_id, client_os, draft_folder)
        return new_obj
    elif isinstance(data, list):
        return [_rewrite_paths_in_json(x, draft_id, client_os, draft_folder) for x in data]
    else:
        return data


def _rewrite_meta_info(data, draft_id: str, client_os: str, draft_folder: str) -> dict:
    """
    Rewrite draft_meta_info.json, specifically updating draft_root_path and draft_fold_path
    🔧 修复：当draft_folder为空时，清空路径字段（相对路径模式）
    🆕 v6: 自动刷新draft_id和时间戳，解决剪映重命名问题
    """
    if not isinstance(data, dict):
        return data
    
    # 🆕 生成新的draft_id和时间戳（每次下载都不同）
    new_draft_id = str(uuid.uuid4()).upper()
    new_timestamp = int(time.time() * 1000000)  # 微秒级时间戳
    
    print(f"[刷新draft_id] {data.get('draft_id', 'N/A')} → {new_draft_id}")
    
    new_obj = {}
    for k, v in data.items():
        if k == "draft_root_path":
            if draft_folder:
                # 重写 draft_root_path 为配置的根路径
                new_obj[k] = normalize_path_by_os(draft_folder, client_os)
            else:
                # 🆕 相对路径模式：清空路径
                new_obj[k] = ""
        elif k == "draft_fold_path":
            if draft_folder:
                # 重写 draft_fold_path 为完整的草稿路径（根路径 + 草稿ID）
                base = draft_folder.rstrip("/\\")
                full_path = f"{base}/{draft_id}"
                new_obj[k] = normalize_path_by_os(full_path, client_os)
            else:
                # 🆕 相对路径模式：清空路径
                new_obj[k] = ""
        elif k == "draft_name":
            # 使用原始草稿ID作为名称（保持文件夹名称一致）
            new_obj[k] = draft_id
        elif k == "draft_id":
            # 🆕 刷新draft_id为全新的UUID
            new_obj[k] = new_draft_id
        elif k == "tm_draft_create":
            # 🆕 更新创建时间戳为当前时间
            new_obj[k] = new_timestamp
        elif k == "tm_draft_modified":
            # 🆕 更新修改时间戳为当前时间
            new_obj[k] = new_timestamp
        else:
            # 其他字段保持不变
            new_obj[k] = v
    
    return new_obj


def ensure_customized_zip(draft_id: str, client_os: str, draft_folder: str) -> Tuple[str, bool]:
    """
    Ensure an OSS object exists for the customized zip.
    Returns (object_key, created)
    """
    print(f"\n[ensure_customized_zip] 开始处理")
    print(f"[ensure_customized_zip] draft_id={draft_id}")
    print(f"[ensure_customized_zip] client_os={client_os}")
    print(f"[ensure_customized_zip] draft_folder='{draft_folder}'")
    print(f"[ensure_customized_zip] REWRITE_VERSION={REWRITE_VERSION}")

    bucket = _ensure_bucket()
    base_key = f"{draft_id}.zip"
    # 在key中加入版本号，当修改重写逻辑后更新版本号可使旧缓存失效
    # 🔧 修复：即使draft_folder为空也加入版本号（相对路径模式）
    key_suffix = _hash_str(f"{REWRITE_VERSION}|{client_os}|{draft_folder}")
    custom_key = f"{draft_id}__{client_os}__{key_suffix}.zip"

    print(f"[ensure_customized_zip] 计算的key: {custom_key}")

    # If already exists, return directly
    try:
        if bucket.object_exists(custom_key):
            print(f"[ensure_customized_zip] ✅ OSS缓存存在，直接返回")
            return custom_key, False
    except Exception:
        # proceed to attempt to create
        pass

    print(f"[ensure_customized_zip] ⚡ OSS缓存不存在，开始生成新版本")

    # 🔧 修复：检查基础版本是否存在
    try:
        if not bucket.object_exists(base_key):
            error_msg = f"基础草稿文件不存在: {base_key}"
            print(f"[ensure_customized_zip] ❌ {error_msg}")
            raise FileNotFoundError(error_msg)
    except Exception as check_err:
        print(f"[ensure_customized_zip] ❌ 检查基础文件失败: {check_err}")
        raise

    # Download base zip into memory/tempfile
    with tempfile.TemporaryDirectory() as td:
        base_zip_path = os.path.join(td, base_key)
        try:
            with open(base_zip_path, "wb") as f:
                # stream download via SDK
                print(f"[ensure_customized_zip] 开始下载基础文件: {base_key}")
                obj = bucket.get_object(base_key)
                f.write(obj.read())
            print(f"[ensure_customized_zip] ✅ 基础文件下载完成")
        except Exception as download_err:
            error_msg = f"下载基础草稿文件失败: {download_err}"
            print(f"[ensure_customized_zip] ❌ {error_msg}")
            raise Exception(error_msg)
        # Read, modify draft_info.json and draft_meta_info.json, write new zip
        custom_zip_path = os.path.join(td, custom_key)
        with zipfile.ZipFile(base_zip_path, "r") as zin, zipfile.ZipFile(custom_zip_path, "w", zipfile.ZIP_DEFLATED) as zout:
            found_draft_info = False
            found_meta_info = False
            
            for item in zin.infolist():
                filename_lower = item.filename.replace("\\", "/").lower()
                
                if filename_lower == "draft_info.json":
                    print(f"[ZIP处理] 找到 draft_info.json")
                    # 重写 draft_info.json 中的素材路径
                    raw = zin.read(item)
                    try:
                        info = json.loads(raw.decode("utf-8"))
                        print(f"[ZIP处理] draft_info.json 解析成功")
                    except Exception as e:
                        # pass through unmodified if parsing fails
                        print(f"[ZIP处理] draft_info.json 解析失败: {e}")
                        info = None
                    # 🔧 最终修复：总是重写路径
                    # draft_folder不为空 → 设置为指定路径
                    # draft_folder为空 → 转换为相对路径（assets/audio/xxx.mp3）
                    if info is not None:
                        print(f"[ZIP处理] 开始重写 draft_info.json 路径...")
                        info2 = _rewrite_paths_in_json(info, draft_id, client_os, draft_folder)
                        data = json.dumps(info2, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                        print(f"[ZIP处理] draft_info.json 重写完成")
                    else:
                        data = raw
                        print(f"[ZIP处理] draft_info.json 保持原样")
                    zi = zipfile.ZipInfo(item.filename)
                    zi.date_time = item.date_time
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zout.writestr(zi, data)
                    found_draft_info = True
                
                elif filename_lower == "draft_meta_info.json":
                    print(f"[ZIP处理] 找到 draft_meta_info.json")
                    # 重写 draft_meta_info.json 中的 draft_root_path 和 draft_fold_path
                    raw = zin.read(item)
                    try:
                        meta_info = json.loads(raw.decode("utf-8"))
                        print(f"[ZIP处理] draft_meta_info.json 解析成功")
                        print(f"[ZIP处理] 原 draft_root_path: {meta_info.get('draft_root_path', 'N/A')[:50]}")
                    except Exception as e:
                        # pass through unmodified if parsing fails
                        print(f"[ZIP处理] draft_meta_info.json 解析失败: {e}")
                        meta_info = None
                    # 🔧 修复：即使draft_folder为空也要重写（清空路径）
                    if meta_info is not None:
                        print(f"[ZIP处理] 开始重写 draft_meta_info.json...")
                        meta_info2 = _rewrite_meta_info(meta_info, draft_id, client_os, draft_folder)
                        print(f"[ZIP处理] 新 draft_root_path: '{meta_info2.get('draft_root_path', 'N/A')}'")
                        print(f"[ZIP处理] 新 draft_fold_path: '{meta_info2.get('draft_fold_path', 'N/A')}'")
                        data = json.dumps(meta_info2, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                        print(f"[ZIP处理] draft_meta_info.json 重写完成")
                    else:
                        data = raw
                        print(f"[ZIP处理] draft_meta_info.json 保持原样")
                    zi = zipfile.ZipInfo(item.filename)
                    zi.date_time = item.date_time
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zout.writestr(zi, data)
                    found_meta_info = True
                
                else:
                    # copy other entries
                    data = zin.read(item)
                    zout.writestr(item, data)
            
            # Log if files are missing (for debugging)
            if not found_draft_info:
                print(f"[ZIP处理] ⚠️ draft_info.json not found in {draft_id}.zip")
            if not found_meta_info:
                print(f"[ZIP处理] ⚠️ draft_meta_info.json not found in {draft_id}.zip")
        
        print(f"[ZIP处理] 开始上传到OSS: {custom_key}")
        # Upload new zip
        bucket.put_object_from_file(custom_key, custom_zip_path)
        print(f"[ZIP处理] ✅ 上传完成")

    print(f"[ensure_customized_zip] ✅ 返回key: {custom_key}\n")
    return custom_key, True


def get_customized_signed_url(draft_id: str, client_os: str, draft_folder: str, expires_seconds: int = 24*60*60) -> str:
    """Create or reuse customized zip on OSS, and return a signed URL."""
    bucket = _ensure_bucket()
    key, _ = ensure_customized_zip(draft_id, client_os, draft_folder)
    url = bucket.sign_url('GET', key, expires_seconds, slash_safe=True)
    return url
