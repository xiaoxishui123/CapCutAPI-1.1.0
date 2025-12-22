# MCP Documentation (stdio)

This project provides an **official-style** MCP entrypoint `mcp_server.py` to stay compatible with the upstream usage described in the [VectCutAPI repository](https://github.com/sun-guannan/VectCutAPI/tree/main).

Think of it like this:
- Your **AI client** (Claude Desktop / Dify) talks to MCP over **stdio**
- `mcp_server.py` converts MCP tool calls into HTTP requests
- `capcut_server.py` (HTTP API) performs the real draft editing operations

---

## 1. Requirements

- Python 3.9+
- CapCutAPI HTTP server running (default: `http://localhost:9000`)

---

## 2. Install MCP deps (optional)

```bash
pip install -r requirements-mcp.txt
```

---

## 3. Run MCP server (stdio)

```bash
python3 mcp_server.py
```

### Environment variables

- `CAPCUT_API_URL`: CapCutAPI HTTP base URL (default: `http://localhost:9000`)
- `CAPCUT_API_TIMEOUT`: timeout in seconds (default: `30`)

Example:

```bash
export CAPCUT_API_URL="http://8.148.70.18:9000"
python3 mcp_server.py
```

---

## 4. Tool list (11 tools)

`mcp_server.py` intentionally exposes **exactly 11 tools** (to match upstream expectations):

- `create_draft`
- `add_video`
- `add_audio`
- `add_image`
- `add_text`
- `add_subtitle`
- `add_effect`
- `add_sticker`
- `add_video_keyframe`
- `save_draft`
- `health`

Each tool forwards to the same-named HTTP API endpoint (e.g. `add_video` -> `POST /add_video`).

---

## 5. Client config example (Claude Desktop / Dify)

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

## 6. Troubleshooting

### `ModuleNotFoundError: No module named 'mcp'`

Install MCP deps:

```bash
pip install -r requirements-mcp.txt
```

### HTTP connection errors

- Ensure `capcut_server.py` is running
- Ensure `CAPCUT_API_URL` is correct

---

## 7. Other MCP options in this repo

- `simple_mcp_server.py`: lightweight, no extra infra
- `mcp_bridge/`: enterprise-grade bridge (monitoring/cache/routing)

`mcp_server.py` is added mainly for upstream compatibility and does not replace the other options.


