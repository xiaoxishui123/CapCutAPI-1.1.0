# CapCutAPI 快速使用指南

## 🚀 **标准工作流程**

### 1. 创建草稿
```bash
curl -X POST http://服务器IP:9000/create_draft \
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

### 3. 保存草稿 ⚠️ **关键步骤**
```bash
curl -X POST http://服务器IP:9000/save_draft \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "项目名称",
    "draft_folder": "F:\\\\jianyin\\\\cgwz\\\\JianyingPro Drafts"
  }'
```

### 4. 下载到Windows
```bash
# 在服务器上压缩
tar -czf 项目名称.tar.gz 项目名称/

# 下载到Windows
scp 用户@服务器:/路径/项目名称.tar.gz ./

# 解压到剪映目录
# 目标位置：F:\jianyin\cgwz\JianyingPro Drafts\项目名称\
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
- **Linux服务器**: 使用正斜杠 `/`
- **Windows剪映**: 必须使用`\\\\`转义格式

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

**⚡ 记住**: 保存草稿时必须使用Windows路径格式`F:\\\\jianyin\\\\cgwz\\\\JianyingPro Drafts`！ 