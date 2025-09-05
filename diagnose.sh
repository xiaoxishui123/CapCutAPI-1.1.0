#!/bin/bash
# CapCutAPI 完整诊断脚本
# 用于快速诊断和排查常见问题

echo "=== CapCutAPI 完整诊断 ==="
echo "时间: $(date)"
echo ""

echo "1. 检查服务状态..."
sudo systemctl is-active capcutapi.service
sudo systemctl status capcutapi.service --no-pager -l
echo ""

echo "2. 检查端口监听..."
netstat -tlnp | grep 9000
echo ""

echo "3. 检查进程..."
ps aux | grep capcut_server
echo ""

echo "4. 检查配置文件..."
if [ -f "config.json" ]; then
    echo "✅ config.json 存在"
    python3 -c "import json; json.load(open('config.json'))" && echo "✅ 配置文件格式正确" || echo "❌ 配置文件格式错误"
else
    echo "❌ config.json 不存在"
fi
echo ""

echo "5. 检查依赖..."
source venv/bin/activate 2>/dev/null || echo "⚠️  虚拟环境未激活"
pip list | grep -E "flask|requests|oss2|imageio|psutil" || echo "❌ 缺少关键依赖"
echo ""

echo "6. 测试API连接..."
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:9000/ 2>/dev/null || echo "❌ 本地连接失败"
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://8.148.70.18:9000/ 2>/dev/null || echo "❌ 外部连接失败"
echo ""

echo "7. 检查最近日志..."
sudo journalctl -u capcutapi.service -n 10 --no-pager
echo ""

echo "8. 检查模板文件..."
if [ -d "templates" ]; then
    echo "✅ templates 目录存在"
    ls -la templates/
    if [ -f "templates/preview.html" ]; then
        echo "✅ preview.html 模板存在"
        # 检查模板语法
        python3 -c "from jinja2 import Template; Template(open('templates/preview.html').read())" 2>/dev/null && echo "✅ 模板语法正确" || echo "❌ 模板语法错误"
    else
        echo "❌ preview.html 模板不存在"
    fi
else
    echo "❌ templates 目录不存在"
fi
echo ""

echo "9. 检查磁盘空间..."
df -h .
echo ""

echo "10. 检查内存使用..."
free -h
echo ""

echo "=== 诊断完成 ==="
echo "如果问题仍然存在，请将此输出结果提供给技术支持。"