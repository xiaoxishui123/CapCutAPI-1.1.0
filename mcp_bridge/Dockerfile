# MCP Bridge Dockerfile
# 版本：v1.0.0
# 更新时间：2025年1月14日

# 使用官方Python 3.11镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd -r mcp && useradd -r -g mcp mcp

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/logs /app/data && \
    chown -R mcp:mcp /app

# 切换到非root用户
USER mcp

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "core.bridge_server:app", "--host", "0.0.0.0", "--port", "8080"]