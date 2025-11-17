# API v1 到 v2 迁移指南

> 最后更新：2025-11-17
> 状态：v1 端点将于 2025-02-15 下线

---

## 📋 概览

CapCutAPI v2 引入了全新的架构设计，提供：
- ✅ RESTful 风格的 API 设计
- ✅ 统一的错误处理格式
- ✅ 自动验证和修复机制
- ✅ 完整的日志和限流保护
- ✅ 更好的类型安全和文档

**迁移时间表**：
- **2025-11-17**: v2 API 正式发布
- **2025-11-17 - 2025-02-15**: v1 和 v2 并行运行（90天过渡期）
- **2025-02-15**: v1 API 正式下线

---

## 🔄 端点映射

### 1. 生成下载链接

#### v1 端点（已废弃）
```http
POST /generate_draft_url

请求体:
{
  "draft_id": "dfd_cat_xxx",
  "client_os": "windows",
  "draft_folder": "/path/to/folder",
  "force_save": false
}

响应:
{
  "success": true,
  "output": {
    "draft_url": "https://...",
    "storage": "oss",
    "client_os": "windows",
    "draft_folder": ""
  }
}
```

#### v2 端点（推荐）
```http
POST /api/v2/drafts/<draft_id>/download/url

请求体:
{
  "client_os": "windows",
  "draft_folder": "/path/to/folder",
  "force_save": false
}

响应:
{
  "success": true,
  "data": {
    "draft_id": "dfd_cat_xxx",
    "download_url": "https://...",
    "file_size": 12345,
    "expires_in": 3600,
    "download_method": "oss"
  },
  "message": "下载链接生成成功"
}
```

**主要变化**：
1. ✅ `draft_id` 从请求体移到 URL 路径参数
2. ✅ 响应格式标准化：`output` → `data`
3. ✅ 新增 `file_size` 和 `expires_in` 字段
4. ✅ 新增 `message` 字段提供友好提示

---

### 2. 流式下载草稿

#### v1 端点（已废弃）
```http
GET /api/drafts/download/proxy/<draft_id>?client_os=windows&draft_folder=/path
```

#### v2 端点（推荐）
```http
GET /api/v2/drafts/<draft_id>/download/stream?client_os=windows&draft_folder=/path
```

**主要变化**：
1. ✅ URL 路径更清晰：`proxy` → `stream`
2. ✅ 自动修复机制（缺失文件自动重新生成）
3. ✅ 自动限流保护（默认 10次/分钟）
4. ✅ 完整的错误日志和追踪

---

### 3. 批量下载草稿

#### v1 端点（已废弃）
```http
POST /api/drafts/batch-download

请求体:
{
  "draft_ids": ["id1", "id2", "id3"],
  "client_os": "windows",
  "draft_folder": "/path/to/folder"
}

响应:
{
  "success": true,
  "message": "已处理 3 个草稿",
  "results": [
    {"draft_id": "id1", "status": "queued", "message": "已加入下载队列"},
    {"draft_id": "id2", "status": "error", "message": "草稿不存在"}
  ]
}
```

#### v2 端点（推荐）
```http
POST /api/v2/drafts/batch/download

请求体:
{
  "draft_ids": ["id1", "id2", "id3"],
  "client_os": "windows",
  "draft_folder": "/path/to/folder"
}

响应:
{
  "success": true,
  "data": {
    "total": 3,
    "succeeded": 2,
    "failed": 1,
    "results": [
      {
        "draft_id": "id1",
        "success": true,
        "download_url": "https://..."
      },
      {
        "draft_id": "id2",
        "success": false,
        "error": "草稿不存在",
        "error_code": 4001
      }
    ]
  },
  "message": "批量下载完成：成功 2 个，失败 1 个"
}
```

**主要变化**：
1. ✅ URL 路径更清晰：`batch-download` → `batch/download`
2. ✅ 新增统计信息：`total`, `succeeded`, `failed`
3. ✅ 每个结果包含完整的下载 URL
4. ✅ 错误信息标准化（包含 `error_code`）
5. ✅ 单次最多支持 50 个草稿

---

### 4. 检查草稿状态（新增）

#### v2 端点（新功能）
```http
GET /api/v2/drafts/<draft_id>/status?client_os=windows&draft_folder=/path

响应:
{
  "success": true,
  "data": {
    "draft_id": "dfd_cat_xxx",
    "exists_in_oss": true,
    "exists_in_database": true,
    "exists_in_cache": true,
    "available_for_download": true,
    "file_size": 12345,
    "last_modified": "2025-11-17T12:00:00Z"
  },
  "message": "状态检查完成"
}
```

**说明**：
- 新增的状态检查端点，v1 无对应功能
- 可用于诊断草稿可用性问题
- 不触发任何修改操作

---

## 📊 错误响应格式变化

### v1 错误响应（不统一）
```json
{
  "success": false,
  "error": "草稿不存在"
}
```

### v2 错误响应（标准化）
```json
{
  "success": false,
  "error": "草稿不存在",
  "error_type": "DRAFT_NOT_FOUND",
  "error_code": 4001,
  "suggestion": "请确认草稿ID是否正确，或尝试重新创建草稿",
  "details": {
    "draft_id": "dfd_cat_xxx"
  }
}
```

**新增字段**：
- `error_type`: 错误类型（枚举值）
- `error_code`: 错误码（4xxx 客户端错误，5xxx 服务器错误）
- `suggestion`: 解决建议
- `details`: 详细信息（可选）

---

## 🔧 迁移步骤

### 步骤 1：识别使用的 v1 端点
```bash
# 搜索代码中的 v1 端点调用
grep -r "generate_draft_url" .
grep -r "download/proxy" .
grep -r "batch-download" .
```

### 步骤 2：更新 API 调用

#### Python 示例
```python
# v1 代码（旧）
response = requests.post('http://localhost:9000/generate_draft_url', json={
    'draft_id': draft_id,
    'client_os': 'windows'
})
url = response.json()['output']['draft_url']

# v2 代码（新）
response = requests.post(f'http://localhost:9000/api/v2/drafts/{draft_id}/download/url', json={
    'client_os': 'windows'
})
url = response.json()['data']['download_url']
```

#### JavaScript 示例
```javascript
// v1 代码（旧）
const response = await fetch('http://localhost:9000/generate_draft_url', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    draft_id: draftId,
    client_os: 'windows'
  })
});
const { output } = await response.json();
const url = output.draft_url;

// v2 代码（新）
const response = await fetch(`http://localhost:9000/api/v2/drafts/${draftId}/download/url`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    client_os: 'windows'
  })
});
const { data } = await response.json();
const url = data.download_url;
```

### 步骤 3：更新错误处理

#### Python 示例
```python
# v1 错误处理（旧）
if not response.json()['success']:
    error = response.json()['error']
    print(f"错误: {error}")

# v2 错误处理（新）
result = response.json()
if not result['success']:
    error_code = result['error_code']
    suggestion = result.get('suggestion', '')
    print(f"错误 {error_code}: {result['error']}")
    print(f"建议: {suggestion}")
```

### 步骤 4：测试和验证
1. 在测试环境中验证 v2 API
2. 检查响应格式是否符合预期
3. 确认错误处理逻辑正常工作
4. 逐步在生产环境中切换

---

## ⚠️ v1 端点废弃警告

调用 v1 端点时，响应会包含废弃警告：

### HTTP 响应头
```
X-API-Deprecated: true
X-API-Deprecation-Info: [DEPRECATED] 端点 generate_draft_url 已废弃，请迁移到 /api/v2/drafts/<draft_id>/download/url，将于 2025-02-15 下线
X-API-Alternative: /api/v2/drafts/<draft_id>/download/url
X-API-Sunset: 2025-02-15
```

### 响应体
```json
{
  "success": true,
  "output": { ... },
  "_deprecation_warning": {
    "message": "[DEPRECATED] 端点 generate_draft_url 已废弃，请迁移到 /api/v2/drafts/<draft_id>/download/url，将于 2025-02-15 下线",
    "deprecated": true,
    "alternative": "/api/v2/drafts/<draft_id>/download/url",
    "sunset_date": "2025-02-15"
  }
}
```

---

## 📈 v2 新增功能

### 1. 自动验证和修复
v2 端点自动包含以下功能：
- ✅ 草稿 ID 格式验证
- ✅ 草稿存在性检查
- ✅ 缺失文件自动重新生成
- ✅ 参数完整性验证

### 2. 限流保护
- 默认限流：10 次/分钟（可配置）
- 超过限制时返回 429 状态码
- 响应头包含 `Retry-After` 提示

### 3. 完整日志
- 每个请求自动记录日志
- 包含请求时间、客户端信息、处理结果
- 便于问题排查和性能分析

### 4. 统一错误码
| 错误码 | 类型 | 说明 |
|-------|------|------|
| 4000 | INVALID_DRAFT_ID | 无效的草稿ID |
| 4001 | DRAFT_NOT_FOUND | 草稿不存在 |
| 4002 | INVALID_PARAMETER | 参数格式错误 |
| 4003 | MISSING_PARAMETER | 缺少必需参数 |
| 4029 | RATE_LIMIT_EXCEEDED | 请求过于频繁 |
| 5000 | INTERNAL_ERROR | 服务器内部错误 |
| 5001 | OSS_ERROR | OSS存储服务错误 |
| 5004 | DOWNLOAD_FAILED | 下载失败 |

---

## 🆘 常见问题 (FAQ)

### Q1: v1 和 v2 可以同时使用吗？
**A**: 可以。在 90 天过渡期内（2025-11-17 至 2025-02-15），v1 和 v2 会并行运行。建议尽快迁移到 v2。

### Q2: v2 的性能如何？
**A**: v2 性能与 v1 相当，装饰器开销 < 1ms，可忽略不计。同时 v2 增加了缓存机制，某些场景下性能更优。

### Q3: 如何处理 draft_id 在 URL 中的问题？
**A**: v2 使用 RESTful 设计，`draft_id` 作为 URL 路径参数。记得对特殊字符进行 URL 编码：
```python
from urllib.parse import quote
encoded_id = quote(draft_id, safe='')
url = f'/api/v2/drafts/{encoded_id}/download/url'
```

### Q4: v2 错误响应格式和 v1 不兼容怎么办？
**A**: 建议创建一个适配器函数来处理响应格式差异：
```python
def parse_response(response):
    data = response.json()
    if 'output' in data:  # v1 格式
        return data['output']
    elif 'data' in data:  # v2 格式
        return data['data']
    else:
        raise ValueError("Unknown response format")
```

### Q5: 迁移后发现问题怎么办？
**A**:
1. 检查日志：`tail -f logs/capcutapi.log`
2. 使用状态检查端点：`GET /api/v2/drafts/<draft_id>/status`
3. 联系技术支持：GitHub Issues

---

## 📚 相关文档

- [API 使用示例](API_USAGE_EXAMPLES.md)
- [错误处理指南](../examples/decorators_usage_example.py)
- [架构分析报告](../DOWNLOAD_ARCHITECTURE_ANALYSIS.md)
- [优化实施总结](../IMPLEMENTATION_SUMMARY.md)

---

**迁移支持**：
如有任何问题，请提交 GitHub Issue 或联系技术支持团队。

**最后更新**：2025-11-17
**维护者**：CapCutAPI Team
