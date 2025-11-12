# Docker 部署指南

## 📦 Docker 配置说明

本项目提供了两套 Docker Compose 配置：

### 1. 生产环境 (`docker-compose.yml`)
- **镜像来源**: GitHub Container Registry (GHCR)
- **自动构建**: GitHub Actions 自动构建并推送
- **使用场景**: 服务器部署、CI/CD 自动部署

### 2. 开发环境 (`docker-compose.dev.yml`)
- **镜像来源**: 本地构建
- **代码挂载**: 支持热重载
- **使用场景**: 本地开发、功能测试

---

## 🚀 快速开始

### 生产环境部署

```bash
# 1. 拉取最新代码
git pull

# 2. 启动服务（使用 GHCR 镜像）
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 健康检查
curl http://localhost:9000/get_intro_animation_types
```

### 本地开发环境

```bash
# 1. 使用开发配置启动
docker-compose -f docker-compose.dev.yml up -d

# 2. 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 3. 停止服务
docker-compose -f docker-compose.dev.yml down
```

---

## 🔧 配置要求

### 必需文件
确保以下文件存在于项目根目录：

- ✅ `config.json` - 服务配置
- ✅ `path_config.json` - 路径配置
- ✅ `.env` - 环境变量（包含 OSS 密钥等）

### .env 文件示例
```env
# Flask 配置
FLASK_ENV=production
FLASK_DEBUG=0

# OSS 配置
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_BUCKET_NAME=your_bucket_name
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
```

---

## 🔄 CI/CD 自动部署流程

当代码推送到 `master` 分支时，GitHub Actions 会自动：

1. ✅ 构建 Docker 镜像（多架构：amd64 + arm64）
2. ✅ 推送到 GHCR (`ghcr.io/xiaoxishui123/capcutapi-1-1-0:latest`)
3. ✅ SSH 登录到部署服务器
4. ✅ 拉取最新镜像
5. ✅ 重启容器
6. ✅ 执行健康检查

### 查看部署状态
- GitHub Actions: https://github.com/xiaoxishui123/CapCutAPI-1.1.0/actions
- 服务地址: http://8.148.70.18:9000

---

## 📋 常用命令

### 镜像管理
```bash
# 拉取最新镜像
docker pull ghcr.io/xiaoxishui123/capcutapi-1-1-0:latest

# 查看本地镜像
docker images | grep capcutapi

# 清理旧镜像
docker image prune -f
```

### 容器管理
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 进入容器
docker exec -it capcutapi bash
```

### 故障排查
```bash
# 查看容器详细信息
docker inspect capcutapi

# 查看容器资源使用
docker stats capcutapi

# 查看最近 100 行日志
docker-compose logs --tail 100

# 重新构建并启动（开发环境）
docker-compose -f docker-compose.dev.yml up -d --build
```

---

## 🐛 常见问题

### 1. 部署失败：找不到 Dockerfile
**原因**: `docker-compose.yml` 配置了本地构建而不是使用 GHCR 镜像
**解决**: 确保使用 `image: ghcr.io/xiaoxishui123/capcutapi-1-1-0:latest`

### 2. 健康检查失败
**原因**: 服务未正常启动或端口未暴露
**解决**:
```bash
# 查看容器日志
docker-compose logs capcutapi

# 检查端口映射
docker ps | grep capcutapi

# 手动测试健康检查
docker exec capcutapi curl -f http://localhost:9000/get_intro_animation_types
```

### 3. 配置文件找不到
**原因**: 挂载的配置文件不存在
**解决**:
```bash
# 检查配置文件
ls -la config.json path_config.json .env

# 从示例创建配置
cp config.json.example config.json
cp .env.example .env
```

### 4. 数据库权限问题
**原因**: 容器内用户无法写入数据库文件
**解决**:
```bash
# 修改数据库文件权限
chmod 666 capcut.db drafts.db

# 或创建空数据库文件
touch capcut.db drafts.db
chmod 666 capcut.db drafts.db
```

---

## 🔐 安全建议

1. **环境变量**: 不要将 `.env` 文件提交到 Git
2. **敏感配置**: 使用 Docker secrets 或 Kubernetes ConfigMap
3. **镜像安全**: 定期更新基础镜像修复安全漏洞
4. **端口暴露**: 生产环境建议使用 Nginx 反向代理

---

## 📚 相关文档

- [部署总结](docs/CapCutAPI部署总结.md)
- [故障排除](docs/TROUBLESHOOTING.md)
- [API 文档](docs/API_USAGE_EXAMPLES.md)
- [GitHub Actions Workflow](.github/workflows/main.yml)

---

**更新时间**: 2025-11-12
**维护者**: CapCutAPI Team
