#!/bin/bash
# CapCutAPI 服务管理脚本 v2.0
# 支持Docker容器、systemd服务、nohup多种启动方式的统一管理
# 
# 主要改进：
# 1. 增加Docker容器检测和管理
# 2. 智能识别当前服务运行方式
# 3. 避免多种启动方式冲突
# 4. 增加端口占用检测

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"
PYTHON_SCRIPT="$SCRIPT_DIR/capcut_server.py"
PID_FILE="$SCRIPT_DIR/capcut_server.pid"
LOG_FILE="$SCRIPT_DIR/logs/capcut_server.log"
SERVICE_PORT=9000

# Docker容器名称（可能的名称）
DOCKER_CONTAINER_NAMES=("capcutapi" "capcutapi-prod-compose" "capcutapi-110-capcutapi")

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

print_section() {
    echo -e "\n${CYAN}═══════════════════════════════════════════${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
}

# 检查Docker容器状态
check_docker_containers() {
    local running_containers=""
    for name in "${DOCKER_CONTAINER_NAMES[@]}"; do
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${name}$"; then
            local ports=$(docker inspect --format='{{range $p, $conf := .NetworkSettings.Ports}}{{range $conf}}{{.HostPort}} {{end}}{{end}}' "$name" 2>/dev/null)
            running_containers="$running_containers\n  - $name (端口: $ports)"
        fi
    done
    echo -e "$running_containers"
}

# 检查端口占用
check_port_usage() {
    local port=$1
    local result=""
    
    # 检查端口是否被占用
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        local pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | head -1)
        local process=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f2 | head -1)
        
        if [ -n "$pid" ] && [ "$pid" != "-" ]; then
            result="端口 $port 被占用 (PID: $pid, 进程: $process)"
        else
            result="端口 $port 被占用 (Docker容器)"
        fi
    fi
    
    echo "$result"
}

# 获取服务运行方式
get_running_mode() {
    local mode=""
    
    # 检查Docker容器
    for name in "${DOCKER_CONTAINER_NAMES[@]}"; do
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${name}$"; then
            mode="docker"
            break
        fi
    done
    
    # 如果没有Docker，检查systemd服务
    if [ -z "$mode" ] && systemctl is-active --quiet capcutapi.service 2>/dev/null; then
        mode="systemd"
    fi
    
    # 如果没有systemd，检查直接运行的进程
    if [ -z "$mode" ]; then
        if pgrep -f "python.*capcut_server.py" > /dev/null 2>&1; then
            mode="process"
        fi
    fi
    
    echo "$mode"
}

# 综合状态检查
check_status() {
    print_section "CapCutAPI 服务状态检查"
    
    local mode=$(get_running_mode)
    local docker_containers=$(check_docker_containers)
    local port_status=$(check_port_usage $SERVICE_PORT)
    local service_ok=false
    
    # 检查Docker容器
    echo -e "\n${BLUE}【Docker容器状态】${NC}"
    if [ -n "$docker_containers" ]; then
        echo -e "${GREEN}✓ 发现运行中的Docker容器:${NC}$docker_containers"
        service_ok=true
    else
        echo -e "${YELLOW}✗ 无CapCutAPI相关Docker容器运行${NC}"
    fi
    
    # 检查systemd服务
    echo -e "\n${BLUE}【Systemd服务状态】${NC}"
    if systemctl is-active --quiet capcutapi.service 2>/dev/null; then
        local pid=$(systemctl show -p MainPID --value capcutapi.service 2>/dev/null)
        echo -e "${GREEN}✓ systemd服务运行中 (PID: $pid)${NC}"
        service_ok=true
    else
        local status=$(systemctl is-active capcutapi.service 2>/dev/null || echo "未安装")
        echo -e "${YELLOW}✗ systemd服务状态: $status${NC}"
    fi
    
    # 检查直接运行的进程
    echo -e "\n${BLUE}【直接进程状态】${NC}"
    local pids=$(pgrep -f "python.*capcut_server.py" | grep -v $$ | head -5)
    if [ -n "$pids" ]; then
        echo -e "${GREEN}✓ 发现运行中的Python进程:${NC}"
        for pid in $pids; do
            local cmd=$(ps -p $pid -o cmd= 2>/dev/null | head -c 60)
            echo "    PID: $pid - $cmd"
        done
        service_ok=true
    else
        echo -e "${YELLOW}✗ 无直接运行的capcut_server进程${NC}"
    fi
    
    # 检查端口占用
    echo -e "\n${BLUE}【端口状态】${NC}"
    if [ -n "$port_status" ]; then
        echo -e "${GREEN}✓ $port_status${NC}"
    else
        echo -e "${YELLOW}✗ 端口 $SERVICE_PORT 未被使用${NC}"
    fi
    
    # 总结
    echo -e "\n${BLUE}【综合诊断】${NC}"
    case "$mode" in
        docker)
            echo -e "${GREEN}✓ 服务通过 Docker 容器运行中${NC}"
            echo -e "  推荐管理方式: docker-compose 或 docker 命令"
            return 0
            ;;
        systemd)
            echo -e "${GREEN}✓ 服务通过 systemd 运行中${NC}"
            echo -e "  推荐管理方式: systemctl 命令"
            return 0
            ;;
        process)
            echo -e "${GREEN}✓ 服务通过直接进程运行中${NC}"
            echo -e "  推荐管理方式: ./service_manager.sh 脚本"
            return 0
            ;;
        *)
            echo -e "${RED}✗ CapCutAPI服务未运行${NC}"
            return 1
            ;;
    esac
}

# 停止所有服务（包括Docker容器）
stop_all() {
    print_section "停止所有CapCutAPI服务"
    
    local stopped=false
    
    # 停止Docker容器
    echo -e "\n${BLUE}【停止Docker容器】${NC}"
    for name in "${DOCKER_CONTAINER_NAMES[@]}"; do
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${name}$"; then
            print_status "停止容器: $name"
            docker stop "$name" 2>/dev/null && print_success "容器 $name 已停止" || print_warning "容器 $name 停止失败"
            stopped=true
        fi
    done
    
    if [ "$stopped" = false ]; then
        echo "  无需停止的Docker容器"
    fi
    
    # 停止systemd服务
    echo -e "\n${BLUE}【停止Systemd服务】${NC}"
    if systemctl is-active --quiet capcutapi.service 2>/dev/null; then
        systemctl stop capcutapi.service
        print_success "systemd服务已停止"
    else
        echo "  systemd服务未运行"
    fi
    
    # 停止直接进程
    echo -e "\n${BLUE}【停止直接进程】${NC}"
    local pids=$(pgrep -f "python.*capcut_server.py")
    if [ -n "$pids" ]; then
        for pid in $pids; do
            print_status "停止进程 PID: $pid"
            kill "$pid" 2>/dev/null
        done
        sleep 2
        # 强制清理
        pkill -9 -f "python.*capcut_server.py" 2>/dev/null
        print_success "进程已清理"
    else
        echo "  无需停止的直接进程"
    fi
    
    # 清理PID文件
    rm -f "$PID_FILE"
    
    print_success "所有服务已停止"
}

# 启动服务（智能选择方式）
start_smart() {
    print_section "智能启动CapCutAPI服务"
    
    local mode=$(get_running_mode)
    
    if [ -n "$mode" ]; then
        print_warning "服务已在运行 (模式: $mode)"
        print_status "如需重启，请使用: ./service_manager.sh restart"
        return 1
    fi
    
    # 检查端口是否可用
    local port_status=$(check_port_usage $SERVICE_PORT)
    if [ -n "$port_status" ]; then
        print_error "$port_status"
        print_status "请先停止占用端口的服务: ./service_manager.sh stop-all"
        return 1
    fi
    
    # 优先使用Docker（如果存在docker-compose.yml）
    if [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
        print_status "检测到docker-compose.yml，推荐使用Docker启动"
        echo -e "  使用: ${CYAN}docker-compose up -d${NC}"
        echo ""
        read -p "是否使用Docker启动? [y/N]: " choice
        if [[ "$choice" =~ ^[Yy]$ ]]; then
            start_docker
            return $?
        fi
    fi
    
    # 使用nohup方式启动
    start_nohup
}

# 启动Docker容器
start_docker() {
    print_status "使用Docker启动CapCutAPI服务..."
    
    cd "$SCRIPT_DIR"
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d
        if [ $? -eq 0 ]; then
            print_success "Docker容器启动成功！"
            sleep 3
            docker-compose ps
            return 0
        else
            print_error "Docker容器启动失败"
            return 1
        fi
    else
        print_error "docker-compose.yml 文件不存在"
        return 1
    fi
}

# 启动服务 - nohup方式
start_nohup() {
    print_status "使用nohup方式启动CapCutAPI服务..."
    
    # 检查端口是否可用
    local port_status=$(check_port_usage $SERVICE_PORT)
    if [ -n "$port_status" ]; then
        print_error "$port_status"
        print_error "端口被占用，无法启动"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    
    # 优先使用虚拟环境
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        PYTHON_CMD="python3"
        print_status "使用虚拟环境: $VENV_PATH"
    elif command -v /usr/local/bin/python3.9 &> /dev/null; then
        PYTHON_CMD="/usr/local/bin/python3.9"
        print_status "使用Python: $PYTHON_CMD"
    else
        PYTHON_CMD="python3"
        print_status "使用系统Python: $PYTHON_CMD"
    fi
    
    nohup $PYTHON_CMD "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1 &
    local new_pid=$!
    echo $new_pid > "$PID_FILE"
    
    print_status "等待服务启动..."
    sleep 5
    
    # 验证服务是否成功启动
    if ps -p $new_pid > /dev/null 2>&1; then
        # 检查端口是否监听
        if netstat -tlnp 2>/dev/null | grep -q ":$SERVICE_PORT "; then
            print_success "服务启动成功！"
            print_status "PID: $new_pid"
            print_status "日志: $LOG_FILE"
            print_status "访问地址: http://localhost:$SERVICE_PORT"
            return 0
        else
            print_warning "进程已启动但端口未监听，请检查日志"
            tail -20 "$LOG_FILE"
            return 1
        fi
    else
        print_error "服务启动失败，请检查日志"
        tail -20 "$LOG_FILE"
        return 1
    fi
}

# 启动服务 - systemd方式
start_systemd() {
    print_status "启动systemd服务..."
    
    # 检查是否有Docker容器在运行
    local docker_containers=$(check_docker_containers)
    if [ -n "$docker_containers" ]; then
        print_error "检测到Docker容器正在运行，端口可能被占用"
        print_status "请先停止Docker容器: ./service_manager.sh stop-all"
        return 1
    fi
    
    # 创建或更新systemd服务文件
    SERVICE_FILE="/etc/systemd/system/capcutapi.service"
    
    # 选择Python路径
    if [ -f "$VENV_PATH/bin/python3" ]; then
        PYTHON_PATH="$VENV_PATH/bin/python3"
    elif command -v /usr/local/bin/python3.9 &> /dev/null; then
        PYTHON_PATH="/usr/local/bin/python3.9"
    else
        PYTHON_PATH="/usr/bin/python3"
    fi
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=CapCutAPI Service
After=network.target
Conflicts=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin
ExecStartPre=/bin/bash -c 'if docker ps --format "{{.Names}}" 2>/dev/null | grep -qE "capcutapi"; then echo "Docker容器正在运行" && exit 1; fi'
ExecStart=$PYTHON_PATH $PYTHON_SCRIPT
Restart=on-failure
RestartSec=10
StandardOutput=append:$SCRIPT_DIR/logs/capcutapi.log
StandardError=append:$SCRIPT_DIR/logs/capcutapi.error.log

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable capcutapi.service
    systemctl start capcutapi.service
    
    sleep 3
    
    if systemctl is-active --quiet capcutapi.service; then
        print_success "systemd服务启动成功！"
        systemctl status capcutapi.service --no-pager
        return 0
    else
        print_error "systemd服务启动失败"
        journalctl -u capcutapi.service -n 20 --no-pager
        return 1
    fi
}

# 重启服务（智能检测当前运行方式）
restart_smart() {
    print_section "智能重启CapCutAPI服务"
    
    local mode=$(get_running_mode)
    
    case "$mode" in
        docker)
            print_status "检测到Docker容器运行，使用docker-compose重启..."
            cd "$SCRIPT_DIR"
            docker-compose restart
            if [ $? -eq 0 ]; then
                print_success "Docker容器重启成功！"
                docker-compose ps
            else
                print_error "重启失败"
                return 1
            fi
            ;;
        systemd)
            print_status "检测到systemd服务，使用systemctl重启..."
            systemctl restart capcutapi.service
            sleep 3
            if systemctl is-active --quiet capcutapi.service; then
                print_success "systemd服务重启成功！"
            else
                print_error "重启失败，尝试查看日志"
                journalctl -u capcutapi.service -n 20 --no-pager
                return 1
            fi
            ;;
        process)
            print_status "检测到直接进程运行，使用脚本重启..."
            stop_all
            sleep 2
            start_nohup
            ;;
        *)
            print_warning "服务未运行，直接启动..."
            start_smart
            ;;
    esac
}

# 查看日志
view_logs() {
    local mode=$(get_running_mode)
    
    print_section "查看CapCutAPI日志"
    
    case "$mode" in
        docker)
            print_status "查看Docker容器日志..."
            for name in "${DOCKER_CONTAINER_NAMES[@]}"; do
                if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${name}$"; then
                    print_status "容器: $name"
                    docker logs --tail 100 -f "$name"
                    return 0
                fi
            done
            ;;
        systemd)
            print_status "查看systemd服务日志..."
            journalctl -u capcutapi.service -f
            ;;
        *)
            if [ -f "$LOG_FILE" ]; then
                print_status "查看日志文件: $LOG_FILE"
                tail -f "$LOG_FILE"
            else
                print_error "日志文件不存在"
            fi
            ;;
    esac
}

# 测试服务
test_service() {
    print_section "测试CapCutAPI服务"
    
    print_status "测试服务连接..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$SERVICE_PORT/" --connect-timeout 5)
    
    if [ "$response" = "200" ]; then
        print_success "服务正常响应！HTTP状态码: $response"
        
        print_status "获取API信息..."
        curl -s "http://localhost:$SERVICE_PORT/" -H "Accept: application/json" | python3 -m json.tool 2>/dev/null || curl -s "http://localhost:$SERVICE_PORT/"
        return 0
    else
        print_error "服务无响应或返回错误 (HTTP: $response)"
        return 1
    fi
}

# 显示帮助
show_help() {
    cat << EOF
${CYAN}╔═══════════════════════════════════════════════════════════════════╗
║          CapCutAPI 服务管理脚本 v2.0                              ║
║          支持Docker、Systemd、Nohup多种启动方式                    ║
╚═══════════════════════════════════════════════════════════════════╝${NC}

${BLUE}用法:${NC} $0 {命令}

${BLUE}常用命令:${NC}
  ${GREEN}status${NC}          - 查看服务综合状态（推荐首先使用）
  ${GREEN}start${NC}           - 智能启动服务（自动选择最佳方式）
  ${GREEN}stop${NC}            - 停止所有运行方式的服务
  ${GREEN}restart${NC}         - 智能重启服务
  ${GREEN}logs${NC}            - 查看服务日志
  ${GREEN}test${NC}            - 测试服务是否正常

${BLUE}特定启动方式:${NC}
  ${YELLOW}start-docker${NC}    - 使用Docker容器启动
  ${YELLOW}start-nohup${NC}     - 使用nohup方式启动
  ${YELLOW}start-systemd${NC}   - 使用systemd服务启动
  ${YELLOW}stop-all${NC}        - 停止所有服务（包括Docker）

${BLUE}使用建议:${NC}
  ${CYAN}生产环境${NC}: 推荐使用 Docker 部署
    docker-compose up -d
    
  ${CYAN}开发测试${NC}: 推荐使用 nohup 方式
    ./service_manager.sh start-nohup
    
  ${CYAN}系统服务${NC}: 使用 systemd（不能与Docker同时运行）
    ./service_manager.sh start-systemd

${BLUE}故障排除:${NC}
  1. 先查看状态: ${GREEN}./service_manager.sh status${NC}
  2. 停止所有服务: ${GREEN}./service_manager.sh stop${NC}
  3. 重新启动: ${GREEN}./service_manager.sh start${NC}
  4. 查看日志: ${GREEN}./service_manager.sh logs${NC}

EOF
}

# 主程序
case "$1" in
    status)
        check_status
        ;;
    start)
        start_smart
        ;;
    start-docker)
        start_docker
        ;;
    start-nohup)
        start_nohup
        ;;
    start-systemd)
        start_systemd
        ;;
    stop|stop-all)
        stop_all
        ;;
    restart)
        restart_smart
        ;;
    logs)
        view_logs
        ;;
    test)
        test_service
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${YELLOW}用法:${NC} $0 {status|start|stop|restart|logs|test|help}"
        echo -e "使用 ${GREEN}$0 help${NC} 查看详细帮助"
        exit 1
        ;;
esac
