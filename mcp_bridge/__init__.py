# MCP Bridge 包初始化文件
"""
MCP Bridge - 统一的MCP协议桥接服务

这个包提供了以下主要功能：
1. MCP协议到HTTP的桥接
2. 工作流管理和执行
3. 缓存和性能优化
4. 监控和日志记录
5. 降级和容错处理

版本: 1.0.0
作者: MCP Bridge Team
"""

__version__ = "1.0.0"
__author__ = "MCP Bridge Team"
__email__ = "support@mcpbridge.com"

# 导入核心模块
from .core import *
from .integrations import *
from .workflows import *

# 设置包级别的日志
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())