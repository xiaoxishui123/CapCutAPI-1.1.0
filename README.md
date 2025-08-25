# CapCutAPI

Open source CapCut API tool.

Try It: https://www.capcutapi.top

[中文说明](https://github.com/sun-guannan/CapCutAPI/blob/main/README-zh.md)

## 服务器部署信息

**当前服务器部署地址**: http://8.148.70.18:9000

**部署状态**: ✅ 已部署并运行中

**重要配置更新**:
- 📁 **草稿保存模式**: 已切换至OSS云存储模式
- ☁️ **云存储**: 自动上传至阿里云OSS，节省本地存储空间
- 🔗 **返回格式**: 草稿保存后返回可下载的云端URL

**访问方式**:
- 🌐 **浏览器访问**: 直接访问 http://8.148.70.18:9000 查看美观的欢迎页面
- 🔧 **API调用**: 使用 `Accept: application/json` 头获取JSON格式的API信息
- 📖 **详细文档**: 查看 `API_USAGE_EXAMPLES.md` 获取完整使用说明

**服务管理命令**:
```bash
# 查看服务状态
sudo systemctl status capcutapi.service

# 启动服务
sudo systemctl start capcutapi.service

# 停止服务
sudo systemctl stop capcutapi.service

# 重启服务
sudo systemctl restart capcutapi.service

# 查看日志
tail -f logs/capcutapi.log

# 查看错误日志
tail -f logs/capcutapi.error.log

# 使用管理脚本
./service_manager.sh status
./service_manager.sh restart
./service_manager.sh logs
./service_manager.sh test
```

## Gallery

**MCP agent**

[![AI Cut](https://img.youtube.com/vi/fBqy6WFC78E/hqdefault.jpg)](https://www.youtube.com/watch?v=fBqy6WFC78E)

**Connect AI generated via CapCutAPI**

[![Airbnb](https://img.youtube.com/vi/1zmQWt13Dx0/hqdefault.jpg)](https://www.youtube.com/watch?v=1zmQWt13Dx0)

[![Horse](https://img.youtube.com/vi/IF1RDFGOtEU/hqdefault.jpg)](https://www.youtube.com/watch?v=IF1RDFGOtEU)

[![Song](https://img.youtube.com/vi/rGNLE_slAJ8/hqdefault.jpg)](https://www.youtube.com/watch?v=rGNLE_slAJ8)

## Project Features

This project is a Python-based CapCut processing tool that offers the following core functionalities:

### Core Features

- **Draft File Management**: Create, read, modify, and save CapCut draft files
- **Material Processing**: Support adding and editing various materials such as videos, audios, images, texts, stickers, etc.
- **Effect Application**: Support adding multiple effects like transitions, filters, masks, animations, etc.
- **API Service**: Provide HTTP API interfaces to support remote calls and automated processing
- **AI Integration**: Integrate multiple AI services to support intelligent generation of subtitles, texts, and images

### Main API Interfaces

- `/create_draft`: Create a draft
- `/add_video`: Add video material to the draft
- `/add_audio`: Add audio material to the draft
- `/add_image`: Add image material to the draft
- `/add_text`: Add text material to the draft
- `/add_subtitle`: Add subtitles to the draft
- `/add_effect`: Add effects to materials
- `/add_sticker`: Add stickers to the draft
- `/save_draft`: Save the draft file

## 快速部署指南

### 自动部署

1. 确保服务器已安装Python3.9和ffmpeg
2. 运行部署脚本：
```bash
chmod +x deploy.sh
./deploy.sh
```

### 手动部署

#### 环境要求

- Python 3.8.20 或更高版本
- ffmpeg
- 系统支持systemd服务管理

#### 部署步骤

1. **安装依赖**
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装ffmpeg (CentOS/RHEL)
sudo yum install -y epel-release
sudo yum install -y ffmpeg

# 或安装ffmpeg (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y ffmpeg
```

2. **配置服务**
```bash
# 复制配置文件
cp config.json.example config.json

# 编辑配置文件，设置端口为9000
vim config.json
```

3. **启动服务**
```bash
# 直接启动
python capcut_server.py

# 或使用systemd服务
sudo systemctl start capcutapi.service
```

## Configuration Instructions

### Configuration File

The project supports custom settings through a configuration file. To use the configuration file:

1. Copy `config.json.example` to `config.json`
2. Modify the configuration items as needed

```bash
cp config.json.example config.json
```

### 草稿保存模式配置

项目支持两种草稿保存模式，通过 `config.json` 中的 `is_upload_draft` 字段控制：

#### OSS云存储模式（当前启用）
```json
{
  "is_upload_draft": true
}
```
**特点**：
- ✅ 草稿自动压缩为zip格式上传至阿里云OSS
- ✅ 返回可下载的云端URL
- ✅ 自动清理本地临时文件，节省存储空间
- ✅ 适合生产环境和多用户场景

#### 本地保存模式
```json
{
  "is_upload_draft": false
}
```
**特点**：
- 📁 草稿保存在本地目录中
- 💾 不会上传到云端
- 🔧 适合开发测试和单机使用

### Environment Configuration

#### ffmpeg

This project depends on ffmpeg. You need to ensure that ffmpeg is installed on your system and added to the system's environment variables.

#### Python Environment

This project requires Python version 3.8.20. Please ensure that the correct version of Python is installed on your system.

#### Install Dependencies

Install the required dependency packages for the project:

```bash
pip install -r requirements.txt
```

### Run the Server

After completing the configuration and environment setup, execute the following command to start the server:

```bash
python capcut_server.py
```

Once the server is started, you can access the related functions through the API interfaces.

## Usage Examples

### Adding a Video

```python
import requests

response = requests.post("http://8.148.70.18:9000/add_video", json={
    "video_url": "http://example.com/video.mp4",
    "start": 0,
    "end": 10,
    "width": 1080,
    "height": 1920
})

print(response.json())
```

### Adding Text

```python
import requests

response = requests.post("http://8.148.70.18:9000/add_text", json={
    "text": "Hello, World!",
    "start": 0,
    "end": 3,
    "font": "ZY_Courage",
    "font_color": "#FF0000",
    "font_size": 30.0
})

print(response.json())
```

### Saving a Draft

```python
import requests

response = requests.post("http://8.148.70.18:9000/save_draft", json={
    "draft_id": "123456",
    "draft_folder": "your capcut draft folder"
})

print(response.json())
```
You can also use the ```rest_client_test.http``` file of the REST Client for HTTP testing. Just need to install the corresponding IDE plugin

### Copying the Draft to CapCut Draft Path

Calling `save_draft` will generate a folder starting with `dfd_` in the current directory of the server. Copy this folder to the CapCut draft directory, and you will be able to see the generated draft.

### More Examples

Please refer to the `example.py` file in the project, which contains more usage examples such as adding audio and effects.

## Project Features

- **Cross-platform Support**: Supports both CapCut China version and CapCut International version
- **Automated Processing**: Supports batch processing and automated workflows
- **Rich APIs**: Provides comprehensive API interfaces for easy integration into other systems
- **Flexible Configuration**: Achieve flexible function customization through configuration files
- **AI Enhancement**: Integrate multiple AI services to improve video production efficiency

## 安全与环境变量配置（推荐）

为避免在`config.json`中硬编码敏感密钥，已支持通过环境变量覆盖以下字段（程序启动时优先使用环境变量）：

- OSS（草稿压缩包上传）
  - `OSS_BUCKET_NAME`
  - `OSS_ACCESS_KEY_ID`
  - `OSS_ACCESS_KEY_SECRET`
  - `OSS_ENDPOINT`（形如`oss-cn-xxx.aliyuncs.com`或带`https://`的完整域名）
  - `OSS_REGION`（如：`cn-xxx`）

- MP4 OSS（视频直链域名）
  - `MP4_OSS_BUCKET_NAME`
  - `MP4_OSS_ACCESS_KEY_ID`
  - `MP4_OSS_ACCESS_KEY_SECRET`
  - `MP4_OSS_ENDPOINT`（建议为自定义加速域名，直接用于拼接直链）
  - `MP4_OSS_REGION`

使用示例（临时导出，仅对当前会话生效）：

```bash
export OSS_BUCKET_NAME="your-bucket"
export OSS_ACCESS_KEY_ID="xxx"
export OSS_ACCESS_KEY_SECRET="yyy"
export OSS_ENDPOINT="oss-cn-xxx.aliyuncs.com"
export OSS_REGION="cn-xxx"

export MP4_OSS_BUCKET_NAME="your-mp4-bucket"
export MP4_OSS_ACCESS_KEY_ID="xxx"
export MP4_OSS_ACCESS_KEY_SECRET="yyy"
export MP4_OSS_ENDPOINT="https://your.cdn.domain"
export MP4_OSS_REGION="cn-xxx"
```

生产环境建议通过 systemd 配置环境变量（`/etc/systemd/system/capcut-api.service` 中添加 `Environment=` 行）或使用密钥管理服务，并及时轮换已暴露的密钥。

## 指定 Python 版本

本项目建议使用 `/usr/local/bin/python3.9` 运行，以获得更稳定的一致性：

```bash
/usr/local/bin/python3.9 capcut_server.py
```

如使用 `service_manager.sh`，可手动修改为优先使用该 Python 路径，或确保虚拟环境基于 Python 3.9 创建并已安装依赖。
