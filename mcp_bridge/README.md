# MCP Bridge - 智能MCP桥接服务

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)](README.md)

## 📖 项目概述

MCP Bridge 是一个智能的 Model Context Protocol (MCP) 桥接服务，旨在为 Dify 等AI应用提供统一、可靠的MCP服务接口。它具备智能路由、自动降级、缓存优化和全面监控等企业级特性。

### 🎯 核心特性

- **🔄 智能路由**: 基于服务健康状态和负载的智能请求分发
- **⚡ 自动降级**: 服务故障时的自动降级和恢复机制
- **💾 缓存优化**: Redis缓存支持，提升响应速度
- **📊 全面监控**: 实时性能监控和健康检查
- **🔧 统一管理**: 集中化的配置和服务管理
- **🛡️ 高可用性**: 多服务端点支持和故障转移

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dify/Client   │───▶│   MCP Bridge    │───▶│  MCP Services   │
│                 │    │                 │    │                 │
│  - HTTP请求     │    │  - 智能路由     │    │  - CapCut MCP   │
│  - JSON-RPC     │    │  - 缓存管理     │    │  - 其他MCP服务  │
│  - 认证授权     │    │  - 监控告警     │    │  - HTTP服务     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Redis Cache    │
                       │  - 响应缓存     │
                       │  - 会话状态     │
                       │  - 监控数据     │
                       └─────────────────┘
```

## 📁 项目结构

```
mcp_bridge/
├── core/                    # 核心模块
│   ├── bridge_server.py     # 主桥接服务器
│   ├── router.py           # 路由管理器
│   ├── mcp_client.py       # MCP客户端
│   ├── cache.py            # 缓存管理
│   ├── monitoring.py       # 监控组件
│   ├── fallback.py         # 降级处理
│   ├── models.py           # 数据模型
│   └── capcut_mcp_server.py # CapCut MCP服务器
├── integrations/           # 集成模块
│   ├── http_bridge.py      # HTTP桥接
│   └── dify_integration.py # Dify集成
├── workflows/              # 工作流模块
│   ├── workflow_manager.py # 工作流管理
│   └── validation.py       # 数据验证
├── config/                 # 配置文件
│   ├── unified_config.yaml # 统一配置
│   └── .env.example        # 环境变量示例
├── tests/                  # 测试文件
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   ├── performance/       # 性能测试
│   └── test_basic.py      # 基础功能测试
├── scripts/               # 管理脚本
│   ├── health_check.sh    # 健康检查
│   ├── start_services.sh  # 启动服务
│   ├── stop_services.sh   # 停止服务
│   └── deploy.sh          # 部署脚本
├── docs/                  # 文档目录
├── logs/                  # 日志目录
├── requirements.txt       # Python依赖
├── setup.py              # 安装配置
├── pytest.ini           # 测试配置
├── Makefile             # 自动化任务
└── README.md            # 项目说明
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Redis 6.0+
- 4GB+ 内存
- 10GB+ 磁盘空间

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd mcp_bridge
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
pip install -e .
```

4. **配置环境**
```bash
cp config/.env.example config/.env
# 编辑 config/.env 文件，设置必要的环境变量
```

5. **启动Redis服务**
```bash
# 使用Docker
docker run -d --name redis -p 6379:6379 redis:latest

# 或使用系统服务
sudo systemctl start redis
```

6. **运行基础测试**
```bash
python tests/test_basic.py
```

7. **启动服务**
```bash
# 使用管理脚本
./scripts/start_services.sh

# 或手动启动
python core/bridge_server.py
```

## ⚙️ 配置说明

### 主配置文件 (config/unified_config.yaml)

```yaml
# 服务配置
services:
  bridge_server:
    host: "0.0.0.0"
    port: 8000
    workers: 4
    timeout: 30
    
  http_bridge:
    host: "0.0.0.0"
    port: 8001
    timeout: 30

# MCP服务端点
mcp_endpoints:
  - name: "capcut_primary"
    type: "mcp"
    url: "http://localhost:8080"
    priority: 1
    timeout: 30
    retry_count: 3

# 缓存配置
cache:
  redis_url: "redis://localhost:6379"
  ttl: 300
  max_connections: 10

# 监控配置
monitoring:
  enabled: true
  metrics_port: 9090
  health_check_interval: 30
```

### 环境变量 (config/.env)

```bash
# 服务配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
HTTP_BRIDGE_PORT=8001

# Redis配置
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/mcp_bridge.log

# 监控配置
ENABLE_MONITORING=true
METRICS_PORT=9090

# CapCut配置
CAPCUT_API_KEY=your_api_key_here
CAPCUT_BASE_URL=https://api.capcut.com
```

## 🔧 使用指南

### 基本API调用

```python
import requests

# MCP请求示例
mcp_request = {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
}

response = requests.post(
    "http://localhost:8000/mcp",
    json=mcp_request,
    headers={"Content-Type": "application/json"}
)

print(response.json())
```

### 健康检查

```bash
# 快速检查
./scripts/health_check.sh --quick

# 完整检查
./scripts/health_check.sh --full

# 检查特定组件
curl http://localhost:8000/health
```

### 监控指标

```bash
# 获取系统指标
curl http://localhost:8000/metrics

# 查看服务状态
curl http://localhost:8000/status
```

## 🧪 测试

### 运行所有测试

```bash
# 使用pytest
pytest tests/ -v

# 使用Makefile
make test
```

### 运行特定测试

```bash
# 单元测试
pytest tests/unit/ -v

# 集成测试
pytest tests/integration/ -v

# 性能测试
pytest tests/performance/ -v

# 基础功能测试
python tests/test_basic.py
```

### 测试覆盖率

```bash
pytest tests/ --cov=mcp_bridge --cov-report=html
```

## 📊 监控和日志

### 日志文件

- `logs/mcp_bridge.log` - 主服务日志
- `logs/http_bridge.log` - HTTP桥接日志
- `logs/workflow.log` - 工作流日志
- `logs/error.log` - 错误日志

### 监控指标

- **请求指标**: 请求数量、响应时间、成功率
- **服务指标**: 服务健康状态、负载情况
- **系统指标**: CPU、内存、磁盘使用率
- **缓存指标**: 缓存命中率、连接数

### 告警配置

系统支持多种告警方式：
- 日志告警
- HTTP回调
- 邮件通知（需配置）
- 钉钉/企业微信（需配置）

## 🔄 部署

### Docker部署

```bash
# 构建镜像
docker build -t mcp-bridge .

# 运行容器
docker run -d \
  --name mcp-bridge \
  -p 8000:8000 \
  -p 8001:8001 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  mcp-bridge
```

### Docker Compose部署

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mcp-bridge
```

### 生产环境部署

```bash
# 使用部署脚本
./scripts/deploy.sh production

# 或使用Makefile
make deploy ENV=production
```

## 🛠️ 开发指南

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 安装pre-commit钩子
pre-commit install

# 运行代码格式化
black mcp_bridge/
flake8 mcp_bridge/
```

### 代码规范

- 遵循PEP 8代码风格
- 使用类型提示
- 编写完整的文档字符串
- 保持函数简洁，单一职责
- 编写对应的单元测试

### 贡献指南

1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 运行测试确保通过
5. 提交Pull Request

## 🔍 故障排除

### 常见问题

**Q: 服务启动失败**
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 检查配置文件
python -c "import yaml; yaml.safe_load(open('config/unified_config.yaml'))"

# 查看详细日志
tail -f logs/mcp_bridge.log
```

**Q: Redis连接失败**
```bash
# 检查Redis服务
redis-cli ping

# 检查连接配置
python -c "import redis; r=redis.Redis(host='localhost', port=6379); print(r.ping())"
```

**Q: MCP服务无响应**
```bash
# 检查服务健康状态
./scripts/health_check.sh --quick

# 手动测试MCP端点
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

### 性能优化

- 调整Redis缓存TTL
- 增加服务worker数量
- 优化数据库查询
- 启用请求压缩
- 配置负载均衡

## 📚 API文档

### MCP Bridge API

#### POST /mcp
处理MCP请求

**请求体:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": 1
}
```

**响应:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [...]
  },
  "id": 1
}
```

#### GET /health
获取服务健康状态

**响应:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-14T10:30:00Z",
  "services": {
    "bridge_server": "healthy",
    "redis": "healthy",
    "mcp_endpoints": "healthy"
  }
}
```

#### GET /metrics
获取系统指标

**响应:**
```json
{
  "requests": {
    "total": 1000,
    "success": 950,
    "error": 50,
    "avg_response_time": 120
  },
  "services": {
    "capcut_primary": {
      "status": "healthy",
      "response_time": 100,
      "success_rate": 0.95
    }
  }
}
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 支持

- 📧 邮箱: support@example.com
- 📱 微信群: [扫码加入]
- 🐛 问题反馈: [GitHub Issues](https://github.com/your-repo/issues)
- 📖 文档: [在线文档](https://docs.example.com)

## 🔄 更新日志

### v1.0.0 (2025-01-14)
- ✅ 初始版本发布
- ✅ 智能路由功能实现
- ✅ 自动降级机制完成
- ✅ Redis缓存支持部署
- ✅ 监控和健康检查系统
- ✅ 高可用性设计实现
- ✅ 完整的测试套件
- ✅ 详细的部署指南
- ✅ 故障恢复机制

### 当前项目状态
- **核心功能**: ✅ 已完成
- **智能路由**: ✅ 已完成  
- **缓存系统**: ✅ 已完成
- **监控告警**: ✅ 已完成
- **测试覆盖**: ✅ 已完成
- **文档完整性**: ✅ 已完成
- **部署就绪**: ✅ 已完成

### 计划中的功能
- 更多MCP服务提供商支持
- 高级缓存策略优化
- 图形化管理界面
- 性能进一步优化
- 多语言SDK支持

---

**感谢使用 MCP Bridge！** 🎉

如果这个项目对你有帮助，请给我们一个 ⭐ Star！