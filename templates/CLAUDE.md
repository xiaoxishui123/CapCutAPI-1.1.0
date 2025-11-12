[根目录](../CLAUDE.md) > **templates**

---

# templates 前端模板模块文档

> 最后更新时间：2025-11-11 22:20:59

## 变更记录 (Changelog)

### 2025-11-11 22:20:59
- 初始化 templates 前端模板模块文档
- 完成模块架构和功能分析

---

## 模块职责

`templates` 模块是 CapCutAPI 项目的前端页面模板目录，包含 Flask 应用的 HTML 模板文件。这些模板提供了草稿预览、管理仪表板、下载向导等用户界面。

**核心功能**：
- 草稿预览页面（官方版和优化版）
- 草稿管理仪表板
- 下载向导和调试页面
- 响应式 Web 界面

**技术栈**：
- Jinja2 模板引擎（Flask 默认）
- Bootstrap 5（CSS 框架）
- JavaScript（交互逻辑）

---

## 入口与启动

### 模板渲染入口
Flask 应用通过 `render_template()` 函数渲染模板：

```python
# capcut_server.py
from flask import render_template

@app.route('/draft/preview/<draft_id>')
def draft_preview(draft_id):
    return render_template('preview.html', draft_id=draft_id)
```

### 访问路由
| 模板文件 | 访问路由 | 说明 |
|---------|---------|------|
| `index.html` | `/` | 主页（欢迎页面） |
| `preview.html` | `/draft/preview/<draft_id>` | 草稿预览页面（优化版） |
| `preview_official.html` | `/draft/preview_official/<draft_id>` | 草稿预览页面（官方版） |
| `dashboard.html` | `/api/drafts/dashboard` | 草稿管理仪表板 |
| `dashboard_static_preview.html` | - | 仪表板静态预览版 |
| `download_guide.html` | `/draft/downloader/<draft_id>` | 下载向导页面 |
| `debug_download.html` | - | 下载调试页面 |
| `test.html` | - | 测试页面 |

---

## 对外接口

### 页面功能

#### 1. index.html（主页）
- **功能**: 项目欢迎页面，展示 CapCutAPI 介绍
- **路由**: `/`
- **特性**:
  - 项目简介
  - 快速开始指南
  - API 端点列表
  - 文档链接

#### 2. preview.html（草稿预览）
- **功能**: 在线预览草稿内容和结构
- **路由**: `/draft/preview/<draft_id>`
- **特性**:
  - 草稿元信息展示（分辨率、时长、素材数量）
  - 素材列表（视频、音频、文本等）
  - 轨道可视化
  - 下载链接

#### 3. dashboard.html（管理仪表板）
- **功能**: 草稿管理和批量操作
- **路由**: `/api/drafts/dashboard`
- **特性**:
  - 草稿列表展示
  - 批量下载
  - 草稿删除
  - 搜索和过滤
  - 统计信息

#### 4. download_guide.html（下载向导）
- **功能**: 引导用户下载草稿到本地
- **路由**: `/draft/downloader/<draft_id>`
- **特性**:
  - 跨平台下载说明（Windows、Linux、macOS）
  - 一键复制草稿路径
  - 下载状态检测
  - 错误提示和故障排除

#### 5. debug_download.html（调试页面）
- **功能**: 调试草稿下载问题
- **特性**:
  - 显示详细的下载信息
  - OSS 签名 URL 检查
  - 网络连通性测试

---

## 关键依赖与配置

### 依赖关系
- **Flask**: Jinja2 模板引擎
- **Bootstrap 5**: CSS 框架（通过 CDN 引入）
- **JavaScript**: 前端交互逻辑

### 模板变量
Flask 应用向模板传递的常见变量：

```python
# 草稿预览页面
render_template('preview.html',
    draft_id='dfd_cat_123456_abc',
    draft_info={
        'width': 1080,
        'height': 1920,
        'duration': 10000000,
        'materials': [...]
    }
)

# 仪表板页面
render_template('dashboard.html',
    drafts=[
        {
            'id': 'draft_1',
            'name': '我的草稿',
            'created_at': '2025-11-11 10:00:00',
            'status': 'completed'
        },
        ...
    ]
)
```

---

## 数据模型

### 草稿预览数据结构
```json
{
    "draft_id": "dfd_cat_1234567890_abc123",
    "meta_info": {
        "width": 1080,
        "height": 1920,
        "duration": 10000000,
        "fps": 30
    },
    "materials": [
        {
            "type": "video",
            "name": "sample.mp4",
            "path": "/path/to/sample.mp4",
            "duration": 5000000
        },
        {
            "type": "audio",
            "name": "bgm.mp3",
            "path": "/path/to/bgm.mp3",
            "duration": 3000000
        }
    ],
    "tracks": [
        {
            "type": "video",
            "segments": [...]
        },
        {
            "type": "audio",
            "segments": [...]
        }
    ]
}
```

---

## 测试与质量

### 测试策略
- **手动测试**: 在浏览器中访问各个页面，检查布局和交互
- **跨浏览器测试**: Chrome、Firefox、Safari、Edge
- **响应式测试**: 桌面、平板、移动设备

### 测试工具
```bash
# 启动服务
python capcut_server.py

# 访问页面
open http://localhost:9000/
open http://localhost:9000/draft/preview/dfd_cat_123456_abc
open http://localhost:9000/api/drafts/dashboard
```

---

## 常见问题 (FAQ)

### Q1: 如何自定义页面样式？
修改模板文件中的 CSS 样式：
```html
<!-- templates/preview.html -->
<style>
    .custom-class {
        color: blue;
        font-size: 16px;
    }
</style>
```

或引入外部 CSS 文件（放在 `static/` 目录）：
```html
<link rel="stylesheet" href="{{ url_for('static', filename='custom.css') }}">
```

### Q2: 如何添加新的页面？
1. 在 `templates/` 目录下创建新的 HTML 文件：
```html
<!-- templates/my_page.html -->
<!DOCTYPE html>
<html>
<head>
    <title>我的页面</title>
</head>
<body>
    <h1>{{ title }}</h1>
    <p>{{ content }}</p>
</body>
</html>
```

2. 在 `capcut_server.py` 中添加路由：
```python
@app.route('/my-page')
def my_page():
    return render_template('my_page.html',
        title='我的页面',
        content='这是一个示例页面'
    )
```

### Q3: 如何在模板中使用 JavaScript？
```html
<script>
    function handleButtonClick() {
        fetch('/api/drafts/list')
            .then(response => response.json())
            .then(data => {
                console.log(data);
            });
    }
</script>
```

### Q4: 如何传递复杂数据到模板？
```python
# capcut_server.py
@app.route('/complex-page')
def complex_page():
    return render_template('complex.html',
        user={'name': 'Alice', 'age': 30},
        items=['item1', 'item2', 'item3'],
        config={'debug': True}
    )
```

```html
<!-- templates/complex.html -->
<p>用户名: {{ user.name }}</p>
<p>年龄: {{ user.age }}</p>
<ul>
    {% for item in items %}
    <li>{{ item }}</li>
    {% endfor %}
</ul>
```

---

## 文件清单

| 文件 | 职责 | 路由 |
|------|------|------|
| `index.html` | 项目主页 | `/` |
| `preview.html` | 草稿预览页面（优化版） | `/draft/preview/<draft_id>` |
| `preview_official.html` | 草稿预览页面（官方版） | `/draft/preview_official/<draft_id>` |
| `dashboard.html` | 草稿管理仪表板 | `/api/drafts/dashboard` |
| `dashboard_static_preview.html` | 仪表板静态预览 | - |
| `download_guide.html` | 下载向导 | `/draft/downloader/<draft_id>` |
| `debug_download.html` | 下载调试页面 | - |
| `test.html` | 测试页面 | - |
| `README_LiveServer.md` | Live Server 使用说明 | - |

---

## 相关模块
- [根目录](../CLAUDE.md) - 项目总览
- [static](../static/) - 静态资源目录
- [capcut_server.py](../capcut_server.py) - Flask 应用主入口

---

**提示**: 修改模板文件后，Flask 应用会自动重新加载（开发模式下）。生产环境建议使用模板缓存提升性能。
