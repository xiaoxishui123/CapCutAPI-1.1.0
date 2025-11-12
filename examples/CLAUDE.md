[根目录](../CLAUDE.md) > **examples**

---

# examples 使用示例模块文档

> 最后更新时间：2025-11-11 22:43:46

## 变更记录 (Changelog)

### 2025-11-11 22:43:46
- 初始化 examples 使用示例模块文档
- 完成模块架构和功能分析

---

## 模块职责

`examples` 模块是 CapCutAPI 项目的使用示例目录，包含各种功能的演示代码和最佳实践。这些示例帮助开发者快速上手 CapCutAPI 的各项功能。

**核心功能**：
- 功能演示代码
- 最佳实践示例
- 常见场景实现

**目标用户**：
- 新手开发者（快速入门）
- 集成开发者（参考实现）
- API 使用者（代码模板）

---

## 文件清单

### 1. relative_path_example.py
**功能**: 相对路径使用示例

**演示内容**:
- 如何使用相对路径指定草稿目录
- 如何处理跨平台路径问题
- 如何配置自定义路径

**代码结构**:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相对路径使用示例

演示如何在 CapCutAPI 中使用相对路径：
- 相对于当前工作目录的路径
- 用户主目录（~）路径
- 上级目录路径
"""

import requests

API_BASE = "http://localhost:9000"

def example_relative_path():
    """示例: 使用相对路径创建草稿"""

    # 1. 相对于当前目录
    response = requests.post(f"{API_BASE}/create_draft", json={
        "width": 1080,
        "height": 1920,
        "draft_folder": "./my_drafts"  # 相对路径
    })

    # 2. 用户主目录
    response = requests.post(f"{API_BASE}/create_draft", json={
        "width": 1080,
        "height": 1920,
        "draft_folder": "~/Documents/Drafts"  # ~ 扩展
    })

    # 3. 上级目录
    response = requests.post(f"{API_BASE}/create_draft", json={
        "width": 1080,
        "height": 1920,
        "draft_folder": "../output/drafts"  # 上级目录
    })

    return response.json()

def example_cross_platform():
    """示例: 跨平台路径处理"""

    # 指定客户端操作系统
    response = requests.post(f"{API_BASE}/create_draft", json={
        "width": 1080,
        "height": 1920,
        "client_os": "windows",  # 或 "linux", "darwin"
        "draft_folder": "C:\\Users\\Admin\\Drafts"  # Windows 路径
    })

    return response.json()

if __name__ == "__main__":
    # 运行示例
    result = example_relative_path()
    print(f"草稿 ID: {result['draft_id']}")
```

**使用方法**:
```bash
# 运行示例
python examples/relative_path_example.py

# 修改示例
vim examples/relative_path_example.py
```

**学习要点**:
1. ✅ 相对路径自动解析为绝对路径
2. ✅ `~` 自动扩展为用户主目录
3. ✅ 支持 `./` 和 `../` 路径
4. ✅ 跨平台路径自动转换

---

## 示例分类

### 基础示例
| 示例 | 文件 | 说明 |
|------|------|------|
| 相对路径 | `relative_path_example.py` | 演示相对路径和跨平台路径处理 |

### 推荐新增示例
| 功能 | 建议文件名 | 说明 |
|------|----------|------|
| 完整工作流 | `complete_workflow_example.py` | 从创建到保存的完整流程 |
| 视频编辑 | `video_editing_example.py` | 添加视频、转场、特效 |
| 字幕生成 | `subtitle_generation_example.py` | 自动生成和添加字幕 |
| 批量处理 | `batch_processing_example.py` | 批量创建和编辑草稿 |
| 模板应用 | `template_application_example.py` | 使用 Pattern 模板 |
| MCP 集成 | `mcp_integration_example.py` | MCP 协议调用示例 |
| 错误处理 | `error_handling_example.py` | 异常处理和重试机制 |

---

## 使用指南

### 如何运行示例
1. **确保服务运行**:
   ```bash
   ./service_manager.sh status
   ```

2. **安装依赖**:
   ```bash
   pip install requests
   ```

3. **运行示例**:
   ```bash
   python examples/relative_path_example.py
   ```

4. **查看结果**:
   ```bash
   # 检查生成的草稿
   ls -la drafts/

   # 查看日志
   tail -f logs/capcutapi.log
   ```

### 如何修改示例
1. **复制示例文件**:
   ```bash
   cp examples/relative_path_example.py examples/my_example.py
   ```

2. **修改代码**:
   ```python
   # 修改 API 参数
   response = requests.post(f"{API_BASE}/create_draft", json={
       "width": 1280,  # 修改分辨率
       "height": 720,
       "draft_folder": "./my_custom_drafts"
   })
   ```

3. **运行测试**:
   ```bash
   python examples/my_example.py
   ```

---

## 常见场景示例

### 场景 1: 创建基础视频草稿
```python
import requests

API_BASE = "http://localhost:9000"

def create_simple_video():
    """创建一个简单的视频草稿"""

    # 1. 创建草稿
    draft_res = requests.post(f"{API_BASE}/create_draft", json={
        "width": 1080,
        "height": 1920
    })
    draft_id = draft_res.json()["draft_id"]

    # 2. 添加视频
    video_res = requests.post(f"{API_BASE}/add_video", json={
        "draft_id": draft_id,
        "url": "https://example.com/video.mp4"
    })

    # 3. 保存草稿
    save_res = requests.post(f"{API_BASE}/save_draft", json={
        "draft_id": draft_id
    })

    return save_res.json()
```

### 场景 2: 添加文字和字幕
```python
def add_text_and_subtitle(draft_id):
    """添加文字和字幕"""

    # 1. 添加文本
    text_res = requests.post(f"{API_BASE}/add_text", json={
        "draft_id": draft_id,
        "content": "欢迎使用 CapCutAPI",
        "font": "思源黑体",
        "font_size": 48,
        "font_color": "#FFFFFF",
        "position": {"x": 0.5, "y": 0.1}
    })

    # 2. 添加字幕
    subtitle_res = requests.post(f"{API_BASE}/add_subtitle", json={
        "draft_id": draft_id,
        "text": "这是一段字幕",
        "start_time": 0,
        "duration": 5000000
    })

    return text_res.json(), subtitle_res.json()
```

### 场景 3: 应用转场和特效
```python
def apply_effects(draft_id):
    """应用转场和特效"""

    # 1. 添加转场
    transition_res = requests.post(f"{API_BASE}/add_transition", json={
        "draft_id": draft_id,
        "type": "fade",
        "duration": 1000000
    })

    # 2. 添加特效
    effect_res = requests.post(f"{API_BASE}/add_effect", json={
        "draft_id": draft_id,
        "effect_type": "blur",
        "intensity": 0.5
    })

    return transition_res.json(), effect_res.json()
```

### 场景 4: 批量处理视频
```python
def batch_process_videos(video_urls):
    """批量处理多个视频"""

    results = []

    for url in video_urls:
        # 创建草稿
        draft_res = requests.post(f"{API_BASE}/create_draft", json={
            "width": 1080,
            "height": 1920
        })
        draft_id = draft_res.json()["draft_id"]

        # 添加视频
        requests.post(f"{API_BASE}/add_video", json={
            "draft_id": draft_id,
            "url": url
        })

        # 保存草稿
        save_res = requests.post(f"{API_BASE}/save_draft", json={
            "draft_id": draft_id
        })

        results.append(save_res.json())

    return results
```

---

## 常见问题 (FAQ)

### Q1: 示例代码运行报错"连接被拒绝"？
**解决方案**:
1. 检查服务是否运行：
   ```bash
   ./service_manager.sh status
   ```
2. 确认端口号正确（默认 9000）
3. 修改 `API_BASE` 变量

### Q2: 如何调试示例代码？
**方法**:
1. 添加详细日志：
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
2. 打印响应内容：
   ```python
   response = requests.post(...)
   print(response.text)
   ```
3. 查看服务器日志：
   ```bash
   tail -f logs/capcutapi.log
   ```

### Q3: 如何扩展示例？
**步骤**:
1. 复制现有示例作为模板
2. 参考 [API_USAGE_EXAMPLES.md](../docs/API_USAGE_EXAMPLES.md)
3. 添加错误处理和日志
4. 提交 Pull Request 贡献示例

### Q4: 示例中的路径在 Windows 下无效？
**解决方案**:
使用 `os.path.join()` 或原始字符串：
```python
import os

# 方法 1: os.path.join
draft_folder = os.path.join(".", "my_drafts")

# 方法 2: 原始字符串
draft_folder = r".\my_drafts"

# 方法 3: 转义反斜杠
draft_folder = ".\\my_drafts"
```

---

## 贡献示例

### 提交新示例
欢迎贡献新的示例代码！请遵循以下规范：

**1. 文件命名**:
```
<功能描述>_example.py
```
示例: `video_editing_example.py`

**2. 代码结构**:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例名称: 视频编辑示例

功能描述:
- 创建草稿
- 添加多个视频
- 应用转场和特效
- 保存草稿

使用方法:
    python examples/video_editing_example.py
"""

import requests

API_BASE = "http://localhost:9000"

def main():
    """主函数"""
    print("开始视频编辑示例...")

    # 实现逻辑
    # ...

    print("示例完成！")

if __name__ == "__main__":
    main()
```

**3. 注释规范**:
- 每个函数添加文档字符串
- 关键步骤添加注释
- 复杂逻辑添加说明

**4. 错误处理**:
```python
try:
    response = requests.post(...)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
    return None
```

---

## 相关模块
- [根目录](../CLAUDE.md) - 项目总览
- [API 文档](../docs/API_USAGE_EXAMPLES.md) - 完整 API 说明
- [pattern](../pattern/CLAUDE.md) - 模板库
- [test_api.py](../test_api.py) - API 测试用例

---

**提示**: examples 目录是学习 CapCutAPI 的最佳起点。建议先运行现有示例，再根据需求修改和扩展。
