import io
import os
import hashlib
import json
import tempfile
import zipfile
from typing import Tuple
from oss import _ensure_bucket
from util import normalize_path_by_os

ASSET_DIRS = ("assets/audio/", "assets/image/", "assets/video/")


def _hash_str(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:12]


def _rewrite_paths_in_json(data, draft_id: str, client_os: str, draft_folder: str) -> dict:
    """Recursively rewrite any paths that contain assets/* to target draft_folder/draft_id/..."""
    def rewrite_path_if_needed(value: str) -> str:
        lower = value.replace("\\", "/").lower()
        if "assets/" not in lower:
            return value
        # try to find the segment from assets/... onwards
        idx = lower.find("assets/")
        rel = value[idx:]  # keep original filename case
        base = draft_folder.rstrip("/\\")
        # join base + draft_id + rel
        joined = f"{base}/{draft_id}/" + rel
        return normalize_path_by_os(joined, client_os)

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


def ensure_customized_zip(draft_id: str, client_os: str, draft_folder: str) -> Tuple[str, bool]:
    """
    Ensure an OSS object exists for the customized zip.
    Returns (object_key, created)
    """
    bucket = _ensure_bucket()
    base_key = f"{draft_id}.zip"
    key_suffix = _hash_str(f"{client_os}|{draft_folder}") if draft_folder else client_os
    custom_key = f"{draft_id}__{client_os}__{key_suffix}.zip"

    # If already exists, return directly
    try:
        if bucket.object_exists(custom_key):
            return custom_key, False
    except Exception:
        # proceed to attempt to create
        pass

    # Download base zip into memory/tempfile
    with tempfile.TemporaryDirectory() as td:
        base_zip_path = os.path.join(td, base_key)
        with open(base_zip_path, "wb") as f:
            # stream download via SDK
            obj = bucket.get_object(base_key)
            f.write(obj.read())
        # Read, modify draft_info.json, write new zip
        custom_zip_path = os.path.join(td, custom_key)
        with zipfile.ZipFile(base_zip_path, "r") as zin, zipfile.ZipFile(custom_zip_path, "w", zipfile.ZIP_DEFLATED) as zout:
            found = False
            for item in zin.infolist():
                if item.filename.replace("\\", "/").lower() == "draft_info.json":
                    # rewrite
                    raw = zin.read(item)
                    try:
                        info = json.loads(raw.decode("utf-8"))
                    except Exception:
                        # pass through unmodified if parsing fails
                        info = None
                    if info is not None and draft_folder:
                        info2 = _rewrite_paths_in_json(info, draft_id, client_os, draft_folder)
                        data = json.dumps(info2, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                    else:
                        data = raw
                    zi = zipfile.ZipInfo(item.filename)
                    zi.date_time = item.date_time
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zout.writestr(zi, data)
                    found = True
                else:
                    # copy other entries
                    data = zin.read(item)
                    zout.writestr(item, data)
            # If draft_info.json missing, still proceed without change
        # Upload new zip
        bucket.put_object_from_file(custom_key, custom_zip_path)

    return custom_key, True


def get_customized_signed_url(draft_id: str, client_os: str, draft_folder: str, expires_seconds: int = 24*60*60) -> str:
    """Create or reuse customized zip on OSS, and return a signed URL."""
    bucket = _ensure_bucket()
    key, _ = ensure_customized_zip(draft_id, client_os, draft_folder)
    url = bucket.sign_url('GET', key, expires_seconds, slash_safe=True)
    return url
