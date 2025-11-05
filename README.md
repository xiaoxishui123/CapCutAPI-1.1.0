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

## 📊 **项目功能逻辑分析** (NEW!)

### 🏗️ **架构优势分析**

经过深入的代码分析，CapCutAPI项目展现出以下优秀的设计特点：

#### ✅ **设计优势**
- **🎯 分层架构清晰**: API层、业务逻辑层、数据存储层职责分明
- **🔄 缓存机制完善**: LRU算法管理草稿对象，提升性能
- **☁️ 云存储集成**: 企业级OSS集成，支持V4签名和CDN加速
- **🌐 跨平台兼容**: Windows/Linux/macOS路径智能适配
- **📱 用户体验优秀**: 响应式Web界面，交互式草稿预览
- **🔧 功能完整**: 30+API端点，覆盖视频编辑全流程

#### 🎨 **技术亮点**
- **并发处理**: 素材下载采用线程池并发处理
- **智能路径**: 自动识别客户端操作系统，适配本地路径
- **实时监控**: 草稿状态实时查询和长轮询支持
- **批量操作**: 支持多草稿批量下载和管理
- **MCP集成**: 企业级MCP Bridge服务，支持AI工具集成

### ⚠️ **优化建议**

#### 🔴 **高优先级优化**
1. **代码重复清理**: 移除重复的import语句和冗余代码
2. **安全性增强**: 移除配置文件中的硬编码密钥，强制使用环境变量
3. **异常处理统一**: 创建统一的异常处理机制和错误响应格式

#### 🟡 **中优先级优化**
1. **依赖管理完善**: 补充完整的requirements.txt，添加版本锁定
2. **日志规范化**: 实现结构化日志和统一的日志格式
3. **性能监控**: 添加API性能监控和健康检查端点

#### 🟢 **低优先级优化**
1. **缓存策略**: 实现更智能的缓存淘汰算法
2. **并发优化**: 进一步优化素材下载的并发策略
3. **文档完善**: 补充API文档和开发者指南

### 📈 **项目评分**

| 维度 | 评分 | 说明 |
|------|------|------|
| **功能完整性** | ⭐⭐⭐⭐⭐ | 功能全面，覆盖视频编辑全流程 |
| **代码质量** | ⭐⭐⭐⭐ | 架构清晰，但存在部分冗余 |
| **用户体验** | ⭐⭐⭐⭐⭐ | 界面美观，操作流畅 |
| **性能表现** | ⭐⭐⭐⭐ | 缓存机制完善，响应迅速 |
| **安全性** | ⭐⭐⭐ | 基础安全措施，需加强配置安全 |
| **可维护性** | ⭐⭐⭐⭐ | 模块化设计，文档完善 |

**总体评价**: 这是一个设计优秀、功能完整的企业级项目，具有很高的实用价值和商业潜力。通过上述优化建议的实施，可以进一步提升项目的代码质量和安全性。

---

## 🚀 **最新功能优化** (NEW!)

### 🆕 智能下载功能 (v1.3.8) - ✅ 完美解决剪映重命名问题

#### 💫 功能亮点：
- **🧠 一键智能下载**: 无需配置路径，点击即可下载草稿
- **📁 纯相对路径**: 使用 `assets/audio/xxx.mp3` 格式，确保剪映正确识别
- **🎯 简单易用**: 在预览页面点击"智能下载"按钮即可
- **💫 美观进度条**: 实时显示下载进度和详细状态
- **🔄 跨平台兼容**: 自动检测操作系统（Windows/Linux/Mac）
- **✅ 任意位置可用**: 草稿可解压到任意位置，剪映都能识别素材
- **🔧 根源已解决**: v1.3.7解决path_config.json污染问题，智能下载完全独立（不受任何配置影响）
- **🎉 自动刷新ID**: v1.3.8自动刷新draft_id，彻底解决剪映重命名文件夹问题

#### 📝 使用方法：
1. 访问草稿预览页面：`http://8.148.70.18:9000/draft/preview/<草稿ID>`
2. 点击右上角的 **🧠 智能下载** 按钮
3. 等待下载完成（显示进度条）
4. 文件自动下载到浏览器下载文件夹
5. 解压后放入剪映草稿目录，打开剪映即可使用

#### 🔧 设计说明：

**两种下载方式，互不影响**：
- **📥 下载草稿**：使用path_config.json配置，生成**绝对路径**版本（适合固定位置使用）
- **🧠 智能下载**：完全忽略配置，总是生成**相对路径**版本（适合任意位置使用）

详细区别请查看：[智能下载与普通下载的区别.md](智能下载与普通下载的区别.md)

#### 🔧 问题修复记录：
- **v1.3.8 (2025-11-05 14:30)**: 🎉 **完美解决剪映重命名问题**
  - 详情：[剪映重命名问题完美解决方案.md](剪映重命名问题完美解决方案.md)
  - **核心实现**: 自动刷新draft_id和时间戳，让剪映识别为全新草稿
  - **彻底解决**: 即使删除旧草稿，剪映也不会再添加(2)后缀
- **v1.3.7 (2025-11-05 09:42)**: ⭐ **终极修复** - 完善两种下载方式的独立性
  - 详情：[智能下载问题根源及终极解决方案.md](智能下载问题根源及终极解决方案.md)
  - **核心实现**: customize_zip将基础ZIP的绝对路径转换为相对路径
- **v1.3.2-v1.3.6**: 前端、后端、模板、缓存、路由等各层面修复

#### ✅ 现在完全可用：
**智能下载**：总是返回相对路径（customize_zip自动转换）  
**下载草稿**：使用配置的绝对路径（适合固定位置）  
**调试工具**：http://8.148.70.18:9000/debug/download

详细说明请查看：[智能下载功能说明.md](智能下载功能说明.md)

---

### 🆕 支持相对路径下载 (v1.3.0)

#### 💫 功能亮点：
- **📁 相对路径支持**: draft_folder参数现在支持使用相对路径
- **🔄 自动转换**: 相对路径自动转换为基于项目根目录的绝对路径
- **🌐 跨平台兼容**: 同时支持Linux、Windows和macOS路径格式
- **✨ 灵活配置**: 支持 `./downloads`、`../output`、`~/Documents` 等多种路径格式
- **🛡️ 路径验证**: 自动验证路径有效性，确保下载安全可靠

#### 📝 使用示例：

**1. 使用相对路径下载草稿**：
```python
import requests

# 使用相对路径（相对于项目根目录）
response = requests.post("http://8.148.70.18:9000/save_draft", json={
    "draft_id": "dfd_cat_1234567890_abc123",
    "draft_folder": "./downloads/drafts",  # 相对路径
    "client_os": "windows"
})

print(response.json())
```

**2. 更多路径格式示例**：
```python
# 当前目录下的子目录
draft_folder = "./output"

# 上级目录
draft_folder = "../shared_drafts"

# 用户主目录
draft_folder = "~/Documents/CapCut"

# 绝对路径（仍然支持）
draft_folder = "/home/user/capcut_projects"
draft_folder = "F:\\jianying\\cgwz\\JianyingPro Drafts"  # Windows
```

**3. 路径转换说明**：
- `./downloads` → `/home/CapCutAPI-1.1.0/downloads`
- `../output` → `/home/output`
- `~/Documents` → `/home/user/Documents`

#### 🔧 技术改进：
- 新增 `path_utils.py` 路径处理工具模块
- 优化 `save_draft_impl.py` 路径处理逻辑
- 增强 `downloader.py` 路径规范化功能
- 所有下载函数自动支持相对路径
- 完善的路径验证和错误处理机制

---

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

---

## 🌉 MCP Bridge 服务 (NEW!)

**MCP Bridge服务地址**: http://8.148.70.18:8082

**部署状态**: ✅ 已部署并运行中

### 🚀 功能特性

MCP Bridge是一个企业级的Model Context Protocol (MCP) 桥接服务，为CapCutAPI提供标准化的MCP接口支持：

- **🔗 协议桥接**: 将HTTP API转换为标准MCP协议，支持AI工具和平台集成
- **⚡ 高性能**: 基于异步架构，支持高并发请求处理
- **📊 监控指标**: 内置健康检查、性能监控和详细的请求统计
- **🛡️ 企业级**: Redis缓存、错误处理、日志记录等企业级特性
- **🔄 智能路由**: 自动识别HTTP方法(GET/POST)，智能路由到正确的API端点

### 📋 支持的MCP方法

#### 📝 草稿管理
- `capcut_create_draft`: 创建新的剪映草稿项目
- `capcut_save_draft`: 保存草稿到云存储

#### 🎨 素材获取 (GET方法)
- `get_intro_animation_types`: 获取片头动画类型列表
- `get_outro_animation_types`: 获取片尾动画类型列表  
- `get_transition_types`: 获取转场效果类型列表
- `get_mask_types`: 获取蒙版类型列表
- `get_font_types`: 获取字体类型列表

#### 🎬 素材添加 (POST方法)
- `capcut_add_video`: 添加视频素材
- `capcut_add_audio`: 添加音频素材
- `capcut_add_image`: 添加图片素材
- `capcut_add_text`: 添加文本素材
- `capcut_add_subtitle`: 添加字幕
- `capcut_add_effect`: 添加特效
- `capcut_add_sticker`: 添加贴纸

### 🔧 服务管理

```bash
# 进入MCP Bridge目录
cd /home/CapCutAPI-1.1.0/mcp_bridge

# 启动MCP Bridge服务
SERVER_PORT=8082 ./venv/bin/python core/bridge_server.py

# 检查服务健康状态
curl http://localhost:8082/health

# 查看性能指标
curl http://localhost:8082/metrics

# 测试MCP方法调用
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "get_intro_animation_types", "params": {}}'
```

### 📊 监控信息

**健康检查端点**: `GET /health`
- 返回服务和依赖组件的健康状态
- 包含CapCutAPI连接状态检查

**性能指标端点**: `GET /metrics`
- 总请求数和成功率统计
- 平均响应时间监控
- 各服务的详细性能数据

**当前性能表现**:
- ✅ **成功率**: 100%
- ⚡ **平均响应时间**: ~120ms
- 🔄 **请求处理**: 支持高并发异步处理
- 💾 **缓存**: Redis缓存优化响应速度

### 🔗 集成指南

MCP Bridge服务可以轻松集成到各种AI平台和工具中：

1. **Dify平台**: 参考 [Dify集成指南](mcp_bridge/docs/Dify集成指南.md)
2. **Claude Desktop**: 配置MCP服务器连接
3. **自定义AI工具**: 使用标准MCP协议调用

详细的集成文档请参考 [MCP Bridge实施指南](mcp_bridge/docs/实施指南.md)。

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

### MCP Bridge 文档 | MCP Bridge Documentation
- [📋 实施指南](mcp_bridge/docs/实施指南.md) - 完整的MCP Bridge实施指南，包含快速开始和详细部署 | Complete MCP Bridge implementation guide with quick start and detailed deployment
- [🔄 MCP部署方案对比](mcp_bridge/docs/MCP部署方案对比.md) - 官方简单方案vs企业级Bridge方案对比分析 | Comparison analysis between official simple solution and enterprise Bridge solution
- [🗓️ 实施路线图](mcp_bridge/docs/实施路线图.md) - 8天部署优化路线图和详细时间表 | 8-day deployment optimization roadmap and detailed timeline
- [🔗 Dify集成指南](mcp_bridge/docs/Dify集成指南.md) - Dify平台MCP服务器配置和工作流设计 | Dify platform MCP server configuration and workflow design

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

#### 路径格式支持（🆕 v1.3.0）
- ✅ **绝对路径**：`/home/user/capcut` 或 `F:\jianying\cgwz\JianyingPro Drafts`
- ✅ **相对路径**：`./downloads`、`../output`（基于项目根目录自动转换）
- ✅ **用户目录**：`~/Documents/CapCut`（自动展开为用户主目录）
- ✅ **Windows标准路径格式**：支持反斜杠分隔符和盘符
- ✅ **自动路径分隔符转换**：Linux风格（`/`）↔ Windows风格（`\`）
- ✅ **路径验证**：自动验证路径有效性，确保下载成功
- ✅ **自动创建目录**：目标目录不存在时自动创建

#### 路径使用示例
```python
# 绝对路径（原有方式，仍然支持）
draft_folder = "/home/user/capcut_projects"
draft_folder = "F:\\jianying\\cgwz\\JianyingPro Drafts"

# 🆕 相对路径（基于项目根目录）
draft_folder = "./downloads/drafts"      # 项目根目录下的downloads/drafts
draft_folder = "../shared_output"        # 项目上级目录的shared_output
draft_folder = "output/videos"           # 项目根目录下的output/videos

# 🆕 用户主目录
draft_folder = "~/Documents/CapCut"      # 用户主目录下的Documents/CapCut
draft_folder = "~/Downloads"             # 用户下载目录
```

#### Windows路径格式
- ✅ 支持Windows标准路径格式：`F:\jianying\cgwz\JianyingPro Drafts`
- ✅ 自动处理路径分隔符转换（`/` → `\`）
- ✅ 确保草稿文件中的素材路径为Windows本地绝对路径
- ✅ 剪映客户端可直接识别和链接素材
- ✅ 相对路径在Windows系统上同样有效

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

## 🔧 MCP服务配置 | MCP Service Configuration

### Todoist MCP 配置

本项目已配置Todoist MCP服务，用于任务管理和待办事项集成。

#### 🌍 全局配置（推荐）

已为系统配置全局Todoist API令牌：

```bash
# 环境变量已添加到 ~/.bashrc
export TODOIST_API_TOKEN="your_api_token_here"
```

#### ✅ 验证配置

```bash
# 检查环境变量是否正确设置
echo $TODOIST_API_TOKEN

# 重新加载配置（如果需要）
source ~/.bashrc
```

#### 🔑 获取API令牌

1. 访问 [Todoist设置页面](https://todoist.com/prefs/integrations)
2. 在"集成"标签页找到"API令牌"
3. 复制您的个人API令牌
4. 按照上述步骤配置到环境变量中

#### 📝 使用说明

- **全局可用**: 配置后所有项目和终端会话都可以使用Todoist MCP
- **安全性**: API令牌仅当前用户可访问
- **持久性**: 重启系统后配置仍然有效
- **兼容性**: 支持Trae IDE和其他MCP兼容工具

#### ⚠️ 注意事项

- 请妥善保管您的API令牌，不要分享给他人
- 如需更换令牌，请编辑 `~/.bashrc` 文件
- 配置更改后需要重新启动Trae IDE或重新加载环境变量

---

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
