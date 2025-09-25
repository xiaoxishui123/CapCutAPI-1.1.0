"""
测试配置文件 - 提供全局测试fixtures和配置
"""
import pytest
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def event_loop():
    """
    创建事件循环用于异步测试
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """
    提供测试配置
    """
    return {
        "test_mode": True,
        "log_level": "DEBUG",
        "timeout": 30,
        "max_retries": 3
    }

@pytest.fixture
def mock_capcut_api():
    """
    模拟CapCut API响应
    """
    class MockCapCutAPI:
        def __init__(self):
            self.base_url = "http://localhost:8080"
            
        async def process_request(self, data):
            return {"status": "success", "data": data}
    
    return MockCapCutAPI()

@pytest.fixture
def sample_workflow_data():
    """
    提供示例工作流数据
    """
    return {
        "workflow_id": "test_workflow_001",
        "name": "测试工作流",
        "steps": [
            {
                "id": "step1",
                "type": "video_edit",
                "parameters": {
                    "action": "trim",
                    "start_time": 0,
                    "end_time": 10
                }
            }
        ]
    }

@pytest.fixture
def temp_config_file(tmp_path):
    """
    创建临时配置文件用于测试
    """
    config_content = """
global:
  debug: true
  log_level: DEBUG

server:
  host: localhost
  port: 8080
  
http_bridge:
  enabled: true
  port: 8081
"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    return str(config_file)