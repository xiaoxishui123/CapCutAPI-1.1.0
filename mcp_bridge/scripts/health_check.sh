#!/bin/bash

# MCP Bridge 健康检查脚本
# 功能：检查所有服务组件的健康状态

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置文件路径
CONFIG_FILE="$PROJECT_ROOT/config/unified_config.yaml"
ENV_FILE="$PROJECT_ROOT/.env"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local service_name=$2
    
    if netstat -tuln | grep -q ":$port "; then
        log_success "$service_name (端口 $port) 正在运行"
        return 0
    else
        log_error "$service_name (端口 $port) 未运行"
        return 1
    fi
}

# 检查HTTP服务响应
check_http_service() {
    local url=$1
    local service_name=$2
    local timeout=${3:-5}
    
    if curl -s --max-time $timeout "$url" > /dev/null 2>&1; then
        log_success "$service_name HTTP服务响应正常"
        return 0
    else
        log_error "$service_name HTTP服务无响应"
        return 1
    fi
}

# 检查进程是否运行
check_process() {
    local process_name=$1
    local service_name=$2
    
    if pgrep -f "$process_name" > /dev/null; then
        log_success "$service_name 进程正在运行"
        return 0
    else
        log_error "$service_name 进程未运行"
        return 1
    fi
}

# 检查文件是否存在
check_file() {
    local file_path=$1
    local file_name=$2
    
    if [ -f "$file_path" ]; then
        log_success "$file_name 存在"
        return 0
    else
        log_error "$file_name 不存在: $file_path"
        return 1
    fi
}

# 检查目录是否存在
check_directory() {
    local dir_path=$1
    local dir_name=$2
    
    if [ -d "$dir_path" ]; then
        log_success "$dir_name 目录存在"
        return 0
    else
        log_error "$dir_name 目录不存在: $dir_path"
        return 1
    fi
}

# 检查Redis连接
check_redis() {
    local redis_host=${1:-localhost}
    local redis_port=${2:-6379}
    
    if command -v redis-cli > /dev/null; then
        if redis-cli -h "$redis_host" -p "$redis_port" ping > /dev/null 2>&1; then
            log_success "Redis服务连接正常 ($redis_host:$redis_port)"
            return 0
        else
            log_error "Redis服务连接失败 ($redis_host:$redis_port)"
            return 1
        fi
    else
        log_warning "redis-cli 未安装，跳过Redis检查"
        return 0
    fi
}

# 检查Python依赖
check_python_dependencies() {
    local requirements_file="$PROJECT_ROOT/requirements.txt"
    
    if [ -f "$requirements_file" ]; then
        log_info "检查Python依赖..."
        
        # 激活虚拟环境
        if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
            source "$PROJECT_ROOT/venv/bin/activate"
        fi
        
        # 检查依赖
        if pip check > /dev/null 2>&1; then
            log_success "Python依赖检查通过"
            return 0
        else
            log_error "Python依赖存在问题"
            pip check
            return 1
        fi
    else
        log_warning "requirements.txt 文件不存在"
        return 0
    fi
}

# 检查配置文件
check_configuration() {
    log_info "检查配置文件..."
    
    local config_ok=0
    
    # 检查主配置文件
    if check_file "$CONFIG_FILE" "主配置文件"; then
        # 验证YAML格式
        if python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>/dev/null; then
            log_success "配置文件格式正确"
        else
            log_error "配置文件格式错误"
            config_ok=1
        fi
    else
        config_ok=1
    fi
    
    # 检查环境变量文件
    if [ -f "$ENV_FILE" ]; then
        log_success "环境变量文件存在"
    else
        log_warning "环境变量文件不存在，将使用默认配置"
    fi
    
    return $config_ok
}

# 检查日志文件
check_logs() {
    log_info "检查日志文件..."
    
    local logs_dir="$PROJECT_ROOT/logs"
    check_directory "$logs_dir" "日志目录"
    
    # 检查主要日志文件
    local log_files=(
        "mcp_bridge.log"
        "http_bridge.log"
        "workflow.log"
        "error.log"
    )
    
    for log_file in "${log_files[@]}"; do
        local log_path="$logs_dir/$log_file"
        if [ -f "$log_path" ]; then
            log_success "日志文件存在: $log_file"
            
            # 检查日志文件大小
            local file_size=$(stat -f%z "$log_path" 2>/dev/null || stat -c%s "$log_path" 2>/dev/null || echo 0)
            if [ "$file_size" -gt 104857600 ]; then  # 100MB
                log_warning "日志文件过大: $log_file ($(($file_size / 1024 / 1024))MB)"
            fi
        else
            log_warning "日志文件不存在: $log_file"
        fi
    done
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间..."
    
    local disk_usage=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -lt 80 ]; then
        log_success "磁盘空间充足 (已使用 ${disk_usage}%)"
    elif [ "$disk_usage" -lt 90 ]; then
        log_warning "磁盘空间不足 (已使用 ${disk_usage}%)"
    else
        log_error "磁盘空间严重不足 (已使用 ${disk_usage}%)"
    fi
}

# 检查内存使用
check_memory() {
    log_info "检查内存使用..."
    
    local mem_info=$(free | grep Mem)
    local total_mem=$(echo $mem_info | awk '{print $2}')
    local used_mem=$(echo $mem_info | awk '{print $3}')
    local mem_usage=$((used_mem * 100 / total_mem))
    
    if [ "$mem_usage" -lt 80 ]; then
        log_success "内存使用正常 (已使用 ${mem_usage}%)"
    elif [ "$mem_usage" -lt 90 ]; then
        log_warning "内存使用较高 (已使用 ${mem_usage}%)"
    else
        log_error "内存使用过高 (已使用 ${mem_usage}%)"
    fi
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    
    # 检查外网连接
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        log_success "外网连接正常"
    else
        log_error "外网连接失败"
    fi
    
    # 检查DNS解析
    if nslookup google.com > /dev/null 2>&1; then
        log_success "DNS解析正常"
    else
        log_error "DNS解析失败"
    fi
}

# 主健康检查函数
main_health_check() {
    echo "=== MCP Bridge 健康检查 ==="
    echo "检查时间: $(date)"
    echo ""
    
    local overall_status=0
    
    # 1. 检查基础环境
    echo "1. 基础环境检查"
    echo "=================="
    check_configuration || overall_status=1
    check_directory "$PROJECT_ROOT/venv" "虚拟环境" || overall_status=1
    check_python_dependencies || overall_status=1
    echo ""
    
    # 2. 检查服务进程
    echo "2. 服务进程检查"
    echo "================"
    check_process "mcp_bridge" "MCP Bridge主服务" || overall_status=1
    check_process "http_bridge" "HTTP桥接服务" || overall_status=1
    echo ""
    
    # 3. 检查端口和网络
    echo "3. 端口和网络检查"
    echo "=================="
    check_port "8000" "MCP Bridge主服务" || overall_status=1
    check_port "8001" "HTTP桥接服务" || overall_status=1
    check_redis "localhost" "6379" || overall_status=1
    echo ""
    
    # 4. 检查HTTP服务
    echo "4. HTTP服务检查"
    echo "================"
    check_http_service "http://localhost:8000/health" "MCP Bridge主服务" || overall_status=1
    check_http_service "http://localhost:8001/health" "HTTP桥接服务" || overall_status=1
    echo ""
    
    # 5. 检查系统资源
    echo "5. 系统资源检查"
    echo "================"
    check_disk_space
    check_memory
    check_network
    echo ""
    
    # 6. 检查日志文件
    echo "6. 日志文件检查"
    echo "================"
    check_logs
    echo ""
    
    # 总结
    echo "=== 健康检查总结 ==="
    if [ $overall_status -eq 0 ]; then
        log_success "所有检查项目通过，系统运行正常"
    else
        log_error "部分检查项目失败，请查看上述详细信息"
    fi
    
    return $overall_status
}

# 快速检查函数
quick_check() {
    echo "=== 快速健康检查 ==="
    
    local status=0
    
    # 检查主要服务
    check_port "8000" "MCP Bridge主服务" || status=1
    check_port "8001" "HTTP桥接服务" || status=1
    
    # 检查HTTP响应
    check_http_service "http://localhost:8000/health" "主服务" 3 || status=1
    check_http_service "http://localhost:8001/health" "HTTP桥接" 3 || status=1
    
    if [ $status -eq 0 ]; then
        log_success "快速检查通过"
    else
        log_error "快速检查失败"
    fi
    
    return $status
}

# 主函数
main() {
    local check_type="${1:-full}"
    
    case "$check_type" in
        "quick"|"q")
            quick_check
            ;;
        "full"|"f"|*)
            main_health_check
            ;;
    esac
}

# 执行主函数
main "$@"