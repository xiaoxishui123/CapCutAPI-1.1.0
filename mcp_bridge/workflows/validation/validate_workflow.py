#!/usr/bin/env python3
"""
工作流配置验证脚本

这个脚本用于验证Dify工作流配置文件的完整性和正确性。
支持验证基本结构、节点配置、边配置、BGM功能、环境变量、数据流和代码语法。

使用方法:
    python scripts/validate_workflow.py [配置文件路径]
    
示例:
    python scripts/validate_workflow.py configs/优化版短视频工作流.yml
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'tests'))

from workflow_validation_test import WorkflowValidator


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="验证Dify工作流配置文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s configs/优化版短视频工作流.yml
  %(prog)s --all  # 验证所有配置文件
        """
    )
    
    parser.add_argument(
        'config_file',
        nargs='?',
        help='要验证的工作流配置文件路径'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='验证configs目录下的所有.yml文件'
    )
    
    parser.add_argument(
        '--output-dir',
        default='configs',
        help='验证报告输出目录 (默认: configs)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='显示详细输出'
    )
    
    args = parser.parse_args()
    
    # 检查参数
    if not args.config_file and not args.all:
        parser.error("请指定配置文件路径或使用 --all 选项")
    
    # 设置日志级别
    import logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # 获取要验证的文件列表
    config_files = []
    
    if args.all:
        configs_dir = project_root / 'configs'
        if configs_dir.exists():
            config_files = list(configs_dir.glob('*.yml'))
            config_files.extend(configs_dir.glob('*.yaml'))
        else:
            print(f"❌ 配置目录不存在: {configs_dir}")
            return 1
    else:
        config_file = Path(args.config_file)
        if not config_file.is_absolute():
            config_file = project_root / config_file
        
        if not config_file.exists():
            print(f"❌ 配置文件不存在: {config_file}")
            return 1
        
        config_files = [config_file]
    
    if not config_files:
        print("❌ 没有找到要验证的配置文件")
        return 1
    
    # 验证每个配置文件
    total_files = len(config_files)
    passed_files = 0
    failed_files = 0
    
    print(f"🔍 开始验证 {total_files} 个配置文件...")
    print("=" * 60)
    
    for config_file in config_files:
        print(f"\n📁 验证文件: {config_file.name}")
        print("-" * 40)
        
        try:
            # 创建验证器并运行验证
            validator = WorkflowValidator(str(config_file))
            success = validator.run_validation()
            
            if success:
                passed_files += 1
                print(f"✅ {config_file.name} 验证通过")
            else:
                failed_files += 1
                print(f"❌ {config_file.name} 验证失败")
                
        except Exception as e:
            failed_files += 1
            print(f"❌ {config_file.name} 验证异常: {e}")
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 验证结果汇总")
    print(f"📁 总文件数: {total_files}")
    print(f"✅ 通过文件: {passed_files}")
    print(f"❌ 失败文件: {failed_files}")
    
    if failed_files == 0:
        print("\n🎉 所有配置文件验证通过！")
        return 0
    else:
        print(f"\n⚠️ 有 {failed_files} 个配置文件验证失败，请检查错误并修复")
        return 1


if __name__ == '__main__':
    sys.exit(main())