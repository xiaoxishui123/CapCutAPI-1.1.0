[根目录](../CLAUDE.md) > **pyJianYingDraft**

---

# pyJianYingDraft 模块文档

> 最后更新时间：2025-11-11 10:35:57

## 变更记录 (Changelog)

### 2025-11-11 10:35:57
- 初始化模块文档
- 完成模块架构分析

---

## 模块职责

`pyJianYingDraft` 是 CapCutAPI 项目的核心库，负责处理剪映（JianYing）和 CapCut 的草稿文件格式。它提供了完整的草稿文件读写、素材管理、特效应用、时间轴控制等功能。

**核心功能**：
- 草稿文件创建与序列化（`draft_folder.py`, `script_file.py`）
- 视频/音频/文本/图片素材对象封装
- 轨道（Track）管理和时间轴控制
- 元数据定义（字体、转场、动画、特效等）
- 关键帧（Keyframe）动画支持
- 时间范围（Timerange）和时间单位工具

---

## 入口与启动

### 模块导入入口
- **文件**: `__init__.py`
- **导出内容**: 所有核心类和元数据类型

```python
from pyJianYingDraft import (
    # 素材类
    Video_material, Audio_material,
    # 片段类
    Video_segment, Audio_segment, Text_segment, Effect_segment,
    # 草稿和脚本
    Script_file, Draft_folder,
    # 元数据
    Font_type, Mask_type, Transition_type, Filter_type,
    # 时间工具
    Timerange, SEC, tim, trange
)
```

### 主要入口类
1. **`Script_file`**: 草稿脚本对象，管理所有轨道和素材
2. **`Draft_folder`**: 草稿文件夹对象，处理草稿的保存和加载
3. **`Track_type`**: 轨道类型枚举（视频、音频、文本、特效等）

---

## 对外接口

### 核心类和方法

#### 1. Script_file（草稿脚本）
```python
# 创建草稿
script = draft.Script_file(width=1080, height=1920)

# 添加视频轨道
video_track = script.tracks.append(track_type=draft.Track_type.video)

# 添加视频片段
video_segment = draft.Video_segment(
    material=video_material,
    start=0,
    duration=10000000  # 微秒单位
)
video_track.segments.append(video_segment)

# 导出草稿数据
draft_data = script.dumps()
```

#### 2. Draft_folder（草稿文件夹）
```python
# 创建草稿文件夹
draft_folder = draft.Draft_folder(folder_path, draft_id)

# 保存草稿
draft_folder.save(script)

# 加载草稿
loaded_script = draft_folder.load()
```

#### 3. 素材对象
```python
# 视频素材
video_material = draft.Video_material(
    path="path/to/video.mp4",
    duration=10000000,
    width=1920,
    height=1080
)

# 音频素材
audio_material = draft.Audio_material(
    path="path/to/audio.mp3",
    duration=5000000
)

# 文本样式
text_style = draft.Text_style(
    font=draft.Font_type.ZY_Courage,
    font_color="#FF0000",
    font_size=30.0
)
```

#### 4. 元数据查询
```python
# 获取所有字体类型
fonts = draft.Font_type.all()

# 获取转场效果
transitions = draft.Transition_type.all()

# 获取动画类型
intros = draft.Intro_type.all()
outros = draft.Outro_type.all()
```

---

## 关键依赖与配置

### 依赖关系
- **无外部依赖**: 本模块为纯 Python 实现，不依赖第三方库
- **内部依赖**:
  - `time_util.py`: 时间单位转换和时间范围管理
  - `util.py`: 通用工具函数

### 配置要点
- **平台适配**: 通过 `settings/local.py` 的 `IS_CAPCUT_ENV` 字段区分剪映（JianYing）和 CapCut 国际版
- **元数据版本**: 不同平台的元数据定义在 `metadata/` 下分别维护

---

## 数据模型

### 核心数据结构

#### 1. 草稿结构层次
```
Script_file (草稿脚本)
├── tracks[] (轨道列表)
│   ├── video_tracks[] (视频轨道)
│   ├── audio_tracks[] (音频轨道)
│   ├── text_tracks[] (文本轨道)
│   └── effect_tracks[] (特效轨道)
├── materials{} (素材字典)
├── canvases[] (画布设置)
└── meta_info{} (元信息)
```

#### 2. 片段（Segment）类型
- **Video_segment**: 视频片段
- **Audio_segment**: 音频片段
- **Text_segment**: 文本片段
- **Effect_segment**: 特效片段
- **Filter_segment**: 滤镜片段
- **Sticker_segment**: 贴纸片段

#### 3. 时间模型
```python
# 时间单位：微秒（1秒 = 1,000,000 微秒）
SEC = 1000000

# 时间范围
timerange = draft.Timerange(start=0, duration=5*SEC)

# 时间工具函数
tim(seconds)      # 秒转微秒
trange(start, end) # 创建时间范围
```

#### 4. 关键帧（Keyframe）
```python
keyframe = draft.Keyframe_property(
    property_type="scale",
    value=1.5,
    time_offset=2*SEC
)
```

---

## 文件清单

### 核心文件
| 文件 | 职责 |
|------|------|
| `__init__.py` | 模块入口，导出所有公共接口 |
| `script_file.py` | 草稿脚本对象，核心数据结构 |
| `draft_folder.py` | 草稿文件夹管理，文件读写 |
| `track.py` | 轨道类型和轨道管理 |
| `segment.py` | 片段基类 |
| `video_segment.py` | 视频片段 |
| `audio_segment.py` | 音频片段 |
| `text_segment.py` | 文本片段 |
| `effect_segment.py` | 特效片段 |
| `local_materials.py` | 本地素材对象定义 |
| `time_util.py` | 时间单位和范围工具 |
| `util.py` | 通用工具函数 |
| `keyframe.py` | 关键帧动画 |
| `animation.py` | 动画效果 |
| `template_mode.py` | 模板模式（缩放、扩展） |
| `exceptions.py` | 自定义异常 |
| `jianying_controller.py` | 剪映控制器（UI 自动化） |
| `jianying_ui_inspector.py` | 剪映 UI 检查器 |

### 元数据目录 (`metadata/`)
| 文件 | 职责 |
|------|------|
| `font_meta.py` | 字体元数据 |
| `transition_meta.py` | 转场元数据（剪映） |
| `capcut_transition_meta.py` | 转场元数据（CapCut） |
| `animation_meta.py` | 动画元数据（剪映） |
| `capcut_animation_meta.py` | 动画元数据（CapCut） |
| `mask_meta.py` | 蒙版元数据（剪映） |
| `capcut_mask_meta.py` | 蒙版元数据（CapCut） |
| `effect_meta.py` | 特效元数据（剪映） |
| `capcut_effect_meta.py` | 特效元数据（CapCut） |
| `audio_effect_meta.py` | 音频特效元数据（剪映） |
| `capcut_audio_effect_meta.py` | 音频特效元数据（CapCut） |
| `video_effect_meta.py` | 视频特效元数据（剪映） |
| `filter_meta.py` | 滤镜元数据 |
| `capcut_text_animation_meta.py` | 文本动画元数据（CapCut） |

---

## 测试与质量

### 测试策略
- **外部测试**: 由父项目的 `test_template.py` 和 `example.py` 进行集成测试
- **无独立单元测试**: 当前模块没有独立的单元测试文件

### 质量工具
- **无 lint 配置**: 未发现独立的代码质量检查配置

### 建议改进
1. 添加单元测试覆盖核心类（Script_file, Draft_folder, Segment 等）
2. 添加 pytest 配置和测试夹具
3. 添加类型注解（Type Hints）以提升代码可读性
4. 添加 mypy 静态类型检查

---

## 常见问题 (FAQ)

### Q1: 如何创建一个简单的草稿？
```python
import pyJianYingDraft as draft

# 创建草稿（1080x1920 分辨率）
script = draft.Script_file(1080, 1920)

# 添加视频轨道
video_track = script.tracks.append(track_type=draft.Track_type.video)

# 创建视频素材
video_material = draft.Video_material(
    path="video.mp4",
    duration=10*draft.SEC,
    width=1920,
    height=1080
)

# 添加视频片段
video_segment = draft.Video_segment(
    material=video_material,
    start=0,
    duration=10*draft.SEC
)
video_track.segments.append(video_segment)

# 保存草稿
draft_folder = draft.Draft_folder("./output", "dfd_cat_123456_abc")
draft_folder.save(script)
```

### Q2: 如何区分剪映和 CapCut 国际版？
```python
from settings.local import IS_CAPCUT_ENV

if IS_CAPCUT_ENV:
    # 使用 CapCut 元数据
    transition = draft.CapCut_Transition_type.fade
else:
    # 使用剪映元数据
    transition = draft.Transition_type.fade
```

### Q3: 时间单位如何使用？
```python
# 时间单位为微秒
SEC = 1000000  # 1秒 = 1,000,000 微秒

# 使用 tim() 函数转换
duration = draft.tim(5)  # 5秒 = 5,000,000 微秒

# 使用 trange() 创建时间范围
timerange = draft.trange(0, 10)  # 0-10秒
```

### Q4: 如何获取所有可用的字体/特效列表？
```python
# 获取所有字体
fonts = draft.Font_type.all()

# 获取所有转场
transitions = draft.Transition_type.all()

# 获取所有动画
intros = draft.Intro_type.all()
```

---

## 相关模块
- [根目录](../CLAUDE.md) - 项目总览
- [mcp_bridge](../mcp_bridge/CLAUDE.md) - MCP 协议桥接服务
- [settings](../settings/CLAUDE.md) - 配置管理模块

---

**提示**: 本模块是 CapCutAPI 的核心依赖，修改需谨慎。建议通过上层 API 实现模块（`add_*_impl.py`）进行功能扩展。
