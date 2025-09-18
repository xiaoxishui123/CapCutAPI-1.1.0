#!/bin/bash

# MCP Bridge 服务监控脚本
# 监控服务健康状态、性能指标和资源使用情况

set -e

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
PID_FILE="$PROJECT_DIR/bridge_server.pid"
LOG_DIR="$PROJECT_DIR/logs"
MONITOR_LOG="$LOG_DIR/monitor.log"

# 监控配置
CHECK_INTERVAL=30  # 检查间隔(秒)
ALERT_THRESHOLD_CPU=80  # CPU使用率告警阈值(%)
ALERT_THRESHOLD_MEM=80  # 内存使用率告警阈值(%)
ALERT_THRESHOLD_RESPONSE=5000  # 响应时间告警阈值(毫秒)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[INFO]${NC} [$timestamp] $1"
    echo "[$timestamp] [INFO] $1" >> "$MONITOR_LOG"
}

log_warn() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[WARN]${NC} [$timestamp] $1"
    echo "[$timestamp] [WARN] $1" >> "$MONITOR_LOG"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[ERROR]${NC} [$timestamp] $1"
    echo "[$timestamp] [ERROR] $1" >> "$MONITOR_LOG"
}

log_debug() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[DEBUG]${NC} [$timestamp] $1"
    echo "[$timestamp] [DEBUG] $1" >> "$MONITOR_LOG"
}

# 初始化监控日志
init_monitor() {
    mkdir -p "$LOG_DIR"
    if [ ! -f "$MONITOR_LOG" ]; then
        touch "$MONITOR_LOG"
    fi
    log_info "监控系统启动"
}

# 检查服务是否运行
is_service_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# 获取服务PID
get_service_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# 检查服务健康状态
check_health() {
    if ! command -v curl > /dev/null; then
        log_error "curl未安装，无法进行健康检查"
        return 1
    fi
    
    local start_time=$(date +%s%3N)
    local response=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8080/health 2>/dev/null)
    local end_time=$(date +%s%3N)
    local response_time=$((end_time - start_time))
    
    if [ "$response" = "200" ]; then
        log_debug "健康检查通过 (响应时间: ${response_time}ms)"
        
        # 检查响应时间告警
        if [ "$response_time" -gt "$ALERT_THRESHOLD_RESPONSE" ]; then
            log_warn "响应时间过长: ${response_time}ms (阈值: ${ALERT_THRESHOLD_RESPONSE}ms)"
        fi
        
        return 0
    else
        log_error "健康检查失败 (HTTP状态码: $response)"
        return 1
    fi
}

# 获取系统资源使用情况
get_system_stats() {
    local pid=$(get_service_pid)
    
    if [ -z "$pid" ]; then
        echo "0,0,0,0"  # cpu%, mem%, rss_mb, vms_mb
        return
    fi
    
    # 获取进程资源使用情况
    if command -v ps > /dev/null; then
        local stats=$(ps -p "$pid" -o pcpu,pmem,rss,vsz --no-headers 2>/dev/null | tr -s ' ')
        if [ -n "$stats" ]; then
            local cpu=$(echo "$stats" | awk '{print $1}')
            local mem=$(echo "$stats" | awk '{print $2}')
            local rss=$(echo "$stats" | awk '{print int($3/1024)}')  # KB to MB
            local vms=$(echo "$stats" | awk '{print int($4/1024)}')  # KB to MB
            echo "$cpu,$mem,$rss,$vms"
        else
            echo "0,0,0,0"
        fi
    else
        echo "0,0,0,0"
    fi
}

# 获取服务指标
get_service_metrics() {
    if ! command -v curl > /dev/null; then
        return 1
    fi
    
    local metrics=$(curl -s http://localhost:8080/metrics 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "$metrics"
        return 0
    else
        return 1
    fi
}

# 检查资源使用告警
check_resource_alerts() {
    local stats=$(get_system_stats)
    local cpu=$(echo "$stats" | cut -d',' -f1)
    local mem=$(echo "$stats" | cut -d',' -f2)
    local rss=$(echo "$stats" | cut -d',' -f3)
    local vms=$(echo "$stats" | cut -d',' -f4)
    
    # CPU使用率告警
    if [ "$(echo "$cpu > $ALERT_THRESHOLD_CPU" | bc 2>/dev/null || echo 0)" = "1" ]; then
        log_warn "CPU使用率过高: ${cpu}% (阈值: ${ALERT_THRESHOLD_CPU}%)"
    fi
    
    # 内存使用率告警
    if [ "$(echo "$mem > $ALERT_THRESHOLD_MEM" | bc 2>/dev/null || echo 0)" = "1" ]; then
        log_warn "内存使用率过高: ${mem}% (阈值: ${ALERT_THRESHOLD_MEM}%)"
    fi
    
    log_debug "资源使用: CPU=${cpu}%, MEM=${mem}%, RSS=${rss}MB, VMS=${vms}MB"
}

# 单次监控检查
single_check() {
    echo "=== MCP Bridge 服务监控报告 ==="
    echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 检查服务状态
    if is_service_running; then
        local pid=$(get_service_pid)
        echo "✓ 服务状态: 运行中 (PID: $pid)"
        
        # 检查健康状态
        if check_health; then
            echo "✓ 健康检查: 通过"
        else
            echo "✗ 健康检查: 失败"
        fi
        
        # 显示资源使用情况
        local stats=$(get_system_stats)
        local cpu=$(echo "$stats" | cut -d',' -f1)
        local mem=$(echo "$stats" | cut -d',' -f2)
        local rss=$(echo "$stats" | cut -d',' -f3)
        local vms=$(echo "$stats" | cut -d',' -f4)
        
        echo "📊 资源使用:"
        echo "   CPU: ${cpu}%"
        echo "   内存: ${mem}%"
        echo "   RSS: ${rss}MB"
        echo "   VMS: ${vms}MB"
        
        # 显示服务指标
        echo "📈 服务指标:"
        local metrics=$(get_service_metrics)
        if [ $? -eq 0 ]; then
            echo "$metrics" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"   总请求数: {data.get('total_requests', 0)}\")
    print(f\"   成功率: {data.get('success_rate', 0):.2f}\")
    print(f\"   错误率: {data.get('error_rate', 0):.2f}\")
    print(f\"   平均响应时间: {data.get('avg_response_time', 0):.2f}ms\")
except:
    print('   指标获取失败')
" 2>/dev/null || echo "   指标获取失败"
        else
            echo "   指标获取失败"
        fi
        
        # 检查端口监听
        if command -v netstat > /dev/null; then
            local port_status=$(netstat -tlnp 2>/dev/null | grep ":8080" | wc -l)
            if [ "$port_status" -gt 0 ]; then
                echo "✓ 端口监听: 8080端口正常"
            else
                echo "✗ 端口监听: 8080端口未监听"
            fi
        fi
        
    else
        echo "✗ 服务状态: 未运行"
    fi
    
    echo ""
}

# 持续监控
continuous_monitor() {
    log_info "开始持续监控 (检查间隔: ${CHECK_INTERVAL}秒)"
    log_info "按 Ctrl+C 停止监控"
    
    # 设置信号处理
    trap 'log_info "监控停止"; exit 0' INT TERM
    
    while true; do
        # 检查服务状态
        if is_service_running; then
            # 健康检查
            if ! check_health; then
                log_error "服务健康检查失败，可能需要重启"
            fi
            
            # 资源使用检查
            check_resource_alerts
            
        else
            log_error "服务未运行，尝试自动重启..."
            
            # 尝试自动重启服务
            if [ -f "$PROJECT_DIR/manage.sh" ]; then
                "$PROJECT_DIR/manage.sh" start
                if [ $? -eq 0 ]; then
                    log_info "服务自动重启成功"
                else
                    log_error "服务自动重启失败"
                fi
            else
                log_error "管理脚本不存在，无法自动重启"
            fi
        fi
        
        sleep "$CHECK_INTERVAL"
    done
}

# 生成监控报告
generate_report() {
    local days=${1:-7}
    local report_file="$LOG_DIR/monitor_report_$(date +%Y%m%d).txt"
    
    echo "=== MCP Bridge 监控报告 ===" > "$report_file"
    echo "报告生成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$report_file"
    echo "统计周期: 最近 $days 天" >> "$report_file"
    echo "" >> "$report_file"
    
    if [ -f "$MONITOR_LOG" ]; then
        # 统计错误和警告
        local error_count=$(grep -c "\[ERROR\]" "$MONITOR_LOG" | tail -n 1000 || echo 0)
        local warn_count=$(grep -c "\[WARN\]" "$MONITOR_LOG" | tail -n 1000 || echo 0)
        
        echo "📊 统计信息:" >> "$report_file"
        echo "   错误数量: $error_count" >> "$report_file"
        echo "   警告数量: $warn_count" >> "$report_file"
        echo "" >> "$report_file"
        
        # 最近的错误和警告
        echo "🚨 最近的错误:" >> "$report_file"
        grep "\[ERROR\]" "$MONITOR_LOG" | tail -10 >> "$report_file" || echo "   无错误记录" >> "$report_file"
        echo "" >> "$report_file"
        
        echo "⚠️  最近的警告:" >> "$report_file"
        grep "\[WARN\]" "$MONITOR_LOG" | tail -10 >> "$report_file" || echo "   无警告记录" >> "$report_file"
        echo "" >> "$report_file"
    fi
    
    # 当前状态
    echo "📋 当前状态:" >> "$report_file"
    if is_service_running; then
        echo "   服务状态: 运行中" >> "$report_file"
        local stats=$(get_system_stats)
        local cpu=$(echo "$stats" | cut -d',' -f1)
        local mem=$(echo "$stats" | cut -d',' -f2)
        echo "   CPU使用率: ${cpu}%" >> "$report_file"
        echo "   内存使用率: ${mem}%" >> "$report_file"
    else
        echo "   服务状态: 未运行" >> "$report_file"
    fi
    
    log_info "监控报告已生成: $report_file"
    echo "报告路径: $report_file"
}

# 清理监控日志
clean_monitor_logs() {
    log_info "清理监控日志..."
    
    if [ -f "$MONITOR_LOG" ]; then
        # 保留最近1000行日志
        tail -1000 "$MONITOR_LOG" > "${MONITOR_LOG}.tmp"
        mv "${MONITOR_LOG}.tmp" "$MONITOR_LOG"
        log_info "监控日志已清理，保留最近1000行"
    fi
    
    # 清理旧的报告文件
    find "$LOG_DIR" -name "monitor_report_*.txt" -type f -mtime +30 -delete 2>/dev/null || true
    log_info "已清理30天前的监控报告"
}

# 显示帮助信息
show_help() {
    echo "MCP Bridge 服务监控脚本"
    echo ""
    echo "用法: $0 <命令> [选项]"
    echo ""
    echo "命令:"
    echo "  check          执行单次监控检查"
    echo "  monitor        开始持续监控"
    echo "  report [天数]  生成监控报告 (默认7天)"
    echo "  clean          清理监控日志"
    echo "  help           显示帮助信息"
    echo ""
    echo "配置:"
    echo "  检查间隔: ${CHECK_INTERVAL}秒"
    echo "  CPU告警阈值: ${ALERT_THRESHOLD_CPU}%"
    echo "  内存告警阈值: ${ALERT_THRESHOLD_MEM}%"
    echo "  响应时间告警阈值: ${ALERT_THRESHOLD_RESPONSE}ms"
    echo ""
    echo "示例:"
    echo "  $0 check               # 执行单次检查"
    echo "  $0 monitor             # 开始持续监控"
    echo "  $0 report 30           # 生成30天监控报告"
    echo "  $0 clean               # 清理监控日志"
    echo ""
}

# 主函数
main() {
    init_monitor
    
    case "${1:-}" in
        check)
            single_check
            ;;
        monitor)
            continuous_monitor
            ;;
        report)
            generate_report "${2:-7}"
            ;;
        clean)
            clean_monitor_logs
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