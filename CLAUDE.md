# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

CapCutAPI-1.1.0是一个开源的CapCut（剪映）API工具，基于Python开发，提供了一系列功能来自动化视频剪辑和混剪流程。项目支持通过API创建和编辑视频，集成了AI功能，并提供云端存储和预览。

## 核心架构

### 服务端
- **Web框架**: Flask (`capcut_server.py`)
- **核心功能**: `pyJianYingDraft`库 - 用于处理剪映的草稿文件
- **配置文件**: `config.json` - 控制服务端口、草稿保存模式等
- **OSS集成**: 支持将草稿上传到阿里云OSS (`oss.py`)

### 草稿保存模式
项目支持两种草稿保存模式，通过`config.json`中的`is_upload_draft`字段控制：
- **OSS云存储模式**: 草稿自动上传到OSS，适合生产环境
- **本地保存模式**: 草稿保存在本地，适合开发测试

### API接口
- `/create_draft`: 创建草稿
- `/add_video`: 添加视频
- `/add_audio`: 添加音频
- `/add_text`: 添加文本
- `/save_draft`: 保存草稿

## 常用命令

### 服务管理
```bash
# 使用管理脚本（推荐）
./service_manager.sh start      # 启动服务
./service_manager.sh stop       # 停止服务
./service_manager.sh restart    # 重启服务
./service_manager.sh status     # 查看状态
./service_manager.sh logs       # 查看日志
./service_manager.sh test       # 测试服务

# 使用systemd
sudo systemctl start capcutapi.service
sudo systemctl stop capcutapi.service
sudo systemctl restart capcutapi.service

# 查看日志
tail -f logs/capcutapi.log
```

### 开发调试
```bash
# 直接启动服务
python capcut_server.py

# 安装依赖
pip install -r requirements.txt

# API测试
# 可以使用 rest_client_test.http 文件进行API测试
```

## 环境要求

- **Python**: 3.9 或更高版本 (`/usr/local/bin/python3.9` 推荐)
- **FFmpeg**: 系统需安装并配置好环境变量
- **依赖**: 见 `requirements.txt` (`imageio`, `psutil`, `flask`, `requests`, `oss2`)

## 部署

### 自动部署
```bash
# 确保服务器已安装Python3.9和ffmpeg
chmod +x deploy.sh
./deploy.sh
```

### 手动部署
1. 安装依赖: `pip install -r requirements.txt`
2. 配置`config.json`: `cp config.json.example config.json`
3. 启动服务: `python capcut_server.py`

## 安全注意事项

### 环境变量
为了避免硬编码敏感密钥，项目支持通过环境变量配置OSS信息：
- `OSS_BUCKET_NAME`
- `OSS_ACCESS_KEY_ID`
- `OSS_ACCESS_KEY_SECRET`
- `OSS_ENDPOINT`
- `OSS_REGION`

## 开发注意事项

### 核心逻辑
- **草稿创建**: `create_draft.py`
- **素材添加**: `add_video_track.py`, `add_audio_track.py`, etc.
- **草稿保存**: `save_draft_impl.py`

### 预览功能
- 项目提供了草稿预览功能，通过`/draft/preview/<draft_id>`访问
- 预览界面采用现代化设计，支持响应式布局

### 代码结构
- **pyJianYingDraft/**: 核心草稿处理库
- **settings/**: 项目配置
- ***.py**: 各个API接口的实现