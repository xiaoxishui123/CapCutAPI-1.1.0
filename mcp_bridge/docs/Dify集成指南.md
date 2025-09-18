# Dify 工作流 MCP 集成完整指南

## 🎯 集成概述

本指南详细说明如何将 CapCut API MCP Bridge 服务集成到 Dify 工作流中，实现智能短视频生成工作流。

## 📋 前置条件

### 1. 服务状态检查

确保以下服务正常运行：

```bash
# 检查 CapCut API 服务
curl http://localhost:9000/get_intro_animation_types

# 检查 MCP Bridge 服务
curl http://localhost:8082/health

# 检查 Redis 服务
redis-cli ping
```

### 2. 网络连通性

确保 Dify 服务器可以访问：
- CapCut API: `http://localhost:9000`
- MCP Bridge: `http://localhost:8082`

## 🔧 Dify MCP 服务器配置

### 步骤 1: 添加 MCP 服务器

1. **登录 Dify 管理界面**
   - 访问 Dify 工作流管理页面
   - 导航到 `工具` → `MCP` → `添加服务器`

2. **配置服务器信息**
   ```yaml
   服务器名称: CapCut MCP Bridge
   服务器URL: http://localhost:8082
   服务器标识: capcut-mcp-bridge
   描述: 剪映视频编辑MCP桥接服务
   超时时间: 30秒
   重试次数: 3
   ```

3. **验证连接**
   - 点击 `测试连接` 按钮
   - 确认显示 "连接成功" 状态
   - 查看可用工具列表

### 步骤 2: 确认可用工具

系统应该自动检测到以下 MCP 工具：

| 工具名称 | 功能描述 | 参数 |
|---------|---------|------|
| `create_draft` | 创建剪映草稿 | `title`, `width`, `height` |
| `add_video` | 添加视频素材 | `draft_id`, `video_path`, `start_time`, `duration` |
| `add_image` | 添加图片素材 | `draft_id`, `image_path`, `duration` |
| `add_text` | 添加文字素材 | `draft_id`, `text`, `font_size`, `color` |
| `add_subtitle` | 添加字幕 | `draft_id`, `subtitle_text`, `start_time`, `end_time` |
| `save_draft` | 保存草稿 | `draft_id`, `export_path` |

## 🔄 工作流设计

### 基础短视频生成工作流

#### 节点 1: 开始节点
```yaml
节点类型: 开始
输入变量:
  - video_topic: 视频主题 (String)
  - video_duration: 视频时长 (Number, 默认30)
  - video_style: 视频风格 (String, 默认"现代简约")
  - output_format: 输出格式 (String, 默认"mp4")
```

#### 节点 2: 内容生成
```yaml
节点类型: LLM
模型: GPT-4
提示词: |
  基于主题"{{video_topic}}"，生成一个{{video_duration}}秒的短视频脚本。
  
  要求：
  1. 包含吸引人的开头
  2. 主要内容清晰简洁
  3. 有明确的结尾
  4. 风格：{{video_style}}
  
  请以JSON格式输出：
  {
    "title": "视频标题",
    "scenes": [
      {
        "text": "场景文字",
        "duration": 5,
        "visual_description": "视觉描述"
      }
    ]
  }

输出变量:
  - video_script: 视频脚本内容
```

#### 节点 3: 创建草稿
```yaml
节点类型: MCP工具
工具: create_draft
参数:
  title: "{{video_script.title}}"
  width: 1080
  height: 1920
  
输出变量:
  - draft_id: 草稿ID
```

#### 节点 4: 添加文字内容
```yaml
节点类型: 代码执行
代码: |
  import json
  
  # 解析视频脚本
  script = json.loads(video_script)
  scenes = script.get('scenes', [])
  
  # 为每个场景添加文字
  text_tasks = []
  current_time = 0
  
  for scene in scenes:
      text_tasks.append({
          'text': scene['text'],
          'start_time': current_time,
          'end_time': current_time + scene['duration'],
          'font_size': 48,
          'color': '#FFFFFF'
      })
      current_time += scene['duration']
  
  return {'text_tasks': text_tasks}

输出变量:
  - text_tasks: 文字任务列表
```

#### 节点 5: 批量添加文字
```yaml
节点类型: 循环
循环变量: text_tasks
循环体:
  - 节点类型: MCP工具
    工具: add_text
    参数:
      draft_id: "{{draft_id}}"
      text: "{{item.text}}"
      start_time: "{{item.start_time}}"
      end_time: "{{item.end_time}}"
      font_size: "{{item.font_size}}"
      color: "{{item.color}}"
```

#### 节点 6: 保存草稿
```yaml
节点类型: MCP工具
工具: save_draft
参数:
  draft_id: "{{draft_id}}"
  export_path: "/tmp/generated_video_{{draft_id}}.mp4"

输出变量:
  - video_path: 生成的视频路径
```

#### 节点 7: 结果输出
```yaml
节点类型: 结束
输出:
  - video_path: "{{video_path}}"
  - draft_id: "{{draft_id}}"
  - video_title: "{{video_script.title}}"
  - generation_time: "{{current_time}}"
```

## 🔧 高级配置

### 1. 错误处理和重试

```yaml
# 在每个 MCP 工具节点中添加
错误处理:
  重试次数: 3
  重试间隔: 2秒
  失败处理: 继续执行
  
条件分支:
  - 条件: "{{error_occurred}}"
    动作: 发送告警通知
```

### 2. 并行处理优化

```yaml
节点类型: 并行
并行分支:
  分支1: 生成视频内容
  分支2: 生成背景音乐
  分支3: 生成字幕文件
汇聚节点: 合并所有素材
```

### 3. 缓存策略

```yaml
节点类型: 条件判断
条件: "{{cache_enabled}}"
真分支:
  - 检查缓存
  - 如果命中，直接返回
假分支:
  - 执行正常流程
  - 保存到缓存
```

## 📊 监控和调试

### 2. 工作流监控

在 Dify 工作流中添加监控节点：

```yaml
节点类型: HTTP请求
URL: http://localhost:8082/metrics
方法: GET
用途: 获取 MCP Bridge 性能指标
```

### 2. 日志记录

```yaml
节点类型: 代码执行
代码: |
  import logging
  import json
  
  # 记录工作流执行日志
  logger = logging.getLogger('dify_workflow')
  
  log_data = {
      'workflow_id': workflow_id,
      'draft_id': draft_id,
      'execution_time': execution_time,
      'status': 'success'
  }
  
  logger.info(f"工作流执行完成: {json.dumps(log_data)}")
```

### 3. 性能分析

```yaml
节点类型: 代码执行
代码: |
  import time
  
  # 记录性能指标
  start_time = time.time()
  
  # ... 执行业务逻辑 ...
  
  end_time = time.time()
  execution_time = end_time - start_time
  
  # 发送性能数据到监控系统
  performance_data = {
      'node_name': 'create_draft',
      'execution_time': execution_time,
      'timestamp': time.time()
  }
```

## 🚨 故障排除

### 常见问题及解决方案

#### 1. MCP 服务器连接失败

**症状**: Dify 显示 "无法连接到 MCP 服务器"

**解决方案**:
```bash
# 检查服务状态
sudo systemctl status mcp-bridge.service

# 检查端口监听
netstat -tlnp | grep 8082

# 查看服务日志
sudo journalctl -u mcp-bridge.service -f
```

#### 2. 工具调用超时

**症状**: MCP 工具调用超过 30 秒超时

**解决方案**:
1. 增加超时时间配置
2. 检查 CapCut API 服务性能
3. 优化请求参数

#### 3. 草稿创建失败

**症状**: `create_draft` 工具返回错误

**解决方案**:
```bash
# 检查 CapCut API 服务
curl -X POST http://localhost:9000/create_draft \
  -H "Content-Type: application/json" \
  -d '{"title":"test","width":1080,"height":1920}'

# 检查存储空间
df -h

# 检查权限
ls -la /tmp/
```

#### 4. 降级机制测试

**测试降级功能**:
```bash
# 停止 MCP 服务模拟故障
sudo systemctl stop mcp-bridge.service

# 观察是否自动降级到 HTTP 服务
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"create_draft","params":{"title":"test"}}'
```

## 📈 性能优化建议

### 1. 批量操作

对于大量文字或素材添加，使用批量接口：

```yaml
节点类型: MCP工具
工具: batch_add_elements
参数:
  draft_id: "{{draft_id}}"
  elements: "{{element_list}}"
```

### 2. 异步处理

对于耗时操作，使用异步模式：

```yaml
节点类型: MCP工具
工具: async_export_video
参数:
  draft_id: "{{draft_id}}"
  callback_url: "{{callback_endpoint}}"
```

### 3. 资源预热

在工作流开始时预热资源：

```yaml
节点类型: MCP工具
工具: warmup_resources
参数:
  resource_types: ["fonts", "effects", "transitions"]
```

## 🔒 安全配置

### 1. API 密钥配置

```yaml
# 在 MCP 服务器配置中添加
认证:
  类型: API密钥
  密钥: "your-secure-api-key"
  请求头: "X-API-Key"
```

### 2. 访问控制

```yaml
# 限制访问来源
访问控制:
  允许的IP: ["127.0.0.1", "10.0.0.0/8"]
  拒绝的IP: []
```

### 3. 请求限流

```yaml
# 配置请求限流
限流:
  每分钟请求数: 100
  突发请求数: 20
  限流策略: "令牌桶"
```

---

## 📞 技术支持

如果在集成过程中遇到问题，请：

1. 查看 MCP Bridge 日志: `sudo journalctl -u mcp-bridge.service -f`
2. 检查 Dify 工作流执行日志
3. 验证网络连通性和服务状态
4. 参考故障排除章节

### 当前配置信息

- **CapCut API 端口**: 9000
- **MCP Bridge 端口**: 8082
- **配置文件**: `/home/CapCutAPI-1.1.0/mcp_bridge/config/bridge_config.yaml`
- **服务状态检查**: `curl http://localhost:8082/health`
- **性能指标**: `curl http://localhost:8082/metrics`

### 服务访问地址

- **CapCut API**: http://localhost:9000
- **MCP Bridge 服务**: http://localhost:8082
- **MCP Bridge MCP端点**: http://localhost:8082/mcp

通过以上配置，您可以在 Dify 工作流中无缝使用 CapCut API MCP Bridge 服务，实现高效的短视频自动化生成。