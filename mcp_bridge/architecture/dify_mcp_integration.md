# Dify工作流MCP节点集成指南

## 🎯 集成概述

本文档详细说明如何在Dify工作流中集成MCP Bridge服务，实现短视频工作流的智能化处理。

## 🔧 MCP服务器配置

### 1. 添加MCP服务器

在Dify工作流中添加MCP服务器：

1. **进入工具管理页面**
   - 导航到 `工作流` → `工具` → `MCP`
   - 点击 `添加MCP服务器(HTTP)`

2. **配置服务器信息**
   ```yaml
   名称: CapCut MCP Bridge
   服务器URL: http://127.0.0.1:9101
   服务器标识: capcut-mcp-bridge
   描述: 剪映视频编辑MCP桥接服务
   ```

3. **验证连接**
   - 系统会自动检测可用工具
   - 确认显示以下工具：
     - `create_draft` - 创建剪映草稿
     - `add_video` - 添加视频素材
     - `add_image` - 添加图片素材
     - `add_text` - 添加文字素材
     - `add_subtitle` - 添加字幕
     - `add_video_keyframe` - 添加视频关键帧
     - `save_draft` - 保存草稿

## 🔄 工作流节点配置

### 2. 短视频生成工作流

#### 节点1: 开始节点
```yaml
节点类型: 开始
输入变量:
  - video_topic: 视频主题 (String)
  - video_duration: 视频时长 (Number, 默认30)
  - video_style: 视频风格 (String, 默认"现代简约")
```

#### 节点2: 视频内容生成
```yaml
节点类型: LLM
模型: GPT-4
提示词: |
  基于主题"{{video_topic}}"，生成一个{{video_duration}}秒的短视频脚本。
  风格要求：{{video_style}}
  
  请输出JSON格式：
  {
    "title": "视频标题",
    "scenes": [
      {
        "duration": 10,
        "description": "场景描述",
        "text": "显示文字",
        "background": "背景描述"
      }
    ]
  }
输出变量: video_script
```

#### 节点3: 创建剪映草稿
```yaml
节点类型: 工具
工具提供商: capcut-mcp-bridge
工具名称: create_draft
参数配置:
  width: 1080
  height: 1920
  project_name: "{{video_script.title}}"
输出变量: draft_info
```

#### 节点4: 添加背景视频
```yaml
节点类型: 工具
工具提供商: capcut-mcp-bridge
工具名称: add_video
参数配置:
  draft_id: "{{draft_info.draft_id}}"
  video_url: "{{background_video_url}}"
  start: 0
  end: "{{video_duration}}"
  volume: 0.3
输出变量: background_clip
```

#### 节点5: 添加文字素材
```yaml
节点类型: 代码执行
代码语言: Python
代码内容: |
  import json
  
  # 解析视频脚本
  script = json.loads(video_script)
  text_clips = []
  
  for i, scene in enumerate(script['scenes']):
      # 为每个场景添加文字
      text_clip = {
          "draft_id": draft_info['draft_id'],
          "text": scene['text'],
          "start": sum(s['duration'] for s in script['scenes'][:i]),
          "end": sum(s['duration'] for s in script['scenes'][:i+1]),
          "font_size": 48,
          "color": "#FFFFFF",
          "position": "center"
      }
      text_clips.append(text_clip)
  
  return {"text_clips": text_clips}
输出变量: text_config
```

#### 节点6: 批量添加文字
```yaml
节点类型: 循环
循环数据: "{{text_config.text_clips}}"
循环节点:
  - 节点类型: 工具
    工具提供商: capcut-mcp-bridge
    工具名称: add_text
    参数配置:
      draft_id: "{{item.draft_id}}"
      text: "{{item.text}}"
      start: "{{item.start}}"
      end: "{{item.end}}"
      font_size: "{{item.font_size}}"
      color: "{{item.color}}"
      position: "{{item.position}}"
```

#### 节点7: 保存草稿
```yaml
节点类型: 工具
工具提供商: capcut-mcp-bridge
工具名称: save_draft
参数配置:
  draft_id: "{{draft_info.draft_id}}"
输出变量: final_draft
```

#### 节点8: 结束节点
```yaml
节点类型: 结束
输出变量:
  draft_path: "{{final_draft.draft_path}}"
  draft_id: "{{draft_info.draft_id}}"
  video_title: "{{video_script.title}}"
  message: "视频草稿已生成完成，可在剪映中打开编辑"
```

## 🛡️ 错误处理与降级

### 3. 降级策略配置

#### 条件判断节点
```yaml
节点类型: 条件判断
条件表达式: "{{draft_info.error}} != null"
真分支: HTTP降级流程
假分支: 继续MCP流程
```

#### HTTP降级节点
```yaml
节点类型: HTTP请求
方法: POST
URL: http://127.0.0.1:9000/create_draft
请求头:
  Content-Type: application/json
请求体:
  width: 1080
  height: 1920
  project_name: "{{video_script.title}}"
```

## 🔍 监控与调试

### 4. 日志配置

#### 日志节点
```yaml
节点类型: 代码执行
代码内容: |
  import json
  import datetime
  
  log_entry = {
      "timestamp": datetime.datetime.now().isoformat(),
      "workflow_id": "{{workflow.id}}",
      "draft_id": draft_info.get('draft_id'),
      "status": "success" if not draft_info.get('error') else "error",
      "error": draft_info.get('error'),
      "execution_time": "{{workflow.execution_time}}"
  }
  
  print(f"[MCP_BRIDGE_LOG] {json.dumps(log_entry)}")
  return log_entry
```

### 5. 健康检查

#### 预检查节点
```yaml
节点类型: HTTP请求
方法: GET
URL: http://127.0.0.1:9101/health
超时: 5秒
重试次数: 2
```

## 🎛️ 环境变量配置

### 6. 工作流环境变量

```yaml
# MCP Bridge配置
CAPCUT_MCP_BRIDGE_BASE: "http://127.0.0.1:9101"
CAPCUT_HTTP_BASE: "http://127.0.0.1:9000"
ENABLE_CAPCUT_MCP: "true"

# 认证配置
X_API_KEY: "your-api-key-here"

# 超时配置
MCP_REQUEST_TIMEOUT: "30"
HTTP_REQUEST_TIMEOUT: "15"

# 重试配置
MAX_RETRIES: "3"
RETRY_DELAY: "2"
```

## 📊 性能优化

### 7. 并发控制

#### 并行处理节点
```yaml
节点类型: 并行
并行分支:
  - 分支1: 添加视频素材
  - 分支2: 生成字幕文件
  - 分支3: 准备背景音乐
汇聚节点: 合并所有素材
```

### 8. 缓存策略

#### 缓存检查节点
```yaml
节点类型: 代码执行
代码内容: |
  import hashlib
  
  # 生成内容哈希
  content_hash = hashlib.md5(
      f"{video_topic}_{video_duration}_{video_style}".encode()
  ).hexdigest()
  
  # 检查缓存
  cache_key = f"video_draft_{content_hash}"
  cached_result = cache.get(cache_key)
  
  return {
      "cache_key": cache_key,
      "cached_result": cached_result,
      "use_cache": cached_result is not None
  }
```

## 🚀 部署清单

### 9. 部署前检查

- [ ] MCP Bridge服务运行正常 (`http://127.0.0.1:9101/health`)
- [ ] CapCutAPI服务可访问 (`http://127.0.0.1:9000/`)
- [ ] Dify工作流MCP服务器已配置
- [ ] 环境变量已设置
- [ ] 网络连接正常
- [ ] 存储空间充足 (至少10GB用于草稿文件)

### 10. 测试验证

#### 基础功能测试
```bash
# 测试MCP Bridge连接
curl -X POST http://127.0.0.1:9101/mcp/create_draft \
  -H 'Content-Type: application/json' \
  -d '{"width":1080,"height":1920,"project_name":"test"}'

# 测试工具调用
curl -X POST http://127.0.0.1:9101/mcp/add_text \
  -H 'Content-Type: application/json' \
  -d '{"draft_id":"test_id","text":"Hello World","start":0,"end":5}'
```

#### 工作流集成测试
1. 创建测试工作流
2. 配置简单的视频生成任务
3. 验证每个节点的输入输出
4. 检查最终生成的草稿文件

## 📚 故障排除

### 常见问题

1. **MCP服务器连接失败**
   - 检查服务器URL和端口
   - 验证防火墙设置
   - 查看MCP Bridge日志

2. **工具调用超时**
   - 增加超时时间设置
   - 检查网络延迟
   - 优化请求参数

3. **草稿生成失败**
   - 验证CapCutAPI服务状态
   - 检查存储空间
   - 查看详细错误日志

4. **降级机制未触发**
   - 检查条件判断逻辑
   - 验证错误检测机制
   - 测试HTTP降级路径

---

通过以上配置，您可以在Dify工作流中无缝集成MCP Bridge服务，实现高效、可靠的短视频自动化生成流程。