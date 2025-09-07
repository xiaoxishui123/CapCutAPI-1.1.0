# CapCutAPI

轻量、灵活、易上手的剪映/CapCutAPI工具，构建全自动化视频剪辑/混剪流水线。

Lightweight, flexible, and easy-to-use CapCut API tool for building fully automated video editing pipelines.

Try It: https://www.capcutapi.top

```
👏👏👏👏 庆祝github 600星，送出价值6000点不记名云渲染券：17740F41-5ECB-44B1-AAAE-1C458A0EFF43
```

## ⚠️ **重要访问说明**

**如果您在本地Windows机器上访问服务，请注意：**

- ❌ **错误访问方式**: `localhost:9000` 或 `127.0.0.1:9000`
- ✅ **正确访问方式**: `http://8.148.70.18:9000`

**原因说明**: 服务部署在远程Linux服务器上，`localhost`指向的是您本地机器，而不是服务器。

**正确的访问地址**:
- 🏠 **主页**: http://8.148.70.18:9000
- 📊 **草稿管理**: http://8.148.70.18:9000/api/drafts/dashboard
- 🎬 **草稿预览**: http://8.148.70.18:9000/draft/preview/[草稿ID]

---

## 🚀 **最新功能优化** (NEW!)

### 🎨 官方风格草稿预览界面优化 (v1.2.0)

#### 💫 设计升级亮点：
- **🎨 官方风格设计**: 采用官方文档的浅色主题，更专业、更现代
- **📱 响应式网格布局**: 使用CSS Grid替代Flexbox，完美适配各种设备
- **🔍 清晰的信息层次**: 优化的视觉层次，更易于扫描和理解
- **⚡ 增强的交互体验**: 悬停效果、选中状态、平滑动画等交互优化
- **🎯 时间轴可视化**: 直观的时间轴显示，素材位置一目了然
- **💾 智能下载管理**: 优化的下载界面，支持路径配置和帮助信息

#### 🌟 视觉风格改进：
- **配色方案**: 官方蓝色主色调 (#0066cc)，浅色背景 (#f5f5f5)
- **卡片设计**: 白色卡片背景，微妙的阴影效果，圆角设计
- **字体优化**: 系统字体栈，等宽字体用于代码和时间显示
- **间距统一**: 24px标准间距，更舒适的视觉体验

#### 🔧 技术实现亮点：
- **CSS Grid布局**: 现代布局技术，更好的响应式控制
- **性能优化**: 减少重绘和回流，优化动画性能
- **无障碍设计**: 合理的颜色对比度，清晰的视觉层次
- **代码质量**: 模块化CSS，易于维护和扩展

### 草稿下载和预览功能全面升级 (v1.1.0)

#### 💫 优化亮点：
- **🎨 全新视觉设计**: 现代化暗色主题，专业视频编辑体验
- **⚡ 智能下载流程**: 自动检测云端文件，支持断点续传
- **📱 响应式设计**: 完美适配桌面端、平板和手机
- **🔄 实时状态监控**: 下载进度实时显示，任务状态透明化
- **📊 可视化预览**: 交互式时间轴，素材详情动态展示
- **🎯 多平台支持**: Windows、Linux、macOS路径智能适配

#### 🆕 新增功能：
1. **草稿管理仪表板** (`/api/drafts/dashboard`)
   - 集中管理所有草稿
   - 支持批量下载操作
   - 实时统计和搜索功能

2. **批量下载API** (`/api/drafts/batch-download`)
   - 一键下载多个草稿
   - 并发处理，提升效率
   - 详细的成功/失败报告

3. **草稿列表API** (`/api/drafts/list`)
   - 自动扫描本地和云端草稿
   - 多数据源整合展示
   - 完整的元数据信息

#### 🌟 增强的页面：
- **`/draft/preview/<draft_id>`**: 沉浸式预览体验
- **`/draft/downloader`**: 智能下载中心
- **`/`**: 美观的欢迎页面

#### 🔧 技术改进：
- 优化了草稿状态查询逻辑
- 增强了错误处理和用户反馈
- 改进了OSS云存储集成
- 添加了调试和监控接口

#### 📁 访问新功能：
```bash
# 草稿管理仪表板
http://8.148.70.18:9000/api/drafts/dashboard

# 草稿预览页面（示例）
http://8.148.70.18:9000/draft/preview/dfd_cat_1756104121_cb774809

# 草稿下载页面（示例）
http://8.148.70.18:9000/draft/downloader?draft_id=dfd_cat_1756104121_cb774809
```

---

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

## 📚 文档导航 | Documentation

### 核心文档 | Core Documentation
- [📋 需求文档](docs/REQUIREMENTS_DOCUMENT.md) - 详细的功能需求和技术规格 | Detailed requirements and specifications
- [📖 操作手册](docs/OPERATION_MANUAL.md) - 完整的操作指南和最佳实践 | Complete operation guide and best practices
- [🚀 功能优化总结](docs/FEATURE_OPTIMIZATION_SUMMARY.md) - 最新功能更新和优化记录 | Latest feature updates and optimization records
- [🔧 故障排除指南](docs/TROUBLESHOOTING.md) - 常见问题解决方案 | Common issues and solutions
- [🛠️ API使用示例](docs/API_USAGE_EXAMPLES.md) - 完整的API调用示例 | Complete API usage examples

### 部署与技术文档 | Deployment & Technical Documentation
- [🚀 部署总结](docs/CapCutAPI部署总结.md) - 服务器部署和配置信息 | Server deployment and configuration
- [⚙️ 技术文档](docs/CLAUDE.md) - 项目架构和技术实现 | Project architecture and technical implementation
- [🔍 数据流分析](docs/CapCutAPI_数据流分析文档.md) - 系统数据流和处理逻辑分析 | System data flow and processing logic analysis
- [🛠️ 跨平台素材识别](docs/CapCutAPI_跨平台素材识别问题解决方案.md) - 跨平台兼容性解决方案 | Cross-platform compatibility solutions
- [☁️ OSS素材识别修复](docs/OSS_Material_Recognition_Fix_Report.md) - OSS云存储素材识别问题修复 | OSS cloud storage material recognition fixes
- [🌐 浏览器工具测试](docs/BROWSER_TOOLS_TEST_REPORT.md) - 浏览器工具功能测试报告 | Browser tools functionality test report

### 历史文档 | Archive
- [📁 archive/](archive/) - 技术报告和历史文档 | Technical reports and historical documents
  - 数据流分析文档
  - 跨平台素材识别问题解决方案
  - OSS素材识别修复报告
  - 浏览器工具测试报告

## 项目功能 | Project Features

本项目是一个基于Python的剪映/CapCut处理工具，提供以下核心功能：

This project is a Python-based CapCut processing tool that offers the following core functionalities:

### 核心功能 | Core Features

- **草稿文件管理 | Draft File Management**: 创建、读取、修改和保存剪映/CapCut草稿文件 | Create, read, modify, and save CapCut draft files
- **素材处理 | Material Processing**: 支持视频、音频、图片、文本、贴纸等多种素材的添加和编辑 | Support adding and editing various materials such as videos, audios, images, texts, stickers, etc.
- **特效应用 | Effect Application**: 支持添加转场、滤镜、蒙版、动画等多种特效 | Support adding multiple effects like transitions, filters, masks, animations, etc.
- **API服务 | API Service**: 提供HTTP API接口，支持远程调用和自动化处理 | Provide HTTP API interfaces to support remote calls and automated processing
- **AI集成 | AI Integration**: 集成多种AI服务，支持智能生成字幕、文本和图像 | Integrate multiple AI services to support intelligent generation of subtitles, texts, and images

### 主要API接口 | Main API Interfaces

- `/create_draft`: 创建草稿 | Create a draft
- `/add_video`: 添加视频素材到草稿 | Add video material to the draft
- `/add_audio`: 添加音频素材到草稿 | Add audio material to the draft
- `/add_image`: 添加图片素材到草稿 | Add image material to the draft
- `/add_text`: 添加文本素材到草稿 | Add text material to the draft
- `/add_subtitle`: 添加字幕到草稿 | Add subtitles to the draft
- `/add_effect`: 添加特效到素材 | Add effects to materials
- `/add_sticker`: 添加贴纸到草稿 | Add stickers to the draft
- `/save_draft`: 保存草稿文件 | Save the draft file

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
- ✅ 支持Windows客户端路径自动配置

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

### Windows客户端路径配置 🪟

#### 自动路径识别
系统现已支持客户端操作系统自动识别，确保Windows客户端能正确识别素材路径：

**客户端调用示例**：
```json
{
  "draft_id": "your_draft_id",
  "client_os": "windows"
}
```

#### 自定义路径配置
用户可以通过以下方式配置自定义下载路径：

**1. 通过API配置**：
```bash
# 设置自定义路径
curl -X POST http://8.148.70.18:9000/api/draft/path/config \
  -H "Content-Type: application/json" \
  -d '{"custom_path": "F:\\jianying\\cgwz\\JianyingPro Drafts"}'

# 获取当前配置
curl -X GET http://8.148.70.18:9000/api/draft/path/config
```

**2. 通过文件配置**：
创建或修改 `path_config.json` 文件：
```json
{
  "custom_download_path": "F:\\jianying\\cgwz\\JianyingPro Drafts"
}
```

#### 路径优先级
系统按以下优先级选择草稿路径：
1. **API传入的 draft_folder 参数**（最高优先级）
2. **用户自定义路径**（path_config.json 中的配置）
3. **客户端操作系统默认路径**（根据 client_os 参数）
4. **服务器操作系统默认路径**（兜底方案）

#### Windows路径格式
- ✅ 支持Windows标准路径格式：`F:\jianying\cgwz\JianyingPro Drafts`
- ✅ 自动处理路径分隔符转换（`/` → `\`）
- ✅ 确保草稿文件中的素材路径为Windows本地绝对路径
- ✅ 剪映客户端可直接识别和链接素材

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

## 项目特点 | Project Features

- **跨平台支持 | Cross-platform Support**: 同时支持剪映和CapCut国际版 | Supports both CapCut China version and CapCut International version
- **自动化处理 | Automated Processing**: 支持批量处理和自动化工作流 | Supports batch processing and automated workflows
- **丰富的API | Rich APIs**: 提供全面的API接口，方便集成到其他系统 | Provides comprehensive API interfaces for easy integration into other systems
- **灵活的配置 | Flexible Configuration**: 通过配置文件实现灵活的功能定制 | Achieve flexible function customization through configuration files
- **AI增强 | AI Enhancement**: 集成多种AI服务，提升视频制作效率 | Integrate multiple AI services to improve video production efficiency

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

## 效果演示 | Demo

📺 **视频演示**: [CapCutAPI 功能演示](https://www.bilibili.com/video/BV1234567890)

## 🔧 故障排除 | Troubleshooting

遇到问题？不要慌！我们为您准备了完整的故障排除指南：

### 📋 快速诊断

```bash
# 运行一键诊断脚本
./diagnose.sh
```

### 📚 详细指南

查看完整的故障排除文档：[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

**包含以下常见问题的解决方案**：
- ❌ 连接被拒绝或无法访问
- 🚫 草稿预览页面无法打开
- ⚠️ ERR_ABORTED 错误（模板渲染失败）
- 🔄 服务启动失败
- 📁 模板和静态文件问题
- 🌐 网络连接问题

### 🆘 紧急求助

如果问题仍未解决：
1. 运行 `./diagnose.sh` 获取诊断信息
2. 查看 [故障排除指南](docs/TROUBLESHOOTING.md)
3. 在 [GitHub Issues](https://github.com/sun-guannan/CapCutAPI/issues) 提交问题

## 进群交流 | Community

🔥 **微信群**: 扫码加入技术交流群

![微信群二维码](https://example.com/wechat-qr.png)

## 合作联系 | Contact

📧 **商务合作**: business@capcutapi.com  
🐛 **问题反馈**: [GitHub Issues](https://github.com/sun-guannan/CapCutAPI/issues)  
📖 **文档更新**: 持续更新中，欢迎贡献

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**

**⭐ If this project helps you, please give it a Star!**
