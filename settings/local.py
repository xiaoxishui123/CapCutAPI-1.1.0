"""
本地配置模块，用于从本地配置文件中加载配置
"""

import os
import json

# 配置文件路径
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

# 默认配置
IS_CAPCUT_ENV = True

# 默认域名配置
DRAFT_DOMAIN = "https://www.install-ai-guider.top"

# 默认预览路由
PREVIEW_ROUTER = "/draft/downloader"

# 是否上传草稿文件
IS_UPLOAD_DRAFT = False

# 端口号
PORT = 9000

# OSS 配置（使用 dict 作为默认值，避免缺键异常）
OSS_CONFIG = {}
MP4_OSS_CONFIG = {}

# 新增：跨平台默认草稿根路径（仅用于展示或作为本地保存默认值）
WINDOWS_DRAFT_FOLDER = "F:/jianyin/cgwz/JianyingPro Drafts"
LINUX_DRAFT_FOLDER = "/data/jianying/drafts"

# 新增：下载自定义请求头（解决鉴权/Referer 导致的 403 等问题）
DOWNLOAD_HEADERS = {}

# 新增：文件服务内网直连（将公网主机名重写为内网/本机地址，避免外网代理/防火墙导致的403）
FILE_SERVER_PUBLIC_HOST = ""
FILE_SERVER_INTERNAL_BASE = ""

# 尝试加载本地配置文件
if os.path.exists(CONFIG_FILE_PATH):
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            local_config = json.load(f)
            
            # 更新是否是国际版
            if "is_capcut_env" in local_config:
                IS_CAPCUT_ENV = local_config["is_capcut_env"]
            
            # 更新域名配置
            if "draft_domain" in local_config:
                DRAFT_DOMAIN = local_config["draft_domain"]

            # 更新端口号配置
            if "port" in local_config:
                PORT = local_config["port"]

            # 更新预览路由
            if "preview_router" in local_config:
                PREVIEW_ROUTER = local_config["preview_router"]
            
            # 更新是否上传草稿文件
            if "is_upload_draft" in local_config:
                IS_UPLOAD_DRAFT = local_config["is_upload_draft"]
                
            # 更新OSS配置
            if "oss_config" in local_config:
                OSS_CONFIG = local_config["oss_config"] or {}
            
            # 更新MP4 OSS配置
            if "mp4_oss_config" in local_config:
                MP4_OSS_CONFIG = local_config["mp4_oss_config"] or {}

            # 新增：草稿根路径
            if "windows_draft_folder" in local_config:
                WINDOWS_DRAFT_FOLDER = local_config["windows_draft_folder"]
            if "linux_draft_folder" in local_config:
                LINUX_DRAFT_FOLDER = local_config["linux_draft_folder"]

            # 新增：下载自定义请求头
            if "download_headers" in local_config and isinstance(local_config["download_headers"], dict):
                DOWNLOAD_HEADERS = local_config["download_headers"]

            # 新增：文件服务内网直连配置
            if "file_server_public_host" in local_config:
                FILE_SERVER_PUBLIC_HOST = (local_config["file_server_public_host"] or "").strip()
            if "file_server_internal_base" in local_config:
                FILE_SERVER_INTERNAL_BASE = (local_config["file_server_internal_base"] or "").strip()

    except (json.JSONDecodeError, IOError):
        # 配置文件加载失败，使用默认配置
        pass

# 新增：环境变量覆盖敏感配置（不修改原 config.json，但优先使用环境变量）
# OSS（草稿上传）
OSS_CONFIG = OSS_CONFIG or {}
_oss_env_overrides = {
    "bucket_name": os.getenv("OSS_BUCKET_NAME"),
    "access_key_id": os.getenv("OSS_ACCESS_KEY_ID"),
    "access_key_secret": os.getenv("OSS_ACCESS_KEY_SECRET"),
    "endpoint": os.getenv("OSS_ENDPOINT"),
    "region": os.getenv("OSS_REGION"),
}
for _k, _v in _oss_env_overrides.items():
    if _v:
        OSS_CONFIG[_k] = _v

# MP4 OSS（视频直链域名）
MP4_OSS_CONFIG = MP4_OSS_CONFIG or {}
_mp4_env_overrides = {
    "bucket_name": os.getenv("MP4_OSS_BUCKET_NAME"),
    "access_key_id": os.getenv("MP4_OSS_ACCESS_KEY_ID"),
    "access_key_secret": os.getenv("MP4_OSS_ACCESS_KEY_SECRET"),
    "endpoint": os.getenv("MP4_OSS_ENDPOINT"),
    "region": os.getenv("MP4_OSS_REGION"),
}
for _k, _v in _mp4_env_overrides.items():
    if _v:
        MP4_OSS_CONFIG[_k] = _v