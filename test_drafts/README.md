# 剪映路径识别测试包

## 📋 测试目的

验证剪映到底支持哪种路径配置方式，以确定素材识别不到的根本原因。

## 📦 测试版本说明

已创建3个不同配置的草稿版本：

### 版本A: 相对路径 + 空root_path
- **文件名**: `dfd_cat_1762313389_ae978ee4__version_A_relative_empty.zip`
- **配置**:
  ```json
  // draft_meta_info.json
  "draft_root_path": "",
  "draft_fold_path": ""
  
  // draft_info.json中的素材路径
  "path": "assets\\audio\\xxx.mp3"
  ```
- **理论**: 剪映应该能通过相对路径自动找到素材

### 版本B: 相对路径 + 设置root_path
- **文件名**: `dfd_cat_1762313389_ae978ee4__version_B_relative_with_root.zip`
- **配置**:
  ```json
  // draft_meta_info.json
  "draft_root_path": "F:\\jianyin\\cgwz\\JianyingPro Drafts",
  "draft_fold_path": "F:\\jianyin\\cgwz\\JianyingPro Drafts\\dfd_cat_1762313389_ae978ee4"
  
  // draft_info.json中的素材路径
  "path": "assets\\audio\\xxx.mp3"
  ```
- **理论**: 剪映会基于root_path + 相对路径来定位素材

### 版本C: 绝对路径 + 设置root_path
- **文件名**: `dfd_cat_1762313389_ae978ee4__version_C_absolute.zip`
- **配置**:
  ```json
  // draft_meta_info.json
  "draft_root_path": "F:\\jianyin\\cgwz\\JianyingPro Drafts",
  "draft_fold_path": "F:\\jianyin\\cgwz\\JianyingPro Drafts\\dfd_cat_1762313389_ae978ee4"
  
  // draft_info.json中的素材路径
  "path": "F:\\jianyin\\cgwz\\JianyingPro Drafts\\dfd_cat_1762313389_ae978ee4\\assets\\audio\\xxx.mp3"
  ```
- **理论**: 传统的绝对路径模式，必须解压到指定位置

## 🧪 测试步骤

### 1. 下载测试文件

下载地址:
- 版本A: http://8.148.70.18:8888/dfd_cat_1762313389_ae978ee4__version_A_relative_empty.zip
- 版本B: http://8.148.70.18:8888/dfd_cat_1762313389_ae978ee4__version_B_relative_with_root.zip
- 版本C: http://8.148.70.18:8888/dfd_cat_1762313389_ae978ee4__version_C_absolute.zip

### 2. 解压到剪映草稿目录

将每个ZIP文件解压到:
```
F:\jianyin\cgwz\JianyingPro Drafts\
```

解压后应该有3个文件夹：
```
F:\jianyin\cgwz\JianyingPro Drafts\
├── dfd_cat_1762313389_ae978ee4  (版本A)
├── dfd_cat_1762313389_ae978ee4  (版本B)
└── dfd_cat_1762313389_ae978ee4  (版本C)
```

⚠️ 注意: 由于文件夹名相同，建议分批测试：
- 先测试版本A，记录结果后删除
- 再测试版本B，记录结果后删除
- 最后测试版本C

### 3. 用剪映打开并观察

对每个版本：
1. 打开剪映
2. 在草稿列表中找到 `dfd_cat_1762313389_ae978ee4`
3. 双击打开草稿
4. 观察是否能识别素材

### 4. 记录测试结果

请记录每个版本的表现：

| 版本 | 能否打开草稿 | 素材识别情况 | 备注 |
|------|------------|------------|------|
| 版本A (相对路径+空root) | ✅/❌ | ✅/❌ | |
| 版本B (相对路径+设置root) | ✅/❌ | ✅/❌ | |
| 版本C (绝对路径+设置root) | ✅/❌ | ✅/❌ | |

## 📸 需要的截图

对于每个版本，如果出现问题，请提供：
1. 剪映打开草稿的截图（显示是否有"链接媒体"对话框）
2. 时间轴上素材的状态（是否显示"媒体丢失"）

## 🎯 预期结果

根据测试结果，我们可以确定：

- **如果版本A成功** → 剪映支持纯相对路径，问题可能在其他地方（元数据、文件格式等）
- **如果版本B成功** → 剪映需要设置root_path但可以使用相对路径
- **如果版本C成功** → 剪映只支持绝对路径模式
- **如果都失败** → 问题不在路径配置，可能是素材元数据、文件完整性等其他问题

## 📝 反馈方式

请将测试结果（包括上面的表格和截图）反馈给我，这样我们就能确定：
1. 剪映到底支持哪种路径模式
2. 当前的"智能下载"功能需要如何调整
3. 是否需要修改路径生成逻辑

## 🔍 额外检查

如果所有版本都失败，请额外检查：

1. **素材文件是否存在**:
   ```
   dfd_cat_1762313389_ae978ee4\
   └── assets\
       ├── audio\
       │   ├── audio_xxx.mp3 (检查文件大小是否>0)
       │   └── ...
       └── image\
           ├── image_xxx.png
           └── ...
   ```

2. **draft_info.json中的元数据**:
   用记事本打开，搜索 `"duration"` 字段，确认不是0:
   ```json
   "duration": 4000000  ← 应该>0
   ```

3. **剪映版本**:
   检查你使用的剪映版本号（设置 → 关于）


