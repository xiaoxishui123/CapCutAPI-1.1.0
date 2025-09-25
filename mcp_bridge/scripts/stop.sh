#!/bin/bash

# MCP Bridge 停止脚本
# 功能：停止所有MCP Bridge服务组件

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

# 停止服务函数
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            log_info "停止 $service_name (PID: $pid)..."
            kill $pid
            
            # 等待进程结束
            local count=0
            while kill -0 $pid 2>/dev/null && [ $count -lt 30 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # 如果进程仍在运行，强制终止
            if kill -0 $pid 2>/dev/null; then
                log_warning "$service_name 未正常停止，强制终止..."
                kill -9 $pid
                sleep 1
            fi
            
            if ! kill -0 $pid 2>/dev/null; then
                log_success "$service_name 已停止"
                rm -f "$pid_file"
            else
                log_error "$service_name 停止失败"
                return 1
            fi
        else
            log_warning "$service_name PID文件存在但进程不在运行"
            rm -f "$pid_file"
        fi
    else
        log_info "$service_name 未在运行"
    fi
}

# 停止主服务
stop_main_service() {
    stop_service "MCP Bridge主服务" "$PROJECT_ROOT/logs/main.pid"
}

# 停止HTTP桥接服务
stop_http_bridge() {
    stop_service "HTTP桥接服务" "$PROJECT_ROOT/logs/http_bridge.pid"
}

# 停止工作流服务
stop_workflow_service() {
    stop_service "工作流服务" "$PROJECT_ROOT/logs/workflow.pid"
}

# 停止所有相关进程
stop_all_processes() {
    log_info "查找并停止所有相关进程..."
    
    # 查找Python进程
    local pids=$(pgrep -f "mcp_bridge\|capcut_http_mcp_bridge" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        log_info "发现相关进程: $pids"
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                log_info "停止进程 $pid..."
                kill $pid
                sleep 1
                
                # 如果进程仍在运行，强制终止
                if kill -0 $pid 2>/dev/null; then
                    kill -9 $pid
                fi
            fi
        done
        log_success "所有相关进程已停止"
    else
        log_info "未发现相关进程"
    fi
}

# 清理临时文件
cleanup_temp_files() {
    log_info "清理临时文件..."
    
    # 清理PID文件
    rm -f "$PROJECT_ROOT/logs/"*.pid
    
    # 清理临时目录
    if [ -d "$PROJECT_ROOT/temp" ]; then
        rm -rf "$PROJECT_ROOT/temp"/*
    fi
    
    log_success "临时文件清理完成"
}

# 显示停止状态
show_stop_status() {
    echo ""
    log_info "=== MCP Bridge 停止状态 ==="
    echo ""
    
    local all_stopped=true
    
    # 检查主服务
    if [ -f "$PROJECT_ROOT/logs/main.pid" ]; then
        local main_pid=$(cat "$PROJECT_ROOT/logs/main.pid")
        if kill -0 $main_pid 2>/dev/null; then
            log_error "主服务: 仍在运行 (PID: $main_pid)"
            all_stopped=false
        else
            log_success "主服务: 已停止"
        fi
    else
        log_success "主服务: 已停止"
    fi
    
    # 检查HTTP桥接服务
    if [ -f "$PROJECT_ROOT/logs/http_bridge.pid" ]; then
        local http_pid=$(cat "$PROJECT_ROOT/logs/http_bridge.pid")
        if kill -0 $http_pid 2>/dev/null; then
            log_error "HTTP桥接服务: 仍在运行 (PID: $http_pid)"
            all_stopped=false
        else
            log_success "HTTP桥接服务: 已停止"
        fi
    else
        log_success "HTTP桥接服务: 已停止"
    fi
    
    echo ""
    if [ "$all_stopped" = true ]; then
        log_success "所有服务已成功停止"
    else
        log_error "部分服务停止失败"
        return 1
    fi
}

# 优雅停止
graceful_stop() {
    log_info "执行优雅停止..."
    
    stop_main_service
    stop_http_bridge
    stop_workflow_service
    
    # 等待一段时间确保所有服务都已停止
    sleep 2
    
    show_stop_status
}

# 强制停止
force_stop() {
    log_warning "执行强制停止..."
    
    stop_all_processes
    cleanup_temp_files
    
    log_success "强制停止完成"
}

# 主函数
main() {
    echo ""
    log_info "=== MCP Bridge 停止脚本 ==="
    echo ""
    
    case "${1:-graceful}" in
        "force")
            force_stop
            ;;
        "graceful"|*)
            graceful_stop
            ;;
    esac
}

# 处理命令行参数
case "${1:-}" in
    "force")
        main "force"
        ;;
    "status")
        show_stop_status
        ;;
    *)
        main "graceful"
        ;;
esac