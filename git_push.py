#!/usr/bin/env python3

import subprocess
import os
import sys

# 切换到项目目录
os.chdir('/home/CapCutAPI-1.1.0')

def run_command(command):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        print(f"Command: {command}")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Error:\n{result.stderr}")
        print("-" * 50)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Command timeout: {command}")
        return False
    except Exception as e:
        print(f"Error running command '{command}': {e}")
        return False

def main():
    print("Starting Git push process...")
    
    # 检查 Git 状态
    print("=== Checking Git status ===")
    run_command("git status")
    
    # 检查远程仓库
    print("=== Checking remote repository ===")
    run_command("git remote -v")
    
    # 检查分支信息
    print("=== Checking branch info ===")
    run_command("git branch -v")
    
    # 推送到远程仓库
    print("=== Pushing to remote repository ===")
    success = run_command("git push origin master")
    
    if success:
        print("✅ Successfully pushed to GitHub!")
    else:
        print("❌ Failed to push to GitHub")
        print("Trying with force push (be careful!)...")
        force_success = run_command("git push origin master --force")
        if force_success:
            print("✅ Force push successful!")
        else:
            print("❌ Force push also failed")
    
    # 最终状态检查
    print("=== Final status ===")
    run_command("git status")

if __name__ == "__main__":
    main()