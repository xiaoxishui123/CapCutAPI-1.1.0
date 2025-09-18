#!/bin/bash

# MCP Bridge 自动化部署脚本
# 支持开发环境、测试环境和生产环境部署

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

# 显示帮助信息
show_help() {
    cat << EOF
MCP Bridge 部署脚本

用法: $0 [选项] <环境>

环境:
    dev         开发环境部署
    test        测试环境部署
    prod        生产环境部署

选项:
    -h, --help              显示此帮助信息
    -v, --verbose           详细输出
    -f, --force             强制重新部署
    --skip-tests            跳过测试
    --skip-build            跳过构建
    --backup                部署前备份
    --rollback <version>    回滚到指定版本

示例:
    $0 dev                  部署到开发环境
    $0 prod --backup        部署到生产环境并备份
    $0 --rollback v1.0.0    回滚到v1.0.0版本

EOF
}

# 默认参数
ENVIRONMENT=""
VERBOSE=false
FORCE=false
SKIP_TESTS=false
SKIP_BUILD=false
BACKUP=false
ROLLBACK_VERSION=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --backup)
            BACKUP=true
            shift
            ;;
        --rollback)
            ROLLBACK_VERSION="$2"
            shift 2
            ;;
        dev|test|prod)
            ENVIRONMENT="$1"
            shift
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 验证环境参数
if [[ -z "$ENVIRONMENT" && -z "$ROLLBACK_VERSION" ]]; then
    log_error "必须指定部署环境或回滚版本"
    show_help
    exit 1
fi

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 环境配置
case $ENVIRONMENT in
    dev)
        COMPOSE_FILE="docker-compose.yml"
        ENV_FILE=".env.dev"
        SERVICE_NAME="mcp-bridge-dev"
        ;;
    test)
        COMPOSE_FILE="docker-compose.test.yml"
        ENV_FILE=".env.test"
        SERVICE_NAME="mcp-bridge-test"
        ;;
    prod)
        COMPOSE_FILE="docker-compose.prod.yml"
        ENV_FILE=".env.prod"
        SERVICE_NAME="mcp-bridge-prod"
        ;;
esac

# 检查必要文件
check_prerequisites() {
    log_info "检查部署前置条件..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
    
    # 检查配置文件
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "环境配置文件 $ENV_FILE 不存在，使用默认配置"
        cp ".env.example" "$ENV_FILE"
    fi
    
    log_success "前置条件检查完成"
}

# 运行测试
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "跳过测试"
        return
    fi
    
    log_info "运行测试套件..."
    
    # 单元测试
    log_info "运行单元测试..."
    python -m pytest tests/test_units.py -v
    
    # 集成测试
    log_info "运行集成测试..."
    python -m pytest tests/test_integration.py -v
    
    # 性能测试（仅在生产环境）
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        log_info "运行性能测试..."
        python -m pytest tests/test_performance.py -v
    fi
    
    log_success "所有测试通过"
}

# 构建镜像
build_image() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log_warning "跳过构建"
        return
    fi
    
    log_info "构建Docker镜像..."
    
    # 获取版本信息
    VERSION=$(git describe --tags --always --dirty)
    BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    GIT_COMMIT=$(git rev-parse HEAD)
    
    # 构建镜像
    docker build \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_TIME="$BUILD_TIME" \
        --build-arg GIT_COMMIT="$GIT_COMMIT" \
        -t "mcp-bridge:$VERSION" \
        -t "mcp-bridge:latest" \
        .
    
    log_success "镜像构建完成: mcp-bridge:$VERSION"
}

# 备份当前部署
backup_deployment() {
    if [[ "$BACKUP" != "true" ]]; then
        return
    fi
    
    log_info "备份当前部署..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份配置文件
    cp "$ENV_FILE" "$BACKUP_DIR/"
    cp "$COMPOSE_FILE" "$BACKUP_DIR/"
    
    # 备份数据库（如果存在）
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q redis; then
        log_info "备份Redis数据..."
        docker-compose -f "$COMPOSE_FILE" exec redis redis-cli BGSAVE
        docker cp "$(docker-compose -f "$COMPOSE_FILE" ps -q redis):/data/dump.rdb" "$BACKUP_DIR/"
    fi
    
    # 记录当前版本
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | grep mcp-bridge > "$BACKUP_DIR/images.txt"
    
    log_success "备份完成: $BACKUP_DIR"
}

# 部署服务
deploy_service() {
    log_info "部署MCP Bridge服务到 $ENVIRONMENT 环境..."
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down || true
    
    # 清理旧容器（如果强制部署）
    if [[ "$FORCE" == "true" ]]; then
        log_info "清理旧容器和镜像..."
        docker system prune -f
    fi
    
    # 启动服务
    log_info "启动新服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 健康检查
    log_info "执行健康检查..."
    for i in {1..30}; do
        if curl -f http://localhost:8080/health > /dev/null 2>&1; then
            log_success "服务启动成功"
            break
        fi
        
        if [[ $i -eq 30 ]]; then
            log_error "服务启动失败"
            docker-compose -f "$COMPOSE_FILE" logs
            exit 1
        fi
        
        sleep 2
    done
    
    # 显示服务状态
    docker-compose -f "$COMPOSE_FILE" ps
    
    log_success "部署完成"
}

# 回滚部署
rollback_deployment() {
    if [[ -z "$ROLLBACK_VERSION" ]]; then
        return
    fi
    
    log_info "回滚到版本: $ROLLBACK_VERSION"
    
    # 检查版本是否存在
    if ! docker images | grep -q "mcp-bridge:$ROLLBACK_VERSION"; then
        log_error "版本 $ROLLBACK_VERSION 不存在"
        exit 1
    fi
    
    # 停止当前服务
    docker-compose -f "$COMPOSE_FILE" down
    
    # 更新镜像标签
    docker tag "mcp-bridge:$ROLLBACK_VERSION" "mcp-bridge:latest"
    
    # 重新启动服务
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "回滚完成"
}

# 部署后验证
post_deploy_verification() {
    log_info "执行部署后验证..."
    
    # API健康检查
    log_info "检查API健康状态..."
    HEALTH_RESPONSE=$(curl -s http://localhost:8080/health)
    if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
        log_success "API健康检查通过"
    else
        log_error "API健康检查失败"
        echo "$HEALTH_RESPONSE"
        exit 1
    fi
    
    # 指标端点检查
    log_info "检查指标端点..."
    if curl -f http://localhost:8080/metrics > /dev/null 2>&1; then
        log_success "指标端点正常"
    else
        log_warning "指标端点异常"
    fi
    
    # 服务发现检查
    log_info "检查服务发现..."
    SERVICES_RESPONSE=$(curl -s http://localhost:8080/api/services)
    if echo "$SERVICES_RESPONSE" | grep -q "services"; then
        log_success "服务发现正常"
    else
        log_warning "服务发现异常"
    fi
    
    log_success "部署后验证完成"
}

# 显示部署信息
show_deployment_info() {
    log_info "部署信息:"
    echo "环境: $ENVIRONMENT"
    echo "版本: $(docker images --format "{{.Tag}}" mcp-bridge:latest | head -1)"
    echo "服务状态:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "访问地址:"
    echo "  API: http://localhost:8080"
    echo "  健康检查: http://localhost:8080/health"
    echo "  指标: http://localhost:8080/metrics"
    echo "  Grafana: http://localhost:3000 (admin/admin)"
    echo ""
    echo "日志查看:"
    echo "  docker-compose -f $COMPOSE_FILE logs -f"
}

# 主函数
main() {
    log_info "开始MCP Bridge部署流程..."
    
    # 回滚模式
    if [[ -n "$ROLLBACK_VERSION" ]]; then
        rollback_deployment
        post_deploy_verification
        show_deployment_info
        return
    fi
    
    # 正常部署流程
    check_prerequisites
    run_tests
    build_image
    backup_deployment
    deploy_service
    post_deploy_verification
    show_deployment_info
    
    log_success "MCP Bridge部署完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"