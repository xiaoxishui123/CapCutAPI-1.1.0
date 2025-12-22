#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CapCutAPI - Official-style MCP Server (stdio)

Why this file exists
- The upstream VectCutAPI README describes starting MCP via: `python mcp_server.py`
- This project previously only had `simple_mcp_server.py` (lightweight) and `mcp_bridge/` (enterprise).
- To reduce migration friction, we provide a compatible `mcp_server.py` entrypoint that exposes a small,
  stable toolset and forwards calls to the existing HTTP API.

How it works (in plain words)
- MCP client (e.g., Claude Desktop / Dify) talks to this process over stdio
- This process calls CapCutAPI HTTP endpoints (default: http://localhost:9000)
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("capcut_mcp_server")


@dataclass
class ServerConfig:
    """MCP server config.

    - capcut_api_url: base URL of CapCutAPI HTTP server
    """

    capcut_api_url: str = "http://localhost:9000"
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "ServerConfig":
        url = os.getenv("CAPCUT_API_URL") or os.getenv("CAPCUTAPI_URL") or cls.capcut_api_url
        timeout = int(os.getenv("CAPCUT_API_TIMEOUT", str(cls.timeout)))
        return cls(capcut_api_url=url, timeout=timeout)


class CapCutAPIClient:
    """Async HTTP client to call the existing CapCutAPI server."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "CapCutAPIClient":
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout))
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    async def call_api(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self._session:
            raise RuntimeError("HTTP session not initialized")

        endpoint = endpoint.lstrip("/")
        url = f"{self.config.capcut_api_url.rstrip('/')}/{endpoint}"

        async with self._session.request(method.upper(), url, json=data) as resp:
            text = await resp.text()
            # Try JSON first (CapCutAPI uses JSON responses for API calls)
            try:
                payload = json.loads(text) if text else {}
            except Exception:
                payload = {"raw": text}

            if resp.status >= 400:
                raise RuntimeError(f"HTTP {resp.status}: {payload}")
            return payload


class CapCutMCPServer:
    """Expose a small, stable set of MCP tools (11 tools) forwarding to HTTP endpoints."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.server = Server("capcut-api")
        self.api_client = CapCutAPIClient(config)
        self._register_tools()

    def _register_tools(self) -> None:
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            # Keep exactly 11 tools to match upstream expectations.
            return [
                Tool(
                    name="create_draft",
                    description="Create a new draft project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {"type": "string", "description": "Optional custom draft id"},
                            "name": {"type": "string", "description": "Optional draft name"},
                            "width": {"type": "integer", "description": "Canvas width", "default": 1080},
                            "height": {"type": "integer", "description": "Canvas height", "default": 1920},
                        },
                    },
                ),
                Tool(
                    name="add_video",
                    description="Add a video clip into the draft timeline",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {"type": "string"},
                            "video_url": {"type": "string"},
                            "start": {"type": "number", "default": 0},
                            "end": {"type": "number"},
                            "track_name": {"type": "string", "default": "video_main"},
                            "volume": {"type": "number", "default": 1.0},
                        },
                        "required": ["draft_id", "video_url"],
                    },
                ),
                Tool(
                    name="add_audio",
                    description="Add an audio clip into the draft timeline",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {"type": "string"},
                            "audio_url": {"type": "string"},
                            "start": {"type": "number", "default": 0},
                            "end": {"type": "number"},
                            "volume": {"type": "number", "default": 1.0},
                            "track_name": {"type": "string", "default": "audio_main"},
                        },
                        "required": ["draft_id", "audio_url"],
                    },
                ),
                Tool(
                    name="add_image",
                    description="Add an image into the draft timeline",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {"type": "string"},
                            "image_url": {"type": "string"},
                            "start": {"type": "number", "default": 0},
                            "end": {"type": "number", "default": 3},
                            "track_name": {"type": "string", "default": "main"},
                            "scale_x": {"type": "number", "default": 1.0},
                            "scale_y": {"type": "number", "default": 1.0},
                        },
                        "required": ["draft_id", "image_url"],
                    },
                ),
                Tool(
                    name="add_text",
                    description="Add a text segment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {"type": "string"},
                            "text": {"type": "string"},
                            "start": {"type": "number", "default": 0},
                            "end": {"type": "number", "default": 3},
                            "font_size": {"type": "number", "default": 30.0},
                            "font_color": {"type": "string", "default": "#FFFFFF"},
                        },
                        "required": ["draft_id", "text"],
                    },
                ),
                Tool(
                    name="add_subtitle",
                    description="Add subtitle text",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {"type": "string"},
                            "subtitle_text": {"type": "string"},
                            "start": {"type": "number"},
                            "end": {"type": "number"},
                            "font_size": {"type": "number", "default": 24.0},
                            "font_color": {"type": "string", "default": "#FFFFFF"},
                        },
                        "required": ["draft_id", "subtitle_text", "start", "end"],
                    },
                ),
                Tool(
                    name="add_effect",
                    description="Add a visual effect",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {"type": "string"},
                            "effect_type": {"type": "string", "description": "Effect type/name"},
                            "start": {"type": "number", "default": 0},
                            "end": {"type": "number", "default": 3},
                        },
                        "required": ["draft_id", "effect_type"],
                    },
                ),
                Tool(
                    name="add_sticker",
                    description="Add a sticker",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {"type": "string"},
                            "resource_id": {"type": "string", "description": "Sticker resource id"},
                            "start": {"type": "number", "default": 0},
                            "end": {"type": "number", "default": 3},
                        },
                        "required": ["draft_id", "resource_id"],
                    },
                ),
                Tool(
                    name="add_video_keyframe",
                    description="Add keyframes to a video track/material",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {"type": "string"},
                            "track_name": {"type": "string", "default": "video_main"},
                            "property_types": {"type": "array", "items": {"type": "string"}},
                            "times": {"type": "array", "items": {"type": "number"}},
                            "values": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["draft_id", "track_name", "property_types", "times", "values"],
                    },
                ),
                Tool(
                    name="save_draft",
                    description="Save/export draft (local or OSS based on server config)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "draft_id": {"type": "string"},
                            "draft_folder": {"type": "string", "description": "Optional client draft folder"},
                            "client_os": {"type": "string", "enum": ["windows", "mac", "linux"], "default": "windows"},
                        },
                        "required": ["draft_id"],
                    },
                ),
                Tool(
                    name="health",
                    description="Health check for CapCutAPI HTTP server",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                logger.info("MCP tool call: %s args=%s", name, arguments)
                async with self.api_client:
                    result = await self._dispatch(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            except Exception as e:
                logger.exception("Tool call failed: %s", name)
                return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, ensure_ascii=False, indent=2))]

    async def _dispatch(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "health":
            return await self.api_client.call_api("health", method="GET")
        if name in {"create_draft", "add_video", "add_audio", "add_image", "add_text", "add_subtitle", "add_effect", "add_sticker", "add_video_keyframe", "save_draft"}:
            method = "POST"
            return await self.api_client.call_api(name, method=method, data=arguments)
        raise ValueError(f"Unknown tool: {name}")

    async def run(self) -> None:
        logger.info("Starting MCP stdio server, forwarding to %s", self.config.capcut_api_url)
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="capcut-api",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


async def main() -> None:
    config = ServerConfig.from_env()
    server = CapCutMCPServer(config)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())


