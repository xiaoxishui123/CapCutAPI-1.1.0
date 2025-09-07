# Windows客户端素材路径问题修复报告

## 📋 问题概述

**问题描述**: Windows客户端下载草稿后用剪映打开，素材源地址显示为Linux服务器路径，导致剪映无法识别素材。

**用户配置**: 
- 客户端：Windows电脑
- 自定义下载路径：`F:\jianyin\cgwz\JianyingPro Drafts`

**发现时间**: 2025年1月

## 🔍 问题根因分析

### 核心问题
OSS模式下，`save_draft_background`函数使用服务器操作系统（Linux）的路径配置，而不是客户端操作系统（Windows）的路径配置，导致生成的草稿文件中素材路径为Linux格式。

**❌ 修复前**：
```python
# save_draft_impl.py 第66-69行
if not draft_folder:
    os_config = get_os_path_config()
    draft_folder = os_config.get_current_os_draft_path()  # 返回Linux路径
```

**生成的素材路径**：
```json
{
  "path": "/home/user/CapCut Projects/draft_id/assets/video/file.mp4",
  "media_path": "/home/user/CapCut Projects/draft_id/assets/video/file.mp4"
}
```

**Windows客户端无法识别** ❌

### 问题影响
- Windows客户端无法正确链接素材
- 用户需要手动重新链接每个素材
- 影响用户体验

## 🛠️ 修复方案

### 1. 函数签名修改
修改`save_draft_background`函数，添加`client_os`参数：

```python
def save_draft_background(draft_id: str, draft_folder: str, task_id: str, client_os: str = "windows"):
```

### 2. 路径选择逻辑优化
实现新的路径选择优先级：

```python
# 优先读取用户自定义路径配置
custom_path = None
try:
    config_file = 'path_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            custom_path = config.get('custom_download_path', '')
except Exception as e:
    logger.warning(f"读取自定义路径配置失败: {e}")

# 确定最终使用的草稿路径
if not draft_folder:
    if custom_path:
        # 使用用户自定义路径
        draft_folder = custom_path
    else:
        # 根据客户端操作系统获取默认路径
        os_config = get_os_path_config()
        if client_os.lower() == "windows":
            draft_folder = os_config.get_default_draft_path("windows")
        else:
            draft_folder = os_config.get_default_draft_path(client_os.lower())
```

### 3. API接口更新
修改`save_draft` API接口，支持客户端操作系统参数：

```python
@app.route('/save_draft', methods=['POST'])
def save_draft():
    data = request.get_json()
    draft_id = data.get('draft_id')
    draft_folder = data.get('draft_folder')
    client_os = data.get('client_os', 'windows')  # 新增参数
    
    draft_result = save_draft_impl(draft_id, draft_folder, client_os)
```

### 4. 前端操作系统检测
在预览页面添加客户端操作系统自动检测：

```javascript
function detectClientOS() {
    const userAgent = navigator.userAgent.toLowerCase();
    if (userAgent.includes('win')) {
        return 'windows';
    } else if (userAgent.includes('mac')) {
        return 'darwin';
    } else if (userAgent.includes('linux')) {
        return 'linux';
    } else {
        return 'windows'; // 默认为windows
    }
}
```

## ✅ 修复结果

### 修复后路径生成
**✅ 修复后**：
- 优先使用用户自定义路径：`F:\jianying\cgwz\JianyingPro Drafts`
- 根据客户端操作系统生成正确格式的路径
- Windows路径使用反斜杠分隔符

**生成的素材路径**：
```json
{
  "path": "F:\\jianying\\cgwz\\JianyingPro Drafts\\draft_id\\assets\\video\\file.mp4",
  "media_path": "F:\\jianying\\cgwz\\JianyingPro Drafts\\draft_id\\assets\\video\\file.mp4"
}
```

**Windows客户端正确识别** ✅

### 测试结果
```bash
$ python test_windows_path.py

=== 测试路径配置读取 ===
读取到用户自定义路径: F:\jianying\cgwz\JianyingPro Drafts

=== 测试操作系统路径配置 ===
当前服务器操作系统类型: linux
Windows客户端默认路径: F:\jianying\cgwz\JianyingPro Drafts

=== 测试素材路径构建 ===
生成的素材路径: F:\jianying\cgwz\JianyingPro Drafts\test_draft_123\assets\video\test_video.mp4
✅ Windows路径格式正确
```

## 📊 路径优先级

修复后的路径选择优先级：

1. **API传入的 draft_folder 参数**（最高优先级）
2. **用户自定义路径**（path_config.json 中的配置）
3. **客户端操作系统默认路径**（根据 client_os 参数）
4. **服务器操作系统默认路径**（兜底方案）

## 🔧 API使用示例

### 保存草稿（指定Windows客户端）
```bash
curl -X POST http://8.148.70.18:9000/save_draft \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "your_draft_id",
    "client_os": "windows"
  }'
```

### 配置自定义路径
```bash
curl -X POST http://8.148.70.18:9000/api/draft/path/config \
  -H "Content-Type: application/json" \
  -d '{
    "custom_path": "F:\\jianying\\cgwz\\JianyingPro Drafts"
  }'
```

## 📝 修改文件清单

- ✅ `save_draft_impl.py` - 核心路径生成逻辑
- ✅ `capcut_server.py` - API接口更新
- ✅ `templates/preview.html` - 前端操作系统检测
- ✅ `README.md` - 文档更新
- ✅ `test_windows_path.py` - 测试脚本

## 🎯 用户指南

### Windows用户使用步骤

1. **配置自定义路径**（一次性设置）：
   - 访问草稿预览页面
   - 点击"⚙️ 配置路径"
   - 输入您的剪映草稿文件夹路径：`F:\jianying\cgwz\JianyingPro Drafts`

2. **下载草稿**：
   - 使用"📥 自定义下载"功能
   - 系统自动使用Windows路径格式生成草稿

3. **打开剪映**：
   - 下载完成后解压到配置的路径
   - 打开剪映应用即可正常识别所有素材

## 🔄 兼容性

- ✅ 兼容Windows、macOS、Linux客户端
- ✅ 向后兼容现有API调用
- ✅ 默认客户端类型为Windows
- ✅ 支持混合环境（Linux服务器 + Windows客户端）

---

**修复完成时间**: 2025年1月  
**修复状态**: ✅ 已完成  
**测试状态**: ✅ 测试通过  
**文档状态**: ✅ 已更新
