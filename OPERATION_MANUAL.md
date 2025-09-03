# CapCutAPI 操作手册

## 📖 文档概述

本操作手册提供CapCutAPI v1.2.0的完整使用指南，包括功能介绍、操作步骤、API调用示例和故障排除等内容。

### 文档结构
- **快速开始**: 基础操作流程
- **功能详解**: 各功能模块详细说明
- **API参考**: 完整的API调用指南
- **用户界面**: Web界面使用说明
- **高级功能**: 批量处理和云端存储
- **故障排除**: 常见问题解决方案

## 🚀 快速开始

### 服务访问信息

- **服务地址**: http://8.148.70.18:9000
- **服务状态**: ✅ 运行中
- **API版本**: v1.2.0

### 基础操作流程

#### 1. 创建第一个草稿

```bash
# 使用curl创建草稿
curl -X POST http://8.148.70.18:9000/create_draft \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "my_first_draft",
    "width": 1080,
    "height": 1920
  }'
```

#### 2. 添加视频素材

```bash
# 添加视频到草稿
curl -X POST http://8.148.70.18:9000/add_video \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "my_first_draft",
    "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
    "start": 0,
    "end": 10,
    "width": 1080,
    "height": 1920
  }'
```

#### 3. 保存草稿

```bash
# 保存草稿到云端
curl -X POST http://8.148.70.18:9000/save_draft \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "my_first_draft"
  }'
```

## 🎯 功能详解

### 1. 草稿管理功能

#### 1.1 创建草稿

**功能描述**: 创建新的剪映草稿项目

**API端点**: `POST /create_draft`

**请求参数**:
```json
{
  "draft_id": "string",     // 草稿唯一标识符
  "width": 1080,            // 视频宽度（像素）
  "height": 1920           // 视频高度（像素）
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "草稿创建成功",
  "draft_id": "my_first_draft",
  "timestamp": "2025-01-21T10:30:00Z"
}
```

**使用场景**:
- 开始新的视频项目
- 设置视频基本参数
- 初始化草稿环境

#### 1.2 保存草稿

**功能描述**: 将草稿保存到本地或云端存储

**API端点**: `POST /save_draft`

**请求参数**:
```json
{
  "draft_id": "string",           // 草稿ID
  "draft_folder": "string"       // 可选：本地保存路径
}
```

**云端保存模式**（推荐）:
```json
{
  "draft_id": "my_first_draft"
}
```

**本地保存模式**:
```json
{
  "draft_id": "my_first_draft",
  "draft_folder": "/path/to/capcut/drafts"
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "草稿保存成功",
  "draft_id": "my_first_draft",
  "save_path": "cloud://oss-bucket/drafts/my_first_draft.zip",
  "download_url": "https://example.oss.com/drafts/my_first_draft.zip"
}
```

#### 1.3 获取草稿列表

**功能描述**: 查询所有可用的草稿

**API端点**: `GET /api/drafts/list`

**响应示例**:
```json
{
  "status": "success",
  "drafts": [
    {
      "draft_id": "my_first_draft",
      "source": "cache",
      "modified_time": "2025-01-21T10:30:00Z",
      "file_size": "2.5MB",
      "video_count": 1,
      "audio_count": 0,
      "text_count": 0,
      "image_count": 0
    }
  ],
  "total_count": 1
}
```

### 2. 素材管理功能

#### 2.1 添加视频素材

**功能描述**: 向草稿添加视频文件

**API端点**: `POST /add_video`

**请求参数**:
```json
{
  "draft_id": "string",       // 草稿ID
  "video_url": "string",     // 视频文件URL
  "start": 0,                 // 开始时间（秒）
  "end": 10,                  // 结束时间（秒）
  "width": 1080,              // 视频宽度
  "height": 1920,             // 视频高度
  "speed": 1.0,               // 播放速度（可选）
  "volume": 1.0               // 音量（可选）
}
```

**高级参数**:
```json
{
  "draft_id": "my_draft",
  "video_url": "https://example.com/video.mp4",
  "start": 5,
  "end": 25,
  "width": 1080,
  "height": 1920,
  "speed": 1.5,               // 1.5倍速播放
  "volume": 0.8,              // 80%音量
  "position_x": 0.5,          // X轴位置（0-1）
  "position_y": 0.5           // Y轴位置（0-1）
}
```

#### 2.2 添加音频素材

**功能描述**: 向草稿添加背景音乐或音效

**API端点**: `POST /add_audio`

**请求参数**:
```json
{
  "draft_id": "string",       // 草稿ID
  "audio_url": "string",     // 音频文件URL
  "start": 0,                 // 开始时间（秒）
  "end": 30,                  // 结束时间（秒）
  "volume": 1.0,              // 音量（0-1）
  "fade_in": 1.0,             // 淡入时长（可选）
  "fade_out": 1.0             // 淡出时长（可选）
}
```

#### 2.3 添加文本素材

**功能描述**: 向草稿添加文字标题或说明

**API端点**: `POST /add_text`

**请求参数**:
```json
{
  "draft_id": "string",       // 草稿ID
  "text": "string",           // 文本内容
  "start": 0,                 // 开始时间（秒）
  "end": 5,                   // 结束时间（秒）
  "font": "ZY_Courage",       // 字体名称
  "font_color": "#FF0000",    // 字体颜色
  "font_size": 30.0,          // 字体大小
  "position_x": 0.5,          // X轴位置（0-1）
  "position_y": 0.5           // Y轴位置（0-1）
}
```

**字体选择**:
```bash
# 获取可用字体列表
curl http://8.148.70.18:9000/get_font_types
```

**高级文本样式**:
```json
{
  "draft_id": "my_draft",
  "text": "欢迎使用CapCutAPI",
  "start": 0,
  "end": 5,
  "font": "ZY_Courage",
  "font_color": "#FFFFFF",
  "font_size": 48.0,
  "position_x": 0.5,
  "position_y": 0.8,
  "stroke_color": "#000000",   // 描边颜色
  "stroke_width": 2.0,         // 描边宽度
  "shadow_color": "#808080",   // 阴影颜色
  "shadow_offset_x": 2,        // 阴影X偏移
  "shadow_offset_y": 2         // 阴影Y偏移
}
```

#### 2.4 添加图片素材

**功能描述**: 向草稿添加图片或图标

**API端点**: `POST /add_image`

**请求参数**:
```json
{
  "draft_id": "string",       // 草稿ID
  "image_url": "string",     // 图片文件URL
  "start": 0,                 // 开始时间（秒）
  "end": 5,                   // 结束时间（秒）
  "width": 500,               // 图片宽度
  "height": 500,              // 图片高度
  "position_x": 0.5,          // X轴位置（0-1）
  "position_y": 0.5           // Y轴位置（0-1）
}
```

#### 2.5 添加字幕

**功能描述**: 向草稿添加字幕文本

**API端点**: `POST /add_subtitle`

**请求参数**:
```json
{
  "draft_id": "string",       // 草稿ID
  "subtitle_text": "string", // 字幕内容
  "start": 0,                 // 开始时间（秒）
  "end": 3,                   // 结束时间（秒）
  "font": "ZY_Courage",       // 字体名称
  "font_color": "#FFFFFF",    // 字体颜色
  "font_size": 24.0           // 字体大小
}
```

### 3. 特效与动画功能

#### 3.1 添加转场效果

**功能描述**: 在视频片段间添加转场动画

**API端点**: `POST /add_effect`

**请求参数**:
```json
{
  "draft_id": "string",       // 草稿ID
  "effect_type": "Transition", // 效果类型
  "effect_name": "Fade",      // 效果名称
  "start": 10,                // 开始时间（秒）
  "end": 11,                  // 结束时间（秒）
  "intensity": 1.0            // 效果强度（可选）
}
```

**获取可用转场类型**:
```bash
curl http://8.148.70.18:9000/get_transition_types
```

#### 3.2 添加动画效果

**入场动画**:
```bash
# 获取入场动画类型
curl http://8.148.70.18:9000/get_intro_animation_types
```

**出场动画**:
```bash
# 获取出场动画类型
curl http://8.148.70.18:9000/get_outro_animation_types
```

**添加动画示例**:
```json
{
  "draft_id": "my_draft",
  "effect_type": "Animation",
  "effect_name": "FadeIn",
  "target_element": "text_1",  // 目标元素ID
  "start": 0,
  "end": 1,
  "easing": "ease-in-out"       // 缓动函数
}
```

## 🖥️ 用户界面操作

### 1. 主页访问

**访问地址**: http://8.148.70.18:9000

**功能特点**:
- 🏠 欢迎页面展示
- 📊 服务状态信息
- 🔗 快速功能入口
- 📖 API文档链接

**操作步骤**:
1. 在浏览器中打开服务地址
2. 查看服务状态和可用功能
3. 点击相应按钮进入功能页面

### 2. 草稿管理仪表板

**访问地址**: http://8.148.70.18:9000/api/drafts/dashboard

**功能特点**:
- 📋 草稿列表展示
- 🔍 搜索和筛选
- 📊 统计信息显示
- 🎬 预览功能
- 📥 下载功能
- 🗑️ 删除功能

**操作步骤**:

#### 2.1 查看草稿列表
1. 访问仪表板页面
2. 系统自动加载所有可用草稿
3. 查看草稿基本信息（ID、修改时间、大小等）

#### 2.2 搜索草稿
1. 在搜索框中输入草稿ID关键词
2. 系统实时过滤显示匹配的草稿
3. 清空搜索框显示所有草稿

#### 2.3 预览草稿
1. 点击草稿项目的"预览"按钮
2. 系统跳转到草稿预览页面
3. 查看草稿详细内容和时间轴

#### 2.4 下载草稿
1. 点击草稿项目的"下载"按钮
2. 系统跳转到下载页面
3. 配置下载参数并开始下载

#### 2.5 删除草稿
1. 点击草稿项目的"删除"按钮
2. 确认删除操作
3. 系统删除草稿并刷新列表

### 3. 草稿预览界面

**访问地址**: http://8.148.70.18:9000/draft/preview/[草稿ID]

**功能特点**:
- 🎬 沉浸式预览体验
- 📊 素材统计信息
- ⏱️ 交互式时间轴
- 🎯 素材详情展示
- 🎨 专业视觉设计

**操作步骤**:

#### 3.1 查看草稿概览
1. 页面顶部显示草稿基本信息
2. 统计卡片显示各类素材数量
3. 总时长和创建时间信息

#### 3.2 时间轴交互
1. 点击时间轴上的素材轨道
2. 查看对应时间点的素材信息
3. 预览区域显示素材详情

#### 3.3 素材详情查看
1. 选择不同类型的素材轨道
2. 查看素材的具体参数
3. 了解素材的时间范围和属性

### 4. 草稿下载界面

**访问地址**: http://8.148.70.18:9000/draft/downloader?draft_id=[草稿ID]

**功能特点**:
- 🔍 自动检测云端文件
- 💻 多平台路径适配
- 📊 下载进度显示
- ⚙️ 路径配置功能
- 🔄 错误重试机制

**操作步骤**:

#### 4.1 配置下载参数
1. 选择目标操作系统（Windows/Linux/macOS）
2. 设置本地草稿文件夹路径
3. 预览生成的目标路径

#### 4.2 开始下载
1. 点击"开始下载"按钮
2. 系统检测云端文件状态
3. 显示下载进度和状态

#### 4.3 处理下载结果
1. 下载成功：显示本地保存路径
2. 下载失败：显示错误信息和重试选项
3. 查看详细的下载日志

## 🚀 高级功能

### 1. 批量下载功能

**功能描述**: 一次性下载多个草稿文件

**API端点**: `POST /api/drafts/batch-download`

**请求参数**:
```json
{
  "draft_ids": ["draft1", "draft2", "draft3"],
  "client_os": "windows",
  "draft_folder": "F:/jianyin/cgwz/JianyingPro Drafts"
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "批量下载完成",
  "results": [
    {
      "draft_id": "draft1",
      "status": "success",
      "local_path": "F:/jianyin/cgwz/JianyingPro Drafts/draft1"
    },
    {
      "draft_id": "draft2",
      "status": "failed",
      "error": "文件不存在"
    }
  ],
  "success_count": 1,
  "failed_count": 1
}
```

**使用场景**:
- 批量备份草稿
- 项目迁移
- 团队协作文件分发

### 2. 云端URL生成

**功能描述**: 生成草稿的云端下载链接

**API端点**: `POST /generate_draft_url`

**标准直链生成**:
```json
{
  "draft_id": "my_draft"
}
```

**定制化链接生成**:
```json
{
  "draft_id": "my_draft",
  "client_os": "windows",
  "draft_folder": "F:/jianyin/cgwz/JianyingPro Drafts"
}
```

**强制保存并生成**:
```json
{
  "draft_id": "my_draft",
  "force_save": true
}
```

**响应示例**:
```json
{
  "status": "success",
  "download_url": "https://example.oss.com/drafts/my_draft_windows.zip",
  "file_size": "2.5MB",
  "expires_at": "2025-01-22T10:30:00Z"
}
```

### 3. 调试和监控

#### 3.1 草稿缓存调试

**API端点**: `GET /debug/cache/[草稿ID]`

**功能**: 查看草稿在缓存中的详细信息

```bash
curl http://8.148.70.18:9000/debug/cache/my_draft
```

#### 3.2 系统状态监控

**API端点**: `GET /api/status`

**功能**: 获取系统运行状态和统计信息

```bash
curl http://8.148.70.18:9000/api/status
```

## 📝 完整示例

### 示例1：创建简单视频项目

```python
import requests
import time

# 服务器地址
BASE_URL = "http://8.148.70.18:9000"

def create_simple_video():
    """创建一个包含视频和文本的简单项目"""
    
    # 1. 创建草稿
    print("步骤1: 创建草稿...")
    response = requests.post(f"{BASE_URL}/create_draft", json={
        "draft_id": "simple_video_001",
        "width": 1080,
        "height": 1920
    })
    print(f"创建结果: {response.json()}")
    
    # 2. 添加视频
    print("\n步骤2: 添加视频...")
    response = requests.post(f"{BASE_URL}/add_video", json={
        "draft_id": "simple_video_001",
        "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
        "start": 0,
        "end": 15,
        "width": 1080,
        "height": 1920
    })
    print(f"添加视频结果: {response.json()}")
    
    # 3. 添加标题文本
    print("\n步骤3: 添加标题...")
    response = requests.post(f"{BASE_URL}/add_text", json={
        "draft_id": "simple_video_001",
        "text": "我的第一个视频",
        "start": 0,
        "end": 5,
        "font": "ZY_Courage",
        "font_color": "#FFFFFF",
        "font_size": 48.0,
        "position_x": 0.5,
        "position_y": 0.2
    })
    print(f"添加文本结果: {response.json()}")
    
    # 4. 添加字幕
    print("\n步骤4: 添加字幕...")
    response = requests.post(f"{BASE_URL}/add_subtitle", json={
        "draft_id": "simple_video_001",
        "subtitle_text": "欢迎观看我的视频内容",
        "start": 5,
        "end": 10,
        "font": "ZY_Courage",
        "font_color": "#FFFF00",
        "font_size": 28.0
    })
    print(f"添加字幕结果: {response.json()}")
    
    # 5. 保存草稿
    print("\n步骤5: 保存草稿...")
    response = requests.post(f"{BASE_URL}/save_draft", json={
        "draft_id": "simple_video_001"
    })
    result = response.json()
    print(f"保存结果: {result}")
    
    # 6. 生成下载链接
    if result.get("status") == "success":
        print("\n步骤6: 生成下载链接...")
        response = requests.post(f"{BASE_URL}/generate_draft_url", json={
            "draft_id": "simple_video_001",
            "client_os": "windows",
            "draft_folder": "F:/jianyin/cgwz/JianyingPro Drafts"
        })
        download_info = response.json()
        print(f"下载链接: {download_info}")
        
        if download_info.get("download_url"):
            print(f"\n✅ 项目创建完成！")
            print(f"📥 下载地址: {download_info['download_url']}")
            print(f"🎬 预览地址: {BASE_URL}/draft/preview/simple_video_001")
            print(f"📊 管理地址: {BASE_URL}/api/drafts/dashboard")

if __name__ == "__main__":
    create_simple_video()
```

### 示例2：批量处理多个草稿

```python
import requests
import json

BASE_URL = "http://8.148.70.18:9000"

def batch_process_drafts():
    """批量处理多个草稿的示例"""
    
    # 草稿配置列表
    draft_configs = [
        {
            "draft_id": "batch_video_001",
            "title": "第一个视频",
            "video_url": "https://example.com/video1.mp4"
        },
        {
            "draft_id": "batch_video_002",
            "title": "第二个视频",
            "video_url": "https://example.com/video2.mp4"
        },
        {
            "draft_id": "batch_video_003",
            "title": "第三个视频",
            "video_url": "https://example.com/video3.mp4"
        }
    ]
    
    created_drafts = []
    
    # 批量创建草稿
    for config in draft_configs:
        print(f"创建草稿: {config['draft_id']}")
        
        # 创建草稿
        requests.post(f"{BASE_URL}/create_draft", json={
            "draft_id": config["draft_id"],
            "width": 1080,
            "height": 1920
        })
        
        # 添加视频
        requests.post(f"{BASE_URL}/add_video", json={
            "draft_id": config["draft_id"],
            "video_url": config["video_url"],
            "start": 0,
            "end": 20,
            "width": 1080,
            "height": 1920
        })
        
        # 添加标题
        requests.post(f"{BASE_URL}/add_text", json={
            "draft_id": config["draft_id"],
            "text": config["title"],
            "start": 0,
            "end": 3,
            "font": "ZY_Courage",
            "font_color": "#FFFFFF",
            "font_size": 42.0,
            "position_x": 0.5,
            "position_y": 0.2
        })
        
        # 保存草稿
        requests.post(f"{BASE_URL}/save_draft", json={
            "draft_id": config["draft_id"]
        })
        
        created_drafts.append(config["draft_id"])
    
    # 批量下载
    print(f"\n批量下载 {len(created_drafts)} 个草稿...")
    response = requests.post(f"{BASE_URL}/api/drafts/batch-download", json={
        "draft_ids": created_drafts,
        "client_os": "windows",
        "draft_folder": "F:/jianyin/cgwz/JianyingPro Drafts"
    })
    
    result = response.json()
    print(f"批量下载结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    print(f"\n✅ 批量处理完成！")
    print(f"📊 成功: {result.get('success_count', 0)} 个")
    print(f"❌ 失败: {result.get('failed_count', 0)} 个")

if __name__ == "__main__":
    batch_process_drafts()
```

## 🔧 故障排除

### 常见问题及解决方案

#### 1. 服务无法访问

**问题现象**: 无法打开 http://8.148.70.18:9000

**可能原因**:
- 服务未启动
- 网络连接问题
- 防火墙阻止

**解决方案**:
```bash
# 检查服务状态
sudo systemctl status capcutapi.service

# 启动服务
sudo systemctl start capcutapi.service

# 检查端口监听
netstat -tlnp | grep 9000

# 检查防火墙
sudo firewall-cmd --list-ports
```

#### 2. API调用失败

**问题现象**: API返回错误或超时

**可能原因**:
- 请求参数错误
- 服务器资源不足
- 网络超时

**解决方案**:
```bash
# 检查API状态
curl -v http://8.148.70.18:9000/api/status

# 查看服务日志
tail -f /home/CapCutAPI-1.1.0/logs/capcutapi.log

# 检查错误日志
tail -f /home/CapCutAPI-1.1.0/logs/capcutapi.error.log
```

#### 3. 草稿保存失败

**问题现象**: 保存草稿时返回错误

**可能原因**:
- OSS配置错误
- 网络连接问题
- 磁盘空间不足

**解决方案**:
```bash
# 检查OSS配置
cat /home/CapCutAPI-1.1.0/config.json

# 检查环境变量
env | grep OSS

# 检查磁盘空间
df -h

# 测试OSS连接
curl -I https://your-bucket.oss-region.aliyuncs.com
```

#### 4. 下载功能异常

**问题现象**: 无法下载草稿文件

**可能原因**:
- 文件不存在
- URL过期
- 权限问题

**解决方案**:
```bash
# 检查草稿是否存在
curl http://8.148.70.18:9000/api/drafts/list

# 调试草稿缓存
curl http://8.148.70.18:9000/debug/cache/[草稿ID]

# 重新生成下载链接
curl -X POST http://8.148.70.18:9000/generate_draft_url \
  -H "Content-Type: application/json" \
  -d '{"draft_id": "your_draft_id", "force_save": true}'
```

#### 5. 界面显示异常

**问题现象**: Web界面无法正常显示

**可能原因**:
- 浏览器兼容性问题
- JavaScript错误
- CSS加载失败

**解决方案**:
1. 使用现代浏览器（Chrome 80+, Firefox 75+）
2. 清除浏览器缓存
3. 检查浏览器控制台错误
4. 尝试无痕模式访问

### 日志分析

#### 应用日志位置
```bash
# 主要日志文件
/home/CapCutAPI-1.1.0/logs/capcutapi.log

# 错误日志文件
/home/CapCutAPI-1.1.0/logs/capcutapi.error.log

# 系统服务日志
sudo journalctl -u capcutapi.service
```

#### 常用日志命令
```bash
# 实时查看日志
tail -f logs/capcutapi.log

# 查看最近100行日志
tail -n 100 logs/capcutapi.log

# 搜索特定错误
grep "ERROR" logs/capcutapi.log

# 查看特定时间段日志
grep "2025-01-21" logs/capcutapi.log
```

### 性能优化建议

#### 1. 服务器性能优化
- 确保充足的内存（推荐4GB+）
- 使用SSD存储提升I/O性能
- 配置适当的并发连接数

#### 2. 网络优化
- 使用CDN加速静态资源
- 启用gzip压缩
- 优化OSS存储区域选择

#### 3. 应用优化
- 定期清理临时文件
- 优化草稿缓存策略
- 监控内存使用情况

## 📞 技术支持

### 获取帮助

1. **查看文档**
   - 需求文档：`REQUIREMENTS_DOCUMENT.md`
   - API文档：`API_USAGE_EXAMPLES.md`
   - 功能总结：`FEATURE_OPTIMIZATION_SUMMARY.md`

2. **在线测试**
   - 主页：http://8.148.70.18:9000
   - 仪表板：http://8.148.70.18:9000/api/drafts/dashboard

3. **服务管理**
   ```bash
   # 使用管理脚本
   ./service_manager.sh status    # 查看状态
   ./service_manager.sh restart   # 重启服务
   ./service_manager.sh logs      # 查看日志
   ./service_manager.sh test      # 测试功能
   ```

### 联系信息

- **项目版本**: v1.2.0 Enhanced Edition
- **最后更新**: 2025年1月21日
- **维护状态**: 持续维护中

---

**操作手册版本**: v1.2.0  
**文档状态**: 完整版  
**适用版本**: CapCutAPI v1.2.0+