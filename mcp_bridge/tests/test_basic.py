"""
MCP Bridge 基础功能测试

这是一个简化的测试文件，用于验证基本功能是否正常工作。
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_basic_imports():
    """测试基本模块导入"""
    try:
        # 测试核心模型导入 - 使用相对导入
        from core.models import ServiceType, ServiceStatus, ServiceEndpoint
        assert ServiceType.MCP == "mcp"
        assert ServiceStatus.ACTIVE == "active"
        
        # 测试基本类创建
        endpoint = ServiceEndpoint(
            id="test-1",
            name="Test Service",
            service_type=ServiceType.HTTP,
            port=8080
        )
        assert endpoint.name == "Test Service"
        assert endpoint.service_type == ServiceType.HTTP
        
        print("✅ 基本导入测试通过")
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False


def test_config_files_exist():
    """测试配置文件是否存在"""
    config_files = [
        "config/unified_config.yaml",
        "requirements.txt",
        "setup.py",
        "pytest.ini"
    ]
    
    missing_files = []
    for config_file in config_files:
        file_path = os.path.join(project_root, config_file)
        if not os.path.exists(file_path):
            missing_files.append(config_file)
    
    if missing_files:
        print(f"❌ 缺失配置文件: {missing_files}")
        return False
    else:
        print("✅ 配置文件检查通过")
        return True


def test_directory_structure():
    """测试目录结构是否正确"""
    required_dirs = [
        "core",
        "integrations", 
        "workflows",
        "config",
        "tests",
        "scripts",
        "docs"
    ]
    
    missing_dirs = []
    for required_dir in required_dirs:
        dir_path = os.path.join(project_root, required_dir)
        if not os.path.exists(dir_path):
            missing_dirs.append(required_dir)
    
    if missing_dirs:
        print(f"❌ 缺失目录: {missing_dirs}")
        return False
    else:
        print("✅ 目录结构检查通过")
        return True


def test_python_version():
    """测试 Python 版本"""
    import sys
    version = sys.version_info
    
    if version.major >= 3 and version.minor >= 9:
        print(f"✅ Python 版本检查通过: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python 版本过低: {version.major}.{version.minor}.{version.micro}, 需要 >= 3.9")
        return False


if __name__ == "__main__":
    """直接运行测试"""
    print("🚀 开始 MCP Bridge 基础功能测试...")
    print("=" * 50)
    
    tests = [
        ("Python 版本检查", test_python_version),
        ("目录结构检查", test_directory_structure), 
        ("配置文件检查", test_config_files_exist),
        ("基本导入测试", test_basic_imports),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"   测试失败: {test_name}")
        except Exception as e:
            print(f"   测试异常: {test_name} - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有基础测试通过！")
        exit(0)
    else:
        print("⚠️  部分测试失败，请检查问题")
        exit(1)