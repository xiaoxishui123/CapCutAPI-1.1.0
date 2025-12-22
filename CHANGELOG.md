# Changelog

本文件记录 CapCutAPI 的重要更新（偏向用户可感知的功能变化）。

## v3.0.8 (2025-12-22)

- **新增：草稿封面 Draft Cover**
  - 新增接口：`POST /set_draft_cover`，支持用图片 URL 或视频抽帧来设置封面（在下一次 `save_draft` 导出时生效）
  - 导出阶段会写入 `draft_cover.jpg` 并更新草稿元数据字段（兼容不同剪映/CapCut 版本）
  - 相关文件：`draft_cover.py`、`save_draft_impl.py`、`capcut_server.py`

- **新增：云渲染 Render Service（任务提交/查询）**
  - 新增服务模块：`render_service.py`
  - 在服务端增加了渲染任务的提交与状态查询能力（用于自动化渲染流程）

- **新增：贴纸资源映射（resource_id → 图片URL）**
  - 新增：`sticker_assets.py`
  - 提供注册/查询贴纸映射的能力，解决“云渲染环境拿不到剪映内置贴纸素材文件”的问题

- **优化：下载链路与 ZIP 结构**
  - 优化下载、打包、路径处理与容错（包含端到端测试脚本）
  - 相关文件：`downloader.py`、`customize_zip.py`、`services/download_service.py`、`docs/API_USAGE_EXAMPLES.md`

- **文档与工具**
  - 新增/补齐 MCP 文档与 `mcp_server.py`（兼容上游启动方式）
  - 新增路由查看脚本：`list_routes.py`

## 历史版本

历史版本标签请以 Git 标签为准（如 `v3.0.7`、`v3.0.6` 等）。


