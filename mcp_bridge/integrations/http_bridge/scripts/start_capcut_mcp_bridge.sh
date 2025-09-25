#!/bin/bash
"""
CapCut MCP Bridge 启动脚本
用于启动修复后的MCP服务，解决Dify平台配置问题
"""

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查并安装依赖
echo "检查Python依赖..."
pip3 install flask requests --quiet

# 检查CapCut API服务是否运行
echo "检查CapCut API服务状态..."
if ! curl -s http://8.148.70.18:9000/health > /dev/null 2>&1; then
    echo "警告: CapCut API服务 (http://8.148.70.18:9000) 似乎未运行"
    echo "请确保CapCut API服务已启动"
fi

# 停止可能已运行的服务
echo "停止可能已运行的MCP Bridge服务..."
pkill -f "capcut_mcp_bridge_fix.py" 2>/dev/null || true

# 等待端口释放
sleep 2

# 启动MCP Bridge服务
echo "启动CapCut MCP Bridge服务..."
echo "服务端口: 8082"
echo "MCP端点: http://localhost:8082/mcp"
echo "健康检查: http://localhost:8082/health"
echo "按 Ctrl+C 停止服务"
echo "=========================="

python3 capcut_mcp_bridge_fix.py