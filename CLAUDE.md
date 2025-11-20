# CapCutAPI 项目文档

> 本文档由 AI 架构师自动生成和维护，最后更新时间：2025-11-20 09:44:24

## 变更记录 (Changelog)

### 2025-11-20 09:44:24（增量更新 - 新增 services 模块）
- 新增 services 业务逻辑层模块文档
- 更新模块结构图，添加 services 模块节点
- 更新模块索引表，包含 services 模块信息
- 更新主要分层说明，补充服务层架构
- 更新覆盖率报告（模块文档覆盖率 12/12）
- 优化架构总览，补充新架构模块导入说明

### 2025-11-13 22:14:06（验证性扫描）
- 执行全面架构验证和覆盖率确认
- 验证所有 11 个模块文档的完整性和准确性
- 确认项目结构与文档一致性（100% 匹配）
- 更新文件统计信息（36 个根目录 Python 文件，17 个文档文件）
- 确认模块结构图和索引表的准确性
- 验证导航面包屑和模块间链接的可用性
- 生成最新覆盖率报告（模块文档覆盖率 100%）
- 更新 index.json 时间戳和扫描记录

### 2025-11-11 22:43:46（增量更新）
- 新增 static 静态资源模块文档
- 新增 tools 工具脚本模块文档
- 新增 examples 使用示例模块文档
- 更新模块结构图，补充完整的模块树
- 更新模块索引表，包含所有 11 个模块
- 更新覆盖率报告（100% 模块文档覆盖）
- 优化导航面包屑和模块间链接

### 2025-11-11 22:20:59
- 全面更新项目架构分析和模块清点
- 优化模块结构图（Mermaid），添加更多子模块
- 新增 pattern 模板库模块文档
- 新增 settings 配置模块文档
- 新增 docs 文档模块文档
- 完善模块索引表格，补充更多模块信息
- 生成完整的覆盖率报告和文件统计

### 2025-11-11 10:35:57
- 初始化项目 AI 上下文文档
- 完成全仓架构分析和模块清点
- 生成根级与模块级文档结构

---

## 项目愿景

CapCutAPI 是一个轻量、灵活、易上手的剪映/CapCut API 工具，旨在构建全自动化视频剪辑/混剪流水线。项目提供 HTTP API 接口，支持远程调用和自动化处理，集成多种 AI 服务，适用于企业级视频内容生产场景。

**核心价值**：
- 提供标准化的剪映草稿创建和编辑 API
- 支持视频、音频、文本、图片、特效等多种素材的自动化添加
- 云端存储和跨平台兼容（Windows、Linux、macOS）
- 企业级 MCP Bridge 服务，支持 AI 工作流集成
- 可复用的视频编辑模板库（Pattern）
- 分层架构设计，业务逻辑与 Web 框架解耦（v1.2.0+）

---

## 架构总览

CapCutAPI 采用分层架构设计，核心由以下部分组成：

### 技术栈
- **语言**: Python 3.9+
- **Web 框架**: Flask（主服务）、FastAPI（MCP Bridge）
- **数据库**: SQLite (capcut.db, drafts.db)
- **云存储**: 阿里云 OSS
- **依赖库**: pyJianYingDraft（草稿处理核心）、imageio、oss2、requests
- **MCP 协议**: WebSocket + JSON-RPC 2.0
- **容器化**: Docker + Docker Compose

### 主要分层
1. **API 层** (`capcut_server.py`): Flask Web 服务，提供 50+ REST API 端点
2. **服务层** (`services/`): 业务逻辑封装，提供可复用的服务类（v1.2.0+）
3. **业务逻辑层**: 草稿创建、素材添加、特效处理、路径适配等实现模块
4. **数据层**: SQLite 数据库、草稿缓存（LRU）、OSS 云存储
5. **核心库层** (`pyJianYingDraft/`): 剪映草稿文件格式处理、元数据管理
6. **MCP 桥接层** (`mcp_bridge/`): 企业级 MCP 协议桥接服务
7. **模板层** (`pattern/`): 可复用的视频编辑模板库
8. **配置层** (`settings/`): 统一配置管理（环境变量+JSON）

---

## 模块结构图

```mermaid
graph TD
    A["(根) CapCutAPI-1.1.0"] --> B["pyJianYingDraft/"];
    A --> C["mcp_bridge/"];
    A --> D["templates/"];
    A --> E["static/"];
    A --> F["docs/"];
    A --> G["settings/"];
    A --> H["pattern/"];
    A --> I["tools/"];
    A --> J["examples/"];
    A --> K["services/"];

    B --> B1["metadata/ - 元数据定义"];
    B --> B2["核心草稿处理模块"];

    C --> C1["core/ - MCP核心服务"];
    C --> C2["integrations/ - Dify集成"];
    C --> C3["workflows/ - 工作流管理"];
    C --> C4["tests/ - 测试套件"];
    C --> C5["scripts/ - 管理脚本"];

    F --> F1["部署文档"];
    F --> F2["API 文档"];
    F --> F3["故障排除"];

    H --> H1["视频编辑模板"];
    H --> H2["模板管理API"];

    K --> K1["download_service.py - 下载服务"];
    K --> K2["业务逻辑封装"];

    click B "./pyJianYingDraft/CLAUDE.md" "查看 pyJianYingDraft 模块文档"
    click C "./mcp_bridge/CLAUDE.md" "查看 mcp_bridge 模块文档"
    click D "./templates/CLAUDE.md" "查看 templates 模块文档"
    click E "./static/CLAUDE.md" "查看 static 模块文档"
    click F "./docs/CLAUDE.md" "查看 docs 模块文档"
    click G "./settings/CLAUDE.md" "查看 settings 模块文档"
    click H "./pattern/CLAUDE.md" "查看 pattern 模块文档"
    click I "./tools/CLAUDE.md" "查看 tools 模块文档"
    click J "./examples/CLAUDE.md" "查看 examples 模块文档"
    click K "./services/CLAUDE.md" "查看 services 模块文档"
```

---

## 模块索引

| 模块路径 | 职责描述 | 入口文件 | 状态 |
|---------|---------|---------|------|
| `/` (根) | Flask API 服务主入口，路由定义 | `capcut_server.py` | ✅ 核心 |
| `services/` | 业务逻辑层（下载、管理等服务）| `__init__.py` | ✅ 核心（v1.2.0+） |
| `pyJianYingDraft/` | 剪映草稿文件格式处理核心库 | `__init__.py` | ✅ 核心 |
| `pyJianYingDraft/metadata/` | 特效、字体、动画等元数据定义 | `__init__.py` | ✅ 核心 |
| `mcp_bridge/` | MCP 协议桥接服务（企业级） | `core/bridge_server.py` | ✅ 核心 |
| `mcp_bridge/core/` | MCP 服务核心：路由、缓存、监控 | `capcut_mcp_server.py` | ✅ 核心 |
| `mcp_bridge/integrations/` | Dify 等平台的 MCP 集成适配器 | `dify_workflow_integration.py` | ✅ 扩展 |
| `mcp_bridge/workflows/` | 工作流管理和验证 | `workflow_manager.py` | ✅ 扩展 |
| `templates/` | Flask HTML 模板（预览、仪表板） | `index.html` | ✅ 前端 |
| `static/` | 静态资源（独立工具、辅助脚本） | `download_manager.html` | ✅ 前端 |
| `docs/` | 项目文档（部署、API、故障排除） | 多个 `.md` 文件 | ✅ 文档 |
| `settings/` | 配置管理模块（环境变量+JSON） | `__init__.py` | ✅ 配置 |
| `pattern/` | 视频编辑模板库（可复用模板） | 多个模板文件 | ✅ 模板 |
| `tools/` | 辅助工具脚本（草稿刷新、维护） | `refresh_draft_id.py` | ✅ 工具 |
| `examples/` | 使用示例（快速入门、最佳实践） | `relative_path_example.py` | ✅ 示例 |

---

## 运行与开发

### 环境要求
- Python 3.9 或更高版本（推荐 `/usr/local/bin/python3.9`）
- FFmpeg（用于视频处理）
- 系统支持 systemd（用于服务管理）
- Redis（可选，用于 MCP Bridge 缓存）
- Docker（可选，用于容器化部署）

### 快速启动

#### 方式 1：使用管理脚本（推荐）
```bash
./service_manager.sh start      # 启动服务
./service_manager.sh status     # 查看状态
./service_manager.sh logs       # 查看日志
./service_manager.sh test       # 测试服务
./service_manager.sh restart    # 重启服务
./service_manager.sh stop       # 停止服务
```

#### 方式 2：使用 systemd
```bash
sudo systemctl start capcutapi.service
sudo systemctl status capcutapi.service
tail -f logs/capcutapi.log
```

#### 方式 3：直接运行（开发）
```bash
# 安装依赖
pip install -r requirements.txt

# 配置文件
cp config.json.example config.json
vim config.json  # 编辑配置（端口、OSS 等）

# 启动服务
python capcut_server.py
```

#### 方式 4：Docker 部署
```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d

# 详见 DOCKER_DEPLOY.md
```

### 主要 API 端点
| 端点 | 方法 | 说明 |
|------|------|------|
| `/create_draft` | POST | 创建新草稿 |
| `/add_video` | POST | 添加视频素材 |
| `/add_audio` | POST | 添加音频素材 |
| `/add_text` | POST | 添加文本素材 |
| `/add_subtitle` | POST | 添加字幕 |
| `/add_effect` | POST | 添加特效 |
| `/add_sticker` | POST | 添加贴纸 |
| `/add_image` | POST | 添加图片素材 |
| `/save_draft` | POST | 保存草稿（本地或云端） |
| `/api/drafts/dashboard` | GET | 草稿管理仪表板 |
| `/draft/preview/<draft_id>` | GET | 草稿预览页面 |
| `/api/patterns/list` | GET | 列出所有视频编辑模板 |
| `/api/patterns/get/<id>` | GET | 获取模板详情和内容 |
| `/api/patterns/download/<id>` | GET | 下载模板文件 |
| `/api/v2/drafts/<draft_id>/download/url` | POST | 生成下载链接（v2）|
| `/api/v2/drafts/<draft_id>/download/stream` | GET | 流式下载（v2）|

*完整 API 列表（50+ 端点）参见 [API_USAGE_EXAMPLES.md](docs/API_USAGE_EXAMPLES.md)*

### MCP Bridge 服务
```bash
# 进入 MCP Bridge 目录
cd mcp_bridge

# 启动 MCP Bridge 服务（端口 8082）
SERVER_PORT=8082 ./venv/bin/python core/bridge_server.py

# 健康检查
curl http://localhost:8082/health

# 性能指标
curl http://localhost:8082/metrics
```

---

## 测试策略

### 测试文件分布
- **单元测试**: `test_api.py`, `test_template.py`, `test_pattern_api.py`, `test_oss_config.py`
- **端到端测试**: `test_e2e.py`
- **API v2 测试**: `test_api_v2.py`, `benchmark_api.py`
- **MCP Bridge 测试**:
  - 单元: `mcp_bridge/tests/unit/test_units.py`
  - 集成: `mcp_bridge/tests/integration/test_integration.py`
  - 性能: `mcp_bridge/tests/performance/test_performance.py`
  - 工作流: `mcp_bridge/tests/workflow/test_workflow_integration.py`

### 运行测试
```bash
# 主服务 API 测试
python test_api.py

# Pattern 模板测试
python test_pattern_api.py

# OSS 配置测试
python test_oss_config.py

# 端到端测试
python test_e2e.py

# API v2 测试
python test_api_v2.py

# MCP Bridge 测试
cd mcp_bridge
pytest tests/
```

### 集成测试
项目提供 `rest_client_test.http` 文件，可使用 VS Code REST Client 插件或 IntelliJ HTTP Client 进行 API 测试。

---

## 编码规范

### 核心约定
1. **Python 版本**: 3.9+，优先使用 `/usr/local/bin/python3.9`
2. **依赖管理**: 所有第三方库记录在 `requirements.txt`
3. **配置文件**: 敏感信息优先使用环境变量（`OSS_*`, `MP4_OSS_*`）
4. **日志规范**: 使用 `logging` 模块，输出到 `logs/capcutapi.log`
5. **错误处理**: 统一返回 JSON 格式错误响应
6. **代码格式**: 遵循 PEP 8 规范，使用 Flake8 进行代码检查
7. **服务层设计**: 业务逻辑优先在 `services/` 模块中实现（v1.2.0+）

### 路径处理规范（重要）
- **支持相对路径**: `./downloads`, `../output`, `~/Documents`（v1.3.0+）
- **跨平台适配**: 自动识别并转换 Windows (`\`) 和 Linux (`/`) 路径分隔符
- **路径优先级**:
  1. API 参数 `draft_folder`
  2. 用户自定义路径 (`path_config.json`)
  3. 客户端操作系统默认路径（根据 `client_os` 参数）
  4. 服务器操作系统默认路径

### 草稿保存模式
通过 `config.json` 的 `is_upload_draft` 字段控制：
- `true`: OSS 云存储模式（生产环境）
- `false`: 本地保存模式（开发测试）

---

## AI 使用指引

### 代码修改注意事项
1. **不要修改** `pyJianYingDraft/` 核心库（除非明确需要）
2. **优先扩展** API 路由和实现模块（`add_*_impl.py`, `save_draft_impl.py`）
3. **服务层优先**: 新业务逻辑优先在 `services/` 中实现，避免直接写在路由中
4. **配置安全**: 避免硬编码 OSS 密钥，使用环境变量
5. **路径处理**: 使用 `path_utils.py` 模块的工具函数
6. **模板开发**: 参考 `pattern/` 目录下的示例，创建可复用模板

### 常见开发任务
- **新增 API 端点**: 在 `capcut_server.py` 添加 `@app.route` 路由
- **新增服务类**: 在 `services/` 目录下创建新的服务模块
- **新增素材类型**: 参考 `add_video_impl.py` 创建对应实现文件
- **修改草稿逻辑**: 编辑 `create_draft.py` 或 `save_draft_impl.py`
- **新增特效元数据**: 在 `pyJianYingDraft/metadata/` 下添加相应定义
- **创建模板**: 在 `pattern/` 目录下添加新的模板脚本
- **新增工具**: 在 `tools/` 目录下添加维护脚本
- **新增示例**: 在 `examples/` 目录下添加使用示例

### 部署与维护
- **部署文档**: [docs/CapCutAPI部署总结.md](docs/CapCutAPI部署总结.md)
- **Docker 部署**: [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md)
- **故障排除**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **API 示例**: [docs/API_USAGE_EXAMPLES.md](docs/API_USAGE_EXAMPLES.md)
- **API v2 迁移**: [docs/API_V1_TO_V2_MIGRATION.md](docs/API_V1_TO_V2_MIGRATION.md)
- **MCP 集成**: [mcp_bridge/docs/实施指南.md](mcp_bridge/docs/实施指南.md)

### 调试技巧
```bash
# 查看实时日志
tail -f logs/capcutapi.log

# 查看草稿缓存
curl http://localhost:9000/debug/cache/<draft_id>

# 查看草稿列表
curl http://localhost:9000/api/drafts/list

# 测试路径配置
curl http://localhost:9000/api/os/info

# 查看所有模板
curl http://localhost:9000/api/patterns/list

# 健康检查
curl http://localhost:9000/health

# 测试下载服务（v2）
curl -X POST http://localhost:9000/api/v2/drafts/<draft_id>/download/url
```

---

## 相关文档索引

### 核心文档
- [需求文档](docs/REQUIREMENTS_DOCUMENT.md)
- [操作手册](docs/OPERATION_MANUAL.md)
- [API 使用示例](docs/API_USAGE_EXAMPLES.md)
- [API v1 到 v2 迁移指南](docs/API_V1_TO_V2_MIGRATION.md)
- [故障排除指南](docs/TROUBLESHOOTING.md)
- [快速使用指南](docs/CapCutAPI_快速使用指南.md)

### 部署文档
- [部署总结](docs/CapCutAPI部署总结.md)
- [Docker 部署指南](DOCKER_DEPLOY.md)
- [技术架构](docs/CLAUDE.md)
- [数据流分析](docs/CapCutAPI_数据流分析文档.md)
- [跨平台兼容性](docs/CapCutAPI_跨平台素材识别问题解决方案.md)

### MCP 文档
- **⭐ [MCP 快速入门](MCP_QUICK_START.md)** - 5分钟上手简化版 MCP (推荐新手)
- **⭐ [MCP 版本对比](docs/MCP_VERSION_COMPARISON.md)** - 简化版 vs 企业版详细对比
- [实施指南](mcp_bridge/docs/实施指南.md) - 企业版完整部署指南
- [Dify 集成指南](mcp_bridge/docs/Dify集成指南.md) - Dify 平台集成
- [部署方案对比](mcp_bridge/docs/MCP部署方案对比.md) - 多种部署方案对比
- [实施路线图](mcp_bridge/docs/实施路线图.md) - 8天部署路线图

### Pattern 模板库
- **⭐ [Pattern 快速开始](pattern/QUICK_START.md)** - 5分钟使用视频模板
- [Pattern 集成报告](docs/PATTERN_INTEGRATION_REPORT.md) - 完整集成报告

### 使用示例
- **⭐ [相对路径示例](examples/relative_path_example.py)** - 跨平台路径处理
- **⭐ [装饰器使用示例](examples/decorators_usage_example.py)** - 装饰器使用（v1.2.0+）
- [examples 模块文档](examples/CLAUDE.md) - 更多使用示例

### 工具脚本
- [草稿 ID 刷新工具](tools/refresh_draft_id.py) - 修复草稿 ID 冲突
- [tools 模块文档](tools/CLAUDE.md) - 工具脚本说明

### 功能实施与优化文档
- [架构分析与优化建议](docs/ARCHITECTURE_ANALYSIS.md)
- [功能优化总结](docs/FEATURE_OPTIMIZATION_SUMMARY.md)
- [OSS 配置诊断](docs/OSS_CONFIG_DIAGNOSTIC.md)
- [输入验证功能](docs/INPUT_VALIDATION_SUMMARY.md)
- [日志系统与健康检查](docs/LOGGING_HEALTH_CHECK_SUMMARY.md)
- [Validators 使用指南](docs/VALIDATORS_GUIDE.md)
- [异步保存最佳实践](docs/ASYNC_SAVE_BEST_PRACTICES.md)

### 下载功能文档
- [下载 API 优化总结](docs/DOWNLOAD_API_OPTIMIZATION_FINAL.md)
- [V2 API 实施报告](docs/STAGE4_V2_API_REPORT.md)
- [Failed to Fetch 错误修复](docs/DOWNLOAD_FAILED_TO_FETCH_FIX.md)
- [下载进度条日志功能](docs/DOWNLOAD_PROGRESS_LOG_GUIDE.md)

---

**提示**: 本文档是项目的"地图"，帮助开发者和 AI 快速定位信息。详细的模块文档请查看各模块目录下的 `CLAUDE.md` 文件。
