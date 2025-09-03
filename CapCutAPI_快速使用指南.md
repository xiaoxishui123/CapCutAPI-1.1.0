# CapCutAPI 快速使用指南

## 🎉 **最新功能更新** (NEW!)

### 🚀 全新草稿管理中心
- **草稿管理仪表板**: `http://服务器IP:9000/api/drafts/dashboard`
  - 🎨 现代化界面，暗色渐变主题
  - 📊 实时统计：总草稿、缓存草稿、本地草稿、测试草稿
  - 🔍 智能搜索和批量操作
  - 📱 完全响应式设计

### 📋 新增API端点
- **草稿列表API**: `GET /api/drafts/list` - 获取所有可用草稿
- **批量下载API**: `POST /api/drafts/batch-download` - 批量下载多个草稿

### 🎬 增强的预览和下载功能
- **草稿预览**: `/draft/preview/<draft_id>` - 沉浸式预览体验
- **智能下载**: `/draft/downloader` - 优化的下载流程
- **主页增强**: `/` - 新增管理功能快速入口

---

## 🚀 **标准工作流程**

### 1. 创建草稿
```bash
curl -X POST http://8.148.70.18:9000/create_draft \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "项目名称",
    "width": 1080,
    "height": 1920
  }'
```

### 2. 添加素材

#### 添加视频
```bash
curl -X POST http://服务器IP:9000/add_video \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "项目名称",
    "video_url": "视频URL",
    "start": 0,
    "end": 10,
    "track_name": "main_video"
  }'
```

#### 添加文本
```bash
curl -X POST http://服务器IP:9000/add_text \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "项目名称",
    "text": "文本内容",
    "start": 1,
    "end": 5,
    "font": "ZY_Courage",
    "font_color": "#FFFFFF",
    "font_size": 8.0
  }'
```

#### 添加图片
```bash
curl -X POST http://服务器IP:9000/add_image \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "项目名称",
    "image_url": "图片URL",
    "start": 5,
    "end": 8,
    "scale_x": 0.5,
    "scale_y": 0.5
  }'
```

### 3. 保存草稿（本地/OSS）
- 本地保存：传 `draft_folder` 为客户端本地草稿根路径（Windows 使用 `\\\\` 转义，Linux 使用 `/`）。
- OSS 模式：`config.json` 中 `is_upload_draft=true` 时，后台会压缩上传到 OSS。
```bash
curl -X POST http://服务器IP:9000/save_draft \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "项目名称",
    "draft_folder": "F:\\\\jianyin\\\\cgwz\\\\JianyingPro Drafts"
  }'
```

### 4. 生成下载链接（推荐）
- 若已上传到 OSS：
```bash
# 标准直链（存在则直接返回）
curl -s -H 'Content-Type: application/json' \
  -d '{"draft_id":"项目名称"}' \
  http://服务器IP:9000/generate_draft_url
```
- 按客户端定制 zip（改写 draft_info.json 中路径并缓存）：
```bash
# 传入 client_os + draft_folder，返回派生 zip 的签名直链
curl -s -H 'Content-Type: application/json' \
  -d '{"draft_id":"项目名称","client_os":"windows","draft_folder":"F:/jianyin/cgwz/JianyingPro Drafts"}' \
  http://服务器IP:9000/generate_draft_url
```
- 未上传时一键触发上传：
```bash
curl -s -H 'Content-Type: application/json' \
  -d '{"draft_id":"项目名称","force_save":true}' \
  'http://服务器IP:9000/generate_draft_url?force_save=true'
```
- 浏览器下载页（含 OS 选择、自定义根路径 base 参数）：
```
http://服务器IP:9000/draft/downloader?draft_id=项目名称&os=windows&base=F:/MyDrafts
```

### 5. 🆕 使用草稿管理中心（推荐）
#### 5.1 访问管理仪表板
```
http://服务器IP:9000/api/drafts/dashboard
```
- **功能特色**：
  - 📊 草稿统计概览
  - 🔍 搜索和筛选
  - 📋 批量选择操作
  - 🎬 一键预览和下载

#### 5.2 获取草稿列表（API）
```bash
curl -s http://服务器IP:9000/api/drafts/list | jq '.'
```
**返回格式**：
```json
{
  "success": true,
  "total": 5,
  "drafts": [
    {
      "draft_id": "项目名称",
      "source": "cache",
      "status": "已缓存",
      "materials_count": 8,
      "last_modified": "2025-01-21T10:30:00",
      "size_mb": 15.2
    }
  ]
}
```

#### 5.3 批量下载草稿（API）
```bash
curl -X POST http://服务器IP:9000/api/drafts/batch-download \
  -H 'Content-Type: application/json' \
  -d '{
    "draft_ids": ["项目1", "项目2", "项目3"],
    "client_os": "windows",
    "draft_folder": "F:/MyDrafts"
  }'
```

#### 5.4 增强的预览功能
```
http://服务器IP:9000/draft/preview/项目名称
```
- **新特性**：
  - 🎨 暗色专业主题
  - 📊 交互式时间轴
  - 📱 响应式设计
  - ⚡ 流畅动画效果


---

## 🔧 **常见问题快速解决**

### ❌ 问题：剪映显示"素材丢失"
**原因**: 视频时长为0  
**解决**: 确保服务器已安装ffmpeg，检查`/usr/bin/ffprobe`是否存在

### ❌ 问题：字体不支持
**解决**: 使用`curl http://服务器:9000/get_font_types`查看支持的字体

### ❌ 问题：网络下载失败
**解决**: 检查服务器网络连接，确保能访问素材URL

### 🆕 新功能相关问题

#### ❌ 问题：管理仪表板404错误
**原因**: 新API端点未正确部署  
**解决**: 
```bash
# 重启服务确保新功能加载
cd /home/CapCutAPI-1.1.0
./service_manager.sh restart

# 检查服务状态
./service_manager.sh status

# 测试API端点
curl -s http://localhost:9000/api/drafts/list
```

#### ❌ 问题：重复函数定义错误
**原因**: `AssertionError: View function mapping is overwriting an existing endpoint function`  
**解决**: 
```bash
# 检查代码语法
python3 -m py_compile capcut_server.py

# 如果有重复定义，需要清理重复的函数
```

#### ❌ 问题：端口占用
**原因**: `Address already in use` 或 `Port 9000 is in use`  
**解决**:
```bash
# 查找占用端口的进程
lsof -i :9000

# 停止现有服务
./service_manager.sh stop

# 或强制杀死进程
sudo killall python3

# 重新启动
./service_manager.sh start
```

---

## 📋 **重要参数说明**

### 时间参数
- `start`, `end`: 素材在时间轴上的位置（秒）
- `duration`: 自动计算，无需手动设置

### 路径参数
- **Linux**: 使用正斜杠 `/`
- **Windows**: API JSON 中使用 `\\\\` 转义；下载页支持 `os` 与 `base` 参数定制展示与派生 zip

### 坐标系统
- **原点**: 画布中心 (0, 0)
- **X轴**: 左负右正
- **Y轴**: 上正下负
- **取值范围**: -1.0 到 1.0

---

## ✅ **检查清单**

### 服务器端
- [ ] ffmpeg已安装 (`/usr/bin/ffprobe -version`)
- [ ] 网络连接正常
- [ ] 服务器运行中 (`ps aux | grep capcut`)
- [ ] 🆕 新API端点可访问 (`curl -s http://localhost:9000/api/drafts/list`)

### 客户端
- [ ] 草稿下载完整 (包含assets文件夹)
- [ ] 放置在正确目录 (`F:\jianyin\cgwz\JianyingPro Drafts\`)
- [ ] 文件权限正常

### 🆕 新功能验证
- [ ] 管理仪表板正常访问 (`http://服务器IP:9000/api/drafts/dashboard`)
- [ ] 草稿列表API返回数据 (`GET /api/drafts/list`)
- [ ] 批量下载API响应正常 (`POST /api/drafts/batch-download`)
- [ ] 预览页面样式正确 (`/draft/preview/<draft_id>`)
- [ ] 主页新按钮功能正常 (`📊 草稿管理` 和 `🎬 预览演示`)

### 验证成功标志
- [ ] draft_info.json中duration > 0
- [ ] assets文件夹包含所有素材文件
- [ ] 剪映能正常识别并预览素材
- [ ] 🆕 管理仪表板显示草稿统计
- [ ] 🆕 预览页面交互式时间轴正常工作

---

## 🆘 **紧急处理**

### 如果剪映仍显示素材丢失
1. 检查duration字段：`grep duration draft_info.json`
2. 如果为0，手动修复：运行自动修复脚本
3. 重新下载最新版本草稿
4. 确认文件夹结构完整

### 快速测试命令
```bash
# 创建简单测试项目
curl -X POST http://服务器:9000/create_draft \
  -d '{"draft_id":"test","width":1080,"height":1920}' \
  -H "Content-Type: application/json" && \
curl -X POST http://服务器:9000/add_video \
  -d '{"draft_id":"test","video_url":"https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4","start":0,"end":5}' \
  -H "Content-Type: application/json" && \
curl -X POST http://服务器:9000/save_draft \
  -d '{"draft_id":"test","draft_folder":"F:\\\\jianyin\\\\cgwz\\\\JianyingPro Drafts"}' \
  -H "Content-Type: application/json"
```

### 🆕 新功能快速测试
```bash
# 测试草稿列表API
curl -s http://服务器IP:9000/api/drafts/list | jq '.total'

# 测试批量下载API
curl -X POST http://服务器IP:9000/api/drafts/batch-download \
  -H 'Content-Type: application/json' \
  -d '{"draft_ids":["test"],"client_os":"windows"}' | jq '.success'

# 检查管理仪表板（浏览器访问）
echo "访问: http://服务器IP:9000/api/drafts/dashboard"

# 检查预览页面（浏览器访问）  
echo "访问: http://服务器IP:9000/draft/preview/test"
```

---

**⚡ 记住**: Windows 客户端路径在 JSON 中需使用 `\\` 转义；Linux 使用 `/`。生成下载链接时也可传 `client_os` 与 `draft_folder` 来得到对应客户端的派生 zip。

---

## 🎉 **新功能推荐工作流程**

### 方案一：使用管理仪表板（推荐给非技术用户）
1. 访问管理仪表板：`http://服务器IP:9000/api/drafts/dashboard`
2. 浏览所有草稿，查看统计信息
3. 使用搜索功能快速定位目标草稿
4. 点击"预览"查看草稿详情，或点击"下载"获取文件
5. 使用批量操作功能一次性下载多个草稿

### 方案二：API集成（推荐给开发者）
1. 调用 `GET /api/drafts/list` 获取草稿列表
2. 根据需要筛选草稿ID
3. 调用 `POST /api/drafts/batch-download` 批量生成下载链接
4. 使用返回的URL进行下载

### 💡 最佳实践
- **团队协作**: 使用管理仪表板进行草稿概览和分享
- **自动化集成**: 使用新API端点构建自动化工作流
- **移动端访问**: 管理仪表板完美支持手机和平板访问
- **批量处理**: 利用批量下载功能提升工作效率

---

## ☁️ 自动镜像到 OSS（推荐，无 403 风险）

当外部文件服务器限制直连（容易 403）时，使用本接口把素材直接上传到后端，由后端写入阿里云 OSS，并返回签名可访问链接。

- 接口：`POST /upload_to_oss`
- 功能：接收二进制文件或 Base64 数据，写入 OSS，返回签名 URL
- 参数：
  - `prefix`：可选，OSS 目录前缀，例如 `capcut/images`
  - `file`：multipart 表单文件（二选一）
  - `data_base64`：JSON Base64 文件数据（二选一），可配合 `filename`

### 方式一：表单上传（multipart/form-data）
```bash
curl -X POST http://服务器IP:9000/upload_to_oss \
  -F 'prefix=capcut/images' \
  -F 'file=@/path/to/your.png'
```
返回示例：
```json
{"success":true,"object":"capcut/images/xxxx.png","oss_url":"https://<bucket>.oss-<region>.aliyuncs.com/capcut/images/xxxx.png?..."}
```

### 方式二：JSON（Base64）上传
```bash
curl -X POST http://服务器IP:9000/upload_to_oss \
  -H 'Content-Type: application/json' \
  -d '{
    "filename": "image.png",
    "data_base64": "<BASE64>",
    "prefix": "capcut/images"
  }'
```

### 与工作流集成建议（以 Dify 为例）
- 若上游产出的是文件（如豆包文生图工具的 `files`）：
  1) 新增 HTTP 节点 → `POST /upload_to_oss`，以 multipart 方式转发 `file`；
  2) 读取返回的 `oss_url`，传给 `add_image` 的 `image_url`。
- 若上游只给了远程 URL 且易触发 403：
  - 改为先把二进制读到客户端，再走 `upload_to_oss`；或在上游阶段就改为由上游直接传文件给此接口。

### 配置说明
- `config.json` 中已配置：
  - `oss_config.region`: 例如 `cn-wuhan-lr`
  - `oss_config.endpoint`: 例如 `oss-cn-wuhan-lr.aliyuncs.com`（无需手动写协议）
  - `is_upload_draft` 与草稿上传逻辑互不影响；本接口独立使用。

> 提示：`/mirror_to_oss` 依赖从外部下载原文件，若外部 403 限制严格，推荐直接使用 `/upload_to_oss`，流程更稳定。