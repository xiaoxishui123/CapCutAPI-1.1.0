[根目录](../CLAUDE.md) > **static**

---

# static 静态资源模块文档

> 最后更新时间：2025-11-11 22:43:46

## 变更记录 (Changelog)

### 2025-11-11 22:43:46
- 初始化 static 静态资源模块文档
- 完成模块架构和功能分析

---

## 模块职责

`static` 模块是 CapCutAPI 项目的静态资源目录，包含独立的 HTML 工具页面、辅助脚本和示例草稿文件。这些资源主要用于本地开发、调试和草稿管理。

**核心功能**：
- 草稿批量下载管理器
- Windows 平台下载辅助脚本
- 示例草稿文件

**特点**：
- 独立运行的 HTML 页面（无需 Flask 服务器）
- 跨平台兼容的下载工具
- 可直接浏览器打开使用

---

## 文件清单

### 1. 下载管理器
**文件**: `download_manager.html`

**功能**: 草稿批量下载和管理工具

**特性**:
- 批量选择和下载草稿
- 下载进度显示
- 自动保存到本地目录
- 支持断点续传
- 下载历史记录

**使用方法**:
```bash
# 直接在浏览器中打开
open static/download_manager.html

# 或通过 HTTP 访问
curl http://localhost:9000/static/download_manager.html
```

**技术实现**:
- 纯前端实现（HTML + JavaScript）
- 使用 Fetch API 调用后端 API
- LocalStorage 保存下载历史

---

### 2. Windows 下载助手
**文件**: `download_helper.bat`

**功能**: Windows 平台草稿下载批处理脚本

**特性**:
- 一键下载草稿到本地
- 自动解压草稿文件
- 放置到剪映草稿目录
- 错误处理和日志记录

**使用方法**:
```cmd
REM 编辑脚本，设置草稿 ID
download_helper.bat

REM 或带参数运行
download_helper.bat dfd_cat_123456_abc
```

**脚本结构**:
```batch
@echo off
REM 设置草稿 ID
SET DRAFT_ID=dfd_cat_123456_abc

REM 下载草稿
curl -o draft.zip "http://localhost:9000/api/drafts/download/%DRAFT_ID%"

REM 解压到剪映目录
unzip draft.zip -d "C:\Users\%USERNAME%\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"

echo 下载完成！
pause
```

---

### 3. 示例草稿文件
**文件**:
- `dfd_cat_1761981498_f549b6e1.zip` - 示例草稿（原始版）
- `dfd_cat_1761981498_f549b6e1_fixed.zip` - 示例草稿（修复版）

**用途**:
- 测试草稿下载功能
- 演示草稿文件结构
- 用于开发调试

**区别**:
- **原始版**: 直接从 API 生成的草稿
- **修复版**: 经过路径修复和优化的草稿（跨平台兼容）

---

## 使用场景

### 场景 1: 批量下载草稿
1. 打开 `download_manager.html`
2. 选择需要下载的草稿
3. 点击"批量下载"按钮
4. 等待下载完成

### 场景 2: Windows 一键导入
1. 复制 `download_helper.bat` 到桌面
2. 编辑脚本，设置草稿 ID
3. 双击运行脚本
4. 草稿自动导入剪映

### 场景 3: 开发测试
1. 使用示例草稿文件测试解压功能
2. 验证草稿文件结构
3. 测试跨平台路径兼容性

---

## 对外接口

### 下载管理器 API 调用
`download_manager.html` 调用以下后端 API：

```javascript
// 获取草稿列表
fetch('/api/drafts/list')
  .then(res => res.json())
  .then(data => {
    // 显示草稿列表
  });

// 下载单个草稿
fetch(`/api/drafts/download/${draft_id}`)
  .then(res => res.blob())
  .then(blob => {
    // 保存文件
  });

// 批量下载
fetch('/api/drafts/batch-download', {
  method: 'POST',
  body: JSON.stringify({
    draft_ids: ['id1', 'id2', 'id3']
  })
});
```

---

## 常见问题 (FAQ)

### Q1: download_manager.html 无法连接到服务器？
**解决方案**:
1. 确保 CapCutAPI 服务正在运行：
   ```bash
   ./service_manager.sh status
   ```
2. 检查端口配置（默认 9000）
3. 修改 HTML 中的 API 地址：
   ```javascript
   const API_BASE = 'http://localhost:9000';
   ```

### Q2: download_helper.bat 提示"找不到命令"？
**解决方案**:
1. 确保安装了 `curl` 和 `unzip`：
   ```cmd
   curl --version
   unzip --version
   ```
2. 使用 PowerShell 版本：
   ```powershell
   Invoke-WebRequest -Uri "..." -OutFile "draft.zip"
   Expand-Archive -Path "draft.zip" -DestinationPath "..."
   ```

### Q3: 示例草稿文件无法导入？
**解决方案**:
1. 使用 `_fixed.zip` 版本（已修复路径问题）
2. 检查解压路径是否正确
3. 确保剪映已安装并初始化

### Q4: 如何自定义下载管理器？
**修改步骤**:
1. 编辑 `download_manager.html`
2. 修改样式（CSS）或功能（JavaScript）
3. 在浏览器中刷新查看效果

---

## 技术细节

### 文件大小
- `download_manager.html`: ~15KB
- `download_helper.bat`: ~2KB
- `dfd_cat_1761981498_f549b6e1.zip`: ~500KB
- `dfd_cat_1761981498_f549b6e1_fixed.zip`: ~500KB

### 浏览器兼容性
`download_manager.html` 兼容：
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### 下载速度优化
- 使用流式下载（Streams API）
- 支持断点续传（Range 请求）
- 本地缓存下载历史

---

## 相关模块
- [根目录](../CLAUDE.md) - 项目总览
- [templates](../templates/CLAUDE.md) - Flask 模板目录
- [capcut_server.py](../capcut_server.py) - 后端 API 服务

---

**提示**: static 目录的文件可以独立使用，不依赖 Flask 服务器。适合快速调试和本地工具开发。
