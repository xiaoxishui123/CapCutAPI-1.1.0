[根目录](../CLAUDE.md) > **pattern**

---

# pattern 模板库模块文档

> 最后更新时间：2025-11-11 22:20:59

## 变更记录 (Changelog)

### 2025-11-11 22:20:59
- 初始化 pattern 模板库模块文档
- 完成模块架构和功能分析

---

## 模块职责

`pattern` 模块是 CapCutAPI 项目的可复用视频编辑模板库，提供预定义的视频编辑流程和模板脚本。用户可以通过 API 快速应用这些模板，实现标准化的视频剪辑效果。

**核心功能**：
- 提供多种视频编辑模板（文案提取、关系图谱等）
- 支持模板列表查询和详情获取
- 支持模板文件下载
- 通过 `pattern_manager.py` 统一管理模板

**应用场景**：
- 批量视频剪辑
- 标准化视频生产流水线
- AI 驱动的视频编辑（结合 Coze、Dify 等平台）

---

## 入口与启动

### 模块访问入口
- **API 管理器**: `pattern_manager.py`（项目根目录）
- **REST API 端点**: `/api/patterns/*`

### API 端点
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/patterns/list` | GET | 列出所有模板 |
| `/api/patterns/get/<id>` | GET | 获取模板详情和内容 |
| `/api/patterns/download/<id>` | GET | 下载模板文件 |

### 使用示例
```bash
# 列出所有模板
curl http://localhost:9000/api/patterns/list

# 获取模板详情
curl http://localhost:9000/api/patterns/get/001-words

# 下载模板文件
curl http://localhost:9000/api/patterns/download/001-words -o 001-words.py
```

---

## 对外接口

### 模板结构
每个模板包含以下信息：
```json
{
    "id": "001-words",
    "name": "文案提取模板",
    "description": "从视频中提取文案并生成字幕",
    "version": "1.0.0",
    "author": "CapCutAPI Team",
    "file": "001-words.py",
    "coze_version": "001-words-coze.md",
    "tags": ["文案", "字幕", "AI"]
}
```

### 模板列表
当前模块包含以下模板：

#### 1. 001-words（文案提取模板）
- **文件**: `001-words.py`
- **Coze 版本**: `001-words-coze.md`
- **功能**: 从视频中提取文案内容
- **应用**: 自动字幕生成、文案分析

#### 2. 002-relationship（关系图谱模板）
- **文件**: `002-relationship.py`
- **功能**: 分析视频中的人物关系
- **应用**: 社交网络分析、关系可视化

### 模板开发规范
新增模板时，需遵循以下命名规范：
```
<编号>-<名称>.py          # Python 脚本
<编号>-<名称>-coze.md     # Coze 平台版本（可选）
```

示例：
```
003-highlight.py
003-highlight-coze.md
```

---

## 关键依赖与配置

### 依赖关系
- **pattern_manager.py**: 模板管理器，负责模板注册和查询
- **capcut_server.py**: 提供 REST API 端点

### 配置要点
- **模板目录**: `/home/CapCutAPI-1.1.0/pattern/`
- **README 文件**:
  - `QUICK_START.md` - 快速入门指南
  - `README.md` - 详细文档

---

## 数据模型

### 模板元数据
```python
class Pattern:
    id: str              # 模板唯一标识
    name: str            # 模板名称
    description: str     # 模板描述
    version: str         # 版本号
    author: str          # 作者
    file: str            # 脚本文件名
    coze_version: str    # Coze 版本文件名（可选）
    tags: List[str]      # 标签列表
```

### 模板执行流程
```
1. 客户端请求模板列表
   ↓
2. pattern_manager 扫描 pattern/ 目录
   ↓
3. 返回模板元数据列表
   ↓
4. 客户端选择并下载模板
   ↓
5. 客户端执行模板脚本
   ↓
6. 调用 CapCutAPI 生成草稿
```

---

## 测试与质量

### 测试文件
- **单元测试**: `test_pattern_api.py`（项目根目录）

### 运行测试
```bash
python test_pattern_api.py
```

### 测试用例
1. 模板列表查询
2. 模板详情获取
3. 模板文件下载
4. 模板脚本执行

---

## 常见问题 (FAQ)

### Q1: 如何创建新的模板？
1. 在 `pattern/` 目录下创建新的 Python 脚本：
```python
# pattern/003-highlight.py
import requests

def generate_highlight_video(video_url):
    """生成视频高光集锦"""
    # 调用 CapCutAPI
    response = requests.post("http://localhost:9000/create_draft", json={
        "width": 1080,
        "height": 1920
    })
    draft_id = response.json()["draft_id"]

    # 添加视频素材
    requests.post("http://localhost:9000/add_video", json={
        "draft_id": draft_id,
        "url": video_url
    })

    # 保存草稿
    requests.post("http://localhost:9000/save_draft", json={
        "draft_id": draft_id
    })

    return draft_id
```

2. 在 `pattern_manager.py` 中注册模板（如需要）

### Q2: 如何在 Coze 平台使用模板？
参考 `001-words-coze.md` 文件，它提供了 Coze 平台的集成步骤。

### Q3: 模板可以包含哪些操作？
模板可以调用所有 CapCutAPI 端点，包括：
- 创建草稿
- 添加视频、音频、文本
- 应用特效和转场
- 保存草稿

### Q4: 如何调试模板脚本？
```bash
# 直接运行模板脚本
python pattern/001-words.py

# 查看 API 日志
tail -f logs/capcutapi.log
```

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `001-words.py` | 文案提取模板脚本 |
| `001-words-coze.md` | 文案提取模板 Coze 版本 |
| `002-relationship.py` | 关系图谱模板脚本 |
| `QUICK_START.md` | 快速入门指南 |
| `README.md` | 详细文档 |

---

## 相关模块
- [根目录](../CLAUDE.md) - 项目总览
- [pattern_manager.py](../pattern_manager.py) - 模板管理器
- [capcut_server.py](../capcut_server.py) - REST API 服务

---

## 相关文档
- [Pattern 快速开始](QUICK_START.md) - 5分钟上手
- [Pattern 集成报告](../docs/PATTERN_INTEGRATION_REPORT.md) - 完整集成报告

---

**提示**: 模板开发时，建议先通过 REST Client 或 Postman 测试 API 调用，确认无误后再编写模板脚本。
