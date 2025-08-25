#!/bin/bash
# CapCutAPI 服务管理脚本
# 提供多种方式启动、停止和管理CapCutAPI服务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"
PYTHON_SCRIPT="$SCRIPT_DIR/capcut_server.py"
PID_FILE="$SCRIPT_DIR/capcut_server.pid"
LOG_FILE="$SCRIPT_DIR/logs/capcut_server.log"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查服务状态 - 改进版本
check_status() {
    # 首先检查systemd服务状态
    if systemctl is-active --quiet capcutapi.service 2>/dev/null; then
        PID=$(systemctl show -p MainPID --value capcutapi.service 2>/dev/null)
        if [ -n "$PID" ] && [ "$PID" != "0" ]; then
            print_success "CapCutAPI服务正在运行 (systemd服务, PID: $PID)"
            return 0
        fi
    fi
    
    # 检查PID文件中的进程
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_success "CapCutAPI服务正在运行 (PID文件, PID: $PID)"
            return 0
        else
            print_warning "PID文件存在但进程不存在，清理PID文件"
            rm -f "$PID_FILE"
        fi
    fi
    
    # 检查是否有相关进程在运行
    RUNNING_PID=$(pgrep -f "python.*capcut_server.py" | head -1)
    if [ -n "$RUNNING_PID" ]; then
        print_success "发现CapCutAPI进程在运行 (PID: $RUNNING_PID)"
        return 0
    fi
    
    print_error "CapCutAPI服务未运行"
    return 1
}

# 启动服务 - nohup方式（推荐）
start_nohup() {
    print_status "使用nohup方式启动CapCutAPI服务..."
    
    if check_status > /dev/null 2>&1; then
        print_warning "服务已在运行，无需重复启动"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    
    # 检查虚拟环境是否存在
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        print_error "虚拟环境不存在: $VENV_PATH"
        print_status "请先创建虚拟环境或使用 systemctl restart capcutapi.service"
        return 1
    fi
    
    source "$VENV_PATH/bin/activate"
    
    nohup python3 "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 3
    
    if check_status > /dev/null 2>&1; then
        print_success "服务启动成功！"
        print_status "日志文件: $LOG_FILE"
        print_status "PID文件: $PID_FILE"
        return 0
    else
        print_error "服务启动失败"
        return 1
    fi
}

# 启动服务 - screen方式
start_screen() {
    print_status "使用screen方式启动CapCutAPI服务..."
    
    if check_status > /dev/null 2>&1; then
        print_warning "服务已在运行，无需重复启动"
        return 1
    fi
    
    # 检查screen是否已安装
    if ! command -v screen &> /dev/null; then
        print_error "screen未安装，请先安装: yum install -y screen"
        print_status "或者使用: ./service_manager.sh start"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    
    # 检查虚拟环境是否存在
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        print_error "虚拟环境不存在: $VENV_PATH"
        return 1
    fi
    
    source "$VENV_PATH/bin/activate"
    
    screen -dmS capcut_api bash -c "python3 $PYTHON_SCRIPT; exec bash"
    
    # 获取screen会话中的python进程PID
    sleep 3
    PID=$(pgrep -f "python3.*capcut_server.py")
    if [ -n "$PID" ]; then
        echo "$PID" > "$PID_FILE"
        print_success "服务在screen会话中启动成功！"
        print_status "查看会话: screen -r capcut_api"
        print_status "分离会话: Ctrl+A, D"
        return 0
    else
        print_error "screen启动失败"
        return 1
    fi
}

# 启动服务 - systemd方式
start_systemd() {
    print_status "创建systemd服务..."
    
    SERVICE_FILE="/etc/systemd/system/capcutapi.service"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=CapCutAPI Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$VENV_PATH/bin
ExecStart=$VENV_PATH/bin/python3 $PYTHON_SCRIPT
Restart=always
RestartSec=10
StandardOutput=file:$LOG_FILE
StandardError=file:$LOG_FILE

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable capcutapi.service
    systemctl start capcutapi.service
    
    if systemctl is-active --quiet capcutapi.service; then
        print_success "systemd服务启动成功！"
        print_status "状态查看: systemctl status capcutapi.service"
        print_status "日志查看: journalctl -u capcutapi.service -f"
        return 0
    else
        print_error "systemd服务启动失败"
        return 1
    fi
}

# 停止服务 - 改进版本
stop_service() {
    print_status "停止CapCutAPI服务..."
    
    # 先尝试systemd方式停止
    if systemctl is-active --quiet capcutapi.service 2>/dev/null; then
        systemctl stop capcutapi.service
        print_success "systemd服务已停止"
    fi
    
    # 停止screen会话
    if command -v screen &> /dev/null && screen -list | grep -q "capcut_api"; then
        screen -S capcut_api -X quit
        print_success "screen会话已停止"
    fi
    
    # 停止PID文件中的进程
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            sleep 2
            if ps -p "$PID" > /dev/null 2>&1; then
                kill -9 "$PID"
            fi
            print_success "进程 $PID 已停止"
        fi
        rm -f "$PID_FILE"
    fi
    
    # 强制清理所有相关进程
    pkill -f "python.*capcut_server.py" 2>/dev/null && print_success "清理了残留进程"
    
    print_success "服务停止完成"
}

# 重启服务 - 改进版本
restart_service() {
    print_status "重启CapCutAPI服务..."
    
    # 检查当前运行方式
    if systemctl is-active --quiet capcutapi.service 2>/dev/null; then
        print_status "检测到systemd服务，使用systemd重启..."
        systemctl restart capcutapi.service
        if systemctl is-active --quiet capcutapi.service; then
            print_success "systemd服务重启成功！"
            return 0
        else
            print_error "systemd服务重启失败"
            return 1
        fi
    else
        print_status "使用脚本方式重启..."
        stop_service
        sleep 2
        start_nohup
    fi
}

# 查看日志
view_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_status "实时查看日志 (Ctrl+C退出):"
        tail -f "$LOG_FILE"
    else
        print_error "日志文件不存在: $LOG_FILE"
        print_status "尝试查看systemd日志: journalctl -u capcutapi.service -f"
    fi
}

# 显示帮助
show_help() {
    echo "CapCutAPI 服务管理脚本"
    echo ""
    echo "用法: $0 {start|start-screen|start-systemd|stop|restart|status|logs|help}"
    echo ""
    echo "命令说明:"
    echo "  start         - 使用nohup方式启动服务（推荐）"
    echo "  start-screen  - 使用screen方式启动服务"
    echo "  start-systemd - 创建并启动systemd系统服务"
    echo "  stop          - 停止所有方式启动的服务"
    echo "  restart       - 重启服务（智能检测当前运行方式）"
    echo "  status        - 查看服务状态"
    echo "  logs          - 实时查看服务日志"
    echo "  help          - 显示此帮助信息"
    echo ""
    echo "推荐使用方式:"
    echo "  开发测试: ./service_manager.sh start"
    echo "  生产环境: ./service_manager.sh start-systemd"
    echo "  调试模式: ./service_manager.sh start-screen"
    echo "  重启服务: ./service_manager.sh restart (自动检测)"
}

# 主程序
case "$1" in
    start)
        start_nohup
        ;;
    start-screen)
        start_screen
        ;;
    start-systemd)
        start_systemd
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "用法: $0 {start|start-screen|start-systemd|stop|restart|status|logs|help}"
        exit 1
        ;;
esac 