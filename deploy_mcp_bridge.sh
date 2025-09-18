#!/bin/bash

# CapCut API MCP Bridge 部署脚本
# 版本：v1.0.0
# 作者：AI Assistant
# 更新时间：2025年1月14日

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查系统要求
check_requirements() {
    log_step "检查系统要求..."
    
    # 检查 Python 版本
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Python 版本: $python_version"
    
    # 检查 Redis
    if ! command -v redis-server &> /dev/null; then
        log_warn "Redis 未安装，正在安装..."
        sudo apt update
        sudo apt install -y redis-server
    fi
    
    # 检查 Docker (可选)
    if command -v docker &> /dev/null; then
        log_info "Docker 已安装"
    else
        log_warn "Docker 未安装，建议安装以便容器化部署"
    fi
}

# 安装依赖
install_dependencies() {
    log_step "安装 Python 依赖..."
    
    cd /home/CapCutAPI-1.1.0/mcp_bridge
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_info "创建虚拟环境完成"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    
    log_info "依赖安装完成"
}

# 配置服务
configure_services() {
    log_step "配置服务..."
    
    # 启动 Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    log_info "Redis 服务已启动"
    
    # 检查 CapCut API 服务
    if curl -s http://localhost:9000/ > /dev/null; then
        log_info "CapCut API 服务运行正常"
    else
        log_warn "CapCut API 服务未运行，请先启动"
        log_info "运行命令: cd /home/CapCutAPI-1.1.0 && ./service_manager.sh start"
    fi
}

# 创建配置文件
create_config() {
    log_step "创建配置文件..."
    
    cat > /home/CapCutAPI-1.1.0/mcp_bridge/config/production.yaml << 'EOF'
# MCP Bridge 生产环境配置
server:
  host: "0.0.0.0"
  port: 9101
  workers: 4
  log_level: "INFO"

services:
  mcp_services:
    - name: "capcut_mcp"
      type: "mcp"
      endpoint: "ws://localhost:3001/mcp"
      priority: 1
      weight: 100
      timeout: 30
      enabled: true
      supported_methods:
        - "capcut_create_draft"
        - "capcut_add_video"
        - "capcut_add_text"
        - "capcut_add_subtitle"
        - "capcut_save_draft"

  http_services:
    - name: "capcut_http"
      type: "http"
      endpoint: "http://localhost:9000"
      priority: 2
      weight: 50
      timeout: 15
      enabled: true
      supported_methods:
        - "get_intro_animation_types"
        - "get_outro_animation_types"
        - "get_transition_types"
        - "create_draft"
        - "add_video"
        - "add_text"
        - "save_draft"

fallback:
  enabled: true
  circuit_breaker:
    failure_threshold: 5
    recovery_timeout: 30
    half_open_max_calls: 3

cache:
  enabled: true
  redis_url: "redis://localhost:6379"
  default_ttl: 300
  max_size: 1000

monitoring:
  enabled: true
  metrics_port: 9102
  health_check_interval: 30

security:
  api_key_required: false
  cors_enabled: true
  rate_limit:
    enabled: true
    requests_per_minute: 100
EOF

    log_info "配置文件创建完成"
}

# 创建 systemd 服务
create_systemd_service() {
    log_step "创建 systemd 服务..."
    
    sudo tee /etc/systemd/system/mcp-bridge.service > /dev/null << EOF
[Unit]
Description=MCP Bridge Service
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/CapCutAPI-1.1.0/mcp_bridge
Environment=PATH=/home/CapCutAPI-1.1.0/mcp_bridge/venv/bin
ExecStart=/home/CapCutAPI-1.1.0/mcp_bridge/venv/bin/python -m uvicorn core.bridge_server:app --host 0.0.0.0 --port 9101 --workers 4
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable mcp-bridge.service
    
    log_info "systemd 服务创建完成"
}

# 启动服务
start_services() {
    log_step "启动服务..."
    
    # 启动 MCP Bridge
    sudo systemctl start mcp-bridge.service
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    if sudo systemctl is-active --quiet mcp-bridge.service; then
        log_info "MCP Bridge 服务启动成功"
    else
        log_error "MCP Bridge 服务启动失败"
        sudo systemctl status mcp-bridge.service
        exit 1
    fi
}

# 测试服务
test_services() {
    log_step "测试服务..."
    
    # 测试健康检查
    if curl -s http://localhost:9101/health > /dev/null; then
        log_info "健康检查通过"
    else
        log_error "健康检查失败"
        exit 1
    fi
    
    # 测试 MCP 端点
    response=$(curl -s -X POST http://localhost:9101/mcp \
        -H "Content-Type: application/json" \
        -d '{"id":"test","method":"capcut_create_draft","params":{"title":"test"}}')
    
    if echo "$response" | grep -q "success\|result"; then
        log_info "MCP 端点测试通过"
    else
        log_warn "MCP 端点测试失败，可能需要检查 CapCut API 服务"
    fi
}

# 显示部署信息
show_deployment_info() {
    log_step "部署完成！"
    
    echo ""
    echo "=========================================="
    echo "         MCP Bridge 部署信息"
    echo "=========================================="
    echo "服务地址: http://localhost:9101"
    echo "健康检查: http://localhost:9101/health"
    echo "指标监控: http://localhost:9102/metrics"
    echo "配置文件: /home/CapCutAPI-1.1.0/mcp_bridge/config/production.yaml"
    echo "日志查看: sudo journalctl -u mcp-bridge.service -f"
    echo ""
    echo "服务管理命令:"
    echo "  启动: sudo systemctl start mcp-bridge.service"
    echo "  停止: sudo systemctl stop mcp-bridge.service"
    echo "  重启: sudo systemctl restart mcp-bridge.service"
    echo "  状态: sudo systemctl status mcp-bridge.service"
    echo ""
    echo "下一步: 在 Dify 工作流中配置 MCP 服务器"
    echo "  服务器URL: http://localhost:9101"
    echo "  服务器标识: capcut-mcp-bridge"
    echo "=========================================="
}

# 主函数
main() {
    log_info "开始部署 CapCut API MCP Bridge 服务..."
    
    check_requirements
    install_dependencies
    configure_services
    create_config
    create_systemd_service
    start_services
    test_services
    show_deployment_info
    
    log_info "部署完成！"
}

# 执行主函数
main "$@"