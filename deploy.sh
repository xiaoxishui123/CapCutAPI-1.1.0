#!/bin/bash

# CapCutAPI 部署脚本
# 作者：AI助手
# 用途：在服务器上部署CapCutAPI服务

echo "=== CapCutAPI 部署脚本开始 ==="

# 检查Python版本
echo "检查Python版本..."
python_version=$(python3.9 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✓ Python版本: $python_version"
else
    echo "✗ 未找到Python3.9，尝试使用系统Python..."
    python_version=$(python3 --version 2>&1)
    if [[ $? -eq 0 ]]; then
        echo "✓ 使用系统Python: $python_version"
    else
        echo "✗ 未找到Python3，请先安装Python3"
        exit 1
    fi
fi

# 检查ffmpeg
echo "检查ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✓ ffmpeg已安装"
else
    echo "✗ ffmpeg未安装，正在安装..."
    if command -v yum &> /dev/null; then
        # CentOS/RHEL系统
        sudo yum install -y epel-release
        sudo yum install -y ffmpeg
    elif command -v apt-get &> /dev/null; then
        # Ubuntu/Debian系统
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    else
        echo "✗ 无法自动安装ffmpeg，请手动安装"
        exit 1
    fi
fi

# 创建虚拟环境
echo "创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3.9 -m venv venv
    echo "✓ 虚拟环境创建成功"
else
    echo "✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装项目依赖..."
pip install -r requirements.txt

# 检查配置文件
if [ ! -f "config.json" ]; then
    echo "创建配置文件..."
    cp config.json.example config.json
    echo "✓ 配置文件已创建"
else
    echo "✓ 配置文件已存在"
fi

# 创建日志目录
mkdir -p logs

# 创建systemd服务文件
echo "创建systemd服务文件..."
sudo tee /etc/systemd/system/capcutapi.service > /dev/null <<EOF
[Unit]
Description=CapCutAPI Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python capcut_server.py
Restart=always
RestartSec=10
StandardOutput=append:$(pwd)/logs/capcutapi.log
StandardError=append:$(pwd)/logs/capcutapi.error.log

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务
echo "启用CapCutAPI服务..."
sudo systemctl enable capcutapi.service

# 启动服务
echo "启动CapCutAPI服务..."
sudo systemctl start capcutapi.service

# 检查服务状态
echo "检查服务状态..."
sleep 3
if sudo systemctl is-active --quiet capcutapi.service; then
    echo "✓ CapCutAPI服务启动成功"
    echo "✓ 服务访问地址: http://8.148.70.18:9000"
    echo "✓ 服务日志位置: $(pwd)/logs/"
else
    echo "✗ 服务启动失败，查看日志:"
    sudo systemctl status capcutapi.service
    echo "查看详细日志:"
    tail -n 20 logs/capcutapi.error.log
fi

echo "=== 部署完成 ==="
echo ""
echo "常用命令:"
echo "  查看服务状态: sudo systemctl status capcutapi.service"
echo "  启动服务: sudo systemctl start capcutapi.service"
echo "  停止服务: sudo systemctl stop capcutapi.service"
echo "  重启服务: sudo systemctl restart capcutapi.service"
echo "  查看日志: tail -f logs/capcutapi.log"
echo "  查看错误日志: tail -f logs/capcutapi.error.log" 