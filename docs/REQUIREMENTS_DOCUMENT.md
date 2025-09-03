# CapCutAPI 需求文档

## 📋 项目概述

### 项目名称
CapCutAPI - 开源剪映API工具

### 项目版本
v1.2.0 Enhanced Edition

### 项目目标
提供一个功能完整、易于使用的剪映API服务，支持草稿创建、素材管理、效果应用、批量处理和云端存储等核心功能，为开发者和内容创作者提供强大的视频编辑自动化解决方案。

### 目标用户
- 视频内容创作者
- 自动化视频生成开发者
- 批量视频处理需求的企业用户
- AI视频生成应用开发者

## 🎯 核心功能需求

### 1. 草稿管理功能

#### 1.0 草稿查询与状态管理
- **需求描述**: 提供草稿查询和状态监控功能
- **功能规格**:
  - 支持草稿内容查询 (`POST /query_script`)
  - 支持草稿状态查询 (`POST /query_draft_status`)
  - 支持长轮询状态监控 (`GET /api/draft/long_poll_status`)
  - 支持草稿编辑功能 (`GET /api/drafts/edit/<draft_id>`)
  - 支持草稿删除功能 (`DELETE /api/drafts/delete/<draft_id>`)
- **优先级**: 高

#### 1.1 草稿创建与编辑
- **需求描述**: 支持创建新的剪映草稿，设置基本参数
- **功能规格**:
  - 支持自定义草稿ID
  - 支持设置视频分辨率（宽度、高度）
  - 支持多种视频比例（9:16, 16:9, 1:1等）
  - 自动生成草稿元数据
- **API端点**: `POST /create_draft`
- **优先级**: 高

#### 1.2 草稿保存与存储
- **需求描述**: 支持将草稿保存到本地或云端存储
- **功能规格**:
  - 本地保存模式：保存到指定目录
  - 云端保存模式：自动上传到阿里云OSS
  - 支持草稿压缩打包
  - 自动清理临时文件
- **API端点**: `POST /save_draft`
- **优先级**: 高

#### 1.3 草稿列表与查询
- **需求描述**: 提供草稿列表查询和管理功能
- **功能规格**:
  - 扫描本地和云端草稿
  - 显示草稿元数据（创建时间、大小、素材数量等）
  - 支持按ID搜索草稿
  - 支持草稿状态分类
- **API端点**: `GET /api/drafts/list`
- **优先级**: 中

### 2. 素材管理功能

#### 2.1 视频素材处理
- **需求描述**: 支持添加和编辑视频素材
- **功能规格**:
  - 支持多种视频格式（MP4, MOV, AVI等）
  - 支持视频裁剪（开始时间、结束时间）
  - 支持视频缩放和位置调整
  - 支持播放速度调整
  - 支持音量控制
  - 支持转场效果添加
  - 支持蒙版效果（矩形、圆形等）
  - 支持背景模糊效果
  - 支持关键帧动画 (`POST /add_video_keyframe`)
- **API端点**: `POST /add_video`
- **优先级**: 高

#### 2.2 音频素材处理
- **需求描述**: 支持添加和编辑音频素材
- **功能规格**:
  - 支持多种音频格式（MP3, WAV, AAC等）
  - 支持音频裁剪
  - 支持音量调整
  - 支持音频淡入淡出效果
- **API端点**: `POST /add_audio`
- **优先级**: 高

#### 2.3 图片素材处理
- **需求描述**: 支持添加和编辑图片素材
- **功能规格**:
  - 支持多种图片格式（JPG, PNG, GIF等）
  - 支持图片缩放和位置调整
  - 支持显示时长设置
  - 支持图片动画效果
- **API端点**: `POST /add_image`
- **优先级**: 中

#### 2.4 文本素材处理
- **需求描述**: 支持添加和编辑文本素材
- **功能规格**:
  - 支持自定义文本内容
  - 支持字体选择和大小调整
  - 支持文本颜色和样式设置
  - 支持文本位置和动画
  - 支持文本描边和阴影效果
- **API端点**: `POST /add_text`
- **优先级**: 高

#### 2.5 字幕功能
- **需求描述**: 支持添加和编辑字幕
- **功能规格**:
  - 支持字幕文本设置
  - 支持字幕样式自定义
  - 支持字幕时间轴控制
  - 支持多语言字幕
- **API端点**: `POST /add_subtitle`
- **优先级**: 中

#### 2.6 贴纸素材处理
- **需求描述**: 支持添加和编辑贴纸素材
- **功能规格**:
  - 支持贴纸位置和大小调整
  - 支持贴纸动画效果
  - 支持贴纸时长控制
- **API端点**: `POST /add_sticker`
- **优先级**: 中

### 3. 特效与动画功能

#### 3.1 转场效果
- **需求描述**: 支持添加视频转场效果
- **功能规格**:
  - 提供多种转场类型（淡入淡出、滑动、缩放等）
  - 支持转场时长调整
  - 支持自定义转场参数
  - 支持CapCut转场效果
- **API端点**: `POST /add_effect`, `GET /api/transition/types`, `GET /api/capcut/transition/types`
- **优先级**: 中

#### 3.2 动画效果
- **需求描述**: 支持为素材添加动画效果
- **功能规格**:
  - 入场动画（从无到有的动画）
  - 出场动画（从有到无的动画）
  - 循环动画（持续播放的动画）
  - 组合动画效果
  - 文本动画（入场、出场、循环）
  - CapCut动画效果支持
  - 自定义动画参数
- **API端点**: 
  - 标准动画: `GET /api/animation/intro`, `GET /api/animation/outro`, `GET /api/animation/group`
  - CapCut动画: `GET /api/capcut/animation/intro`, `GET /api/capcut/animation/outro`, `GET /api/capcut/animation/group`
  - 文本动画: `GET /api/text/animation/intro`, `GET /api/text/animation/outro`, `GET /api/text/animation/loop`
  - CapCut文本动画: `GET /api/capcut/text/animation/intro`, `GET /api/capcut/text/animation/outro`, `GET /api/capcut/text/animation/loop`
- **优先级**: 中

#### 3.3 滤镜和遮罩
- **需求描述**: 支持添加视觉滤镜和遮罩效果
- **功能规格**:
  - 多种滤镜效果（美颜、复古、黑白等）
  - 遮罩形状选择（圆形、方形、自定义等）
  - 效果强度调整
  - CapCut遮罩效果支持
- **API端点**: `GET /api/mask/types`, `GET /api/capcut/mask/types`
- **优先级**: 低

#### 3.4 视频和音频特效
- **需求描述**: 支持添加视频和音频特效
- **功能规格**:
  - 视频场景特效和角色特效
  - 音频音调、场景、语音特效
  - CapCut特效库支持
  - 特效参数自定义
- **API端点**: 
  - 视频特效: `GET /api/video/scene/effects`, `GET /api/video/character/effects`
  - CapCut视频特效: `GET /api/capcut/video/scene/effects`, `GET /api/capcut/video/character/effects`
  - 音频特效: `GET /api/audio/tone/effects`, `GET /api/audio/scene/effects`, `GET /api/audio/speech/effects`
  - CapCut音频特效: `GET /api/capcut/audio/voice/filters`, `GET /api/capcut/audio/characters`, `GET /api/capcut/audio/speech`
- **优先级**: 中

#### 3.5 字体管理
- **需求描述**: 支持字体类型查询和管理
- **功能规格**:
  - 系统字体列表获取
  - 自定义字体支持
  - 字体预览功能
- **API端点**: `GET /api/font/types`
- **优先级**: 低

### 4. 用户界面功能

#### 4.1 草稿管理仪表板
- **需求描述**: 提供可视化的草稿管理界面
- **功能规格**:
  - 草稿列表展示：显示所有草稿的基本信息（名称、状态、创建时间、更新时间、文件大小、素材数量等）
  - 草稿搜索和过滤：支持按名称实时搜索过滤草稿
  - 草稿操作：支持新建、查看、预览、下载、删除草稿
  - 状态管理：实时显示草稿的处理状态（草稿、处理中、活跃、错误等），使用不同颜色标识
  - 统计信息：显示草稿总数、各状态草稿数量等统计数据
  - 响应式设计：支持桌面和移动设备访问
- **技术实现**:
  - 前端：`templates/dashboard.html` - 完整的HTML + CSS + JavaScript实现
  - 样式设计：现代化卡片布局，深色主题，响应式网格设计
  - 交互功能：实时搜索、状态过滤、操作按钮、错误处理
  - 后端：Flask路由处理，SQLite数据库存储
  - 数据格式化：时间戳格式化、文件大小格式化、HTML转义
- **访问路径**: 通过主页面的"打开草稿管理"按钮访问 `/api/drafts/dashboard`
- **已实现功能**:
  - ✅ 完整的草稿管理界面（dashboard.html）
  - ✅ 草稿列表API（/api/drafts/list）
  - ✅ 草稿删除API（/api/drafts/delete/<draft_id>）
  - ✅ 状态映射和显示
  - ✅ 搜索过滤功能
  - ✅ 响应式设计
  - ✅ 错误处理机制
- **优先级**: 中

#### 4.2 草稿预览界面
- **需求描述**: 提供沉浸式的草稿预览体验
- **功能规格**:
  - 时间轴显示：可视化展示视频、音频、文本、图片等素材在时间轴上的分布和层级关系
  - 素材详情：显示每个素材的详细信息（类型、时长、位置、文件名、大小等）
  - 三栏布局：左侧素材列表、中间时间轴预览、右侧详细信息
  - 深色主题：专业的视频编辑界面风格
  - 响应式设计：适配不同屏幕尺寸，移动端友好
  - 交互功能：点击素材查看详情、时间轴缩放、素材高亮显示
- **技术实现**:
  - 前端：`templates/preview.html` - 完整的HTML + CSS + JavaScript实现
  - 时间轴渲染：CSS绝对定位实现素材块的精确布局
  - 素材分层：不同类型素材分配不同轨道（视频、音频、文本、图片）
  - 数据处理：服务端渲染（SSR）+ 客户端交互
  - 样式设计：现代化界面，深色主题，专业视觉效果
- **访问路径**: `/draft/preview/<draft_id>`
- **已实现功能**:
  - ✅ 完整的预览界面（preview.html）
  - ✅ 时间轴可视化渲染
  - ✅ 素材分层显示（视频、音频、文本、图片等）
  - ✅ 三栏响应式布局
  - ✅ 深色专业主题
  - ✅ 素材详情展示
  - ✅ 服务端渲染优化
  - ✅ 移动端适配
- **优先级**: 中

#### 4.3 草稿下载界面
- **需求描述**: 提供智能化的草稿下载功能
- **功能规格**:
  - 下载方式：支持直接下载和生成下载链接两种方式
  - 状态检查：下载前检查草稿状态，确保草稿可用
  - 错误处理：完善的错误提示和重试机制
  - 批量下载：支持选择多个草稿进行批量下载
  - 进度跟踪：支持长轮询获取下载进度
  - 多平台支持：兼容不同操作系统的文件路径
- **技术实现**:
  - 下载路由：`/draft/downloader` 重定向到具体下载API
  - 文件处理：后端生成下载链接或直接文件流响应
  - 进度跟踪：长轮询机制实现实时进度更新
  - 文件压缩：支持ZIP格式打包下载
  - 路径处理：跨平台文件路径规范化
  - OSS集成：支持云存储文件下载
- **访问路径**: `/draft/downloader?draft_id=<draft_id>`
- **已实现功能**:
  - ✅ 草稿下载路由（/draft/downloader）
  - ✅ 单个草稿下载API
  - ✅ 批量下载功能
  - ✅ 下载进度跟踪
  - ✅ 错误处理机制
  - ✅ 状态检查和验证
  - ✅ 多平台路径支持
  - ✅ OSS云存储集成
- **优先级**: 中

### 5. 批量处理功能

#### 5.1 批量下载
- **需求描述**: 支持一次性下载多个草稿
- **功能规格**:
  - 支持多草稿ID批量处理
  - 并发下载提升效率
  - 详细的成功/失败报告
  - 支持断点续传
  - 下载进度跟踪 (`GET /api/draft/download/progress/<task_id>`)
  - 操作系统路径适配 (`GET /api/os/info`)
  - 自定义下载路径配置 (`POST /api/draft/path/config`)
- **API端点**: `POST /api/drafts/batch-download`, `POST /api/draft/download`, `GET /api/drafts/download/<draft_id>`
- **优先级**: 中

#### 5.2 批量操作
- **需求描述**: 支持对多个草稿进行批量操作
- **功能规格**:
  - 批量删除草稿
  - 批量修改草稿属性
  - 批量导出草稿
- **优先级**: 低

### 6. 云端存储功能

#### 6.1 OSS集成
- **需求描述**: 集成阿里云OSS存储服务
- **功能规格**:
  - 自动上传草稿到OSS
  - 生成可下载的云端URL
  - 支持大文件分片上传
  - 自动清理本地临时文件
  - 草稿镜像到OSS (`POST /mirror_to_oss`)
  - MP4文件上传支持
- **配置项**: `is_upload_draft: true`
- **优先级**: 高

#### 6.2 URL生成
- **需求描述**: 生成草稿的下载链接
- **功能规格**:
  - 标准直链生成
  - 定制化下载链接（按客户端系统）
  - 链接有效期管理
  - 访问权限控制
  - 签名URL安全生成
  - 自定义URL参数支持
- **API端点**: `POST /generate_draft_url`
- **优先级**: 高

### 7. 调试和开发功能

#### 7.1 缓存管理
- **需求描述**: 提供草稿缓存查询和管理功能
- **功能规格**:
  - 草稿缓存数据查询
  - 缓存状态监控
  - 缓存清理功能
- **API端点**: `GET /debug/cache/<draft_id>`
- **优先级**: 低

#### 7.2 系统信息
- **需求描述**: 提供系统运行状态和配置信息
- **功能规格**:
  - 操作系统信息获取
  - 系统资源监控
  - 配置参数查询
- **API端点**: `GET /api/os/info`
- **优先级**: 低

## 🔧 技术需求

### 1. 系统架构需求

#### 1.1 后端架构
- **框架**: Flask (Python)
- **数据库**: SQLite (本地) / PostgreSQL (生产)
- **存储**: 本地文件系统 + 阿里云OSS
- **缓存**: 内存缓存 + 文件缓存

#### 1.2 数据存储架构
- **数据库存储**:
  - SQLite数据库管理草稿和素材数据
  - 草稿表存储基本信息和脚本数据
  - 素材表管理关联关系和JSON数据
  - 自动数据库初始化和维护

- **本地文件存储**:
  - 按草稿ID组织文件夹结构
  - assets子目录分类存储素材
  - draft_info.json元数据文件
  - 文件完整性验证和自动清理

#### 1.3 前端架构
- **技术栈**: 纯HTML/CSS/JavaScript
- **设计**: 响应式设计，支持多设备
- **样式**: CSS Grid/Flexbox布局
- **交互**: 原生JavaScript，无第三方依赖

#### 1.4 模板系统
- **主页模板**: 服务信息展示和API导航
- **草稿仪表板**: 草稿列表管理和批量操作
- **草稿预览**: 沉浸式预览和交互式时间轴
- **响应式设计**: 支持多端设备访问

#### 1.5 配置管理
- **环境配置**: CapCut环境和服务配置
- **OSS云存储**: 访问密钥和存储桶配置
- **路径配置**: 跨平台路径处理和适配
- **数据库配置**: 连接池和事务管理

#### 1.6 工具函数库
- **通用工具**: 文件处理、数据转换、验证工具
- **下载工具**: 文件下载管理和断点续传
- **压缩工具**: 自定义压缩和签名URL生成
- **缓存管理**: 草稿缓存操作和内存管理

### 2. 性能需求

#### 2.1 响应时间
- **API响应时间**: 
  - 简单查询API < 500ms
  - 复杂操作API < 2秒
  - 草稿创建 < 3秒
  - 素材添加 < 5秒
- **文件处理时间**:
  - 文件上传响应时间 < 30秒
  - 草稿保存时间 < 60秒
  - 批量下载启动 < 10秒
  - OSS上传 < 120秒
- **界面响应时间**:
  - 页面加载 < 3秒
  - 交互响应 < 200ms
  - 实时更新延迟 < 1秒

#### 2.2 并发处理
- **用户并发**:
  - 支持50个并发用户访问
  - 支持10个并发API请求
  - 支持5个并发草稿处理
- **任务并发**:
  - 批量下载并发数 ≤ 3
  - OSS上传并发数 ≤ 2
  - 后台保存队列管理
- **资源保护**:
  - 请求频率限制
  - 连接池管理
  - 超时机制保护

#### 2.3 资源使用
- **内存管理**:
  - 基础内存使用 < 512MB
  - 峰值内存使用 < 2GB
  - 内存泄漏检测和清理
- **CPU性能**:
  - 空闲时CPU使用率 < 5%
  - 处理时CPU使用率 < 80%
  - 多核心任务分配
- **存储管理**:
  - 系统磁盘空间预留 > 10GB
  - 临时文件自动清理
  - 数据库文件大小监控
- **网络性能**:
  - 带宽使用优化
  - 连接复用机制
  - 断线重连处理

### 3. 安全需求

#### 3.1 数据安全
- 敏感信息环境变量配置
- API访问频率限制
- 文件上传安全检查

#### 3.2 系统安全
- 非root用户运行服务
- 防火墙端口控制
- 日志记录和监控

### 4. 兼容性需求

#### 4.1 系统兼容性
- Linux (CentOS, Ubuntu)
- Windows (开发环境)
- macOS (开发环境)
- 跨平台路径处理和适配

#### 4.2 Python版本
- Python 3.8.20+
- 推荐使用Python 3.9
- 依赖库兼容性管理

#### 4.3 浏览器兼容性
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+
- 移动端浏览器支持

#### 4.4 数据库兼容性
- SQLite 3.x (主要)
- PostgreSQL (生产环境可选)
- 数据迁移和备份支持

## 📊 质量需求

### 1. 可靠性
- **系统稳定性**:
  - 系统可用性 > 99.5%
  - 平均故障恢复时间 < 5分钟
  - 无数据丢失保证
- **数据完整性**:
  - 数据库事务一致性
  - 文件完整性校验
  - 自动备份和恢复
- **错误处理**:
  - 全面的异常捕获
  - 优雅的错误降级
  - 自动重试机制
- **容错能力**:
  - 网络中断恢复
  - 存储故障处理
  - 服务重启恢复

### 2. 可维护性
- **代码质量**:
  - 代码注释覆盖率 > 90%
  - 函数级文档完整
  - 代码规范统一
- **架构设计**:
  - 模块化设计原则
  - 低耦合高内聚
  - 清晰的分层架构
- **监控和调试**:
  - 完整的日志记录
  - 性能监控指标
  - 调试信息输出
- **文档维护**:
  - API文档自动生成
  - 部署文档更新
  - 故障排查指南

### 3. 可扩展性
- **功能扩展**:
  - 支持新素材类型扩展
  - 支持新API端点扩展
  - 支持新特效类型扩展
- **存储扩展**:
  - 支持新存储后端扩展
  - 支持多云存储适配
  - 支持分布式存储
- **性能扩展**:
  - 水平扩展能力
  - 负载均衡支持
  - 缓存策略优化
- **集成扩展**:
  - 第三方服务集成
  - 插件系统支持
  - API版本兼容性

### 4. 安全性
- **数据安全**:
  - 敏感数据加密存储
  - 传输数据加密
  - 访问权限控制
- **API安全**:
  - 请求验证机制
  - 防止恶意攻击
  - 输入数据验证
- **系统安全**:
  - 文件访问权限控制
  - 进程权限最小化
  - 安全配置管理

### 5. 用户体验
- **界面友好性**:
  - 直观的操作界面
  - 清晰的状态反馈
  - 响应式设计适配
- **操作便捷性**:
  - 一键批量操作
  - 智能默认配置
  - 快捷键支持
- **错误提示**:
  - 友好的错误信息
  - 操作指导提示
  - 问题解决建议

## 🚀 部署需求

### 1. 环境要求
- Python 3.8.20+
- ffmpeg (媒体处理)
- systemd服务管理
- 网络连接（用于云端存储）
- SQLite数据库支持

### 2. 配置要求
- **主配置文件**: `settings/local.py`
- **环境变量**: OSS相关配置
- **数据库文件**: `capcut.db`
- **服务端口**: 9000（可配置）
- **日志目录**: `logs/`
- **模板目录**: `templates/`

### 3. 服务管理
- systemd服务配置
- 自动启动和重启
- 日志轮转和清理
- 健康检查机制
- 数据库自动初始化
- 缓存管理和清理

## 📋 验收标准

### 1. 功能验收
- [ ] 所有API端点正常响应
- [ ] 草稿创建和保存功能正常
- [ ] 素材添加功能完整
- [ ] 用户界面功能正常
- [ ] 批量处理功能可用
- [ ] 云端存储功能稳定
- [ ] 数据库操作功能正常
- [ ] 模板渲染功能正常
- [ ] 配置管理功能完整
- [ ] 工具函数库功能稳定

### 2. 性能验收
- [ ] **响应时间验收**:
  - [ ] API响应时间测试通过
  - [ ] 文件处理时间测试通过
  - [ ] 界面响应时间测试通过
- [ ] **并发处理验收**:
  - [ ] 用户并发测试通过
  - [ ] 任务并发测试通过
  - [ ] 资源保护机制测试通过
- [ ] **资源使用验收**:
  - [ ] 内存使用测试通过
  - [ ] CPU性能测试通过
  - [ ] 存储管理测试通过
  - [ ] 网络性能测试通过

### 3. 质量验收
- [ ] **可靠性验收**:
  - [ ] 系统稳定性测试通过
  - [ ] 数据完整性测试通过
  - [ ] 错误处理测试通过
  - [ ] 容错能力测试通过
- [ ] **可维护性验收**:
  - [ ] 代码质量检查通过
  - [ ] 架构设计评审通过
  - [ ] 监控和调试功能测试通过
  - [ ] 文档完整性检查通过
- [ ] **可扩展性验收**:
  - [ ] 功能扩展测试通过
  - [ ] 存储扩展测试通过
  - [ ] 性能扩展测试通过
  - [ ] 集成扩展测试通过
- [ ] **安全性验收**:
  - [ ] 数据安全测试通过
  - [ ] API安全测试通过
  - [ ] 系统安全测试通过
- [ ] **用户体验验收**:
  - [ ] 界面友好性测试通过
  - [ ] 操作便捷性测试通过
  - [ ] 错误提示测试通过

### 4. 集成验收
- [ ] **端到端测试**:
  - [ ] 完整工作流程测试通过
  - [ ] 跨模块集成测试通过
  - [ ] 第三方服务集成测试通过
- [ ] **兼容性测试**:
  - [ ] 操作系统兼容性测试通过
  - [ ] 浏览器兼容性测试通过
  - [ ] Python版本兼容性测试通过
- [ ] **部署验收**:
  - [ ] 生产环境部署测试通过
  - [ ] 配置管理测试通过
  - [ ] 服务管理测试通过
  - [ ] 监控告警测试通过

## 📅 开发计划

### 阶段一：核心功能开发（已完成）
- ✅ 草稿创建与管理API
- ✅ 素材添加功能（视频、音频、文本、字幕、图片、贴纸、特效）
- ✅ 基础用户界面
- ✅ 数据库存储系统
- ✅ 本地文件管理

### 阶段二：高级功能开发（已完成）
- ✅ 批量处理功能
- ✅ 云端存储集成（阿里云OSS）
- ✅ 草稿管理仪表板
- ✅ 在线预览功能
- ✅ 下载中心界面
- ✅ 性能优化

### 阶段三：用户界面优化（已完成）
- ✅ 响应式设计实现
- ✅ 交互式预览界面
- ✅ 实时状态更新
- ✅ 专业暗色主题
- ✅ 多端设备适配

### 阶段四：系统集成与优化（已完成）
- ✅ 跨平台路径处理
- ✅ 配置管理系统
- ✅ 工具函数库
- ✅ 缓存管理机制
- ✅ 错误处理优化

### 阶段五：测试与部署（已完成）
- ✅ 功能测试
- ✅ 性能测试
- ✅ 兼容性测试
- ✅ 生产环境部署
- ✅ 监控和日志系统

### 阶段六：文档与维护（当前阶段）
- ✅ API文档编写
- ✅ 用户使用指南
- 🔄 需求文档更新（当前任务）
- ⏳ 部署文档完善
- ⏳ 维护计划制定

### 未来规划
- **功能扩展**：
  - 新素材类型支持
  - 更多特效和转场
  - AI智能剪辑功能
- **性能提升**：
  - 分布式处理
  - 更高并发支持
  - 智能缓存策略
- **集成扩展**：
  - 更多云存储支持
  - 第三方服务集成
  - 插件系统开发

## 📚 附录

### A. API接口清单

#### A.1 草稿管理API
- `POST /create_draft` - 创建新草稿
- `POST /query_script` - 查询草稿脚本
- `POST /query_draft_status` - 查询草稿状态
- `POST /save_draft` - 保存草稿
- `GET /api/drafts/list` - 获取草稿列表
- `GET /api/drafts/preview/<draft_id>` - 预览草稿
- `GET /api/drafts/edit/<draft_id>` - 编辑草稿
- `DELETE /api/drafts/delete/<draft_id>` - 删除草稿
- `GET /api/draft/long_poll_status` - 长轮询状态

#### A.2 素材添加API
- `POST /add_video` - 添加视频
- `POST /add_audio` - 添加音频
- `POST /add_text` - 添加文本
- `POST /add_subtitle` - 添加字幕
- `POST /add_image` - 添加图片
- `POST /add_sticker` - 添加贴纸
- `POST /add_effect` - 添加特效
- `POST /add_video_keyframe` - 添加视频关键帧

#### A.3 元数据API
- `GET /api/animation/intro` - 获取入场动画
- `GET /api/animation/outro` - 获取出场动画
- `GET /api/animation/group` - 获取组合动画
- `GET /api/transition/types` - 获取转场类型
- `GET /api/mask/types` - 获取蒙版类型
- `GET /api/font/types` - 获取字体类型
- `GET /api/text/animation/intro` - 获取文本入场动画
- `GET /api/text/animation/outro` - 获取文本出场动画
- `GET /api/text/animation/loop` - 获取文本循环动画
- `GET /api/video/scene/effects` - 获取视频场景特效
- `GET /api/video/character/effects` - 获取视频角色特效
- `GET /api/audio/tone/effects` - 获取音频音调特效
- `GET /api/audio/scene/effects` - 获取音频场景特效
- `GET /api/audio/speech/effects` - 获取音频语音特效

#### A.4 CapCut特效API
- `GET /api/capcut/animation/intro` - CapCut入场动画
- `GET /api/capcut/animation/outro` - CapCut出场动画
- `GET /api/capcut/animation/group` - CapCut组合动画
- `GET /api/capcut/transition/types` - CapCut转场类型
- `GET /api/capcut/mask/types` - CapCut蒙版类型
- `GET /api/capcut/text/animation/intro` - CapCut文本入场动画
- `GET /api/capcut/text/animation/outro` - CapCut文本出场动画
- `GET /api/capcut/text/animation/loop` - CapCut文本循环动画
- `GET /api/capcut/video/scene/effects` - CapCut视频场景特效
- `GET /api/capcut/video/character/effects` - CapCut视频角色特效
- `GET /api/capcut/audio/voice/filters` - CapCut音频语音滤镜
- `GET /api/capcut/audio/characters` - CapCut音频角色
- `GET /api/capcut/audio/speech` - CapCut音频语音

#### A.5 云存储API
- `POST /mirror_to_oss` - 镜像到OSS
- `POST /generate_draft_url` - 生成草稿URL

#### A.6 批量处理API
- `POST /api/drafts/batch-download` - 批量下载
- `POST /api/draft/download` - 单个下载
- `GET /api/drafts/download/<draft_id>` - 获取下载链接
- `GET /api/draft/download/progress/<task_id>` - 下载进度

#### A.7 系统API
- `GET /debug/cache/<draft_id>` - 调试缓存
- `GET /api/os/info` - 操作系统信息
- `POST /api/draft/path/config` - 配置草稿路径

#### A.8 用户界面路由
- `/` - 主页
- `/api/drafts/dashboard` - 草稿管理仪表板
- `/draft/preview/<draft_id>` - 草稿预览界面
- `/draft/downloader` - 草稿下载界面

### B. 数据库设计

#### B.1 草稿表 (drafts)
```sql
CREATE TABLE drafts (
    id TEXT PRIMARY KEY,
    status TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    message TEXT,
    script_data TEXT,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### B.2 素材表 (materials)
```sql
CREATE TABLE materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id TEXT,
    material_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (draft_id) REFERENCES drafts (id)
);
```

### C. 配置文件说明

#### C.1 主配置文件 (settings/local.py)
```python
# CapCut环境配置
IS_CAPCUT_ENV = True
DRAFT_DOMAIN = "your-domain.com"
PREVIEW_ROUTER = "/preview"
PORT = 9000
IS_UPLOAD_DRAFT = True

# OSS配置
OSS_CONFIG = {
    "access_key_id": "your-access-key",
    "access_key_secret": "your-secret-key",
    "bucket_name": "your-bucket",
    "endpoint": "your-endpoint"
}
```

#### C.2 路径配置 (os_path_config.py)
- Windows路径处理
- Linux/macOS路径处理
- 跨平台路径转换

### D. 部署指南

#### D.1 环境准备
1. 安装Python 3.8.20+
2. 安装ffmpeg
3. 配置systemd服务
4. 准备OSS存储

#### D.2 服务启动
```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -c "from database import init_db; init_db()"

# 启动服务
python capcut_server.py
```

#### D.3 服务管理
```bash
# 启动服务
sudo systemctl start capcut-api

# 停止服务
sudo systemctl stop capcut-api

# 查看状态
sudo systemctl status capcut-api
```

### E. 故障排查

#### E.1 常见问题
- **数据库连接失败**：检查capcut.db文件权限
- **OSS上传失败**：验证OSS配置信息
- **草稿保存失败**：检查磁盘空间和权限
- **API响应超时**：检查网络连接和服务状态

#### E.2 日志查看
```bash
# 查看服务日志
journalctl -u capcut-api -f

# 查看应用日志
tail -f logs/capcut.log
```

#### E.3 性能监控
- CPU使用率监控
- 内存使用监控
- 磁盘空间监控
- 网络连接监控

### F. 版本历史

#### v1.2.0 Enhanced Edition (当前版本)
- ✅ 完整的草稿管理系统
- ✅ 丰富的素材添加功能
- ✅ 专业的用户界面
- ✅ 云存储集成
- ✅ 批量处理功能
- ✅ 跨平台支持
- ✅ 性能优化和安全加固

#### v1.1.0 (前一版本)
- 基础API功能完善
- 用户界面优化
- 云存储初步集成

#### v1.0.0 (初始版本)
- 基础API功能
- 简单的草稿操作
- 本地存储支持

---

**文档版本**: v1.2.0 Enhanced Edition  
**最后更新**: 2025年1月21日  
**状态**: 已完成核心功能，持续优化中  
**维护团队**: CapCutAPI开发团队