# CapCutAPI 快速使用指南

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


---

## 🔧 **常见问题快速解决**

### ❌ 问题：剪映显示"素材丢失"
**原因**: 视频时长为0  
**解决**: 确保服务器已安装ffmpeg，检查`/usr/bin/ffprobe`是否存在

### ❌ 问题：字体不支持
**解决**: 使用`curl http://服务器:9000/get_font_types`查看支持的字体

### ❌ 问题：网络下载失败
**解决**: 检查服务器网络连接，确保能访问素材URL

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

### 客户端
- [ ] 草稿下载完整 (包含assets文件夹)
- [ ] 放置在正确目录 (`F:\jianyin\cgwz\JianyingPro Drafts\`)
- [ ] 文件权限正常

### 验证成功标志
- [ ] draft_info.json中duration > 0
- [ ] assets文件夹包含所有素材文件
- [ ] 剪映能正常识别并预览素材

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

---

**⚡ 记住**: Windows 客户端路径在 JSON 中需使用 `\\` 转义；Linux 使用 `/`。生成下载链接时也可传 `client_os` 与 `draft_folder` 来得到对应客户端的派生 zip。

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