"""
MCP Bridge 安装配置文件

本文件定义了 MCP Bridge 项目的安装配置，包括依赖管理、
包信息和入口点等。
"""

from setuptools import setup, find_packages
import os

# 读取 README 文件
def read_readme():
    """读取 README 文件内容"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "MCP Bridge - 统一的 MCP 协议桥接服务"

# 读取依赖文件
def read_requirements():
    """读取 requirements.txt 文件内容"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="mcp-bridge",
    version="1.1.0",
    author="MCP Bridge Team",
    author_email="support@mcpbridge.com",
    description="统一的 MCP 协议桥接服务",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/mcpbridge/mcp-bridge",
    packages=find_packages(exclude=['tests*']),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
            'pytest-mock>=3.10.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'test': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
            'pytest-mock>=3.10.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'mcp-bridge=mcp_bridge.main:main',
            'mcp-bridge-server=mcp_bridge.core.bridge_server:main',
            'mcp-bridge-http=mcp_bridge.integrations.http_bridge:main',
        ],
    },
    include_package_data=True,
    package_data={
        'mcp_bridge': [
            'config/*.yaml',
            'config/*.json',
            'templates/*.html',
            'static/*',
        ],
    },
    zip_safe=False,
    keywords="mcp bridge protocol http websocket grpc",
    project_urls={
        "Bug Reports": "https://github.com/mcpbridge/mcp-bridge/issues",
        "Source": "https://github.com/mcpbridge/mcp-bridge",
        "Documentation": "https://mcpbridge.readthedocs.io/",
    },
)