[根目录](../CLAUDE.md) > **mcp_bridge**

---

# MCP Bridge 模块文档

> 最后更新时间：2025-11-11 10:35:57

## 变更记录 (Changelog)

### 2025-11-11 10:35:57
- 初始化 MCP Bridge 模块文档
- 完成模块架构和功能分析

---

## 模块职责

MCP Bridge 是一个企业级的 Model Context Protocol (MCP) 桥接服务，负责将 CapCutAPI 的 HTTP API 转换为标准 MCP 协议接口，供 Dify 等 AI 工作流平台调用。

**核心价值**：
- 提供标准化的 MCP 协议支持
- 智能路由和负载均衡
- 自动降级和故障恢复
- Redis 缓存优化响应速度
- 全面监控和性能指标

**技术栈**：
- FastAPI (异步 Web 框架)
- Redis (缓存和会话管理)
- WebSocket (MCP 协议通信)
- Pydantic (数据验证)
- Structlog (结构化日志)

---

## 入口与启动

### 服务启动入口
- **主服务器**: `core/bridge_server.py`
- **CapCut MCP 服务器**: `core/capcut_mcp_server.py`

### 启动方式

#### 方式 1：直接启动
```bash
cd /home/CapCutAPI-1.1.0/mcp_bridge

# 启动 MCP Bridge 服务（端口 8082）
SERVER_PORT=8082 ./venv/bin/python core/bridge_server.py
```

#### 方式 2：使用管理脚本
```bash
cd /home/CapCutAPI-1.1.0/mcp_bridge

# 启动服务
./manage.sh start

# 停止服务
./manage.sh stop

# 重启服务
./manage.sh restart

# 查看状态
./manage.sh status

# 查看日志
./manage.sh logs
```

#### 方式 3：使用 Docker Compose
```bash
cd /home/CapCutAPI-1.1.0/mcp_bridge

# 启动所有服务（包括 Redis）
docker-compose up -d

# 停止服务
docker-compose down
```

### 健康检查
```bash
# 检查服务健康状态
curl http://localhost:8082/health

# 查看性能指标
curl http://localhost:8082/metrics
```

---

## 对外接口

### MCP 协议端点
- **端点**: `POST /mcp`
- **协议**: JSON-RPC 2.0
- **传输**: HTTP POST

### 支持的 MCP 方法

#### 草稿管理
| 方法 | 描述 | HTTP 方法 |
|------|------|----------|
| `capcut_create_draft` | 创建新的剪映草稿项目 | POST |
| `capcut_save_draft` | 保存草稿到云存储 | POST |

#### 素材获取（GET 方法）
| 方法 | 描述 |
|------|------|
| `get_intro_animation_types` | 获取片头动画类型列表 |
| `get_outro_animation_types` | 获取片尾动画类型列表 |
| `get_transition_types` | 获取转场效果类型列表 |
| `get_mask_types` | 获取蒙版类型列表 |
| `get_font_types` | 获取字体类型列表 |

#### 素材添加（POST 方法）
| 方法 | 描述 |
|------|------|
| `capcut_add_video` | 添加视频素材 |
| `capcut_add_audio` | 添加音频素材 |
| `capcut_add_image` | 添加图片素材 |
| `capcut_add_text` | 添加文本素材 |
| `capcut_add_subtitle` | 添加字幕 |
| `capcut_add_effect` | 添加特效 |
| `capcut_add_sticker` | 添加贴纸 |

### 调用示例
```bash
# 调用 MCP 方法
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "get_intro_animation_types",
    "params": {}
  }'

# 创建草稿
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "capcut_create_draft",
    "params": {
      "width": 1080,
      "height": 1920
    }
  }'
```

---

## 关键依赖与配置

### 依赖关系
```
mcp_bridge/
├── fastapi==0.104.1
├── uvicorn==0.24.0
├── aiohttp==3.9.1
├── httpx==0.25.2
├── redis==5.0.1
├── pyyaml==6.0.1
├── pydantic==2.5.0
├── structlog==23.2.0
└── prometheus-client==0.19.0
```

### 配置文件

#### 1. 统一配置 (`config/unified_config.yaml`)
```yaml
bridge:
  host: "0.0.0.0"
  port: 8082
  workers: 4

services:
  capcut_api:
    base_url: "http://localhost:9000"
    timeout: 30

cache:
  enabled: true
  redis_url: "redis://localhost:6379/0"
  ttl: 3600
```

#### 2. 环境变量 (`.env`)
```bash
# MCP Bridge 配置
SERVER_PORT=8082
SERVER_HOST=0.0.0.0

# CapCut API 配置
CAPCUT_API_BASE_URL=http://localhost:9000

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/mcp_bridge.log
```

---

## 数据模型

### 核心数据结构

#### 1. MCP 请求模型
```python
@dataclass
class MCPRequest:
    method: str              # MCP 方法名
    params: Dict[str, Any]   # 方法参数
    id: Optional[str]        # 请求 ID
    jsonrpc: str = "2.0"     # JSON-RPC 版本
```

#### 2. MCP 响应模型
```python
@dataclass
class MCPResponse:
    result: Optional[Any]    # 成功结果
    error: Optional[Dict]    # 错误信息
    id: Optional[str]        # 请求 ID
    jsonrpc: str = "2.0"     # JSON-RPC 版本
```

#### 3. 服务端点模型
```python
@dataclass
class ServiceEndpoint:
    url: str                 # 服务 URL
    type: ServiceType        # 服务类型
    priority: int            # 优先级
    status: ServiceStatus    # 健康状态
    timeout: int             # 超时时间
```

#### 4. 路由结果模型
```python
@dataclass
class RouteResult:
    endpoint: ServiceEndpoint  # 选中的端点
    strategy: RoutingStrategy  # 路由策略
    metrics: ServiceMetrics    # 服务指标
```

---

## 架构设计

### 核心组件

#### 1. Bridge Server (`core/bridge_server.py`)
- FastAPI 应用主入口
- 路由注册和中间件配置
- 请求处理和响应封装

#### 2. Router (`core/router.py`)
- 智能路由管理器
- 负载均衡策略（优先级、轮询、最少连接、权重）
- 健康检查和服务发现

#### 3. MCP Client (`core/mcp_client.py`)
- MCP 协议客户端实现
- WebSocket 通信
- 请求序列化和响应解析

#### 4. Cache (`core/cache.py`)
- Redis 缓存管理
- 缓存策略（TTL、LRU）
- 会话状态存储

#### 5. Monitoring (`core/monitoring.py`)
- 性能指标收集
- Prometheus 集成
- 实时监控和告警

#### 6. Fallback (`core/fallback.py`)
- 自动降级处理
- 故障恢复机制
- 错误处理和重试

### 路由策略

#### 1. 优先级路由 (PRIORITY)
按服务优先级选择，优先级高的服务优先处理。

#### 2. 轮询 (ROUND_ROBIN)
依次轮询所有健康的服务端点。

#### 3. 最少连接 (LEAST_CONNECTIONS)
选择当前活跃连接数最少的服务。

#### 4. 权重路由 (WEIGHTED)
根据服务权重分配流量。

---

## 集成指南

### Dify 平台集成

#### 1. 配置 MCP 服务器
在 Dify 中添加 MCP 服务器连接：
```json
{
  "name": "CapCut MCP",
  "url": "http://localhost:8082/mcp",
  "type": "http",
  "auth": {
    "type": "none"
  }
}
```

#### 2. 使用 MCP 工具
在 Dify 工作流中选择 CapCut MCP 工具，例如：
- 创建草稿
- 添加视频素材
- 添加文本
- 保存草稿

详细集成步骤参见：[Dify集成指南](docs/Dify集成指南.md)

### Claude Desktop 集成
编辑 `claude_desktop_config.json`：
```json
{
  "mcpServers": {
    "capcut": {
      "url": "http://localhost:8082/mcp",
      "type": "http"
    }
  }
}
```

---

## 测试与质量

### 测试套件
- **单元测试**: `tests/unit/test_units.py`
- **集成测试**: `tests/integration/test_integration.py`
- **性能测试**: `tests/performance/test_performance.py`
- **工作流测试**: `tests/workflow/test_workflow_integration.py`

### 运行测试
```bash
cd /home/CapCutAPI-1.1.0/mcp_bridge

# 安装测试依赖
pip install -r requirements.txt

# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行性能测试
pytest tests/performance/

# 生成覆盖率报告
pytest --cov=core --cov-report=html tests/
```

### 质量工具
- **代码格式化**: Black
- **代码检查**: Flake8
- **类型检查**: Mypy
- **安全扫描**: Pre-commit hooks

```bash
# 运行代码格式化
black core/ integrations/ workflows/

# 运行代码检查
flake8 core/ integrations/ workflows/

# 运行类型检查
mypy core/ integrations/ workflows/
```

---

## 常见问题 (FAQ)

### Q1: 如何配置 Redis 缓存？
编辑 `config/unified_config.yaml`：
```yaml
cache:
  enabled: true
  redis_url: "redis://localhost:6379/0"
  ttl: 3600  # 缓存过期时间（秒）
```

### Q2: 如何查看服务性能指标？
```bash
# 查看 Prometheus 格式指标
curl http://localhost:8082/metrics

# 查看 JSON 格式指标
curl http://localhost:8082/health
```

### Q3: 如何添加新的 MCP 方法？
1. 在 `core/capcut_mcp_server.py` 中定义方法：
```python
async def handle_new_method(self, params: Dict) -> Dict:
    """处理新的 MCP 方法"""
    # 实现逻辑
    return {"status": "success"}
```

2. 注册方法到路由器：
```python
self.method_handlers["new_method"] = self.handle_new_method
```

### Q4: 如何调试 MCP Bridge？
```bash
# 启用调试日志
export LOG_LEVEL=DEBUG
./venv/bin/python core/bridge_server.py

# 查看实时日志
tail -f logs/mcp_bridge.log

# 使用健康检查端点
curl http://localhost:8082/health
```

---

## 相关文件清单

### 核心模块 (`core/`)
| 文件 | 职责 |
|------|------|
| `bridge_server.py` | MCP Bridge 主服务器 |
| `capcut_mcp_server.py` | CapCut MCP 服务器实现 |
| `router.py` | 路由管理器 |
| `mcp_client.py` | MCP 协议客户端 |
| `cache.py` | 缓存管理 |
| `monitoring.py` | 监控组件 |
| `fallback.py` | 降级处理 |
| `models.py` | 数据模型 |

### 集成模块 (`integrations/`)
| 文件 | 职责 |
|------|------|
| `dify_workflow_integration.py` | Dify 平台集成适配器 |

### 工作流模块 (`workflows/`)
| 文件 | 职责 |
|------|------|
| `workflow_manager.py` | 工作流管理器 |
| `validation.py` | 数据验证 |

### 配置文件 (`config/`)
| 文件 | 职责 |
|------|------|
| `unified_config.yaml` | 统一配置文件 |
| `bridge_config.yaml` | Bridge 配置 |
| `.env.example` | 环境变量示例 |

---

## 相关文档
- [根目录](../CLAUDE.md) - 项目总览
- [实施指南](docs/实施指南.md) - 完整部署指南
- [Dify集成指南](docs/Dify集成指南.md) - Dify 平台集成
- [部署方案对比](docs/MCP部署方案对比.md) - 方案对比分析
- [实施路线图](docs/实施路线图.md) - 8天部署路线图

---

**提示**: MCP Bridge 是企业级服务，建议在生产环境中配置 Redis 缓存和监控告警。
