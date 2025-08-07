#!/usr/bin/env python3
"""
OSS功能测试 - 绕过Cursor terminal问题
直接使用subprocess执行测试
"""

import subprocess
import sys
import os
import json

def run_oss_test():
    """运行OSS功能测试"""
    print("🚀 开始OSS功能测试 (绕过Cursor terminal问题)")
    print("=" * 60)
    
    # 确保在正确的目录
    os.chdir('/home/CapCutAPI-1.1.0')
    
    # 构建测试命令
    cmd = [
        '/usr/local/bin/python3.9', 
        'test_api.py', 
        '--mode', 'oss', 
        '--server', 'http://8.148.70.18:9000'
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        # 执行测试
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        print(f"\n📊 测试完成")
        print(f"退出码: {result.returncode}")
        print(f"成功: {'✅' if result.returncode == 0 else '❌'}")
        
        if result.stdout:
            print(f"\n📝 测试输出:")
            print(result.stdout)
        
        if result.stderr:
            print(f"\n⚠️ 错误信息:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 执行测试时发生错误: {e}")
        return False

def check_service_status():
    """检查服务状态"""
    print("\n🔍 检查CapCutAPI服务状态")
    
    try:
        # 检查服务状态
        result = subprocess.run([
            'systemctl', 'is-active', 'capcutapi.service'
        ], capture_output=True, text=True)
        
        status = result.stdout.strip()
        print(f"服务状态: {status}")
        
        if status == 'active':
            print("✅ 服务运行正常")
            return True
        else:
            print("❌ 服务未运行")
            return False
            
    except Exception as e:
        print(f"❌ 检查服务状态失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 CapCutAPI OSS功能验证")
    print("解决Cursor terminal工具问题")
    print("=" * 60)
    
    # 检查服务状态
    service_ok = check_service_status()
    
    if not service_ok:
        print("⚠️ 服务未运行，尝试启动服务")
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'capcutapi.service'], check=True)
            print("✅ 服务启动成功")
        except Exception as e:
            print(f"❌ 启动服务失败: {e}")
            return 1
    
    # 运行OSS测试
    success = run_oss_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 OSS功能测试通过！")
        print("✅ OSS签名修复成功")
        print("✅ 所有功能正常工作")
        return 0
    else:
        print("⚠️ OSS功能测试未完全通过")
        print("🔧 请查看上述输出了解详情")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 