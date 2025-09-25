#!/bin/bash

# MCP Bridge 项目管理脚本
# 用于快速执行常见的项目操作

PROJECT_DIR="/home/dify/MCP_Bridge_Project"
cd "$PROJECT_DIR"

case "$1" in
    "test")
        echo "🧪 运行集成测试..."
        python3 tests/test_workflow_integration.py
        ;;
    "status")
        echo "📊 检查服务状态..."
        echo "检查 MCP Bridge 服务..."
        curl -s http://localhost:8082/health || echo "❌ MCP Bridge 服务不可用"
        echo "检查 CapCut API 服务..."
        curl -s http://localhost:8083/health || echo "❌ CapCut API 服务不可用"
        ;;
    "structure")
        echo "📁 项目文件结构:"
        tree -a || find . -type f | sort
        ;;
    "docs")
        echo "📚 可用文档:"
        echo "- 集成方案: docs/MCP_Bridge_集成方案.md"
        echo "- 部署指南: docs/MCP_Bridge_部署指南.md"
        echo "- 项目说明: README.md"
        ;;
    "report")
        echo "📋 查看最新测试报告..."
        if [ -f "reports/integration_test_report.json" ]; then
            python3 -m json.tool reports/integration_test_report.json
        else
            echo "❌ 测试报告不存在，请先运行测试"
        fi
        ;;
    "help"|*)
        echo "🚀 MCP Bridge 项目管理工具"
        echo ""
        echo "用法: ./manage.sh [命令]"
        echo ""
        echo "可用命令:"
        echo "  test      - 运行集成测试"
        echo "  status    - 检查服务状态"
        echo "  structure - 显示项目结构"
        echo "  docs      - 列出可用文档"
        echo "  report    - 查看测试报告"
        echo "  help      - 显示此帮助信息"
        echo ""
        echo "示例:"
        echo "  ./manage.sh test     # 运行测试"
        echo "  ./manage.sh status   # 检查状态"
        ;;
esac