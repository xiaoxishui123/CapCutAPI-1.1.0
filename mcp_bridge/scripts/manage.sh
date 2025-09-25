#!/bin/bash

# MCP Bridge 管理脚本
# 功能：提供统一的服务管理接口

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_header() {
    echo -e "${PURPLE}$1${NC}"
}

# 显示帮助信息
show_help() {
    echo ""
    log_header "=== MCP Bridge 管理脚本 ==="
    echo ""
    echo "用法: $0 <命令> [选项]"
    echo ""
    echo "可用命令:"
    echo "  start           启动所有服务"
    echo "  stop            停止所有服务"
    echo "  restart         重启所有服务"
    echo "  status          显示服务状态"
    echo "  health          执行健康检查"
    echo "  logs            查看日志"
    echo "  test            运行测试"
    echo "  install         安装依赖"
    echo "  backup          备份配置和数据"
    echo "  restore         恢复配置和数据"
    echo "  clean           清理临时文件"
    echo "  update          更新项目"
    echo "  config          配置管理"
    echo "  monitor         监控服务"
    echo "  help            显示此帮助信息"
    echo ""
    echo "选项:"
    echo "  --force         强制执行操作"
    echo "  --verbose       详细输出"
    echo "  --config FILE   指定配置文件"
    echo ""
    echo "示例:"
    echo "  $0 start                    # 启动所有服务"
    echo "  $0 stop --force             # 强制停止所有服务"
    echo "  $0 logs --follow            # 实时查看日志"
    echo "  $0 test --unit              # 运行单元测试"
    echo ""
}

# 启动服务
start_services() {
    log_info "启动MCP Bridge服务..."
    bash "$SCRIPT_DIR/start.sh"
}

# 停止服务
stop_services() {
    local force_flag=""
    if [[ "$*" == *"--force"* ]]; then
        force_flag="force"
    fi
    
    log_info "停止MCP Bridge服务..."
    bash "$SCRIPT_DIR/stop.sh" $force_flag
}

# 重启服务
restart_services() {
    log_info "重启MCP Bridge服务..."
    stop_services "$@"
    sleep 3
    start_services
}

# 显示服务状态
show_status() {
    bash "$SCRIPT_DIR/start.sh" status
}

# 健康检查
health_check() {
    bash "$SCRIPT_DIR/start.sh" health
}

# 查看日志
view_logs() {
    local log_type="${2:-all}"
    local follow_flag=""
    
    if [[ "$*" == *"--follow"* ]] || [[ "$*" == *"-f"* ]]; then
        follow_flag="-f"
    fi
    
    case "$log_type" in
        "main")
            tail $follow_flag "$PROJECT_ROOT/logs/mcp_bridge.log"
            ;;
        "http")
            tail $follow_flag "$PROJECT_ROOT/logs/http_bridge.log"
            ;;
        "workflow")
            tail $follow_flag "$PROJECT_ROOT/logs/workflow.log"
            ;;
        "error")
            tail $follow_flag "$PROJECT_ROOT/logs/error.log"
            ;;
        "all"|*)
            log_info "显示所有日志文件..."
            echo ""
            echo "=== 主服务日志 ==="
            tail -n 20 "$PROJECT_ROOT/logs/mcp_bridge.log" 2>/dev/null || echo "日志文件不存在"
            echo ""
            echo "=== HTTP桥接日志 ==="
            tail -n 20 "$PROJECT_ROOT/logs/http_bridge.log" 2>/dev/null || echo "日志文件不存在"
            echo ""
            echo "=== 错误日志 ==="
            tail -n 20 "$PROJECT_ROOT/logs/error.log" 2>/dev/null || echo "日志文件不存在"
            ;;
    esac
}

# 运行测试
run_tests() {
    local test_type="${2:-all}"
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate 2>/dev/null || true
    
    case "$test_type" in
        "unit")
            log_info "运行单元测试..."
            python -m pytest tests/unit/ -v
            ;;
        "integration")
            log_info "运行集成测试..."
            python -m pytest tests/integration/ -v
            ;;
        "performance")
            log_info "运行性能测试..."
            python -m pytest tests/performance/ -v
            ;;
        "workflow")
            log_info "运行工作流测试..."
            python -m pytest tests/workflow/ -v
            ;;
        "all"|*)
            log_info "运行所有测试..."
            python -m pytest tests/ -v
            ;;
    esac
}

# 安装依赖
install_dependencies() {
    log_info "安装项目依赖..."
    
    cd "$PROJECT_ROOT"
    
    # 创建虚拟环境
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
    fi
    
    # 安装开发依赖
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    fi
    
    log_success "依赖安装完成"
}

# 备份配置和数据
backup_data() {
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    
    log_info "创建备份到: $backup_dir"
    mkdir -p "$backup_dir"
    
    # 备份配置文件
    cp -r "$PROJECT_ROOT/config" "$backup_dir/"
    
    # 备份日志文件
    if [ -d "$PROJECT_ROOT/logs" ]; then
        cp -r "$PROJECT_ROOT/logs" "$backup_dir/"
    fi
    
    # 备份数据文件
    if [ -d "$PROJECT_ROOT/data" ]; then
        cp -r "$PROJECT_ROOT/data" "$backup_dir/"
    fi
    
    # 创建备份信息文件
    cat > "$backup_dir/backup_info.txt" << EOF
备份时间: $(date)
项目版本: $(git rev-parse HEAD 2>/dev/null || echo "未知")
备份内容:
- 配置文件
- 日志文件
- 数据文件
EOF
    
    log_success "备份完成: $backup_dir"
}

# 恢复配置和数据
restore_data() {
    local backup_dir="$2"
    
    if [ -z "$backup_dir" ]; then
        log_error "请指定备份目录"
        echo "用法: $0 restore <备份目录>"
        return 1
    fi
    
    if [ ! -d "$backup_dir" ]; then
        log_error "备份目录不存在: $backup_dir"
        return 1
    fi
    
    log_warning "这将覆盖当前配置，是否继续？(y/N)"
    read -r confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        return 0
    fi
    
    log_info "从备份恢复: $backup_dir"
    
    # 恢复配置文件
    if [ -d "$backup_dir/config" ]; then
        cp -r "$backup_dir/config"/* "$PROJECT_ROOT/config/"
        log_success "配置文件已恢复"
    fi
    
    # 恢复数据文件
    if [ -d "$backup_dir/data" ]; then
        cp -r "$backup_dir/data"/* "$PROJECT_ROOT/data/"
        log_success "数据文件已恢复"
    fi
    
    log_success "恢复完成"
}

# 清理临时文件
clean_temp() {
    log_info "清理临时文件..."
    
    # 清理Python缓存
    find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # 清理临时目录
    if [ -d "$PROJECT_ROOT/temp" ]; then
        rm -rf "$PROJECT_ROOT/temp"/*
    fi
    
    # 清理日志文件（保留最近7天）
    if [ -d "$PROJECT_ROOT/logs" ]; then
        find "$PROJECT_ROOT/logs" -name "*.log.*" -mtime +7 -delete 2>/dev/null || true
    fi
    
    log_success "清理完成"
}

# 更新项目
update_project() {
    log_info "更新项目..."
    
    # 检查Git状态
    if git status &>/dev/null; then
        log_info "拉取最新代码..."
        git pull origin main
        
        # 更新依赖
        install_dependencies
        
        log_success "项目更新完成"
    else
        log_warning "不是Git仓库，跳过代码更新"
    fi
}

# 配置管理
manage_config() {
    local action="${2:-show}"
    
    case "$action" in
        "show")
            log_info "当前配置:"
            cat "$PROJECT_ROOT/config/unified_config.yaml"
            ;;
        "validate")
            log_info "验证配置文件..."
            python -c "
import yaml
try:
    with open('$PROJECT_ROOT/config/unified_config.yaml', 'r') as f:
        yaml.safe_load(f)
    print('配置文件格式正确')
except Exception as e:
    print(f'配置文件错误: {e}')
    exit(1)
"
            ;;
        "edit")
            ${EDITOR:-nano} "$PROJECT_ROOT/config/unified_config.yaml"
            ;;
        *)
            log_error "未知配置操作: $action"
            echo "可用操作: show, validate, edit"
            ;;
    esac
}

# 监控服务
monitor_services() {
    log_info "启动服务监控..."
    
    while true; do
        clear
        echo "=== MCP Bridge 服务监控 ==="
        echo "时间: $(date)"
        echo ""
        
        # 显示服务状态
        show_status
        
        echo ""
        echo "按 Ctrl+C 退出监控"
        sleep 5
    done
}

# 主函数
main() {
    local command="${1:-help}"
    
    case "$command" in
        "start")
            start_services
            ;;
        "stop")
            stop_services "$@"
            ;;
        "restart")
            restart_services "$@"
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        "logs")
            view_logs "$@"
            ;;
        "test")
            run_tests "$@"
            ;;
        "install")
            install_dependencies
            ;;
        "backup")
            backup_data
            ;;
        "restore")
            restore_data "$@"
            ;;
        "clean")
            clean_temp
            ;;
        "update")
            update_project
            ;;
        "config")
            manage_config "$@"
            ;;
        "monitor")
            monitor_services
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"