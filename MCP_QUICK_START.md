# MCP 快速入门指南 - 5分钟上手

> 🎯 **适合人群**: 个人开发者、快速测试、学习 MCP 协议

---

## 📚 什么是 MCP？

**MCP (Model Context Protocol)** 是一个标准化的协议，让 AI 工具（如 Claude Desktop、Dify）能够调用外部服务。

**为什么需要 MCP？**
- ✅ 让 AI 助手直接操作剪映/CapCut
- ✅ 自动化视频编辑流程
- ✅ 与 AI 工作流平台无缝集成

---

## ⚡ 两种使用方式

CapCutAPI 提供**两种 MCP 服务**，根据您的需求选择：

| 特性 | 简化版 | 企业版 (MCP Bridge) |
|------|--------|---------------------|
| **适用场景** | 个人开发、快速测试 | 生产环境、企业部署 |
| **启动时间** | < 10 秒 | 需要配置 Redis 等 |
| **配置难度** | ⭐ 简单 | ⭐⭐⭐ 复杂 |
| **功能** | 核心 MCP 功能 | 监控、缓存、负载均衡 |
| **依赖** | Python 3.9+ | Python、Redis、Docker |
| **推荐指数** | ⭐⭐⭐⭐⭐ 新手首选 | ⭐⭐⭐ 企业用户 |

**建议**:
- 🟢 **新手/个人开发**: 使用简化版
- 🟡 **生产环境/团队**: 使用企业版

---

## 🚀 简化版 - 5分钟快速启动

### 步骤 1: 检查环境

```bash
# 确认 Python 版本
python3 --version  # 需要 3.9+

# 确认 CapCutAPI 服务运行中
curl http://localhost:9000/health
```

### 步骤 2: 安装 MCP SDK

```bash
# 安装 MCP Python SDK
pip install mcp aiohttp
```

### 步骤 3: 启动简化版 MCP 服务器

```bash
# 进入项目目录
cd /home/CapCutAPI-1.1.0

# 直接启动（使用默认配置）
python3 simple_mcp_server.py
```

**看到以下输出表示成功**:
```
INFO - CapCut MCP 服务器已启动
INFO - 连接到 CapCut API: http://localhost:9000
INFO - 等待 MCP 客户端连接...
```

**就这样！** 🎉 简化版 MCP 服务器已经运行了！

### 步骤 4: 配置 AI 客户端

#### 选项 A: Claude Desktop

编辑配置文件（根据操作系统选择）:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

添加以下配置：

```json
{
  "mcpServers": {
    "capcut": {
      "command": "python3",
      "args": ["/home/CapCutAPI-1.1.0/simple_mcp_server.py"],
      "env": {
        "CAPCUT_API_URL": "http://localhost:9000"
      }
    }
  }
}
```

**重启 Claude Desktop**，然后您可以对 Claude 说：

> "帮我创建一个剪映草稿，添加一段文字'Hello MCP!'"

#### 选项 B: Python 脚本测试

```python
# test_simple_mcp.py
import subprocess
import json

# 启动 MCP 服务器（后台运行）
process = subprocess.Popen(
    ["python3", "simple_mcp_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# 发送 MCP 请求
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "create_draft",
        "arguments": {
            "width": 1080,
            "height": 1920
        }
    }
}

# 写入请求
process.stdin.write((json.dumps(request) + "\n").encode())
process.stdin.flush()

# 读取响应
response = process.stdout.readline()
print(f"响应: {response.decode()}")
```

### 步骤 5: 测试功能

使用 Claude Desktop 测试以下命令：

```
1. 创建草稿:
   "创建一个 1920x1080 的剪映草稿"

2. 添加文字:
   "在草稿中添加文字 '你好世界'，持续 5 秒"

3. 添加视频:
   "添加这个视频到草稿: https://example.com/video.mp4"

4. 保存草稿:
   "保存草稿到本地"
```

---

## 🎓 简化版 vs 企业版对比

### 🟢 简化版 (`simple_mcp_server.py`)

**优点**:
- ✅ 一个命令启动，无需额外配置
- ✅ 零依赖（只需 Python 和 MCP SDK）
- ✅ 完整的 MCP 功能
- ✅ 适合学习和开发

**缺点**:
- ❌ 无性能监控
- ❌ 无缓存优化
- ❌ 无负载均衡

**适用场景**:
- 个人开发者学习 MCP
- 快速原型验证
- 小规模自动化脚本
- 本地测试环境

### 🟡 企业版 (`mcp_bridge/`)

**优点**:
- ✅ Redis 缓存加速
- ✅ Prometheus 监控
- ✅ 智能路由和降级
- ✅ Docker 容器化部署
- ✅ 支持高并发

**缺点**:
- ❌ 配置复杂（需要 Redis、配置文件等）
- ❌ 启动慢（需要初始化多个服务）
- ❌ 资源占用大

**适用场景**:
- 生产环境部署
- 团队协作开发
- 高并发场景
- 需要监控和日志

---

## 🔧 简化版配置（可选）

如需自定义配置，创建 `simple_config.json`:

```json
{
  "capcut_api_url": "http://localhost:9000",
  "timeout": 30,
  "max_retries": 3,
  "log_level": "INFO"
}
```

**配置项说明**:
- `capcut_api_url`: CapCut API 服务地址
- `timeout`: 请求超时时间（秒）
- `max_retries`: 失败重试次数
- `log_level`: 日志级别 (DEBUG/INFO/WARNING/ERROR)

---

## 💡 常见问题

### Q1: 简化版和企业版可以同时运行吗？
**A**: 可以！它们使用不同的端口，互不干扰。

### Q2: 简化版支持哪些功能？
**A**: 简化版支持所有核心 MCP 功能：
- ✅ 创建和管理草稿
- ✅ 添加视频、音频、文本
- ✅ 应用特效和转场
- ✅ 保存和导出

### Q3: 简化版的性能如何？
**A**:
- 单用户使用：完全够用 ✅
- 10+ 并发请求：建议升级到企业版
- 批量处理：建议升级到企业版

### Q4: 如何从简化版升级到企业版？
**A**:
```bash
# 停止简化版
# 按 Ctrl+C

# 启动企业版
cd /home/CapCutAPI-1.1.0/mcp_bridge
./manage.sh start
```

### Q5: 简化版出错了怎么办？
**A**:
1. 查看日志：`cat simple_mcp_server.log`
2. 确认 CapCut API 运行：`curl http://localhost:9000/health`
3. 检查 Python 版本：`python3 --version` (需要 3.9+)

---

## 📚 进阶使用

### 在 Dify 中使用简化版

1. 在 Dify 中添加 MCP 服务器
2. 配置连接方式为 `stdio`
3. 命令: `python3 /home/CapCutAPI-1.1.0/simple_mcp_server.py`

### 在工作流中使用

```python
# workflow.py
import asyncio
from mcp.client import Client

async def create_video():
    async with Client("python3", ["simple_mcp_server.py"]) as client:
        # 1. 创建草稿
        draft = await client.call_tool("create_draft", {
            "width": 1920,
            "height": 1080
        })

        # 2. 添加内容
        await client.call_tool("add_text", {
            "draft_id": draft["draft_id"],
            "text": "AI 生成视频",
            "start": 0,
            "end": 5
        })

        # 3. 保存
        await client.call_tool("save_draft", {
            "draft_id": draft["draft_id"]
        })

# 运行
asyncio.run(create_video())
```

---

## 🎯 学习路径

### 第 1 天: 基础
- ✅ 启动简化版 MCP 服务器
- ✅ 在 Claude Desktop 中配置
- ✅ 创建第一个草稿

### 第 2-3 天: 核心功能
- ✅ 添加视频、音频、文本
- ✅ 应用特效和动画
- ✅ 保存和导出草稿

### 第 4-7 天: 自动化
- ✅ 编写 Python 脚本调用 MCP
- ✅ 与 AI 工作流集成
- ✅ 批量生成视频

### 第 2 周+: 进阶
- ✅ 升级到企业版（如需要）
- ✅ 自定义 MCP 工具
- ✅ 集成到生产环境

---

## 📖 更多资源

### 简化版相关
- **代码**: `simple_mcp_server.py` (581 行)
- **日志**: `simple_mcp_server.log`
- **配置**: `simple_config.json` (可选)

### 企业版相关
- **文档**: [mcp_bridge/docs/实施指南.md](mcp_bridge/docs/实施指南.md)
- **部署**: [mcp_bridge/docs/deployment_guide.md](mcp_bridge/docs/deployment_guide.md)
- **对比**: [mcp_bridge/docs/MCP部署方案对比.md](mcp_bridge/docs/MCP部署方案对比.md)

### API 文档
- **API 示例**: [docs/API_USAGE_EXAMPLES.md](docs/API_USAGE_EXAMPLES.md)
- **架构文档**: [CLAUDE.md](CLAUDE.md)
- **快速入门**: [README.md](README.md)

### 视频教程
- MCP 基础概念（计划中）
- 简化版快速上手（计划中）
- 企业版部署指南（计划中）

---

## 🆘 获取帮助

**遇到问题？**

1. **查看日志**: `cat simple_mcp_server.log`
2. **测试 API**: `curl http://localhost:9000/health`
3. **GitHub Issues**: [提交问题](https://github.com/sun-guannan/CapCutAPI/issues)
4. **Email**: abelchrisnic@gmail.com

**常用调试命令**:
```bash
# 测试 CapCut API
curl http://localhost:9000/health

# 测试简化版 MCP（查看输出）
python3 simple_mcp_server.py --debug

# 查看进程
ps aux | grep simple_mcp_server

# 停止服务
pkill -f simple_mcp_server.py
```

---

## ✨ 快速命令参考

```bash
# 启动简化版 MCP
python3 simple_mcp_server.py

# 启动企业版 MCP
cd mcp_bridge && ./manage.sh start

# 查看简化版日志
tail -f simple_mcp_server.log

# 查看企业版日志
cd mcp_bridge && ./manage.sh logs

# 测试 CapCut API
curl http://localhost:9000/health

# 测试 MCP Bridge
curl http://localhost:8082/health
```

---

**开始您的 MCP 之旅吧！** 🚀

如果您是新手，强烈推荐从简化版开始，只需一个命令即可体验 MCP 的强大功能！

