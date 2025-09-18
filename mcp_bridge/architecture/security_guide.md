# MCP Bridge 安全指南

## 🔒 安全概述

本文档详细说明MCP Bridge的安全设计和最佳实践，确保系统在生产环境中的安全性和可靠性。

## 🛡️ 安全架构

### 安全层次模型
```
┌─────────────────────────────────────────────────────────────┐
│                      安全防护层次                           │
├─────────────────────────────────────────────────────────────┤
│ L1: 网络安全层                                              │
│     ├── 防火墙规则                                         │
│     ├── VPN/专线接入                                       │
│     ├── DDoS防护                                           │
│     └── 网络隔离                                           │
├─────────────────────────────────────────────────────────────┤
│ L2: 应用安全层                                              │
│     ├── API认证授权                                        │
│     ├── 输入验证                                           │
│     ├── 输出编码                                           │
│     └── 会话管理                                           │
├─────────────────────────────────────────────────────────────┤
│ L3: 数据安全层                                              │
│     ├── 数据加密                                           │
│     ├── 敏感信息脱敏                                       │
│     ├── 访问控制                                           │
│     └── 审计日志                                           │
├─────────────────────────────────────────────────────────────┤
│ L4: 基础设施安全层                                          │
│     ├── 容器安全                                           │
│     ├── 主机加固                                           │
│     ├── 密钥管理                                           │
│     └── 安全监控                                           │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 认证与授权

### 1. API密钥管理

```python
# API密钥配置
API_KEY_CONFIG = {
    "algorithm": "HS256",
    "key_length": 32,
    "rotation_period": "30d",
    "storage": {
        "type": "vault",
        "path": "/secret/mcp-bridge/api-keys",
        "encryption": "AES-256-GCM"
    },
    "validation": {
        "rate_limit": "100/hour",
        "ip_whitelist": ["10.0.0.0/8", "172.16.0.0/12"],
        "require_https": True
    }
}
```

### 2. JWT令牌管理

```python
# JWT配置
JWT_CONFIG = {
    "algorithm": "RS256",
    "private_key_path": "/etc/ssl/private/jwt-private.pem",
    "public_key_path": "/etc/ssl/certs/jwt-public.pem", 
    "issuer": "mcp-bridge",
    "audience": "dify-workflow",
    "expiration": 3600,  # 1小时
    "refresh_threshold": 300,  # 5分钟
    "blacklist_enabled": True
}
```

### 3. 权限控制模型

```python
# RBAC权限模型
RBAC_CONFIG = {
    "roles": {
        "admin": {
            "permissions": ["*"],
            "description": "系统管理员"
        },
        "operator": {
            "permissions": [
                "draft:create", "draft:read", "draft:update",
                "video:add", "image:add", "text:add"
            ],
            "description": "操作员"
        },
        "viewer": {
            "permissions": ["draft:read", "health:check"],
            "description": "只读用户"
        }
    },
    "resources": {
        "draft": ["create", "read", "update", "delete"],
        "video": ["add", "remove", "modify"],
        "image": ["add", "remove", "modify"],
        "text": ["add", "remove", "modify"],
        "health": ["check"],
        "metrics": ["read"]
    }
}
```

## 🔍 输入验证与防护

### 4. 输入验证规则

```python
# 输入验证配置
INPUT_VALIDATION = {
    "draft_creation": {
        "width": {
            "type": "integer",
            "min": 480,
            "max": 4096,
            "required": True
        },
        "height": {
            "type": "integer", 
            "min": 360,
            "max": 4096,
            "required": True
        },
        "project_name": {
            "type": "string",
            "min_length": 1,
            "max_length": 100,
            "pattern": "^[a-zA-Z0-9_\\-\\s]+$",
            "required": True
        }
    },
    "file_upload": {
        "max_size": "100MB",
        "allowed_types": [
            "video/mp4", "video/avi", "video/mov",
            "image/jpeg", "image/png", "image/gif"
        ],
        "scan_malware": True,
        "quarantine_suspicious": True
    }
}
```

### 5. SQL注入防护

```python
# 数据库安全配置
DATABASE_SECURITY = {
    "use_parameterized_queries": True,
    "escape_special_chars": True,
    "validate_sql_syntax": True,
    "query_timeout": 30,
    "max_query_length": 10000,
    "blocked_keywords": [
        "DROP", "DELETE", "TRUNCATE", "ALTER",
        "EXEC", "EXECUTE", "UNION", "SCRIPT"
    ]
}
```

### 6. XSS防护

```python
# XSS防护配置
XSS_PROTECTION = {
    "input_sanitization": {
        "enabled": True,
        "whitelist_tags": ["b", "i", "u", "strong", "em"],
        "remove_scripts": True,
        "encode_html": True
    },
    "output_encoding": {
        "html_encode": True,
        "js_encode": True,
        "url_encode": True,
        "css_encode": True
    },
    "csp_headers": {
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline'",
        "style-src": "'self' 'unsafe-inline'",
        "img-src": "'self' data: https:",
        "connect-src": "'self'"
    }
}
```

## 🔒 数据加密

### 7. 传输加密

```python
# TLS配置
TLS_CONFIG = {
    "version": "TLSv1.3",
    "cipher_suites": [
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_GCM_SHA256"
    ],
    "certificate": {
        "path": "/etc/ssl/certs/mcp-bridge.crt",
        "key_path": "/etc/ssl/private/mcp-bridge.key",
        "ca_path": "/etc/ssl/certs/ca.crt",
        "verify_client": True
    },
    "hsts": {
        "enabled": True,
        "max_age": 31536000,
        "include_subdomains": True,
        "preload": True
    }
}
```

### 8. 存储加密

```python
# 数据加密配置
ENCRYPTION_CONFIG = {
    "at_rest": {
        "algorithm": "AES-256-GCM",
        "key_derivation": "PBKDF2",
        "iterations": 100000,
        "salt_length": 32
    },
    "in_transit": {
        "algorithm": "ChaCha20-Poly1305",
        "key_exchange": "ECDH-P256"
    },
    "key_management": {
        "provider": "vault",
        "rotation_period": "90d",
        "backup_keys": 3,
        "secure_deletion": True
    }
}
```

## 🚨 安全监控

### 9. 入侵检测

```python
# 入侵检测配置
IDS_CONFIG = {
    "enabled": True,
    "rules": [
        {
            "name": "brute_force_detection",
            "pattern": "failed_login_attempts > 5 in 5m",
            "action": "block_ip",
            "duration": "1h"
        },
        {
            "name": "sql_injection_attempt",
            "pattern": "request contains sql_keywords",
            "action": "alert_and_log",
            "severity": "high"
        },
        {
            "name": "unusual_traffic_pattern",
            "pattern": "request_rate > 1000/min from single_ip",
            "action": "rate_limit",
            "threshold": "100/min"
        }
    ],
    "response": {
        "alert_channels": ["email", "slack", "webhook"],
        "auto_block": True,
        "forensic_logging": True
    }
}
```

### 10. 安全审计

```python
# 审计日志配置
AUDIT_CONFIG = {
    "enabled": True,
    "events": [
        "authentication", "authorization", "data_access",
        "configuration_change", "privilege_escalation",
        "system_error", "security_violation"
    ],
    "format": "json",
    "fields": [
        "timestamp", "user_id", "ip_address", "user_agent",
        "action", "resource", "result", "risk_score"
    ],
    "storage": {
        "type": "elasticsearch",
        "index": "mcp-bridge-audit",
        "retention": "2y",
        "encryption": True
    },
    "alerting": {
        "high_risk_threshold": 8,
        "anomaly_detection": True,
        "real_time_alerts": True
    }
}
```

## 🛠️ 安全配置

### 11. 容器安全

```dockerfile
# 安全的Dockerfile配置
FROM python:3.11-slim

# 创建非root用户
RUN groupadd -r mcpbridge && useradd -r -g mcpbridge mcpbridge

# 安装安全更新
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 设置安全的文件权限
COPY --chown=mcpbridge:mcpbridge . /app
WORKDIR /app

# 移除不必要的权限
RUN chmod -R 755 /app && \
    chmod 644 /app/config/*.yaml

# 使用非root用户运行
USER mcpbridge

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:9101/health || exit 1

# 设置安全标签
LABEL security.scan="enabled" \
      security.policy="strict" \
      maintainer="security@company.com"
```

### 12. Kubernetes安全配置

```yaml
# 安全的K8s部署配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-bridge
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: mcp-bridge
        image: mcp-bridge:latest
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            cpu: 1000m
            memory: 1Gi
          requests:
            cpu: 500m
            memory: 512Mi
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
---
apiVersion: v1
kind: NetworkPolicy
metadata:
  name: mcp-bridge-netpol
spec:
  podSelector:
    matchLabels:
      app: mcp-bridge
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: dify
    ports:
    - protocol: TCP
      port: 9101
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: capcut-api
    ports:
    - protocol: TCP
      port: 9000
```

## 🔧 安全检查清单

### 13. 部署前安全检查

```bash
#!/bin/bash
# 安全检查脚本

echo "🔍 开始安全检查..."

# 1. 检查敏感信息泄露
echo "检查敏感信息..."
grep -r "password\|secret\|key" --include="*.py" --include="*.yaml" . || echo "✅ 未发现硬编码敏感信息"

# 2. 检查依赖漏洞
echo "检查依赖漏洞..."
safety check || echo "⚠️  发现依赖漏洞，请及时修复"

# 3. 检查代码质量
echo "检查代码安全..."
bandit -r . -f json -o security_report.json || echo "⚠️  发现安全问题"

# 4. 检查容器镜像
echo "检查容器镜像..."
trivy image mcp-bridge:latest || echo "⚠️  镜像存在安全漏洞"

# 5. 检查配置文件
echo "检查配置安全..."
if [ -f "config/production.yaml" ]; then
    grep -i "debug.*true" config/production.yaml && echo "❌ 生产环境不应开启调试模式"
fi

echo "✅ 安全检查完成"
```

### 14. 运行时安全监控

```python
# 运行时安全监控
RUNTIME_SECURITY = {
    "file_integrity": {
        "enabled": True,
        "monitored_paths": [
            "/app/config/",
            "/app/core/",
            "/etc/ssl/"
        ],
        "alert_on_change": True
    },
    "process_monitoring": {
        "enabled": True,
        "whitelist_processes": [
            "python", "gunicorn", "redis-server"
        ],
        "alert_on_unknown": True
    },
    "network_monitoring": {
        "enabled": True,
        "allowed_connections": [
            {"host": "capcut-api", "port": 9000},
            {"host": "redis", "port": 6379},
            {"host": "prometheus", "port": 9090}
        ],
        "block_unknown": True
    }
}
```

## 📋 安全事件响应

### 15. 事件响应流程

```python
# 安全事件响应配置
INCIDENT_RESPONSE = {
    "severity_levels": {
        "critical": {
            "response_time": "15m",
            "escalation": ["security_team", "management"],
            "actions": ["isolate_system", "preserve_evidence"]
        },
        "high": {
            "response_time": "1h", 
            "escalation": ["security_team"],
            "actions": ["investigate", "contain_threat"]
        },
        "medium": {
            "response_time": "4h",
            "escalation": ["ops_team"],
            "actions": ["monitor", "log_analysis"]
        }
    },
    "playbooks": {
        "data_breach": "/security/playbooks/data_breach.md",
        "ddos_attack": "/security/playbooks/ddos_response.md",
        "malware_detection": "/security/playbooks/malware_response.md"
    }
}
```

---

通过实施以上安全措施，MCP Bridge可以在生产环境中提供企业级的安全保障，确保数据和系统的安全性。