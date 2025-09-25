# MCP Bridge 部署指南

## 📋 目录

1. [环境准备](#环境准备)
2. [开发环境部署](#开发环境部署)
3. [生产环境部署](#生产环境部署)
4. [Docker部署](#docker部署)
5. [高可用部署](#高可用部署)
6. [监控配置](#监控配置)
7. [安全配置](#安全配置)
8. [故障排除](#故障排除)

## 🔧 环境准备

### 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 18.04+ / CentOS 7+ | Ubuntu 20.04+ |
| Python | 3.9+ | 3.11+ |
| 内存 | 2GB | 4GB+ |
| 磁盘 | 10GB | 20GB+ |
| CPU | 2核 | 4核+ |

### 依赖服务

- **Redis**: 6.0+
- **Docker**: 20.10+ (可选)
- **Nginx**: 1.18+ (生产环境)

### 网络端口

| 服务 | 端口 | 用途 |
|------|------|------|
| MCP Bridge | 8000 | 主服务端口 |
| HTTP Bridge | 8001 | HTTP桥接端口 |
| Redis | 6379 | 缓存服务 |
| Monitoring | 9090 | 监控指标 |

## 🚀 开发环境部署

### 1. 环境准备

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装Python和pip
sudo apt install python3.11 python3.11-venv python3-pip -y

# 安装Redis
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 2. 项目设置

```bash
# 克隆项目
git clone <repository-url>
cd mcp_bridge

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 3. 配置文件

```bash
# 复制配置文件
cp config/.env.example config/.env

# 编辑环境变量
vim config/.env
```

**config/.env 示例:**
```bash
# 服务配置
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
HTTP_BRIDGE_PORT=8001

# Redis配置
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# 日志配置
LOG_LEVEL=DEBUG
LOG_FILE=logs/mcp_bridge.log

# 开发模式
ENVIRONMENT=development
DEBUG=true
```

### 4. 启动服务

```bash
# 创建日志目录
mkdir -p logs

# 运行基础测试
python tests/test_basic.py

# 启动开发服务器
python core/bridge_server.py
```

### 5. 验证部署

```bash
# 检查服务健康状态
curl http://localhost:8000/health

# 检查监控指标
curl http://localhost:8000/metrics

# 运行健康检查脚本
./scripts/health_check.sh --quick
```

## 🏭 生产环境部署

### 1. 系统优化

```bash
# 调整系统限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p
```

### 2. 用户和目录

```bash
# 创建专用用户
sudo useradd -r -s /bin/false mcpbridge

# 创建应用目录
sudo mkdir -p /opt/mcp_bridge
sudo chown mcpbridge:mcpbridge /opt/mcp_bridge

# 切换到应用目录
cd /opt/mcp_bridge
```

### 3. 应用部署

```bash
# 下载应用代码
sudo -u mcpbridge git clone <repository-url> .

# 创建虚拟环境
sudo -u mcpbridge python3.11 -m venv venv
sudo -u mcpbridge ./venv/bin/pip install -r requirements.txt
sudo -u mcpbridge ./venv/bin/pip install -e .
```

### 4. 生产配置

**config/.env (生产环境):**
```bash
# 服务配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
HTTP_BRIDGE_PORT=8001
WORKERS=4

# Redis配置
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_secure_password
REDIS_MAX_CONNECTIONS=20

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/mcp_bridge/mcp_bridge.log

# 生产模式
ENVIRONMENT=production
DEBUG=false

# 安全配置
API_KEY=your_secure_api_key
SECRET_KEY=your_secret_key

# CapCut配置
CAPCUT_API_KEY=your_capcut_api_key
CAPCUT_BASE_URL=https://api.capcut.com
```

### 5. 系统服务

创建systemd服务文件：

```bash
sudo tee /etc/systemd/system/mcp-bridge.service << EOF
[Unit]
Description=MCP Bridge Service
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=mcpbridge
Group=mcpbridge
WorkingDirectory=/opt/mcp_bridge
Environment=PATH=/opt/mcp_bridge/venv/bin
ExecStart=/opt/mcp_bridge/venv/bin/python core/bridge_server.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

# 安全配置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/mcp_bridge /var/log/mcp_bridge

[Install]
WantedBy=multi-user.target
EOF
```

启动服务：

```bash
# 创建日志目录
sudo mkdir -p /var/log/mcp_bridge
sudo chown mcpbridge:mcpbridge /var/log/mcp_bridge

# 启动并启用服务
sudo systemctl daemon-reload
sudo systemctl enable mcp-bridge
sudo systemctl start mcp-bridge

# 检查服务状态
sudo systemctl status mcp-bridge
```

### 6. Nginx反向代理

```bash
# 安装Nginx
sudo apt install nginx -y

# 创建配置文件
sudo tee /etc/nginx/sites-available/mcp-bridge << EOF
upstream mcp_bridge {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001 backup;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 代理配置
    location / {
        proxy_pass http://mcp_bridge;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://mcp_bridge/health;
        access_log off;
    }
    
    # 监控指标
    location /metrics {
        proxy_pass http://mcp_bridge/metrics;
        allow 127.0.0.1;
        deny all;
    }
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/mcp-bridge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🐳 Docker部署

### 1. 单容器部署

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 安装应用
RUN pip install -e .

# 创建非root用户
RUN useradd -r -s /bin/false appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "core/bridge_server.py"]
```

构建和运行：

```bash
# 构建镜像
docker build -t mcp-bridge:latest .

# 运行容器
docker run -d \
    --name mcp-bridge \
    -p 8000:8000 \
    -p 8001:8001 \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/logs:/app/logs \
    --restart unless-stopped \
    mcp-bridge:latest
```

### 2. Docker Compose部署

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  redis:
    image: redis:7.2-alpine
    container_name: mcp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  mcp-bridge:
    build: .
    container_name: mcp-bridge
    ports:
      - "8000:8000"
      - "8001:8001"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: mcp-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - mcp-bridge
    restart: unless-stopped

volumes:
  redis_data:

networks:
  default:
    name: mcp-bridge-network
```

启动服务栈：

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mcp-bridge

# 停止服务
docker-compose down
```

## 🏗️ 高可用部署

### 1. 多实例部署

**docker-compose.ha.yml:**
```yaml
version: '3.8'

services:
  redis-master:
    image: redis:7.2-alpine
    container_name: redis-master
    ports:
      - "6379:6379"
    volumes:
      - redis_master_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

  redis-slave:
    image: redis:7.2-alpine
    container_name: redis-slave
    ports:
      - "6380:6379"
    volumes:
      - redis_slave_data:/data
    command: redis-server --slaveof redis-master 6379 --appendonly yes
    depends_on:
      - redis-master
    restart: unless-stopped

  mcp-bridge-1:
    build: .
    container_name: mcp-bridge-1
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - REDIS_URL=redis://redis-master:6379
      - INSTANCE_ID=1
    depends_on:
      - redis-master
    restart: unless-stopped

  mcp-bridge-2:
    build: .
    container_name: mcp-bridge-2
    ports:
      - "8002:8000"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - REDIS_URL=redis://redis-master:6379
      - INSTANCE_ID=2
    depends_on:
      - redis-master
    restart: unless-stopped

  nginx-lb:
    image: nginx:alpine
    container_name: nginx-lb
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-ha.conf:/etc/nginx/nginx.conf
    depends_on:
      - mcp-bridge-1
      - mcp-bridge-2
    restart: unless-stopped

volumes:
  redis_master_data:
  redis_slave_data:
```

**nginx-ha.conf:**
```nginx
upstream mcp_bridge_backend {
    least_conn;
    server mcp-bridge-1:8000 max_fails=3 fail_timeout=30s;
    server mcp-bridge-2:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://mcp_bridge_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 健康检查
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
    
    location /health {
        proxy_pass http://mcp_bridge_backend/health;
        access_log off;
    }
}
```

### 2. Kubernetes部署

**k8s/namespace.yaml:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mcp-bridge
```

**k8s/redis.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: mcp-bridge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.2-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: mcp-bridge
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

**k8s/mcp-bridge.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-bridge
  namespace: mcp-bridge
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-bridge
  template:
    metadata:
      labels:
        app: mcp-bridge
    spec:
      containers:
      - name: mcp-bridge
        image: mcp-bridge:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: ENVIRONMENT
          value: "production"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-bridge-service
  namespace: mcp-bridge
spec:
  selector:
    app: mcp-bridge
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

部署到Kubernetes：

```bash
# 创建命名空间
kubectl apply -f k8s/namespace.yaml

# 部署Redis
kubectl apply -f k8s/redis.yaml

# 部署MCP Bridge
kubectl apply -f k8s/mcp-bridge.yaml

# 查看部署状态
kubectl get pods -n mcp-bridge
kubectl get services -n mcp-bridge
```

## 📊 监控配置

### 1. Prometheus配置

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "mcp_bridge_rules.yml"

scrape_configs:
  - job_name: 'mcp-bridge'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

**mcp_bridge_rules.yml:**
```yaml
groups:
  - name: mcp_bridge_alerts
    rules:
      - alert: MCPBridgeDown
        expr: up{job="mcp-bridge"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MCP Bridge is down"
          description: "MCP Bridge has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(mcp_bridge_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: mcp_bridge_response_time_seconds > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "Response time is {{ $value }} seconds"
```

### 2. Grafana仪表板

创建Grafana仪表板配置：

```json
{
  "dashboard": {
    "title": "MCP Bridge Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mcp_bridge_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mcp_bridge_errors_total[5m])",
            "legendFormat": "Errors/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "mcp_bridge_response_time_seconds",
            "legendFormat": "Response Time"
          }
        ]
      }
    ]
  }
}
```

## 🔒 安全配置

### 1. 防火墙配置

```bash
# 安装ufw
sudo apt install ufw -y

# 默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许SSH
sudo ufw allow ssh

# 允许HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许应用端口（仅内网）
sudo ufw allow from 10.0.0.0/8 to any port 8000
sudo ufw allow from 172.16.0.0/12 to any port 8000
sudo ufw allow from 192.168.0.0/16 to any port 8000

# 启用防火墙
sudo ufw enable
```

### 2. SSL/TLS配置

```bash
# 使用Let's Encrypt获取证书
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. 应用安全

**config/security.yaml:**
```yaml
security:
  api_key:
    enabled: true
    header_name: "X-API-Key"
    required_for_paths:
      - "/mcp"
      - "/metrics"
  
  rate_limit:
    enabled: true
    requests_per_minute: 1000
    burst_size: 100
    
  cors:
    enabled: true
    allowed_origins:
      - "https://your-domain.com"
    allowed_methods:
      - "GET"
      - "POST"
    allowed_headers:
      - "Content-Type"
      - "Authorization"
      - "X-API-Key"
  
  input_validation:
    max_request_size: 10485760  # 10MB
    timeout: 30
```

## 🔧 故障排除

### 1. 常见问题

**服务无法启动:**
```bash
# 检查端口占用
sudo netstat -tlnp | grep :8000

# 检查配置文件
python -c "import yaml; yaml.safe_load(open('config/unified_config.yaml'))"

# 检查权限
ls -la /opt/mcp_bridge
sudo chown -R mcpbridge:mcpbridge /opt/mcp_bridge
```

**Redis连接失败:**
```bash
# 检查Redis状态
sudo systemctl status redis-server

# 测试连接
redis-cli ping

# 检查配置
redis-cli config get "*"
```

**性能问题:**
```bash
# 检查系统资源
top
free -h
df -h

# 检查网络连接
ss -tlnp

# 查看应用日志
tail -f /var/log/mcp_bridge/mcp_bridge.log
```

### 2. 日志分析

```bash
# 查看错误日志
grep "ERROR" /var/log/mcp_bridge/mcp_bridge.log

# 查看访问统计
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr

# 监控实时日志
tail -f /var/log/mcp_bridge/mcp_bridge.log | grep -E "(ERROR|WARNING)"
```

### 3. 性能调优

**系统级优化:**
```bash
# 调整文件描述符限制
echo "fs.file-max = 65536" >> /etc/sysctl.conf

# 调整网络参数
echo "net.core.rmem_max = 16777216" >> /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" >> /etc/sysctl.conf

# 应用配置
sysctl -p
```

**应用级优化:**
```yaml
# config/performance.yaml
performance:
  workers: 4
  max_connections: 1000
  keepalive_timeout: 65
  client_max_body_size: 10m
  
  cache:
    ttl: 300
    max_size: 1000
    
  database:
    pool_size: 20
    max_overflow: 30
    pool_timeout: 30
```

## 📋 部署检查清单

### 部署前检查

- [ ] 系统要求满足
- [ ] 依赖服务已安装
- [ ] 网络端口已开放
- [ ] SSL证书已配置
- [ ] 配置文件已准备
- [ ] 备份策略已制定

### 部署后验证

- [ ] 服务正常启动
- [ ] 健康检查通过
- [ ] API接口可访问
- [ ] 监控指标正常
- [ ] 日志记录正常
- [ ] 性能测试通过

### 运维检查

- [ ] 监控告警已配置
- [ ] 备份任务已设置
- [ ] 日志轮转已配置
- [ ] 安全扫描已完成
- [ ] 文档已更新
- [ ] 团队已培训

---

**部署支持**: 如有问题，请联系技术支持团队或查看[故障排除指南](troubleshooting.md)。