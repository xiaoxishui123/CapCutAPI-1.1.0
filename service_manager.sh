#!/bin/bash

# CapCutAPI 服务管理脚本
# 作者：AI助手
# 用途：管理CapCutAPI服务的启动、停止、重启等操作

SERVICE_NAME="capcutapi.service"
PROJECT_DIR="/home/CapCutAPI-1.1.0"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查服务状态
check_status() {
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        print_message $GREEN "✓ 服务正在运行"
        return 0
    else
        print_message $RED "✗ 服务未运行"
        return 1
    fi
}

# 显示服务状态
show_status() {
    print_message $BLUE "=== CapCutAPI 服务状态 ==="
    sudo systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    
    # 检查端口
    if netstat -tlnp | grep -q ":9000 "; then
        print_message $GREEN "✓ 端口9000正在监听"
    else
        print_message $RED "✗ 端口9000未监听"
    fi
    
    # 检查API响应
    if curl -s http://localhost:9000/get_intro_animation_types > /dev/null 2>&1; then
        print_message $GREEN "✓ API服务响应正常"
    else
        print_message $RED "✗ API服务无响应"
    fi
}

# 启动服务
start_service() {
    print_message $BLUE "启动CapCutAPI服务..."
    sudo systemctl start $SERVICE_NAME
    
    sleep 2
    
    if check_status; then
        print_message $GREEN "✓ 服务启动成功"
        print_message $GREEN "✓ 访问地址: http://8.148.70.18:9000"
    else
        print_message $RED "✗ 服务启动失败"
        print_message $YELLOW "查看错误日志: sudo journalctl -u $SERVICE_NAME -n 20"
    fi
}

# 停止服务
stop_service() {
    print_message $BLUE "停止CapCutAPI服务..."
    sudo systemctl stop $SERVICE_NAME
    
    sleep 2
    
    if ! check_status; then
        print_message $GREEN "✓ 服务已停止"
    else
        print_message $RED "✗ 服务停止失败"
    fi
}

# 重启服务
restart_service() {
    print_message $BLUE "重启CapCutAPI服务..."
    sudo systemctl restart $SERVICE_NAME
    
    sleep 3
    
    if check_status; then
        print_message $GREEN "✓ 服务重启成功"
        print_message $GREEN "✓ 访问地址: http://8.148.70.18:9000"
    else
        print_message $RED "✗ 服务重启失败"
        print_message $YELLOW "查看错误日志: sudo journalctl -u $SERVICE_NAME -n 20"
    fi
}

# 查看日志
show_logs() {
    print_message $BLUE "=== 服务日志 ==="
    echo "选择日志类型:"
    echo "1) 实时日志 (实时查看)"
    echo "2) 最近日志 (最近50行)"
    echo "3) 错误日志 (最近50行)"
    echo "4) 系统日志 (最近50行)"
    read -p "请选择 (1-4): " choice
    
    case $choice in
        1)
            print_message $YELLOW "按 Ctrl+C 退出实时日志"
            sudo journalctl -u $SERVICE_NAME -f
            ;;
        2)
            sudo journalctl -u $SERVICE_NAME -n 50 --no-pager
            ;;
        3)
            sudo journalctl -u $SERVICE_NAME -n 50 --no-pager | grep -i error
            ;;
        4)
            sudo journalctl -u $SERVICE_NAME -n 50 --no-pager
            ;;
        *)
            print_message $RED "无效选择"
            ;;
    esac
}

# 测试API
test_api() {
    print_message $BLUE "=== API测试 ==="
    cd $PROJECT_DIR
    if [ -f "test_api.py" ]; then
        python3 test_api.py
    else
        print_message $YELLOW "测试脚本不存在，进行简单测试..."
        curl -s http://localhost:9000/get_intro_animation_types | head -c 100
        echo "..."
    fi
}

# 显示帮助信息
show_help() {
    print_message $BLUE "=== CapCutAPI 服务管理脚本 ==="
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  start    启动服务"
    echo "  stop     停止服务"
    echo "  restart  重启服务"
    echo "  status   查看服务状态"
    echo "  logs     查看服务日志"
    echo "  test     测试API功能"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动服务"
    echo "  $0 status   # 查看状态"
    echo "  $0 logs     # 查看日志"
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
            show_status
            ;;
        logs)
            show_logs
            ;;
        test)
            test_api
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            print_message $RED "错误: 未知命令 '$1'"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    print_message $YELLOW "注意: 某些操作可能需要sudo权限"
fi

# 执行主函数
main "$@" 