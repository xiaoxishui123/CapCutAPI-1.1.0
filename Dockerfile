# CapCutAPI Docker 镜像
# 基于 Python 3.9 官方镜像
FROM python:3.9-slim

# 设置维护者信息
LABEL maintainer="CapCutAPI Team"
LABEL description="CapCutAPI - 剪映视频编辑自动化 API 服务"

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 安装系统依赖（FFmpeg 和其他必要工具）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p logs data

# 暴露端口（默认 9000）
EXPOSE 9000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9000/get_intro_animation_types || exit 1

# 启动命令
CMD ["python", "capcut_server.py"]
