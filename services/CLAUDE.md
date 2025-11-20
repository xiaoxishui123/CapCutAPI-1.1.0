[根目录](../CLAUDE.md) > **services**

---

# services 模块文档

> 最后更新时间：2025-11-20 09:44:24

## 变更记录 (Changelog)

### 2025-11-20 09:44:24
- 初始化 services 模块文档
- 完成模块架构分析和功能说明

---

## 模块职责

`services` 模块是 CapCutAPI v1.2.0+ 引入的业务逻辑层，负责将业务逻辑从 Flask 路由中分离，提高代码的可测试性、可维护性和可复用性。

**核心价值**：
- 分离业务逻辑与 Web 框架（Flask）
- 提供统一的服务接口和错误处理
- 支持单元测试和集成测试
- 便于后续扩展新的服务模块

**设计原则**：
- 单一职责原则（SRP）
- 依赖注入（DI）
- 面向接口编程

---

## 入口与启动

### 模块导入入口
- **文件**: `__init__.py`
- **导出内容**: 所有服务类和工厂函数

```python
from services import (
    DraftDownloadService,  # 草稿下载服务
    get_download_service   # 下载服务工厂函数
)
```

### 服务实例化

```python
# 获取全局下载服务实例
download_service = get_download_service()

# 或手动创建实例
from services.download_service import DraftDownloadService
download_service = DraftDownloadService(oss_client=None, cache_manager=None)
```

---

## 对外接口

### 1. DraftDownloadService（草稿下载服务）

**文件**: `download_service.py`

**职责**：
- 生成草稿下载链接（OSS/本地）
- 流式下载草稿文件
- 批量下载处理
- 自动修复机制（路径适配、文件修复）
- 草稿存在性检查

#### 核心方法

##### 1.1 check_draft_exists()
检查草稿是否存在于 OSS、数据库和缓存中

```python
result = download_service.check_draft_exists(
    draft_id='dfd_cat_1234567890_abcdef12',
    client_os='windows',
    draft_folder='C:\\JianyingPro\\User Data\\Projects\\com.lveditor.draft'
)
# 返回: {
#     'draft_id': str,
#     'exists_in_oss': bool,
#     'exists_in_database': bool,
#     'exists_in_cache': bool,
#     'base_key': str,
#     'customized_version': {...}
# }
```

**参数**：
- `draft_id` (str): 草稿 ID
- `client_os` (str, 可选): 客户端操作系统（'windows', 'linux', 'macos'）
- `draft_folder` (str, 可选): 草稿文件夹路径

**返回值**：
- `dict`: 包含草稿存在性和详细信息

##### 1.2 generate_download_url()
生成草稿下载链接（OSS 签名 URL）

```python
url_info = download_service.generate_download_url(
    draft_id='dfd_cat_1234567890_abcdef12',
    client_os='windows',
    draft_folder='C:\\JianyingPro\\User Data\\Projects\\com.lveditor.draft',
    expires=3600  # 链接有效期（秒）
)
# 返回: {
#     'url': str,
#     'expires_at': datetime,
#     'customized': bool
# }
```

##### 1.3 stream_download()
流式下载草稿文件（用于直接下载）

```python
response = download_service.stream_download(
    draft_id='dfd_cat_1234567890_abcdef12',
    client_os='windows',
    draft_folder='C:\\JianyingPro\\User Data\\Projects\\com.lveditor.draft'
)
# 返回: Flask Response 对象（流式下载）
```

**返回值**：
- `Response`: Flask 响应对象，Content-Type 为 `application/octet-stream`

##### 1.4 batch_download()
批量下载多个草稿

```python
results = download_service.batch_download(
    draft_ids=['dfd_cat_123_abc', 'dfd_cat_456_def'],
    client_os='windows',
    draft_folder='...'
)
# 返回: [
#     {'draft_id': str, 'success': bool, 'url': str, 'error': str},
#     ...
# ]
```

##### 1.5 auto_fix_draft()
自动修复草稿文件（路径适配、缺失文件补全）

```python
fixed = download_service.auto_fix_draft(
    draft_id='dfd_cat_1234567890_abcdef12',
    client_os='windows',
    draft_folder='...'
)
# 返回: {
#     'success': bool,
#     'fixed_key': str,
#     'changes': List[str]
# }
```

---

## 关键依赖与配置

### 依赖项
- **Flask**: Web 框架（用于 Response 对象）
- **requests**: HTTP 客户端（用于下载 OSS 文件）
- **oss2**: 阿里云 OSS SDK
- **sqlite3**: 数据库查询

### 配置来源
服务类通过依赖注入获取配置，主要配置项：
- `OSS_CONFIG`: OSS 配置（bucket, access_key, secret, endpoint）
- `IS_UPLOAD_DRAFT`: 是否启用 OSS 上传模式
- `DRAFT_CACHE`: 草稿缓存管理器

### 工厂函数模式

`get_download_service()` 工厂函数提供单例模式：

```python
def get_download_service() -> DraftDownloadService:
    """获取全局下载服务实例（单例模式）"""
    global _download_service_instance
    if _download_service_instance is None:
        from oss import _ensure_bucket
        from draft_cache import DRAFT_CACHE
        _download_service_instance = DraftDownloadService(
            oss_client=_ensure_bucket(),
            cache_manager=DRAFT_CACHE
        )
    return _download_service_instance
```

---

## 数据模型

### 草稿检查结果
```python
{
    'draft_id': str,                  # 草稿 ID
    'exists_in_oss': bool,            # OSS 中是否存在
    'exists_in_database': bool,       # 数据库中是否存在
    'exists_in_cache': bool,          # 缓存中是否存在
    'base_key': str,                  # OSS 基础文件键（如 draft_id.zip）
    'customized_version': {           # 定制化版本信息（可选）
        'key': str,                   # OSS 定制化文件键
        'exists': bool,               # 是否存在定制化版本
        'client_os': str              # 客户端操作系统
    },
    'draft_info': {                   # 草稿详情（可选）
        'status': str,                # 草稿状态
        'created_at': str             # 创建时间
    }
}
```

### 下载 URL 信息
```python
{
    'url': str,                       # 下载 URL（OSS 签名 URL）
    'expires_at': datetime,           # 链接过期时间
    'customized': bool                # 是否为定制化版本
}
```

### 批量下载结果
```python
[
    {
        'draft_id': str,              # 草稿 ID
        'success': bool,              # 是否成功
        'url': str,                   # 下载 URL（成功时）
        'error': str                  # 错误信息（失败时）
    },
    ...
]
```

---

## 测试与质量

### 单元测试
- **位置**: 待添加 `services/tests/test_download_service.py`
- **覆盖**: 所有核心方法的单元测试

### 集成测试
- **位置**: 在 `capcut_server.py` 的路由中集成调用
- **测试端点**:
  - `/api/v2/drafts/<draft_id>/download/url` - 生成下载链接
  - `/api/v2/drafts/<draft_id>/download/stream` - 流式下载
  - `/api/v2/drafts/batch/download` - 批量下载
  - `/api/v2/drafts/<draft_id>/status` - 草稿状态检查

### 使用示例

#### 示例 1：在 Flask 路由中使用
```python
from flask import jsonify
from services import get_download_service

@app.route('/api/v2/drafts/<draft_id>/download/url', methods=['POST'])
def get_download_url(draft_id):
    """生成草稿下载链接（API v2）"""
    download_service = get_download_service()

    data = request.json or {}
    client_os = data.get('client_os', 'windows')
    draft_folder = data.get('draft_folder', '')

    try:
        url_info = download_service.generate_download_url(
            draft_id=draft_id,
            client_os=client_os,
            draft_folder=draft_folder
        )
        return jsonify({
            'success': True,
            'data': url_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

#### 示例 2：批量下载
```python
from services import get_download_service

download_service = get_download_service()
results = download_service.batch_download(
    draft_ids=['draft_1', 'draft_2', 'draft_3'],
    client_os='windows'
)

for result in results:
    if result['success']:
        print(f"✅ {result['draft_id']}: {result['url']}")
    else:
        print(f"❌ {result['draft_id']}: {result['error']}")
```

---

## 常见问题 (FAQ)

### Q1: 为什么要创建 services 模块？
**A**: 将业务逻辑从 Flask 路由中分离，提高代码可测试性、可维护性和可复用性。遵循分层架构和单一职责原则。

### Q2: 如何扩展新的服务类？
**A**:
1. 在 `services/` 目录下创建新的服务文件（如 `draft_management_service.py`）
2. 定义服务类，实现核心业务逻辑
3. 在 `services/__init__.py` 中导出新服务
4. 在 Flask 路由中注入并使用

### Q3: 服务类是否支持依赖注入？
**A**: 是的，所有服务类通过构造函数注入依赖（如 OSS 客户端、缓存管理器），便于测试和模拟（Mock）。

### Q4: 如何测试服务类？
**A**: 使用 `pytest` 编写单元测试，通过 Mock 模拟外部依赖（如 OSS 客户端、数据库）：

```python
import pytest
from unittest.mock import Mock
from services.download_service import DraftDownloadService

def test_check_draft_exists():
    # Mock 依赖
    mock_oss = Mock()
    mock_cache = Mock()

    # 创建服务实例
    service = DraftDownloadService(oss_client=mock_oss, cache_manager=mock_cache)

    # 测试方法
    result = service.check_draft_exists('test_draft_id')
    assert 'draft_id' in result
```

### Q5: 服务类是否线程安全？
**A**: 当前实现为单例模式，在多线程环境下需要额外的同步机制。建议每个请求创建新的服务实例，或使用线程本地存储（Thread Local）。

---

## 相关文件清单

### 核心文件
- `services/__init__.py` - 模块入口，导出所有服务
- `services/download_service.py` - 草稿下载服务实现

### 调用方
- `capcut_server.py` - Flask 路由中调用下载服务
- `utils/decorators.py` - 装饰器中使用服务进行草稿检查

### 依赖文件
- `oss.py` - OSS 客户端封装
- `draft_cache.py` - 草稿缓存管理器
- `database.py` - SQLite 数据库操作
- `customize_zip.py` - 定制化草稿生成

### 测试文件
- 待添加: `services/tests/test_download_service.py`
- 集成测试: `test_api_v2.py`（测试 API v2 端点）

---

## 下一步建议

### 建议新增的服务模块
1. **DraftManagementService** - 草稿管理服务（创建、删除、列表）
2. **MaterialService** - 素材管理服务（添加、查询、验证）
3. **TemplateService** - 模板服务（Pattern 管理）
4. **OSSService** - 统一 OSS 操作服务（上传、下载、删除）
5. **CacheService** - 统一缓存服务（LRU Cache、Redis）

### 待优化项
- ✅ 已完成：DraftDownloadService 实现
- ⏳ 待添加：单元测试覆盖
- ⏳ 待添加：类型注解（Type Hints）
- ⏳ 待优化：线程安全机制
- ⏳ 待扩展：更多服务类

---

**最后更新**: 2025-11-20 09:44:24
**文档版本**: v1.0.0
**维护者**: AI 架构师
