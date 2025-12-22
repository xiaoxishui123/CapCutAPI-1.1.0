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
# v7: 修复空draft_folder时使用默认路径，解决剪映打开草稿空白问题
REWRITE_VERSION = "v7_fix_empty_folder"


def _hash_str(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:12]


def _check_base_file_with_retry(bucket, base_key: str, draft_id: str, max_wait_seconds: int = 30) -> bool:
    """
    智能检查基础文件是否存在，支持重试机制

    解决 OSS 最终一致性问题：
    - 如果草稿刚保存完成，OSS 可能还在同步中
    - 使用指数退避重试策略，最多等待 max_wait_seconds 秒

    Args:
        bucket: OSS bucket 实例
        base_key: 基础文件的 key (如 "draft_id.zip")
        draft_id: 草稿 ID
        max_wait_seconds: 最大等待时间（秒）

    Returns:
        bool: 文件是否存在
    """
    import sqlite3
    from datetime import datetime

    # 1️⃣ 先快速检查一次
    print(f"[重试检查] 第一次快速检查: {base_key}")
    try:
        if bucket.object_exists(base_key):
            print(f"[重试检查] ✅ 文件存在（第一次检查）")
            return True
    except Exception as e:
        print(f"[重试检查] ⚠️ 第一次检查失败: {e}")

    # 2️⃣ 查询草稿状态，判断是否需要重试
    print(f"[重试检查] 查询草稿状态...")
    try:
        conn = sqlite3.connect('capcut.db')
        c = conn.cursor()
        c.execute("""
            SELECT status, created_at, oss_uploaded, oss_verified
            FROM drafts
            WHERE id = ?
        """, (draft_id,))
        result = c.fetchone()
        conn.close()

        if not result:
            print(f"[重试检查] ❌ 草稿不存在于数据库")
            return False

        status, created_at, oss_uploaded, oss_verified = result
        print(f"[重试检查] 草稿状态: status={status}, oss_uploaded={oss_uploaded}, oss_verified={oss_verified}")

        # 3️⃣ 判断是否需要重试
        # 条件：草稿状态为 'completed' 或 'processing'，且创建时间在最近 2 分钟内
        if status not in ['completed', 'processing']:
            print(f"[重试检查] ⚠️ 草稿状态不是 completed/processing，不重试")
            return False

        # 计算草稿创建时间（秒）
        try:
            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            time_since_created = (datetime.now() - created_time).total_seconds()
            print(f"[重试检查] 草稿创建于 {time_since_created:.1f} 秒前")

            # 如果创建时间超过 5 分钟，不重试（文件应该已经同步）
            if time_since_created > 300:
                print(f"[重试检查] ⚠️ 草稿创建超过 5 分钟，文件应该存在，不重试")
                return False
        except Exception as e:
            print(f"[重试检查] ⚠️ 解析创建时间失败: {e}，继续重试")

    except Exception as e:
        print(f"[重试检查] ⚠️ 查询数据库失败: {e}，继续重试")

    # 4️⃣ 开始指数退避重试
    print(f"[重试检查] 🔄 开始重试策略（最多 {max_wait_seconds} 秒）")
    retry_delays = [1, 2, 4, 8, 15]  # 指数退避：1s, 2s, 4s, 8s, 15s（总计30秒）
    total_waited = 0

    for attempt, delay in enumerate(retry_delays, start=1):
        if total_waited >= max_wait_seconds:
            print(f"[重试检查] ⏰ 已达到最大等待时间 {max_wait_seconds} 秒")
            break

        print(f"[重试检查] 等待 {delay} 秒后重试（第 {attempt}/{len(retry_delays)} 次）...")
        time.sleep(delay)
        total_waited += delay

        # 检查文件是否存在
        try:
            if bucket.object_exists(base_key):
                print(f"[重试检查] ✅ 文件存在（第 {attempt} 次重试成功，共等待 {total_waited} 秒）")
                return True
            else:
                print(f"[重试检查] ⏳ 文件仍不存在（第 {attempt} 次重试）")
        except Exception as e:
            print(f"[重试检查] ⚠️ 第 {attempt} 次检查失败: {e}")

    # 5️⃣ 所有重试都失败
    print(f"[重试检查] ❌ 文件不存在（已重试 {len(retry_delays)} 次，总计等待 {total_waited} 秒）")
    return False


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

    🔧 修复：添加智能重试机制，解决 OSS 最终一致性导致的下载失败问题
    🔧 修复（2025-12-09）：当 draft_folder 为空时，使用配置的默认路径
    """
    # 🔧 关键修复：当 draft_folder 为空时，使用配置的默认路径
    # 解决剪映打开草稿显示空白的问题（因为相对路径剪映无法定位素材）
    if not draft_folder:
        try:
            from settings.local import WINDOWS_DRAFT_FOLDER, LINUX_DRAFT_FOLDER
            if client_os == 'windows':
                draft_folder = WINDOWS_DRAFT_FOLDER or "F:\\jianyin\\cgwz\\JianyingPro Drafts"
                # 确保Windows路径使用反斜杠
                draft_folder = draft_folder.replace('/', '\\')
            else:
                draft_folder = LINUX_DRAFT_FOLDER or "/data/jianying/drafts"
            print(f"[ensure_customized_zip] 使用默认草稿路径: {draft_folder}")
        except ImportError:
            # 如果无法导入设置，使用硬编码的默认值
            if client_os == 'windows':
                draft_folder = "F:\\jianyin\\cgwz\\JianyingPro Drafts"
            else:
                draft_folder = "/data/jianying/drafts"
            print(f"[ensure_customized_zip] 无法读取配置，使用默认路径: {draft_folder}")
    
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

    # 🔧 修复：智能检查基础版本是否存在（支持重试）
    base_file_exists = _check_base_file_with_retry(bucket, base_key, draft_id)

    if not base_file_exists:
        error_msg = f"基础草稿文件不存在: {base_key}（已重试多次）"
        print(f"[ensure_customized_zip] ❌ {error_msg}")
        raise FileNotFoundError(error_msg)

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
            
            # 🔧 检测并移除顶级目录前缀（解决两层嵌套问题）
            # 检测ZIP是否有统一的顶级目录（如 dfd_cat_xxx/）
            top_level_dir = None
            all_names = zin.namelist()
            if all_names:
                first_parts = set()
                for name in all_names:
                    parts = name.replace("\\", "/").split("/")
                    if parts[0]:
                        first_parts.add(parts[0])
                # 如果所有文件都在同一个顶级目录下，且该目录与draft_id匹配
                if len(first_parts) == 1:
                    potential_top = list(first_parts)[0]
                    if potential_top == draft_id or potential_top.startswith(draft_id):
                        top_level_dir = potential_top
                        print(f"[ZIP处理] 检测到顶级目录: {top_level_dir}/, 将移除此前缀")
            
            for item in zin.infolist():
                filename = item.filename.replace("\\", "/")
                filename_lower = filename.lower()
                
                # 🔧 移除顶级目录前缀
                if top_level_dir and filename.startswith(f"{top_level_dir}/"):
                    new_filename = filename[len(top_level_dir) + 1:]  # 移除 "dfd_cat_xxx/" 前缀
                    if not new_filename:  # 跳过顶级目录本身
                        continue
                else:
                    new_filename = filename
                
                # 🔧 修复：支持ZIP内部有顶级目录的情况（如 dfd_cat_xxx/draft_info.json）
                basename_lower = new_filename.lower().split("/")[-1] if "/" in new_filename else new_filename.lower()
                
                if basename_lower == "draft_info.json":
                    print(f"[ZIP处理] 找到 draft_info.json: {filename} -> {new_filename}")
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
                    # 🔧 使用移除顶级目录后的新文件名
                    zi = zipfile.ZipInfo(new_filename)
                    zi.date_time = item.date_time
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zout.writestr(zi, data)
                    found_draft_info = True
                
                elif basename_lower == "draft_meta_info.json":
                    print(f"[ZIP处理] 找到 draft_meta_info.json: {filename} -> {new_filename}")
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
                    # 🔧 使用移除顶级目录后的新文件名
                    zi = zipfile.ZipInfo(new_filename)
                    zi.date_time = item.date_time
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zout.writestr(zi, data)
                    found_meta_info = True
                
                else:
                    # 🔧 复制其他文件，使用移除顶级目录后的新文件名
                    data = zin.read(item)
                    zi = zipfile.ZipInfo(new_filename)
                    zi.date_time = item.date_time
                    zi.compress_type = item.compress_type
                    zout.writestr(zi, data)
            
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
