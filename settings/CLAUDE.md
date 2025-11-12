[根目录](../CLAUDE.md) > **settings**

---

# settings 配置模块文档

> 最后更新时间：2025-11-11 22:20:59

## 变更记录 (Changelog)

### 2025-11-11 22:20:59
- 初始化 settings 配置模块文档
- 完成模块架构和功能分析

---

## 模块职责

`settings` 模块是 CapCutAPI 项目的统一配置管理中心，负责从多个来源（环境变量、JSON 配置文件）加载和管理项目配置。它采用分层加载策略，确保敏感信息安全和配置灵活性。

**核心功能**：
- 从 `.env` 文件和环境变量加载配置
- 从 `config.json` 文件加载本地配置
- 提供默认配置和配置覆盖机制
- 统一导出配置，供其他模块使用
- 支持平台信息查询（剪映/CapCut）

**配置优先级**（从高到低）：
1. 环境变量（`.env` 文件或系统环境变量）
2. `config.json` 本地配置文件
3. 代码内默认配置

---

## 入口与启动

### 模块导入入口
- **文件**: `__init__.py`
- **导出内容**: 所有配置项和辅助函数

```python
from settings import (
    IS_CAPCUT_ENV,      # 是否为 CapCut 国际版环境
    DRAFT_DOMAIN,       # 草稿域名
    PREVIEW_ROUTER,     # 预览路由
    PORT,               # 服务端口
    IS_UPLOAD_DRAFT,    # 是否上传草稿到云端
    OSS_CONFIG,         # OSS 配置字典
    MP4_OSS_CONFIG,     # MP4 OSS 配置字典
    get_platform_info   # 平台信息获取函数
)
```

### 加载顺序
1. 加载 `.env` 文件（如果存在）
2. 定义默认配置
3. 尝试加载 `config.json` 文件
4. 用环境变量覆盖敏感配置

---

## 对外接口

### 核心配置项

#### 1. 环境配置
```python
IS_CAPCUT_ENV: bool         # 是否为 CapCut 国际版（True）或剪映（False）
PORT: int                   # 服务监听端口（默认 9000）
```

#### 2. 域名和路由配置
```python
DRAFT_DOMAIN: str          # 草稿访问域名
PREVIEW_ROUTER: str        # 预览页面路由
```

#### 3. 存储配置
```python
IS_UPLOAD_DRAFT: bool      # 是否上传草稿到 OSS（True）或本地保存（False）
OSS_CONFIG: dict           # 阿里云 OSS 配置
MP4_OSS_CONFIG: dict       # MP4 素材 OSS 配置
```

#### 4. 路径配置
```python
WINDOWS_DRAFT_FOLDER: str  # Windows 系统默认草稿路径
LINUX_DRAFT_FOLDER: str    # Linux 系统默认草稿路径
```

#### 5. 网络配置
```python
DOWNLOAD_HEADERS: dict     # 自定义下载请求头（解决 403 等问题）
FILE_SERVER_PUBLIC_HOST: str    # 文件服务器公网主机名
FILE_SERVER_INTERNAL_BASE: str  # 文件服务器内网地址
```

### 辅助函数

#### get_platform_info()
```python
def get_platform_info() -> dict:
    """
    获取平台信息，用于 CapCut 环境下的草稿序列化

    Returns:
        dict: 平台信息字典（包含 app_id, os, device_id 等）
        None: 如果不是 CapCut 环境
    """
```

**返回示例**（CapCut 环境）：
```json
{
    "app_id": 359289,
    "app_source": "cc",
    "app_version": "6.5.0",
    "device_id": "c4ca4238a0b923820dcc509a6f75849b",
    "hard_disk_id": "307563e0192a94465c0e927fbc482942",
    "mac_address": "c3371f2d4fb02791c067ce44d8fb4ed5",
    "os": "mac",
    "os_version": "15.5"
}
```

---

## 关键依赖与配置

### 依赖库
- **python-dotenv**: 加载 `.env` 文件

### 配置文件结构

#### 1. `.env` 文件（环境变量）
```bash
# OSS 配置（敏感信息）
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_BUCKET_NAME=your_bucket_name
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com

# MP4 OSS 配置
MP4_OSS_ACCESS_KEY_ID=your_mp4_access_key
MP4_OSS_ACCESS_KEY_SECRET=your_mp4_access_key_secret
MP4_OSS_BUCKET_NAME=your_mp4_bucket
MP4_OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com

# 服务配置
PORT=9000
DRAFT_DOMAIN=https://www.example.com
```

#### 2. `config.json` 文件（非敏感配置）
```json
{
    "is_capcut_env": true,
    "draft_domain": "https://www.install-ai-guider.top",
    "preview_router": "/draft/downloader",
    "port": 9000,
    "is_upload_draft": false,
    "windows_draft_folder": "F:/jianyin/cgwz/JianyingPro Drafts",
    "linux_draft_folder": "/data/jianying/drafts",
    "oss_config": {
        "access_key_id": "${OSS_ACCESS_KEY_ID}",
        "access_key_secret": "${OSS_ACCESS_KEY_SECRET}",
        "bucket_name": "${OSS_BUCKET_NAME}",
        "endpoint": "${OSS_ENDPOINT}"
    },
    "download_headers": {
        "User-Agent": "CapCutAPI/1.0",
        "Referer": "https://www.example.com"
    },
    "file_server_public_host": "cdn.example.com",
    "file_server_internal_base": "http://192.168.1.100"
}
```

---

## 数据模型

### 配置加载流程
```
1. 加载 .env 文件（dotenv）
   ↓
2. 定义默认配置（代码内）
   ↓
3. 加载 config.json 文件
   ↓
4. 环境变量覆盖敏感配置
   ↓
5. 导出最终配置
```

### 配置优先级示例
假设有以下配置来源：

**默认配置**（代码内）：
```python
PORT = 9000
IS_UPLOAD_DRAFT = False
```

**config.json**：
```json
{
    "port": 8080,
    "is_upload_draft": true
}
```

**环境变量**：
```bash
PORT=7000
```

**最终配置**：
```python
PORT = 7000                 # 环境变量优先级最高
IS_UPLOAD_DRAFT = True      # config.json 覆盖默认值
```

---

## 测试与质量

### 测试策略
- **配置加载测试**: 验证不同配置源的加载顺序和优先级
- **默认值测试**: 验证缺失配置时的默认值处理
- **环境变量覆盖测试**: 验证环境变量正确覆盖配置文件

### 建议测试
```python
# 测试配置加载
def test_config_loading():
    from settings import PORT, IS_CAPCUT_ENV, OSS_CONFIG
    assert isinstance(PORT, int)
    assert isinstance(IS_CAPCUT_ENV, bool)
    assert isinstance(OSS_CONFIG, dict)

# 测试平台信息
def test_platform_info():
    from settings import get_platform_info, IS_CAPCUT_ENV
    info = get_platform_info()
    if IS_CAPCUT_ENV:
        assert "app_id" in info
        assert "os" in info
    else:
        assert info is None
```

---

## 常见问题 (FAQ)

### Q1: 如何安全地存储 OSS 密钥？
**推荐方式**：使用 `.env` 文件或系统环境变量
```bash
# 创建 .env 文件
cp .env.example .env
vim .env  # 编辑并添加真实密钥

# 确保 .env 文件被 .gitignore 忽略
echo ".env" >> .gitignore
```

### Q2: 如何切换剪映和 CapCut 环境？
修改 `config.json` 或设置环境变量：
```json
{
    "is_capcut_env": false  // false = 剪映，true = CapCut
}
```

或使用环境变量：
```bash
export IS_CAPCUT_ENV=false
```

### Q3: 如何自定义草稿保存路径？
在 `config.json` 中配置：
```json
{
    "windows_draft_folder": "D:/MyDrafts",
    "linux_draft_folder": "/home/user/drafts"
}
```

### Q4: OSS 配置为空字典，会导致错误吗？
不会。代码中使用 `OSS_CONFIG.get()` 方法安全访问配置项，避免 KeyError。

### Q5: 如何启用内网直连优化？
配置文件服务器映射：
```json
{
    "file_server_public_host": "cdn.example.com",
    "file_server_internal_base": "http://192.168.1.100"
}
```

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `__init__.py` | 配置导出入口，统一导出所有配置项 |
| `local.py` | 本地配置加载逻辑，从 `.env` 和 `config.json` 加载配置 |

---

## 相关模块
- [根目录](../CLAUDE.md) - 项目总览
- [capcut_server.py](../capcut_server.py) - 使用配置的主服务
- [pyJianYingDraft](../pyJianYingDraft/CLAUDE.md) - 使用 `get_platform_info()` 序列化草稿

---

**提示**: 修改配置时，优先使用环境变量存储敏感信息，避免将密钥提交到 Git 仓库。
