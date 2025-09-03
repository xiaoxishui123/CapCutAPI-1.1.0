#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCutAPI服务启动脚本
"""

import subprocess
import sys
import os
import time
import signal
import psutil

def start_service():
    """启动CapCutAPI服务"""
    print("🚀 启动CapCutAPI服务...")
    
    # 检查虚拟环境
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    if not os.path.exists(venv_path):
        print("❌ 虚拟环境不存在，请先创建虚拟环境")
        return False
    
    # 检查主服务器文件
    server_file = os.path.join(os.path.dirname(__file__), 'capcut_server.py')
    if not os.path.exists(server_file):
        print("❌ 主服务器文件不存在")
        return False
    
    try:
        # 激活虚拟环境并启动服务
        activate_script = os.path.join(venv_path, 'bin', 'activate')
        python_path = os.path.join(venv_path, 'bin', 'python')
        
        # 使用nohup启动服务
        cmd = [
            'nohup', python_path, server_file,
            '>', 'logs/capcut_server_new.log', '2>&1', '&'
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        
        # 启动服务
        process = subprocess.Popen(
            [python_path, server_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        print(f"✅ 服务启动成功！PID: {process.pid}")
        
        # 等待几秒钟让服务启动
        print("⏳ 等待服务启动...")
        time.sleep(5)
        
        # 检查服务是否真的在运行
        if check_service_running():
            print("🎉 服务已成功启动并运行！")
            return True
        else:
            print("❌ 服务启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 启动服务时出错: {e}")
        return False

def check_service_running():
    """检查服务是否在运行"""
    try:
        import requests
        response = requests.get('http://localhost:9000/', timeout=5)
        return response.status_code == 200
    except:
        return False

def stop_service():
    """停止服务"""
    print("🛑 停止CapCutAPI服务...")
    
    # 查找并停止相关进程
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'capcut_server.py' in ' '.join(proc.info['cmdline']):
                print(f"停止进程 {proc.info['pid']}")
                proc.terminate()
                proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            pass
    
    print("✅ 服务已停止")

def main():
    if len(sys.argv) < 2:
        print("用法: python start_service.py {start|stop|status}")
        return 1
    
    command = sys.argv[1]
    
    if command == 'start':
        if start_service():
            return 0
        else:
            return 1
    elif command == 'stop':
        stop_service()
        return 0
    elif command == 'status':
        if check_service_running():
            print("✅ 服务正在运行")
            return 0
        else:
            print("❌ 服务未运行")
            return 1
    else:
        print("未知命令，支持: start, stop, status")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 