# 集成模块初始化文件
"""
MCP Bridge 集成模块

包含以下集成：
- http_bridge: HTTP桥接服务
- dify_integration: Dify平台集成
"""

# 导入HTTP桥接相关模块
try:
    from .http_bridge import *
except ImportError:
    pass

# 导入Dify集成相关模块
try:
    from .dify_integration import *
except ImportError:
    pass

__all__ = []