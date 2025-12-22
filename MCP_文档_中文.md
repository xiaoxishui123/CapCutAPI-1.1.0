# MCP 中文文档（stdio 模式）

本项目参考上游仓库 [VectCutAPI](https://github.com/sun-guannan/VectCutAPI/tree/main) 的使用方式，提供 `mcp_server.py` 作为 **MCP（Model Context Protocol）服务器入口**。

你可以把它理解成：
- **AI 客户端（Claude Desktop / Dify）** 通过 MCP “发命令”
- **`mcp_server.py`** 把命令翻译成 HTTP 请求
- **`capcut_server.py`（HTTP API）** 真正去创建草稿、加素材、保存草稿

---

## 1. 你需要准备什么？

- Python 3.9+（建议与项目一致）
- CapCutAPI 的 HTTP 服务已经在运行（默认 `http://localhost:9000`）

---

## 2. 安装 MCP 依赖（可选）

> 如果你已经装过 `mcp` / `aiohttp`，可以跳过。

```bash
pip install -r requirements-mcp.txt
```

---

## 3. 启动 MCP 服务器（stdio）

```bash
python3 mcp_server.py
```

### 常用环境变量

- `CAPCUT_API_URL`：CapCutAPI HTTP 服务地址（默认 `http://localhost:9000`）
- `CAPCUT_API_TIMEOUT`：超时时间（秒，默认 30）

示例（把 HTTP 服务地址指向远程服务器）：

```bash
export CAPCUT_API_URL="http://8.148.70.18:9000"
python3 mcp_server.py
```

---

## 4. MCP 工具列表（共 11 个）

`mcp_server.py` 固定提供 11 个工具（tool），与上游 README 中“Got 11 available tools”的预期保持一致：

- `create_draft`：创建草稿
- `add_video`：添加视频
- `add_audio`：添加音频
- `add_image`：添加图片
- `add_text`：添加文本
- `add_subtitle`：添加字幕
- `add_effect`：添加特效
- `add_sticker`：添加贴纸
- `add_video_keyframe`：添加关键帧
- `save_draft`：保存草稿（本地或 OSS，取决于 HTTP 服务配置）
- `health`：健康检查

> 注意：这些工具本质上就是调用同名的 HTTP API 端点（例如 `add_video` -> `POST /add_video`）。

---

## 5. AI 客户端配置示例（Claude Desktop / Dify）

不同客户端的配置文件位置不同，但核心思路一样：

```json
{
  "mcpServers": {
    "capcut-api": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "cwd": "/home/CapCutAPI-1.1.0",
      "env": {
        "CAPCUT_API_URL": "http://localhost:9000",
        "CAPCUT_API_TIMEOUT": "30"
      }
    }
  }
}
```

---

## 6. 常见问题（很重要）

### Q1：启动 MCP 后没反应？

这是正常的：stdio 模式会“等待 AI 客户端连接”，它不会像 Web 服务那样开一个网页端口。

### Q2：报错 `ModuleNotFoundError: No module named 'mcp'`

说明 MCP 依赖没装：

```bash
pip install -r requirements-mcp.txt
```

### Q3：报错 HTTP 连接失败 / 404

说明你的 CapCutAPI HTTP 服务没启动或地址不对：

- 先确认 `capcut_server.py` 在跑
- 再确认 `CAPCUT_API_URL` 是否正确

---

## 7. 你也可以用简化版/企业版

本项目还保留两个更“本地化”的方案：

- `python3 simple_mcp_server.py`：简化版，零配置，适合个人学习
- `mcp_bridge/`：企业版，带监控、缓存、路由等

`mcp_server.py` 只是为了兼容上游“官方文件名/启动方式”，不会影响你当前系统。


