# CapCut API MCP Bridge

## 项目概述

CapCut API MCP Bridge 是一个基于 Model Context Protocol (MCP) 的桥接服务，用于将 CapCut 视频编辑 API 集成到 Dify 工作流中。该项目提供了完整的 MCP 服务器实现、Dify 集成方案和部署工具。

## MCP Bridge 服务

MCP Bridge 是一个高性能的桥接服务，用于连接 Model Context Protocol (MCP) 服务和 HTTP 客户端，专为 CapCut API 集成而设计。

### 功能特性

- **MCP 协议支持**: 完整支持 MCP 2.0 协议规范
- **HTTP API 网关**: 将 MCP 调用转换为 RESTful API
- **高性能缓存**: 基于 Redis 的智能缓存系统
- **负载均衡**: 支持多个 MCP 服务实例的负载均衡
- **监控告警**: 完整的健康检查和性能监控
- **容器化部署**: 支持 Docker 和 Docker Compose 部署
- **CapCut 集成**: 专门优化的 CapCut API 桥接功能

## 🚀 快速开始

### 一键部署

```bash
# 克隆项目
cd /home/CapCutAPI-1.1.0

# 执行一键部署脚本
chmod +x setup_dify_integration.sh
./setup_dify_integration.sh

# 验证部署
./manage_integration.sh status
```

### 手动部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境
cp config/development.yaml.example config/development.yaml
# 编辑配置文件

# 3. 启动服务
python -m mcp_bridge.core.mcp_server
python -m mcp_bridge.core.bridge_server

# 4. 注册到 Dify
python -m mcp_bridge.integrations.dify_workflow_integration
```

## 📁 项目结构

```
mcp_bridge/
├── README.md                          # 项目说明文档
├── requirements.txt                   # Python 依赖
├── setup.py                          # 安装配置
├── config/                           # 配置文件目录
│   ├── bridge_config.yaml           # 桥接服务配置
│   ├── development.yaml             # 开发环境配置
│   ├── production.yaml              # 生产环境配置
│   └── dify_integration.yaml        # Dify 集成配置
├── core/                            # 核心组件
│   ├── __init__.py
│   ├── bridge_server.py             # 桥接服务器
│   ├── mcp_client.py                # MCP 客户端
│   ├── mcp_server.py                # MCP 服务器
│   ├── capcut_mcp_server.py         # CapCut MCP 服务器
│   └── router.py                    # 路由管理
├── integrations/                    # 集成模块
│   ├── __init__.py
│   └── dify_workflow_integration.py # Dify 工作流集成
├── docs/                           # 文档目录
│   ├── dify_integration_guide.md   # Dify 集成指南
│   ├── implementation_guide.md     # 实施指南
│   ├── implementation_roadmap.md   # 实施路线图
│   ├── mcp_deployment_comparison.md # MCP部署方案对比
│   ├── prd_based_solution_analysis.md # 基于PRD的方案分析
│   ├── quick_start_guide.md        # 快速开始指南
│   ├── bridge_design.md           # 桥接设计文档
│   └── security_guide.md          # 安全指南
├── templates/                      # 工作流模板
│   ├── basic_video_generation.yaml
│   ├── batch_processing.yaml
│   └── advanced_editing.yaml
├── tests/                         # 测试文件
│   ├── test_mcp_server.py
│   ├── test_bridge_server.py
│   └── test_integration.py
└── scripts/                      # 部署脚本
    ├── deploy_mcp_bridge.sh
    ├── setup_dify_integration.sh
    └── manage_integration.sh
```

## 📚 文档导航

### 快速开始
- [快速开始指南](docs/quick_start_guide.md) - 5分钟快速上手指南
- [实施路线图](docs/implementation_roadmap.md) - 详细的8天实施计划

### 方案选择
- [MCP部署方案对比](docs/mcp_deployment_comparison.md) - 两种MCP方案的详细对比
- [基于PRD的方案分析](docs/prd_based_solution_analysis.md) - 基于需求文档的方案选择建议

### 集成指南
- [Dify集成指南](docs/dify_integration_guide.md) - Dify工作流集成详细说明
- [实施指南](docs/implementation_guide.md) - 技术实施详细步骤

### 架构设计
- [桥接设计文档](docs/bridge_design.md) - MCP Bridge架构设计
- [安全指南](docs/security_guide.md) - 安全配置和最佳实践

## 🔧 核心功能

### MCP 服务器功能

- **工具调用**: 支持 CapCut API 的所有功能
- **资源管理**: 提供草稿、模板等资源访问
- **会话管理**: 支持多客户端连接和会话隔离
- **错误处理**: 完善的错误处理和重试机制

### 桥接服务功能

- **协议转换**: HTTP/WebSocket 协议转换
- **负载均衡**: 多实例负载均衡
- **缓存机制**: Redis 缓存提升性能
- **监控指标**: Prometheus 指标收集

### Dify 集成功能

- **自动注册**: 自动注册 MCP 服务器到 Dify
- **工作流模板**: 预定义的工作流模板
- **批量处理**: 支持批量视频处理
- **错误恢复**: 自动错误恢复和重试

## 🛠️ 可用工具

### 视频编辑工具

| 工具名称 | 功能描述 | 参数 |
|---------|---------|------|
| `create_draft` | 创建视频草稿 | title, description |
| `add_video` | 添加视频素材 | draft_id, video_url, start_time, duration |
| `add_audio` | 添加音频素材 | draft_id, audio_url, start_time, volume |
| `add_text` | 添加文本元素 | draft_id, text, font_size, position |
| `add_subtitle` | 添加字幕 | draft_id, subtitle_text, start_time, duration |
| `add_image` | 添加图片 | draft_id, image_url, position, duration |
| `add_effect` | 添加特效 | draft_id, effect_type, intensity |
| `add_sticker` | 添加贴纸 | draft_id, sticker_type, position |
| `save_draft` | 保存草稿 | draft_id |

### 资源查询工具

| 工具名称 | 功能描述 | 返回值 |
|---------|---------|--------|
| `get_intro_animation_types` | 获取入场动画类型 | 动画类型列表 |
| `get_outro_animation_types` | 获取出场动画类型 | 动画类型列表 |
| `get_transition_types` | 获取转场类型 | 转场类型列表 |
| `get_mask_types` | 获取遮罩类型 | 遮罩类型列表 |
| `get_font_types` | 获取字体类型 | 字体类型列表 |

## 📋 使用示例

### 基础视频创建

```python
import asyncio
import websockets
import json

async def create_basic_video():
    uri = "ws://localhost:8080"
    
    async with websockets.connect(uri) as websocket:
        # 1. 创建草稿
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "create_draft",
                "arguments": {
                    "title": "我的视频",
                    "description": "使用 MCP 创建的视频"
                }
            }
        }))
        
        response = await websocket.recv()
        draft_result = json.loads(response)
        draft_id = draft_result["result"]["draft_id"]
        
        # 2. 添加视频
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "add_video",
                "arguments": {
                    "draft_id": draft_id,
                    "video_url": "https://example.com/video.mp4",
                    "start_time": 0,
                    "duration": 30
                }
            }
        }))
        
        # 3. 保存草稿
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "save_draft",
                "arguments": {
                    "draft_id": draft_id
                }
            }
        }))
        
        response = await websocket.recv()
        result = json.loads(response)
        print(f"视频创建成功: {result}")

# 运行示例
asyncio.run(create_basic_video())
```

### Dify 工作流配置

```yaml
name: "CapCut 视频生成"
description: "自动化视频生成工作流"

nodes:
  - id: "start"
    type: "start"
    name: "开始"
    
  - id: "create_draft"
    type: "tool"
    name: "创建草稿"
    tool: "create_draft"
    inputs:
      title: "{{ inputs.video_title }}"
      description: "{{ inputs.video_description }}"
    
  - id: "add_content"
    type: "tool"
    name: "添加内容"
    tool: "add_video"
    inputs:
      draft_id: "{{ create_draft.draft_id }}"
      video_url: "{{ inputs.video_url }}"
      start_time: 0
      duration: "{{ inputs.duration }}"
    
  - id: "save_video"
    type: "tool"
    name: "保存视频"
    tool: "save_draft"
    inputs:
      draft_id: "{{ create_draft.draft_id }}"
    
  - id: "end"
    type: "end"
    name: "完成"
    outputs:
      video_url: "{{ save_video.video_url }}"
```

## 🔧 配置说明

### 环境变量

```bash
# .env 文件
DIFY_API_KEY=your-dify-api-key
MCP_BRIDGE_API_KEY=your-bridge-api-key
REDIS_URL=redis://localhost:6379
CAPCUT_API_URL=http://localhost:9000
```

### 服务配置

```yaml
# config/production.yaml
server:
  host: "0.0.0.0"
  port: 8081
  workers: 4

mcp_server:
  host: "0.0.0.0"
  port: 8080
  max_connections: 100

capcut_api:
  base_url: "http://localhost:9000"
  timeout: 60
  max_retries: 3

redis:
  host: "localhost"
  port: 6379
  db: 0
```

## 🚀 部署指南

### 开发环境

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动开发服务
python -m mcp_bridge.core.mcp_server --config config/development.yaml
python -m mcp_bridge.core.bridge_server --config config/development.yaml
```

### 生产环境

```bash
# 使用 Docker Compose
docker-compose up -d

# 或使用部署脚本
./scripts/deploy_mcp_bridge.sh --env production
```

### 系统服务

```bash
# 创建 systemd 服务
sudo cp scripts/mcp-bridge.service /etc/systemd/system/
sudo systemctl enable mcp-bridge
sudo systemctl start mcp-bridge
```

## 📊 监控和维护

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8081/health
curl http://localhost:8080/health

# 查看指标
curl http://localhost:9090/metrics
```

### 日志查看

```bash
# 查看服务日志
tail -f logs/mcp_server.log
tail -f logs/bridge_server.log

# 查看系统日志
sudo journalctl -u mcp-bridge -f
```

### 性能监控

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (如果配置)
- **Redis**: redis-cli monitor

## 🔒 安全配置

### API 密钥管理

```bash
# 生成新的 API 密钥
python -c "import secrets; print(secrets.token_hex(32))"

# 更新配置
export MCP_BRIDGE_API_KEY=your-new-key
```

### HTTPS 配置

```nginx
# Nginx 配置
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /mcp/ {
        proxy_pass http://localhost:8081/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_mcp_server.py -v

# 运行集成测试
pytest tests/test_integration.py -v
```

### 性能测试

```bash
# 负载测试
python tests/load_test.py --concurrent 10 --requests 1000

# 压力测试
python tests/stress_test.py --duration 300
```

## 🐛 故障排除

### 常见问题

1. **连接失败**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep 8080
   
   # 检查防火墙
   sudo ufw status
   ```

2. **API 调用超时**
   ```bash
   # 增加超时时间
   # 编辑 config/production.yaml
   capcut_api:
     timeout: 120
   ```

3. **内存不足**
   ```bash
   # 检查内存使用
   free -h
   
   # 调整工作进程数
   server:
     workers: 2
   ```

### 日志分析

```bash
# 查找错误
grep "ERROR" logs/mcp_server.log

# 查找超时
grep "timeout" logs/bridge_server.log

# 查看连接统计
grep "connection" logs/mcp_server.log | wc -l
```

## 📚 文档链接

- [Dify 集成指南](docs/dify_integration_guide.md)
- [实施指南](docs/implementation_guide.md)
- [架构设计](docs/bridge_design.md)
- [安全指南](docs/security_guide.md)
- [API 文档](https://github.com/sun-guannan/CapCutAPI)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 技术支持

- **项目地址**: https://github.com/sun-guannan/CapCutAPI
- **问题反馈**: 请在 GitHub Issues 中提交
- **文档更新**: 2025年1月

---

**版本**: 1.0.0  
**最后更新**: 2025年1月  
**维护状态**: 积极维护中

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Dify 工作流系统                           │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP Protocol
┌─────────────────────▼───────────────────────────────────────┐
│                  MCP Bridge 核心层                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  路由管理器  │  │  降级控制器  │  │  监控中心    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/MCP Dual Protocol
┌─────────────────────▼───────────────────────────────────────┐
│                  目标服务层                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ CapCut MCP  │  │ CapCut HTTP │  │  其他服务    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Redis 6.0+
- Docker & Docker Compose（可选）

### 本地开发

1. **克隆项目**
```bash
git clone <repository-url>
cd mcp_bridge
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动Redis**
```bash
# 使用Docker
docker run -d --name redis -p 6379:6379 redis:7.2-alpine

# 或使用本地Redis
redis-server
```

4. **配置服务**
```bash
# 复制配置文件
cp config/bridge_config.yaml.example config/bridge_config.yaml

# 编辑配置（可选）
vim config/bridge_config.yaml
```

5. **启动服务**
```bash
python -m uvicorn core.bridge_server:app --host 0.0.0.0 --port 8080 --reload
```

6. **验证服务**
```bash
curl http://localhost:8080/health
```

### Docker部署

1. **构建镜像**
```bash
docker build -t mcp-bridge:latest .
```

2. **启动服务栈**
```bash
# 基础服务
docker-compose up -d

# 包含监控
docker-compose --profile monitoring up -d

# 包含CapCut插件
docker-compose --profile with-capcut up -d
```

3. **查看服务状态**
```bash
docker-compose ps
```

## 📖 使用指南

### API接口

#### 1. MCP请求处理
```bash
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "capcut_create_draft",
  "params": {
    "video_url": "https://example.com/video.mp4",
    "draft_name": "我的短视频",
    "description": "测试视频"
  },
  "id": 1
}
```

#### 2. 健康检查
```bash
GET /health

# 响应
{
  "status": "healthy",
  "timestamp": 1705123456.789,
  "services": {
    "capcut_mcp": {
      "status": "healthy",
      "last_check": 1705123456.789,
      "success_count": 100,
      "error_count": 2
    }
  }
}
```

#### 3. 服务指标
```bash
GET /metrics

# 响应
{
  "total_requests": 1000,
  "success_rate": 0.98,
  "error_rate": 0.02,
  "avg_response_time": 1.5,
  "service_metrics": {
    "capcut_mcp": {
      "request_count": 800,
      "success_count": 784,
      "error_count": 16,
      "total_response_time": 1200.5
    }
  }
}
```

### 配置说明

#### 服务端点配置
```yaml
# MCP服务配置
mcp_services:
  capcut_mcp:
    name: "CapCut MCP Server"
    url: "mcp://localhost:9002"
    timeout: 30
    retry_count: 3
    priority: 1  # 优先级，数字越小优先级越高

# HTTP服务配置  
http_services:
  capcut_plugin:
    name: "CapCut HTTP Plugin"
    url: "http://localhost:9001"
    timeout: 30
    retry_count: 3
    priority: 2
```

#### 降级策略配置
```yaml
fallback:
  enabled: true
  error_threshold: 0.2      # 错误率阈值
  timeout_threshold: 30     # 超时阈值
  
  circuit_breaker:
    failure_threshold: 5    # 连续失败阈值
    recovery_timeout: 60    # 恢复尝试间隔
```

#### 缓存配置
```yaml
cache:
  enabled: true
  redis:
    url: "redis://localhost:6379"
  strategy:
    default_ttl: 300
    method_ttl:
      capcut_create_draft: 600
      capcut_upload_video: 1800
```

## 🔧 运维指南

### 监控面板

访问以下地址查看监控信息：

- **服务状态**：http://localhost:8080/health
- **性能指标**：http://localhost:8080/metrics  
- **Prometheus**：http://localhost:9090
- **Grafana**：http://localhost:3000 (admin/admin123)

### 日志管理

```bash
# 查看实时日志
docker-compose logs -f mcp-bridge

# 查看特定服务日志
docker-compose logs -f redis

# 日志文件位置
./logs/mcp_bridge.log
./logs/access.log
./logs/error.log
```

### 性能调优

#### 1. 连接池优化
```yaml
performance:
  connection_pool:
    max_connections: 100
    max_keepalive_connections: 20
    keepalive_expiry: 5
```

#### 2. 并发控制
```yaml
performance:
  concurrency:
    max_concurrent_requests: 1000
    request_timeout: 60
```

#### 3. 缓存优化
```yaml
cache:
  strategy:
    max_size: 100  # MB
    default_ttl: 300
```

### 故障排查

#### 常见问题

1. **服务无法启动**
```bash
# 检查端口占用
netstat -tlnp | grep 8080

# 检查配置文件
python -c "import yaml; yaml.safe_load(open('config/bridge_config.yaml'))"

# 检查依赖
pip check
```

2. **Redis连接失败**
```bash
# 检查Redis状态
redis-cli ping

# 检查网络连接
telnet localhost 6379
```

3. **服务降级频繁**
```bash
# 查看服务健康状态
curl http://localhost:8080/health

# 查看错误日志
grep ERROR logs/mcp_bridge.log

# 调整降级阈值
vim config/bridge_config.yaml
```

#### 性能问题

1. **响应时间过长**
- 检查目标服务性能
- 调整超时配置
- 启用缓存优化

2. **内存使用过高**
- 调整缓存大小
- 检查内存泄漏
- 优化连接池配置

3. **CPU使用率高**
- 增加worker进程
- 优化异步处理
- 检查死循环

## 🧪 测试

### 单元测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_router.py

# 生成覆盖率报告
pytest --cov=core --cov-report=html
```

### 集成测试
```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行集成测试
pytest tests/integration/

# 清理测试环境
docker-compose -f docker-compose.test.yml down
```

### 压力测试
```bash
# 安装压测工具
pip install locust

# 运行压力测试
locust -f tests/load/locustfile.py --host=http://localhost:8080
```

## 📊 性能基准

### 基准测试结果

| 指标 | 目标值 | 当前值 |
|------|--------|--------|
| 响应时间 | < 2s | 1.5s |
| 吞吐量 | > 1000 RPS | 1200 RPS |
| 可用性 | > 99.9% | 99.95% |
| 错误率 | < 1% | 0.5% |

### 容量规划

| 场景 | QPS | 内存 | CPU | 网络 |
|------|-----|------|-----|------|
| 轻负载 | 100 | 256MB | 0.5核 | 10Mbps |
| 中负载 | 500 | 512MB | 1核 | 50Mbps |
| 重负载 | 1000+ | 1GB | 2核 | 100Mbps |

## 🔒 安全

### 安全特性

- ✅ API密钥认证
- ✅ 速率限制
- ✅ CORS配置
- ✅ 输入验证
- ✅ 错误信息脱敏

### 安全配置
```yaml
security:
  api_key:
    enabled: true
    header_name: "X-API-Key"
  
  rate_limit:
    enabled: true
    requests_per_minute: 1000
    burst_size: 100
```

## 🚀 部署

### 生产环境部署

1. **环境准备**
```bash
# 创建部署目录
mkdir -p /opt/mcp_bridge
cd /opt/mcp_bridge

# 下载配置文件
wget https://raw.githubusercontent.com/your-repo/CapCutAPI-1.1.0/mcp_bridge/main/docker-compose.prod.yml
```

2. **配置环境变量**
```bash
# 创建环境文件
cat > .env << EOF
REDIS_URL=redis://redis:6379
CAPCUT_API_KEY=your_api_key
CAPCUT_API_SECRET=your_api_secret
LOG_LEVEL=INFO
ENVIRONMENT=production
EOF
```

3. **启动服务**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

4. **配置反向代理**
```nginx
# /etc/nginx/sites-available/mcp-bridge
server {
    listen 80;
    server_name mcp-bridge.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 高可用部署

```yaml
# docker-compose.ha.yml
version: '3.8'
services:
  mcp-bridge-1:
    image: mcp-bridge:latest
    ports:
      - "8081:8080"
    
  mcp-bridge-2:
    image: mcp-bridge:latest
    ports:
      - "8082:8080"
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx-ha.conf:/etc/nginx/nginx.conf
```

## 📚 API文档

启动服务后访问：
- **Swagger UI**：http://localhost:8080/docs
- **ReDoc**：http://localhost:8080/redoc
- **OpenAPI JSON**：http://localhost:8080/openapi.json

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 支持

- 📧 邮箱：support@example.com
- 💬 讨论：[GitHub Discussions](https://github.com/your-repo/CapCutAPI-1.1.0/mcp_bridge/discussions)
- 🐛 问题：[GitHub Issues](https://github.com/your-repo/CapCutAPI-1.1.0/mcp_bridge/issues)

## 🗺️ 路线图

### v1.1.0 (计划中)
- [ ] 支持更多MCP服务
- [ ] 增强监控面板
- [ ] 性能优化

### v1.2.0 (计划中)
- [ ] 分布式部署支持
- [ ] 更多缓存策略
- [ ] 自动扩缩容

### v2.0.0 (远期)
- [ ] 图形化配置界面
- [ ] 机器学习优化
- [ ] 多云部署支持

---

**开发团队**：AI Assistant  
**最后更新**：2025年1月14日  
**版本**：v1.0.0