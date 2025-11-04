# draft_meta_info.json 路径修复说明

## 📅 修复时间
2025年11月4日 19:06

## 🐛 问题描述

**用户反馈**：
> 我设置路径是：D:\test  
> 下载草稿后生成的draft_meta_info.json文件里面draft_root_path路径还是修改设置之前的路径（F:\jianyin\cgwz\JianyingPro Drafts）

**问题原因**：
1. `customize_zip.py` 只重写了 `draft_info.json`，完全忽略了 `draft_meta_info.json`
2. OSS缓存机制导致修改代码后仍返回旧版本的zip包

## ✅ 修复内容

### 1. 添加 draft_meta_info.json 重写逻辑

**新增函数** `_rewrite_meta_info()`:
```python
def _rewrite_meta_info(data, draft_id: str, client_os: str, draft_folder: str) -> dict:
    """重写 draft_meta_info.json，特别是更新 draft_root_path"""
    if not isinstance(data, dict):
        return data
    
    new_obj = {}
    for k, v in data.items():
        if k == "draft_root_path" and draft_folder:
            # 重写 draft_root_path 为配置的路径
            new_obj[k] = normalize_path_by_os(draft_folder, client_os)
        else:
            # 其他字段保持不变
            new_obj[k] = v
    
    return new_obj
```

**修改** `ensure_customized_zip()` 函数：
- 添加对 `draft_meta_info.json` 文件的检测和处理
- 当检测到 `draft_meta_info.json` 时，调用 `_rewrite_meta_info()` 更新 `draft_root_path`

### 2. 添加版本号机制解决缓存问题

**新增版本号常量**:
```python
# 版本号：修改路径重写逻辑后需要更新此版本号，以使OSS缓存失效
REWRITE_VERSION = "v2_meta_info_fix"
```

**修改缓存key生成逻辑**:
```python
# 在key中加入版本号，当修改重写逻辑后更新版本号可使旧缓存失效
key_suffix = _hash_str(f"{REWRITE_VERSION}|{client_os}|{draft_folder}") if draft_folder else client_os
```

## 🔄 修复效果

### 修复前
```json
{
  "draft_root_path": "F:\\jianyin\\cgwz\\JianyingPro Drafts"  // ❌ 旧路径
}
```

### 修复后
```json
{
  "draft_root_path": "D:\\test"  // ✅ 配置的路径
}
```

## 🧪 测试验证

### 自动化测试结果
```
✅ Windows路径配置: D:\test → 正确重写
✅ Linux路径配置: /home/user/drafts → 正确重写
✅ Mac路径配置: /Users/mac/Documents/Drafts → 正确重写
✅ 其他字段保持不变
```

### 手动测试步骤

1. **配置下载路径**:
   ```
   在页面上点击"配置路径"按钮
   输入: D:\test
   点击"确定"保存
   ```

2. **下载草稿**:
   ```
   选择一个草稿
   点击"下载草稿"按钮
   下载完成后解压到本地
   ```

3. **验证结果**:
   ```
   打开解压后的文件夹
   用文本编辑器打开 draft_meta_info.json
   检查 draft_root_path 字段的值
   
   预期结果: "draft_root_path": "D:\\test"
   ```

## 📋 修改的文件

| 文件 | 修改内容 | 状态 |
|-----|---------|------|
| `customize_zip.py` | 添加 draft_meta_info.json 重写逻辑 | ✅ 已修改 |
| `customize_zip.py` | 添加版本号机制 | ✅ 已修改 |
| `capcutapi.service` | 重启服务 | ✅ 已重启 |

## 🚀 部署状态

- ✅ 代码修改完成
- ✅ 语法检查通过
- ✅ 自动化测试通过
- ✅ 服务已重启
- ✅ 修复已生效

**服务状态**: Active (running)  
**重启时间**: 2025-11-04 19:06:16 CST  
**进程ID**: 1339857

## 📝 使用说明

### 现在的完整流程

1. **配置路径**: 在页面上设置 `D:\test`
2. **下载草稿**: 点击"下载草稿"按钮
3. **解压文件**: 将zip包解压到 `D:\test` 目录
4. **打开剪映**: 启动剪映应用

### 验证文件内容

下载的zip包中包含两个重要的JSON文件：

1. **draft_info.json**: 
   - 包含素材路径（path、media_path等字段）
   - 所有包含 `assets/` 的路径都会被重写为: `D:\test\{草稿ID}\assets\...`

2. **draft_meta_info.json**:
   - 包含草稿根路径（draft_root_path字段）
   - 会被重写为: `D:\test`

## ⚠️ 重要提示

### 1. 首次下载需要等待
由于加入了版本号，之前下载过的草稿会重新生成新的zip包，可能需要几秒钟时间。

### 2. 解压位置很重要
**必须将下载的zip包解压到配置的路径**（例如 `D:\test`），否则剪映无法找到素材文件。

正确的目录结构应该是：
```
D:\test\
  └── dfd_cat_xxx\
      ├── draft_info.json
      ├── draft_meta_info.json
      └── assets\
          ├── audio\
          ├── image\
          └── video\
```

### 3. 路径格式
- Windows: `D:\test` 或 `D:/test` (会自动转换为 `D:\test`)
- Linux: `/home/user/drafts`
- Mac: `/Users/mac/Documents/Drafts`

## 🔍 如何验证修复是否成功

### 方法1：检查JSON文件
```bash
# 解压下载的zip包
# 用文本编辑器打开 draft_meta_info.json
# 查找 draft_root_path 字段

# 应该看到：
"draft_root_path": "D:\\test"  # Windows
# 或
"draft_root_path": "/home/user/drafts"  # Linux
```

### 方法2：在剪映中打开
```
1. 将zip包解压到 D:\test
2. 打开剪映应用
3. 在草稿列表中找到解压的草稿
4. 点击打开
5. 检查素材是否正常加载
```

如果素材能正常显示，说明路径配置正确！

## 🎉 修复完成

现在你可以：
1. ✅ 在页面上配置任意下载路径
2. ✅ 下载草稿时，draft_info.json 中的素材路径会正确更新
3. ✅ 下载草稿时，draft_meta_info.json 中的 draft_root_path 也会正确更新
4. ✅ 支持 Windows、Linux、Mac 三种操作系统

**请在页面上重新测试，应该可以看到正确的路径了！** 🎊

---

**修复人员**: AI Assistant  
**修复日期**: 2025年11月4日  
**修复版本**: v2_meta_info_fix

