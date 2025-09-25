#!/bin/bash

# MCP Bridge 服务管理脚本
# 提供启动、停止、重启、状态检查、日志查看等功能

set -e

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/venv"
PID_FILE="$PROJECT_DIR/bridge_server.pid"
LOG_DIR="$PROJECT_DIR/logs"
CONFIG_FILE="$PROJECT_DIR/.env"

# 加载环境变量
if [ -f "$CONFIG_FILE" ]; then
    export $(grep -v '^#' "$CONFIG_FILE" | xargs)
fi

# 设置默认端口
SERVER_PORT=${SERVER_PORT:-8080}

# 颜色输出
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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查虚拟环境
check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_error "虚拟环境不存在: $VENV_DIR"
        log_info "请先运行: ./deploy.sh install"
        exit 1
    fi
}

# 激活虚拟环境
activate_venv() {
    source "$VENV_DIR/bin/activate"
}

# 检查服务是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID文件存在但进程不存在，清理PID文件
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# 获取服务PID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# 启动服务
start_service() {
    log_info "启动MCP Bridge服务..."
    
    if is_running; then
        log_warn "服务已经在运行中 (PID: $(get_pid))"
        return 0
    fi
    
    check_venv
    activate_venv
    
    # 确保日志目录存在
    mkdir -p "$LOG_DIR"
    
    # 启动服务
    cd "$PROJECT_DIR"
    nohup python core/bridge_server.py > "$LOG_DIR/bridge_server.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # 等待服务启动
    sleep 3
    
    if is_running; then
        log_info "服务启动成功 (PID: $pid)"
        log_info "服务地址: http://localhost:$SERVER_PORT"
        log_info "健康检查: http://localhost:$SERVER_PORT/health"
        log_info "指标监控: http://localhost:$SERVER_PORT/metrics"
    else
        log_error "服务启动失败"
        if [ -f "$LOG_DIR/bridge_server.log" ]; then
            log_error "错误日志:"
            tail -20 "$LOG_DIR/bridge_server.log"
        fi
        exit 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止MCP Bridge服务..."
    
    if ! is_running; then
        log_warn "服务未运行"
        return 0
    fi
    
    local pid=$(get_pid)
    log_info "正在停止服务 (PID: $pid)..."
    
    # 发送TERM信号
    kill -TERM "$pid" 2>/dev/null || true
    
    # 等待进程结束
    local count=0
    while [ $count -lt 10 ] && ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
    done
    
    # 如果进程仍在运行，强制杀死
    if ps -p "$pid" > /dev/null 2>&1; then
        log_warn "进程未正常结束，强制杀死..."
        kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    fi
    
    # 清理PID文件
    rm -f "$PID_FILE"
    
    log_info "服务已停止"
}

# 重启服务
restart_service() {
    log_info "重启MCP Bridge服务..."
    stop_service
    sleep 2
    start_service
}

# 查看服务状态
status_service() {
    echo "=== MCP Bridge 服务状态 ==="
    
    if is_running; then
        local pid=$(get_pid)
        log_info "服务状态: ${GREEN}运行中${NC}"
        log_info "进程ID: $pid"
        
        # 获取进程信息
        if command -v ps > /dev/null; then
            echo "进程信息:"
            ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem 2>/dev/null || true
        fi
        
        # 检查端口
        if command -v netstat > /dev/null; then
            echo "端口监听:"
            netstat -tlnp 2>/dev/null | grep ":$SERVER_PORT" || echo "端口$SERVER_PORT未监听"
        fi
        
        # 健康检查
        echo "健康检查:"
        if command -v curl > /dev/null; then
            curl -s -f http://localhost:$SERVER_PORT/health > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                log_info "健康检查: ${GREEN}通过${NC}"
            else
                log_error "健康检查: ${RED}失败${NC}"
            fi
        else
            log_warn "curl未安装，无法进行健康检查"
        fi
    else
        log_error "服务状态: ${RED}未运行${NC}"
    fi
    
    echo ""
}

# 查看日志
logs_service() {
    local lines=${1:-50}
    local log_file="$LOG_DIR/bridge_server.log"
    
    if [ ! -f "$log_file" ]; then
        log_error "日志文件不存在: $log_file"
        return 1
    fi
    
    echo "=== MCP Bridge 服务日志 (最近 $lines 行) ==="
    tail -n "$lines" "$log_file"
}

# 实时查看日志
follow_logs() {
    local log_file="$LOG_DIR/bridge_server.log"
    
    if [ ! -f "$log_file" ]; then
        log_error "日志文件不存在: $log_file"
        return 1
    fi
    
    log_info "实时查看日志 (Ctrl+C 退出)..."
    tail -f "$log_file"
}

# 测试服务
test_service() {
    log_info "测试MCP Bridge服务..."
    
    if ! is_running; then
        log_error "服务未运行，请先启动服务"
        return 1
    fi
    
    if ! command -v curl > /dev/null; then
        log_error "curl未安装，无法进行测试"
        return 1
    fi
    
    echo "=== 服务测试结果 ==="
    
    # 测试健康检查
    echo "1. 健康检查测试:"
    if curl -s -f http://localhost:8082/health > /dev/null; then
        log_info "✓ 健康检查通过"
        curl -s http://localhost:8082/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8082/health
    else
        log_error "✗ 健康检查失败"
    fi
    
    echo ""
    
    # 测试指标监控
    echo "2. 指标监控测试:"
    if curl -s -f http://localhost:8082/metrics > /dev/null; then
        log_info "✓ 指标监控正常"
        curl -s http://localhost:8082/metrics | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8082/metrics
    else
        log_error "✗ 指标监控失败"
    fi
    
    echo ""
    
    # 测试MCP接口
    echo "3. MCP接口测试:"
    local test_data='{"jsonrpc": "2.0", "id": 1, "method": "capcut_create_draft", "params": {"title": "测试视频", "description": "这是一个测试视频"}}'
    
    if curl -s -f -X POST -H "Content-Type: application/json" -d "$test_data" http://localhost:8082/mcp > /dev/null; then
        log_info "✓ MCP接口正常"
        curl -s -X POST -H "Content-Type: application/json" -d "$test_data" http://localhost:8082/mcp | python3 -m json.tool 2>/dev/null
    else
        log_error "✗ MCP接口失败"
    fi
    
    echo ""
}

# 清理日志
clean_logs() {
    log_info "清理日志文件..."
    
    if [ -d "$LOG_DIR" ]; then
        find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
        find "$LOG_DIR" -name "*.log.*" -type f -mtime +7 -delete 2>/dev/null || true
        log_info "已清理7天前的日志文件"
    fi
}

# 显示帮助信息
show_help() {
    echo "MCP Bridge 服务管理脚本"
    echo ""
    echo "用法: $0 <命令> [选项]"
    echo ""
    echo "命令:"
    echo "  start          启动服务"
    echo "  stop           停止服务"
    echo "  restart        重启服务"
    echo "  status         查看服务状态"
    echo "  logs [行数]    查看日志 (默认50行)"
    echo "  follow         实时查看日志"
    echo "  test           测试服务功能"
    echo "  clean          清理旧日志文件"
    echo "  help           显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start                # 启动服务"
    echo "  $0 logs 100            # 查看最近100行日志"
    echo "  $0 follow              # 实时查看日志"
    echo "  $0 test                # 测试服务功能"
    echo ""
}

# 主函数
main() {
    case "${1:-}" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            status_service
            ;;
        logs)
            logs_service "${2:-50}"
            ;;
        follow)
            follow_logs
            ;;
        test)
            test_service
            ;;
        clean)
            clean_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            log_error "请指定命令"
            echo ""
            show_help
            exit 1
            ;;
        *)
            log_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"