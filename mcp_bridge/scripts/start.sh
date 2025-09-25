#!/bin/bash

# MCP Bridge 启动脚本
# 功能：启动所有MCP Bridge服务组件

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查pip
    if ! command -v pip &> /dev/null; then
        log_error "pip 未安装"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 设置环境
setup_environment() {
    log_info "设置环境..."
    
    cd "$PROJECT_ROOT"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        log_info "安装Python依赖..."
        pip install -r requirements.txt
    fi
    
    log_success "环境设置完成"
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."
    
    # 检查主配置文件
    if [ ! -f "$PROJECT_ROOT/config/unified_config.yaml" ]; then
        log_error "配置文件不存在: config/unified_config.yaml"
        exit 1
    fi
    
    # 检查环境变量文件
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            log_warning "未找到.env文件，复制.env.example"
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            log_warning "请编辑.env文件设置正确的配置值"
        else
            log_error "未找到环境变量配置文件"
            exit 1
        fi
    fi
    
    log_success "配置文件检查完成"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/temp"
    mkdir -p "$PROJECT_ROOT/data"
    
    log_success "目录创建完成"
}

# 启动Redis（如果需要）
start_redis() {
    if command -v redis-server &> /dev/null; then
        if ! pgrep -x "redis-server" > /dev/null; then
            log_info "启动Redis服务..."
            redis-server --daemonize yes
            sleep 2
            log_success "Redis服务已启动"
        else
            log_info "Redis服务已在运行"
        fi
    else
        log_warning "Redis未安装，缓存功能将被禁用"
    fi
}

# 启动主服务
start_main_service() {
    log_info "启动MCP Bridge主服务..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    
    # 启动主服务
    nohup python src/main.py > logs/mcp_bridge.log 2>&1 &
    MAIN_PID=$!
    echo $MAIN_PID > logs/main.pid
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否启动成功
    if kill -0 $MAIN_PID 2>/dev/null; then
        log_success "MCP Bridge主服务已启动 (PID: $MAIN_PID)"
    else
        log_error "MCP Bridge主服务启动失败"
        exit 1
    fi
}

# 启动HTTP桥接服务
start_http_bridge() {
    log_info "启动HTTP桥接服务..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    # 启动HTTP桥接服务
    nohup python integrations/http_bridge/capcut_http_mcp_bridge.py > logs/http_bridge.log 2>&1 &
    HTTP_PID=$!
    echo $HTTP_PID > logs/http_bridge.pid
    
    # 等待服务启动
    sleep 2
    
    # 检查服务是否启动成功
    if kill -0 $HTTP_PID 2>/dev/null; then
        log_success "HTTP桥接服务已启动 (PID: $HTTP_PID)"
    else
        log_error "HTTP桥接服务启动失败"
        exit 1
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查主服务
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        log_success "主服务健康检查通过"
    else
        log_warning "主服务健康检查失败"
    fi
    
    # 检查HTTP桥接服务
    if curl -s http://localhost:8081/health > /dev/null 2>&1; then
        log_success "HTTP桥接服务健康检查通过"
    else
        log_warning "HTTP桥接服务健康检查失败"
    fi
}

# 显示服务状态
show_status() {
    echo ""
    log_info "=== MCP Bridge 服务状态 ==="
    echo ""
    
    # 主服务状态
    if [ -f "$PROJECT_ROOT/logs/main.pid" ]; then
        MAIN_PID=$(cat "$PROJECT_ROOT/logs/main.pid")
        if kill -0 $MAIN_PID 2>/dev/null; then
            log_success "主服务: 运行中 (PID: $MAIN_PID, 端口: 8080)"
        else
            log_error "主服务: 已停止"
        fi
    else
        log_error "主服务: 未启动"
    fi
    
    # HTTP桥接服务状态
    if [ -f "$PROJECT_ROOT/logs/http_bridge.pid" ]; then
        HTTP_PID=$(cat "$PROJECT_ROOT/logs/http_bridge.pid")
        if kill -0 $HTTP_PID 2>/dev/null; then
            log_success "HTTP桥接服务: 运行中 (PID: $HTTP_PID, 端口: 8081)"
        else
            log_error "HTTP桥接服务: 已停止"
        fi
    else
        log_error "HTTP桥接服务: 未启动"
    fi
    
    echo ""
    log_info "日志文件位置:"
    echo "  - 主服务: $PROJECT_ROOT/logs/mcp_bridge.log"
    echo "  - HTTP桥接: $PROJECT_ROOT/logs/http_bridge.log"
    echo ""
    log_info "API端点:"
    echo "  - 主服务: http://localhost:8080"
    echo "  - HTTP桥接: http://localhost:8081"
    echo "  - 健康检查: http://localhost:8080/health"
    echo ""
}

# 主函数
main() {
    echo ""
    log_info "=== MCP Bridge 启动脚本 ==="
    echo ""
    
    # 执行启动步骤
    check_dependencies
    setup_environment
    check_config
    create_directories
    start_redis
    start_main_service
    start_http_bridge
    
    # 等待服务完全启动
    sleep 5
    
    # 执行健康检查
    health_check
    
    # 显示服务状态
    show_status
    
    log_success "MCP Bridge 启动完成！"
}

# 处理命令行参数
case "${1:-}" in
    "status")
        show_status
        ;;
    "health")
        health_check
        ;;
    *)
        main
        ;;
esac