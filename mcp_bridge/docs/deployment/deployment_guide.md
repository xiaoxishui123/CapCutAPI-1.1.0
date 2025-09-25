# MCP Bridge 部署指南

## 概述

MCP Bridge 是一个企业级的模型上下文协议（MCP）桥接服务，集成了HTTP桥接和工作流管理功能。本指南将帮助您完成系统的部署和配置。

## 系统要求

### 硬件要求
- CPU: 2核心以上
- 内存: 4GB以上
- 存储: 10GB可用空间
- 网络: 稳定的互联网连接

### 软件要求
- Python 3.8+
- Docker (可选)
- Redis (用于缓存)
- PostgreSQL (可选，用于持久化存储)

## 快速部署

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd mcp_bridge

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件设置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

### 3. 启动服务

```bash
# 使用管理脚本启动
./scripts/start.sh

# 或手动启动
python src/main.py
```

## Docker 部署

### 1. 使用 Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 2. 单独使用 Docker

```bash
# 构建镜像
docker build -t mcp-bridge .

# 运行容器
docker run -d \
  --name mcp-bridge \
  -p 8080:8080 \
  -p 8081:8081 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  mcp-bridge
```

## 配置说明

### 主要配置项

#### 全局配置
```yaml
global:
  debug: false
  log_level: INFO
  environment: production
```

#### 服务器配置
```yaml
server:
  host: 0.0.0.0
  port: 8080
  workers: 4
```

#### HTTP桥接配置
```yaml
http_bridge:
  enabled: true
  port: 8081
  capcut_api_url: "https://api.capcut.com"
  timeout: 30
  max_retries: 3
```

#### 工作流配置
```yaml
workflow:
  enabled: true
  validation_enabled: true
  max_concurrent_workflows: 10
```

### 环境变量

关键环境变量说明：

```bash
# 服务配置
MCP_BRIDGE_HOST=0.0.0.0
MCP_BRIDGE_PORT=8080

# CapCut API配置
CAPCUT_API_URL=https://api.capcut.com
CAPCUT_API_KEY=your_api_key_here

# 缓存配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# 安全配置
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
```

## 服务验证

### 1. 健康检查

```bash
# 检查主服务
curl http://localhost:8080/health

# 检查HTTP桥接服务
curl http://localhost:8081/health
```

### 2. 功能测试

```bash
# 运行测试套件
python -m pytest tests/

# 运行集成测试
python -m pytest tests/integration/

# 运行性能测试
python -m pytest tests/performance/
```

## 监控和日志

### 日志配置

日志文件位置：
- 主服务日志: `logs/mcp_bridge.log`
- HTTP桥接日志: `logs/http_bridge.log`
- 工作流日志: `logs/workflow.log`
- 错误日志: `logs/error.log`

### 监控指标

系统提供以下监控端点：
- `/metrics` - Prometheus格式的指标
- `/health` - 健康检查
- `/status` - 服务状态

## 故障排除

### 常见问题

1. **服务启动失败**
   - 检查端口是否被占用
   - 验证配置文件格式
   - 查看错误日志

2. **API调用失败**
   - 检查网络连接
   - 验证API密钥
   - 查看超时设置

3. **性能问题**
   - 检查系统资源使用
   - 调整并发设置
   - 优化缓存配置

### 日志分析

```bash
# 查看实时日志
tail -f logs/mcp_bridge.log

# 搜索错误
grep "ERROR" logs/*.log

# 分析性能
grep "PERFORMANCE" logs/mcp_bridge.log
```

## 安全配置

### 1. HTTPS配置

```yaml
server:
  ssl_enabled: true
  ssl_cert_path: /path/to/cert.pem
  ssl_key_path: /path/to/key.pem
```

### 2. 访问控制

```yaml
security:
  cors_enabled: true
  allowed_origins:
    - "https://yourdomain.com"
  rate_limiting:
    enabled: true
    requests_per_minute: 100
```

### 3. API密钥管理

```bash
# 生成新的API密钥
python scripts/generate_api_key.py

# 轮换密钥
python scripts/rotate_keys.py
```

## 扩展部署

### 负载均衡

使用Nginx进行负载均衡：

```nginx
upstream mcp_bridge {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://mcp_bridge;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 集群部署

对于高可用部署，建议：
1. 使用多个实例
2. 配置共享存储
3. 设置数据库集群
4. 实施监控和告警

## 维护和更新

### 备份

```bash
# 备份配置
./scripts/backup_config.sh

# 备份数据
./scripts/backup_data.sh
```

### 更新

```bash
# 停止服务
./scripts/stop.sh

# 更新代码
git pull origin main

# 重启服务
./scripts/start.sh
```

## 支持和联系

如需技术支持，请：
1. 查看文档和FAQ
2. 检查GitHub Issues
3. 联系技术支持团队

---

更多详细信息请参考：
- [API文档](../api/)
- [用户指南](../user_guide/)
- [开发文档](../development/)