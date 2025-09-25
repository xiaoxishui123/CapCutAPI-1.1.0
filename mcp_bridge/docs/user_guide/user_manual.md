# MCP Bridge 用户手册

## 简介

MCP Bridge 是一个强大的模型上下文协议（MCP）桥接服务，为用户提供了统一的接口来访问各种AI服务和工作流管理功能。

## 功能概览

### 核心功能
- **MCP协议桥接**: 提供标准的MCP协议接口
- **HTTP桥接服务**: 轻量级HTTP API接口
- **工作流管理**: 自动化工作流程处理
- **CapCut集成**: 无缝对接CapCut视频编辑服务

### 主要特性
- 高性能异步处理
- 灵活的配置管理
- 完善的错误处理
- 实时监控和日志
- 安全的API访问控制

## 快速开始

### 1. 基本使用

#### 启动服务
```bash
# 使用默认配置启动
python src/main.py

# 使用自定义配置启动
python src/main.py --config config/custom_config.yaml
```

#### 验证服务
```bash
# 检查服务状态
curl http://localhost:8080/health

# 获取服务信息
curl http://localhost:8080/info
```

### 2. API调用示例

#### MCP协议调用
```python
import asyncio
from mcp_client import MCPClient

async def main():
    client = MCPClient("http://localhost:8080")
    
    # 发送MCP请求
    response = await client.send_request({
        "method": "tools/call",
        "params": {
            "name": "capcut_edit",
            "arguments": {
                "video_url": "https://example.com/video.mp4",
                "action": "trim",
                "start_time": 0,
                "end_time": 10
            }
        }
    })
    
    print(response)

asyncio.run(main())
```

#### HTTP API调用
```python
import requests

# 视频编辑请求
response = requests.post("http://localhost:8081/api/v1/edit", json={
    "video_url": "https://example.com/video.mp4",
    "operations": [
        {
            "type": "trim",
            "start_time": 0,
            "end_time": 10
        }
    ]
})

print(response.json())
```

## API参考

### MCP协议端点

#### 工具调用
- **端点**: `/mcp/tools/call`
- **方法**: POST
- **描述**: 调用指定的MCP工具

**请求格式**:
```json
{
    "method": "tools/call",
    "params": {
        "name": "tool_name",
        "arguments": {
            "param1": "value1",
            "param2": "value2"
        }
    }
}
```

**响应格式**:
```json
{
    "result": {
        "content": [
            {
                "type": "text",
                "text": "操作结果"
            }
        ]
    }
}
```

### HTTP API端点

#### 视频编辑
- **端点**: `/api/v1/edit`
- **方法**: POST
- **描述**: 执行视频编辑操作

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| video_url | string | 是 | 视频文件URL |
| operations | array | 是 | 编辑操作列表 |

**操作类型**:
- `trim`: 裁剪视频
- `merge`: 合并视频
- `filter`: 应用滤镜
- `transition`: 添加转场

#### 工作流管理
- **端点**: `/api/v1/workflow`
- **方法**: POST/GET/PUT/DELETE
- **描述**: 管理工作流

**创建工作流**:
```json
{
    "name": "视频处理工作流",
    "description": "自动化视频编辑流程",
    "steps": [
        {
            "id": "step1",
            "type": "video_upload",
            "config": {
                "max_size": "100MB"
            }
        },
        {
            "id": "step2",
            "type": "video_edit",
            "config": {
                "operations": ["trim", "filter"]
            }
        }
    ]
}
```

## 配置指南

### 基本配置

#### 服务器设置
```yaml
server:
  host: 0.0.0.0
  port: 8080
  debug: false
  workers: 4
```

#### HTTP桥接设置
```yaml
http_bridge:
  enabled: true
  port: 8081
  cors_enabled: true
  rate_limiting:
    enabled: true
    requests_per_minute: 100
```

#### CapCut集成设置
```yaml
capcut:
  api_url: "https://api.capcut.com"
  api_key: "your_api_key"
  timeout: 30
  max_retries: 3
```

### 高级配置

#### 缓存配置
```yaml
cache:
  enabled: true
  backend: redis
  redis:
    host: localhost
    port: 6379
    db: 0
  ttl: 3600
```

#### 监控配置
```yaml
monitoring:
  enabled: true
  metrics_port: 9090
  health_check_interval: 30
  log_level: INFO
```

## 工作流使用

### 创建工作流

1. **定义工作流结构**
```yaml
workflow:
  name: "视频批处理"
  version: "1.0"
  description: "批量处理视频文件"
  
  inputs:
    - name: video_files
      type: array
      required: true
    - name: output_format
      type: string
      default: "mp4"
  
  steps:
    - id: validate
      type: validation
      config:
        rules:
          - file_size_max: 100MB
          - format_allowed: [mp4, avi, mov]
    
    - id: process
      type: video_edit
      depends_on: [validate]
      config:
        operations:
          - type: compress
            quality: high
          - type: watermark
            position: bottom_right
```

2. **提交工作流**
```bash
curl -X POST http://localhost:8080/api/v1/workflow \
  -H "Content-Type: application/json" \
  -d @workflow.json
```

### 执行工作流

```python
import requests

# 启动工作流执行
response = requests.post("http://localhost:8080/api/v1/workflow/execute", json={
    "workflow_id": "workflow_123",
    "inputs": {
        "video_files": [
            "https://example.com/video1.mp4",
            "https://example.com/video2.mp4"
        ],
        "output_format": "mp4"
    }
})

execution_id = response.json()["execution_id"]

# 查询执行状态
status_response = requests.get(f"http://localhost:8080/api/v1/workflow/execution/{execution_id}")
print(status_response.json())
```

## 错误处理

### 常见错误码

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求格式和参数 |
| 401 | 认证失败 | 验证API密钥 |
| 403 | 权限不足 | 检查访问权限 |
| 429 | 请求频率超限 | 降低请求频率 |
| 500 | 服务器内部错误 | 查看服务器日志 |

### 错误响应格式

```json
{
    "error": {
        "code": "INVALID_PARAMETER",
        "message": "参数 'video_url' 是必需的",
        "details": {
            "parameter": "video_url",
            "expected_type": "string"
        }
    }
}
```

## 最佳实践

### 1. 性能优化

- **使用缓存**: 启用Redis缓存以提高响应速度
- **批量处理**: 对于大量文件，使用批量API
- **异步调用**: 使用异步客户端进行并发请求

### 2. 安全建议

- **API密钥管理**: 定期轮换API密钥
- **HTTPS使用**: 生产环境中使用HTTPS
- **访问控制**: 配置适当的CORS和IP白名单

### 3. 监控和调试

- **日志记录**: 启用详细日志记录
- **指标监控**: 使用Prometheus监控服务指标
- **健康检查**: 定期检查服务健康状态

## 故障排除

### 常见问题

1. **连接超时**
   - 检查网络连接
   - 增加超时设置
   - 验证服务器状态

2. **API调用失败**
   - 验证API密钥
   - 检查请求格式
   - 查看错误日志

3. **工作流执行失败**
   - 检查工作流定义
   - 验证输入参数
   - 查看执行日志

### 调试技巧

```bash
# 启用调试模式
export DEBUG=true
python src/main.py

# 查看详细日志
tail -f logs/mcp_bridge.log

# 测试API连接
curl -v http://localhost:8080/health
```

## 示例和教程

### 完整示例：视频处理流水线

```python
import asyncio
import aiohttp

class VideoPipeline:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
    
    async def process_video(self, video_url, operations):
        """
        处理单个视频文件
        """
        async with aiohttp.ClientSession() as session:
            # 1. 上传视频
            upload_response = await session.post(
                f"{self.base_url}/api/v1/upload",
                json={"url": video_url}
            )
            video_id = (await upload_response.json())["video_id"]
            
            # 2. 执行编辑操作
            edit_response = await session.post(
                f"{self.base_url}/api/v1/edit",
                json={
                    "video_id": video_id,
                    "operations": operations
                }
            )
            
            # 3. 获取结果
            result = await edit_response.json()
            return result["output_url"]

# 使用示例
async def main():
    pipeline = VideoPipeline()
    
    result_url = await pipeline.process_video(
        "https://example.com/input.mp4",
        [
            {"type": "trim", "start": 0, "end": 30},
            {"type": "filter", "name": "vintage"},
            {"type": "watermark", "text": "My Video"}
        ]
    )
    
    print(f"处理完成: {result_url}")

asyncio.run(main())
```

## 更新日志

### v1.0.0 (当前版本)
- 初始发布
- 支持基本MCP协议
- HTTP桥接功能
- 工作流管理
- CapCut集成

### 计划功能
- 更多视频编辑工具
- 批量处理优化
- 实时协作功能
- 插件系统

## 支持和反馈

如果您在使用过程中遇到问题或有改进建议，请：

1. 查看[常见问题](../faq.md)
2. 提交[GitHub Issue](https://github.com/your-repo/issues)
3. 联系技术支持: support@example.com

---

感谢使用MCP Bridge！