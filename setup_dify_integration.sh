#!/bin/bash

# CapCut API MCP 服务与 Dify 工作流集成部署脚本
# 
# 功能：
# 1. 部署 MCP Bridge 服务
# 2. 配置 Dify 集成
# 3. 创建工作流模板
# 4. 验证集成功能
#
# 作者：AI Assistant
# 版本：v1.0.0
# 更新时间：2025年1月14日

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

# 配置变量
PROJECT_ROOT="/home/CapCutAPI-1.1.0"
MCP_BRIDGE_DIR="$PROJECT_ROOT/mcp_bridge"
DIFY_PROJECT_DIR="/home/dify"
VENV_DIR="$PROJECT_ROOT/venv"

# 默认配置
MCP_SERVER_PORT=8080
BRIDGE_SERVER_PORT=8081
DIFY_API_URL="http://localhost:5001"
DIFY_API_KEY=""

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查 Python 版本
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
        log_error "需要 Python 3.8 或更高版本，当前版本: $python_version"
        exit 1
    fi
    
    # 检查必要的命令
    for cmd in pip3 curl jq; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd 未安装"
            exit 1
        fi
    done
    
    # 检查 Docker（可选）
    if command -v docker &> /dev/null; then
        log_info "检测到 Docker，将支持容器化部署"
    else
        log_warning "Docker 未安装，将使用本地部署模式"
    fi
    
    log_success "系统要求检查通过"
}

# 创建虚拟环境
setup_virtual_environment() {
    log_info "设置 Python 虚拟环境..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        log_success "虚拟环境创建成功"
    else
        log_info "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 升级 pip
    pip install --upgrade pip
    
    log_success "虚拟环境设置完成"
}

# 安装依赖
install_dependencies() {
    log_info "安装项目依赖..."
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 安装 MCP Bridge 依赖
    if [ -f "$MCP_BRIDGE_DIR/requirements.txt" ]; then
        pip install -r "$MCP_BRIDGE_DIR/requirements.txt"
    else
        # 安装基础依赖
        pip install \
            fastapi \
            uvicorn \
            websockets \
            aiohttp \
            pydantic \
            redis \
            prometheus-client \
            pyyaml \
            requests \
            asyncio-mqtt \
            python-multipart
    fi
    
    # 安装 CapCut API 依赖
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements.txt"
    fi
    
    log_success "依赖安装完成"
}

# 配置 MCP Bridge
configure_mcp_bridge() {
    log_info "配置 MCP Bridge..."
    
    # 创建配置目录
    mkdir -p "$MCP_BRIDGE_DIR/config"
    mkdir -p "$MCP_BRIDGE_DIR/logs"
    mkdir -p "$MCP_BRIDGE_DIR/data"
    
    # 生成 MCP Bridge 配置文件
    cat > "$MCP_BRIDGE_DIR/config/production.yaml" << EOF
# MCP Bridge 生产环境配置
server:
  host: "0.0.0.0"
  port: $BRIDGE_SERVER_PORT
  workers: 4
  
mcp_server:
  host: "0.0.0.0"
  port: $MCP_SERVER_PORT
  max_connections: 100
  timeout: 30
  
capcut_api:
  base_url: "http://localhost:9000"
  timeout: 60
  max_retries: 3
  
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: ""
  
logging:
  level: "INFO"
  file: "$MCP_BRIDGE_DIR/logs/bridge.log"
  max_size: "100MB"
  backup_count: 5
  
monitoring:
  enabled: true
  metrics_port: 9090
  health_check_interval: 30
  
security:
  api_key_required: false
  cors_enabled: true
  rate_limit:
    enabled: true
    requests_per_minute: 100
EOF
    
    log_success "MCP Bridge 配置完成"
}

# 配置 Dify 集成
configure_dify_integration() {
    log_info "配置 Dify 集成..."
    
    # 检查 Dify 项目是否存在
    if [ ! -d "$DIFY_PROJECT_DIR" ]; then
        log_warning "Dify 项目目录不存在: $DIFY_PROJECT_DIR"
        log_info "请确保 Dify 已正确安装"
        return 1
    fi
    
    # 创建 Dify MCP 配置
    cat > "$MCP_BRIDGE_DIR/config/dify_integration.yaml" << EOF
# Dify 集成配置
dify:
  api_base_url: "$DIFY_API_URL"
  api_key: "$DIFY_API_KEY"
  timeout: 30
  
mcp_server:
  name: "CapCut API MCP Server"
  description: "CapCut 视频编辑 API 的 MCP 服务器"
  url: "ws://localhost:$MCP_SERVER_PORT"
  capabilities:
    tools: true
    resources: true
  
workflows:
  templates_dir: "$MCP_BRIDGE_DIR/templates"
  auto_deploy: false
  
integration:
  auto_register: true
  health_check_interval: 60
  retry_count: 3
EOF
    
    # 创建工作流模板目录
    mkdir -p "$MCP_BRIDGE_DIR/templates"
    
    log_success "Dify 集成配置完成"
}

# 启动 Redis 服务
start_redis() {
    log_info "启动 Redis 服务..."
    
    if command -v redis-server &> /dev/null; then
        # 检查 Redis 是否已运行
        if pgrep redis-server > /dev/null; then
            log_info "Redis 服务已在运行"
        else
            redis-server --daemonize yes
            sleep 2
            if pgrep redis-server > /dev/null; then
                log_success "Redis 服务启动成功"
            else
                log_error "Redis 服务启动失败"
                return 1
            fi
        fi
    elif command -v docker &> /dev/null; then
        # 使用 Docker 启动 Redis
        if ! docker ps | grep -q redis-mcp; then
            docker run -d --name redis-mcp -p 6379:6379 redis:alpine
            log_success "Redis 容器启动成功"
        else
            log_info "Redis 容器已在运行"
        fi
    else
        log_error "Redis 未安装且 Docker 不可用"
        return 1
    fi
}

# 启动 CapCut API 服务
start_capcut_api() {
    log_info "启动 CapCut API 服务..."
    
    cd "$PROJECT_ROOT"
    
    # 检查服务是否已运行
    if pgrep -f "python.*app.py" > /dev/null; then
        log_info "CapCut API 服务已在运行"
        return 0
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 启动服务
    if [ -f "service_manager.sh" ]; then
        chmod +x service_manager.sh
        ./service_manager.sh start
    else
        nohup python app.py > logs/capcut_api.log 2>&1 &
    fi
    
    # 等待服务启动
    sleep 5
    
    # 验证服务
    if curl -s http://localhost:9000/get_intro_animation_types > /dev/null; then
        log_success "CapCut API 服务启动成功"
    else
        log_error "CapCut API 服务启动失败"
        return 1
    fi
}

# 启动 MCP Bridge 服务
start_mcp_bridge() {
    log_info "启动 MCP Bridge 服务..."
    
    cd "$MCP_BRIDGE_DIR"
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 启动 MCP 服务器
    nohup python -m core.capcut_mcp_server \
        --port $MCP_SERVER_PORT \
        --config config/production.yaml \
        > logs/mcp_server.log 2>&1 &
    
    # 启动 Bridge 服务器
    nohup python -m core.bridge_server \
        --port $BRIDGE_SERVER_PORT \
        --config config/production.yaml \
        > logs/bridge_server.log 2>&1 &
    
    # 等待服务启动
    sleep 5
    
    # 验证服务
    if curl -s http://localhost:$BRIDGE_SERVER_PORT/health > /dev/null; then
        log_success "MCP Bridge 服务启动成功"
    else
        log_error "MCP Bridge 服务启动失败"
        return 1
    fi
}

# 注册 MCP 服务器到 Dify
register_mcp_to_dify() {
    log_info "注册 MCP 服务器到 Dify..."
    
    if [ -z "$DIFY_API_KEY" ]; then
        log_warning "Dify API 密钥未设置，跳过自动注册"
        log_info "请手动在 Dify 管理界面添加 MCP 服务器："
        log_info "  名称: CapCut API MCP Server"
        log_info "  URL: ws://localhost:$MCP_SERVER_PORT"
        return 0
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 运行注册脚本
    cd "$MCP_BRIDGE_DIR"
    python -m integrations.dify_workflow_integration \
        --dify-api "$DIFY_API_URL" \
        --dify-key "$DIFY_API_KEY" \
        --mcp-server "ws://localhost:$MCP_SERVER_PORT" \
        --action register
    
    if [ $? -eq 0 ]; then
        log_success "MCP 服务器注册成功"
    else
        log_error "MCP 服务器注册失败"
        return 1
    fi
}

# 部署工作流模板
deploy_workflow_templates() {
    log_info "部署工作流模板..."
    
    if [ -z "$DIFY_API_KEY" ]; then
        log_warning "Dify API 密钥未设置，跳过工作流模板部署"
        log_info "工作流模板配置已导出到 templates/ 目录"
        return 0
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    cd "$MCP_BRIDGE_DIR"
    
    # 部署视频生成工作流
    python -m integrations.dify_workflow_integration \
        --dify-api "$DIFY_API_URL" \
        --dify-key "$DIFY_API_KEY" \
        --mcp-server "ws://localhost:$MCP_SERVER_PORT" \
        --action deploy \
        --export-config "templates/video_generation_workflow.yaml"
    
    if [ $? -eq 0 ]; then
        log_success "工作流模板部署成功"
    else
        log_error "工作流模板部署失败"
        return 1
    fi
}

# 验证集成
verify_integration() {
    log_info "验证集成功能..."
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    cd "$MCP_BRIDGE_DIR"
    
    # 运行集成测试
    python -m integrations.dify_workflow_integration \
        --dify-api "$DIFY_API_URL" \
        --dify-key "$DIFY_API_KEY" \
        --mcp-server "ws://localhost:$MCP_SERVER_PORT" \
        --action test
    
    if [ $? -eq 0 ]; then
        log_success "集成验证通过"
    else
        log_error "集成验证失败"
        return 1
    fi
}

# 创建服务管理脚本
create_service_manager() {
    log_info "创建服务管理脚本..."
    
    cat > "$PROJECT_ROOT/manage_integration.sh" << 'EOF'
#!/bin/bash

# CapCut API MCP 集成服务管理脚本

PROJECT_ROOT="/home/CapCutAPI-1.1.0"
VENV_DIR="$PROJECT_ROOT/venv"
MCP_BRIDGE_DIR="$PROJECT_ROOT/mcp_bridge"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

start_services() {
    log_info "启动所有服务..."
    
    # 启动 Redis
    if ! pgrep redis-server > /dev/null; then
        redis-server --daemonize yes
        log_info "Redis 服务已启动"
    fi
    
    # 启动 CapCut API
    cd "$PROJECT_ROOT"
    if [ -f "service_manager.sh" ]; then
        ./service_manager.sh start
    fi
    
    # 启动 MCP Bridge
    cd "$MCP_BRIDGE_DIR"
    source "$VENV_DIR/bin/activate"
    
    if ! pgrep -f "capcut_mcp_server" > /dev/null; then
        nohup python -m core.capcut_mcp_server > logs/mcp_server.log 2>&1 &
        log_info "MCP 服务器已启动"
    fi
    
    if ! pgrep -f "bridge_server" > /dev/null; then
        nohup python -m core.bridge_server > logs/bridge_server.log 2>&1 &
        log_info "Bridge 服务器已启动"
    fi
    
    log_success "所有服务已启动"
}

stop_services() {
    log_info "停止所有服务..."
    
    # 停止 MCP Bridge
    pkill -f "capcut_mcp_server" 2>/dev/null || true
    pkill -f "bridge_server" 2>/dev/null || true
    
    # 停止 CapCut API
    cd "$PROJECT_ROOT"
    if [ -f "service_manager.sh" ]; then
        ./service_manager.sh stop
    fi
    
    log_success "所有服务已停止"
}

status_services() {
    log_info "检查服务状态..."
    
    echo "Redis: $(pgrep redis-server > /dev/null && echo '运行中' || echo '已停止')"
    echo "CapCut API: $(pgrep -f 'python.*app.py' > /dev/null && echo '运行中' || echo '已停止')"
    echo "MCP Server: $(pgrep -f 'capcut_mcp_server' > /dev/null && echo '运行中' || echo '已停止')"
    echo "Bridge Server: $(pgrep -f 'bridge_server' > /dev/null && echo '运行中' || echo '已停止')"
}

restart_services() {
    log_info "重启所有服务..."
    stop_services
    sleep 3
    start_services
}

show_logs() {
    service=${1:-all}
    
    case $service in
        "capcut")
            tail -f "$PROJECT_ROOT/logs/capcutapi.log"
            ;;
        "mcp")
            tail -f "$MCP_BRIDGE_DIR/logs/mcp_server.log"
            ;;
        "bridge")
            tail -f "$MCP_BRIDGE_DIR/logs/bridge_server.log"
            ;;
        "all"|*)
            tail -f "$PROJECT_ROOT/logs/capcutapi.log" \
                   "$MCP_BRIDGE_DIR/logs/mcp_server.log" \
                   "$MCP_BRIDGE_DIR/logs/bridge_server.log"
            ;;
    esac
}

test_integration() {
    log_info "测试集成功能..."
    
    cd "$MCP_BRIDGE_DIR"
    source "$VENV_DIR/bin/activate"
    
    python -m integrations.dify_workflow_integration \
        --mcp-server "ws://localhost:8080" \
        --action test
}

case "$1" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        status_services
        ;;
    "logs")
        show_logs "$2"
        ;;
    "test")
        test_integration
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs [service]|test}"
        echo "服务: capcut, mcp, bridge, all"
        exit 1
        ;;
esac
EOF
    
    chmod +x "$PROJECT_ROOT/manage_integration.sh"
    log_success "服务管理脚本创建完成"
}

# 生成部署报告
generate_deployment_report() {
    log_info "生成部署报告..."
    
    cat > "$PROJECT_ROOT/INTEGRATION_DEPLOYMENT_REPORT.md" << EOF
# CapCut API MCP 与 Dify 工作流集成部署报告

## 部署信息

- **部署时间**: $(date '+%Y年%m月%d日 %H:%M:%S')
- **项目路径**: $PROJECT_ROOT
- **MCP Bridge 路径**: $MCP_BRIDGE_DIR
- **Dify 项目路径**: $DIFY_PROJECT_DIR

## 服务配置

### MCP 服务器
- **端口**: $MCP_SERVER_PORT
- **访问地址**: ws://localhost:$MCP_SERVER_PORT
- **配置文件**: $MCP_BRIDGE_DIR/config/production.yaml

### Bridge 服务器
- **端口**: $BRIDGE_SERVER_PORT
- **访问地址**: http://localhost:$BRIDGE_SERVER_PORT
- **健康检查**: http://localhost:$BRIDGE_SERVER_PORT/health

### CapCut API 服务
- **端口**: 9000
- **访问地址**: http://localhost:9000
- **状态检查**: http://localhost:9000/get_intro_animation_types

## Dify 集成配置

### MCP 服务器注册信息
- **服务器名称**: CapCut API MCP Server
- **服务器描述**: CapCut 视频编辑 API 的 MCP 服务器
- **连接 URL**: ws://localhost:$MCP_SERVER_PORT
- **支持功能**: 工具调用、资源访问

### 可用工具列表
- create_draft - 创建视频草稿
- add_video - 添加视频文件
- add_audio - 添加音频文件
- add_text - 添加文本内容
- add_subtitle - 添加字幕
- add_image - 添加图片
- add_effect - 添加视觉效果
- add_sticker - 添加贴纸
- save_draft - 保存草稿

## 工作流模板

### 1. 视频生成工作流
- **模板名称**: CapCut 视频生成工作流
- **描述**: 使用 CapCut API 自动生成视频的工作流
- **配置文件**: $MCP_BRIDGE_DIR/templates/video_generation_workflow.yaml

### 2. 批量视频处理工作流
- **模板名称**: CapCut 批量视频处理工作流
- **描述**: 批量处理多个视频文件的工作流
- **配置文件**: $MCP_BRIDGE_DIR/templates/batch_video_workflow.yaml

## 服务管理

### 启动所有服务
\`\`\`bash
./manage_integration.sh start
\`\`\`

### 停止所有服务
\`\`\`bash
./manage_integration.sh stop
\`\`\`

### 查看服务状态
\`\`\`bash
./manage_integration.sh status
\`\`\`

### 查看服务日志
\`\`\`bash
./manage_integration.sh logs [service]
\`\`\`

### 测试集成功能
\`\`\`bash
./manage_integration.sh test
\`\`\`

## 在 Dify 中使用

### 1. 添加 MCP 服务器
1. 登录 Dify 管理界面
2. 进入"设置" -> "模型供应商" -> "MCP 服务器"
3. 点击"添加 MCP 服务器"
4. 填写以下信息：
   - 名称: CapCut API MCP Server
   - URL: ws://localhost:$MCP_SERVER_PORT
   - 描述: CapCut 视频编辑 API 的 MCP 服务器
5. 点击"测试连接"确认连接成功
6. 保存配置

### 2. 创建工作流
1. 进入"应用" -> "创建应用" -> "工作流"
2. 选择"从模板创建"或"空白工作流"
3. 在节点库中找到"CapCut API"相关工具
4. 拖拽所需工具到画布
5. 配置节点参数和连接
6. 测试和发布工作流

### 3. 使用预设模板
导入 $MCP_BRIDGE_DIR/templates/ 目录下的工作流模板文件

## 故障排除

### 常见问题

1. **MCP 服务器连接失败**
   - 检查服务是否启动: \`./manage_integration.sh status\`
   - 查看服务日志: \`./manage_integration.sh logs mcp\`
   - 确认端口未被占用: \`netstat -tlnp | grep $MCP_SERVER_PORT\`

2. **工具调用失败**
   - 检查 CapCut API 服务状态
   - 验证 API 接口可访问性
   - 查看 Bridge 服务器日志

3. **Dify 集成问题**
   - 确认 Dify API 密钥正确
   - 检查网络连接
   - 验证 MCP 服务器注册状态

### 日志文件位置
- CapCut API: $PROJECT_ROOT/logs/capcutapi.log
- MCP Server: $MCP_BRIDGE_DIR/logs/mcp_server.log
- Bridge Server: $MCP_BRIDGE_DIR/logs/bridge_server.log

## 性能监控

### 监控指标
- 服务可用性
- API 调用次数
- 响应时间
- 错误率

### 监控端点
- Bridge 健康检查: http://localhost:$BRIDGE_SERVER_PORT/health
- Prometheus 指标: http://localhost:9090/metrics

## 安全配置

### 访问控制
- MCP 服务器默认无认证（内网使用）
- Bridge 服务器支持 API 密钥认证
- 建议在生产环境启用 HTTPS

### 网络安全
- 防火墙配置
- 端口访问限制
- SSL/TLS 加密

## 维护建议

### 定期维护
- 检查服务状态
- 清理日志文件
- 更新依赖包
- 备份配置文件

### 监控告警
- 服务异常告警
- 性能指标监控
- 错误日志分析

---

**部署完成时间**: $(date '+%Y年%m月%d日 %H:%M:%S')
**部署状态**: ✅ 成功
**集成状态**: ✅ 已配置
**服务管理**: ./manage_integration.sh
EOF
    
    log_success "部署报告已生成: $PROJECT_ROOT/INTEGRATION_DEPLOYMENT_REPORT.md"
}

# 主函数
main() {
    echo "========================================"
    echo "CapCut API MCP 与 Dify 工作流集成部署"
    echo "========================================"
    echo
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dify-api)
                DIFY_API_URL="$2"
                shift 2
                ;;
            --dify-key)
                DIFY_API_KEY="$2"
                shift 2
                ;;
            --mcp-port)
                MCP_SERVER_PORT="$2"
                shift 2
                ;;
            --bridge-port)
                BRIDGE_SERVER_PORT="$2"
                shift 2
                ;;
            --help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --dify-api URL      Dify API 基础 URL (默认: http://localhost:5001)"
                echo "  --dify-key KEY      Dify API 密钥"
                echo "  --mcp-port PORT     MCP 服务器端口 (默认: 8080)"
                echo "  --bridge-port PORT  Bridge 服务器端口 (默认: 8081)"
                echo "  --help              显示此帮助信息"
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                exit 1
                ;;
        esac
    done
    
    # 显示配置信息
    log_info "部署配置:"
    echo "  项目根目录: $PROJECT_ROOT"
    echo "  MCP Bridge 目录: $MCP_BRIDGE_DIR"
    echo "  Dify 项目目录: $DIFY_PROJECT_DIR"
    echo "  MCP 服务器端口: $MCP_SERVER_PORT"
    echo "  Bridge 服务器端口: $BRIDGE_SERVER_PORT"
    echo "  Dify API URL: $DIFY_API_URL"
    echo "  Dify API Key: ${DIFY_API_KEY:+已设置}"
    echo
    
    # 执行部署步骤
    check_requirements
    setup_virtual_environment
    install_dependencies
    configure_mcp_bridge
    configure_dify_integration
    start_redis
    start_capcut_api
    start_mcp_bridge
    
    # 如果设置了 Dify API 密钥，则进行自动集成
    if [ -n "$DIFY_API_KEY" ]; then
        register_mcp_to_dify
        deploy_workflow_templates
    fi
    
    verify_integration
    create_service_manager
    generate_deployment_report
    
    echo
    echo "========================================"
    log_success "集成部署完成！"
    echo "========================================"
    echo
    log_info "下一步操作："
    echo "1. 查看部署报告: cat $PROJECT_ROOT/INTEGRATION_DEPLOYMENT_REPORT.md"
    echo "2. 管理服务: ./manage_integration.sh {start|stop|status|logs|test}"
    echo "3. 在 Dify 中配置 MCP 服务器 (如果未自动注册)"
    echo "4. 导入工作流模板到 Dify"
    echo
    log_info "访问地址："
    echo "- CapCut API: http://localhost:9000"
    echo "- MCP Server: ws://localhost:$MCP_SERVER_PORT"
    echo "- Bridge Server: http://localhost:$BRIDGE_SERVER_PORT"
    echo "- Dify: $DIFY_API_URL"
}

# 执行主函数
main "$@"