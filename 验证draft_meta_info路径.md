# 验证 draft_meta_info.json 路径格式

## 📝 快速验证步骤

### 1. 创建新草稿并下载

```bash
# 假设创建了新草稿，ID为 test_draft_xxx
# 使用智能下载
```

访问：`http://8.148.70.18:9000/draft/preview/test_draft_xxx`  
点击：**🧠 智能下载** 按钮

### 2. 解压并检查

```bash
# Windows PowerShell
Expand-Archive test_draft_xxx.zip -DestinationPath .

# 或使用解压软件解压
```

### 3. 打开 draft_meta_info.json

使用文本编辑器打开，查找以下字段：

```json
{
    "draft_root_path": "",     // ✅ 应该是空字符串
    "draft_fold_path": "",     // ✅ 应该是空字符串
    "draft_name": "test_draft_xxx"
}
```

---

## ✅ 正确的格式

### draft_meta_info.json
```json
{
    "cloud_package_completed_time": "",
    "draft_cloud_capcut_purchase_info": "",
    ...
    "draft_root_path": "",  // ✅ 空字符串，不是绝对路径
    "draft_fold_path": "",  // ✅ 空字符串，不是绝对路径
    "draft_name": "草稿ID",
    ...
}
```

### draft_info.json（素材路径）
```json
{
    "materials": {
        "audios": [
            {
                "path": "assets/audio/audio_xxx.mp3",  // ✅ 相对路径
                ...
            }
        ],
        "videos": [
            {
                "path": "assets/video/video_xxx.mp4",  // ✅ 相对路径
                ...
            }
        ]
    }
}
```

---

## ❌ 错误的格式（旧版本）

### draft_meta_info.json（修复前）
```json
{
    "draft_root_path": "F:\\jianyin\\cgwz\\JianyingPro Drafts",  // ❌ 绝对路径
    "draft_fold_path": "F:\\jianyin\\cgwz\\JianyingPro Drafts\\dfd_cat_xxx",  // ❌ 绝对路径
    ...
}
```

### draft_info.json（修复前）
```json
{
    "materials": {
        "audios": [
            {
                "path": "F:\\jianyin\\cgwz\\JianyingPro Drafts\\dfd_cat_xxx\\assets\\audio\\xxx.mp3",  // ❌ 绝对路径
                ...
            }
        ]
    }
}
```

---

## 🔍 使用命令行验证

### Windows PowerShell

```powershell
# 解压草稿
Expand-Archive test_draft_xxx.zip -DestinationPath test_draft_xxx

# 查看 draft_meta_info.json 中的路径字段
Get-Content test_draft_xxx\draft_meta_info.json | Select-String "draft_root_path|draft_fold_path"

# 期望输出：
# "draft_root_path":""
# "draft_fold_path":""
```

### Linux/Mac

```bash
# 解压草稿
unzip test_draft_xxx.zip -d test_draft_xxx

# 查看路径字段
grep -E "draft_root_path|draft_fold_path" test_draft_xxx/draft_meta_info.json

# 期望输出：
# "draft_root_path":""
# "draft_fold_path":""
```

---

## 📊 对比表格

| 字段 | 修复前 ❌ | 修复后 ✅ |
|------|----------|----------|
| `draft_root_path` | `F:\jianyin\cgwz\JianyingPro Drafts` | `""` (空字符串) |
| `draft_fold_path` | `F:\jianyin\cgwz\JianyingPro Drafts\dfd_cat_xxx` | `""` (空字符串) |
| `materials.audios[].path` | `F:\jianyin\...\assets\audio\xxx.mp3` | `assets/audio/xxx.mp3` |
| `materials.videos[].path` | `F:\jianyin\...\assets\video\xxx.mp4` | `assets/video/xxx.mp4` |

---

## 🎯 为什么使用空字符串？

### 原理说明

1. **空字符串 = 相对路径模式**
   - 剪映看到空的 `draft_root_path`，会使用草稿所在目录作为根目录
   - 素材路径 `assets/audio/xxx.mp3` 会被解析为相对于草稿目录的路径

2. **好处**：
   - ✅ 草稿可以放在任意位置
   - ✅ 剪映自动找到正确的素材
   - ✅ 跨平台兼容（Windows/Mac/Linux）
   - ✅ 不依赖特定的目录结构

3. **实际路径解析**：
   ```
   草稿位置：F:\jianyin\cgwz\JianyingPro Drafts\test_draft_xxx\
   
   draft_root_path: "" (空)
   ↓
   剪映解析为：F:\jianyin\cgwz\JianyingPro Drafts\test_draft_xxx\
   
   素材路径: assets\audio\xxx.mp3
   ↓
   完整路径：F:\jianyin\cgwz\JianyingPro Drafts\test_draft_xxx\assets\audio\xxx.mp3
   ↓
   结果：✅ 找到素材
   ```

---

## ⚠️ 注意事项

### 1. 必须是新草稿

旧草稿（修复前生成的）不会自动更新，必须创建新草稿。

### 2. 文件结构必须完整

解压后的文件夹结构必须是：
```
test_draft_xxx/
├── assets/
│   ├── audio/
│   ├── image/
│   └── video/
├── draft_content/
├── draft_info.json
└── draft_meta_info.json
```

### 3. 不要手动修改

不要手动修改 draft_meta_info.json，使用智能下载自动生成即可。

---

## 📞 验证失败？

如果验证发现仍是绝对路径，请检查：

1. **草稿创建时间**：
   - 必须是 2025-11-04 21:22 之后创建的
   - 旧草稿不会自动更新

2. **下载方式**：
   - 必须使用"智能下载"按钮
   - 不要使用其他下载方式

3. **服务版本**：
   - 检查服务是否已重启
   - 版本应该是 v1.3.4

4. **提供信息**：
   - 草稿ID
   - draft_meta_info.json 的完整内容截图
   - 草稿创建时间

---

**文档版本**: v1.0  
**更新时间**: 2025-11-04 21:30  
**适用版本**: CapCutAPI v1.3.4及以后

