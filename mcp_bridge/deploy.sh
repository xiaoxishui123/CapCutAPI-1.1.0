#!/bin/bash

# MCP Bridge 一键部署脚本
# 版本：v1.0.0
# 更新时间：2025年1月14日
# 作者：AI Assistant

set -e  # 遇到错误立即退出

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

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装"
        return 1
    fi
    return 0
}

# 检查系统环境
check_environment() {
    log_info "检查系统环境..."
    
    # 检查Python
    if ! check_command python3; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查pip
    if ! check_command pip3; then
        log_error "pip3 未安装"
        exit 1
    fi
    
    # 检查Redis
    if ! systemctl is-active --quiet redis; then
        log_warning "Redis 服务未运行，尝试启动..."
        sudo systemctl start redis || {
            log_error "Redis 启动失败"
            exit 1
        }
    fi
    
    log_success "系统环境检查完成"
}

# 安装Python依赖
install_dependencies() {
    log_info "安装Python依赖..."
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "依赖安装完成"
    else
        log_error "requirements.txt 文件不存在"
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    # 创建日志目录
    sudo mkdir -p /var/log/mcp_bridge
    sudo chown $USER:$USER /var/log/mcp_bridge
    
    # 创建本地日志目录
    mkdir -p logs
    
    # 创建配置目录（如果不存在）
    mkdir -p config
    
    log_success "目录创建完成"
}

# 配置服务
configure_service() {
    log_info "配置MCP Bridge服务..."
    
    # 检查配置文件
    if [ ! -f "config/bridge_config.yaml" ]; then
        log_error "配置文件 config/bridge_config.yaml 不存在"
        exit 1
    fi
    
    # 检查环境变量文件
    if [ ! -f ".env" ]; then
        log_warning ".env 文件不存在，使用默认配置"
    fi
    
    log_success "服务配置完成"
}

# 启动服务
start_service() {
    log_info "启动MCP Bridge服务..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 检查端口是否被占用
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null; then
        log_warning "端口8080已被占用，尝试停止现有服务..."
        pkill -f "bridge_server" || true
        sleep 2
    fi
    
    # 启动服务
    nohup python core/bridge_server.py > logs/bridge_server.log 2>&1 &
    
    # 获取进程ID
    BRIDGE_PID=$!
    echo $BRIDGE_PID > logs/bridge_server.pid
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否启动成功
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        log_success "MCP Bridge服务启动成功 (PID: $BRIDGE_PID)"
        log_info "服务地址: http://localhost:8080"
        log_info "健康检查: http://localhost:8080/health"
        log_info "指标监控: http://localhost:8080/metrics"
    else
        log_error "MCP Bridge服务启动失败"
        log_info "请检查日志文件: logs/bridge_server.log"
        exit 1
    fi
}

# 运行健康检查
health_check() {
    log_info "运行健康检查..."
    
    # 检查主服务
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        log_success "MCP Bridge服务健康"
    else
        log_error "MCP Bridge服务不健康"
        return 1
    fi
    
    # 检查Redis连接
    if redis-cli ping >/dev/null 2>&1; then
        log_success "Redis连接正常"
    else
        log_error "Redis连接失败"
        return 1
    fi
    
    return 0
}

# 显示服务状态
show_status() {
    log_info "服务状态信息:"
    echo "=================================="
    
    # MCP Bridge服务状态
    if [ -f "logs/bridge_server.pid" ]; then
        PID=$(cat logs/bridge_server.pid)
        if ps -p $PID > /dev/null; then
            echo "MCP Bridge: 运行中 (PID: $PID)"
        else
            echo "MCP Bridge: 已停止"
        fi
    else
        echo "MCP Bridge: 未启动"
    fi
    
    # Redis状态
    if systemctl is-active --quiet redis; then
        echo "Redis: 运行中"
    else
        echo "Redis: 已停止"
    fi
    
    # 端口监听状态
    echo ""
    echo "端口监听状态:"
    netstat -tlnp | grep -E ":(8080|6379|9001|9002)" || echo "无相关端口监听"
    
    echo "=================================="
}

# 停止服务
stop_service() {
    log_info "停止MCP Bridge服务..."
    
    if [ -f "logs/bridge_server.pid" ]; then
        PID=$(cat logs/bridge_server.pid)
        if ps -p $PID > /dev/null; then
            kill $PID
            sleep 2
            if ps -p $PID > /dev/null; then
                kill -9 $PID
            fi
            rm -f logs/bridge_server.pid
            log_success "MCP Bridge服务已停止"
        else
            log_warning "MCP Bridge服务未运行"
            rm -f logs/bridge_server.pid
        fi
    else
        log_warning "未找到PID文件，尝试强制停止..."
        pkill -f "bridge_server" || true
    fi
}

# 重启服务
restart_service() {
    log_info "重启MCP Bridge服务..."
    stop_service
    sleep 2
    start_service
}

# 查看日志
view_logs() {
    if [ -f "logs/bridge_server.log" ]; then
        tail -f logs/bridge_server.log
    else
        log_error "日志文件不存在"
    fi
}

# 清理环境
cleanup() {
    log_info "清理环境..."
    stop_service
    
    # 清理日志文件
    rm -f logs/*.log
    rm -f logs/*.pid
    
    # 清理虚拟环境（可选）
    read -p "是否删除虚拟环境? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        log_success "虚拟环境已删除"
    fi
    
    log_success "环境清理完成"
}

# 显示帮助信息
show_help() {
    echo "MCP Bridge 部署脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  install     安装并启动服务"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  status      显示服务状态"
    echo "  health      运行健康检查"
    echo "  logs        查看实时日志"
    echo "  cleanup     清理环境"
    echo "  help        显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 install    # 完整安装并启动"
    echo "  $0 status     # 查看服务状态"
    echo "  $0 logs       # 查看实时日志"
}

# 主函数
main() {
    case "${1:-install}" in
        "install")
            log_info "开始MCP Bridge完整部署..."
            check_environment
            install_dependencies
            create_directories
            configure_service
            start_service
            health_check
            show_status
            log_success "MCP Bridge部署完成!"
            ;;
        "start")
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            restart_service
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        "logs")
            view_logs
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 检查是否在正确的目录
if [ ! -f "core/bridge_server.py" ]; then
    log_error "请在MCP Bridge项目根目录下运行此脚本"
    exit 1
fi

# 运行主函数
main "$@"