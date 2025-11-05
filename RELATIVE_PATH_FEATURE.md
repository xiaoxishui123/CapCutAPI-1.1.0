# 相对路径下载功能文档
# Relative Path Download Feature Documentation

版本：v1.3.0  
日期：2025-11-04  
作者：CapCutAPI Team

---

## 📋 功能概述

CapCutAPI v1.3.0 新增了**相对路径下载支持**功能，允许用户在调用API时使用相对路径指定草稿下载位置，系统会自动将相对路径转换为绝对路径，极大地提升了使用的灵活性和便利性。

---

## ✨ 主要特性

### 1. 多种路径格式支持

| 路径类型 | 示例 | 说明 |
|---------|------|------|
| **相对路径** | `./downloads` | 相对于项目根目录 |
| **上级目录** | `../output` | 访问上级目录 |
| **用户主目录** | `~/Documents` | 自动展开为用户目录 |
| **绝对路径** | `/home/user/path` | 直接使用完整路径 |
| **Windows路径** | `F:\jianying\cgwz` | Windows盘符格式 |

### 2. 自动路径转换

系统会根据路径类型自动执行以下转换：

- **相对路径** → 基于项目根目录转换为绝对路径
- **波浪号(~)** → 展开为用户主目录
- **路径分隔符** → 自动规范化（`/` 或 `\`）
- **. 和 ..** → 解析为当前目录和上级目录

### 3. 路径验证

- ✅ 自动验证路径格式有效性
- ✅ 检测路径类型（绝对/相对/Windows）
- ✅ 支持路径存在性验证
- ✅ 防止非法路径访问

### 4. 跨平台兼容

- ✅ Linux系统完全支持
- ✅ Windows路径格式支持
- ✅ macOS系统支持
- ✅ 自动处理不同系统的路径差异

---

## 📝 使用方法

### 基本用法

```python
import requests

# API地址
API_URL = "http://8.148.70.18:9000/save_draft"

# 使用相对路径
response = requests.post(API_URL, json={
    "draft_id": "dfd_cat_1756104121_cb774809",
    "draft_folder": "./downloads/drafts",  # 相对路径
    "client_os": "windows"
})

print(response.json())
```

### 路径转换示例

| 输入路径 | 转换后（Linux） | 转换后（Windows） |
|---------|----------------|------------------|
| `./downloads` | `/home/CapCutAPI-1.1.0/downloads` | `C:\CapCutAPI-1.1.0\downloads` |
| `../output` | `/home/output` | `C:\output` |
| `~/Documents` | `/home/user/Documents` | `C:\Users\username\Documents` |
| `/absolute/path` | `/absolute/path` | `/absolute/path` |

### 完整示例

详细的使用示例请参考：[examples/relative_path_example.py](examples/relative_path_example.py)

---

## 🔧 技术实现

### 核心模块

#### 1. `path_utils.py` - 路径处理工具模块

提供以下核心功能：

```python
# 判断是否为Windows路径
is_windows_path(path: str) -> bool

# 判断是否为绝对路径
is_absolute_path(path: str) -> bool

# 规范化路径（相对路径→绝对路径）
normalize_path(path: str, base_dir: Optional[str] = None) -> str

# 验证路径有效性
validate_path(path: str, must_exist: bool = False, must_be_dir: bool = False) -> tuple

# 确保目录存在
ensure_directory_exists(path: str) -> bool

# 路径格式转换
convert_to_windows_path(linux_path: str) -> str
convert_to_linux_path(windows_path: str) -> str

# 安全的路径连接
safe_join(*paths) -> str
```

#### 2. 集成到现有模块

**save_draft_impl.py**:
- 在保存草稿时自动处理相对路径
- 支持路径优先级：API参数 > 自定义配置 > 系统默认
- 自动验证和转换路径

**downloader.py**:
- 所有下载函数支持相对路径
- 自动创建必要的目录结构
- 统一的路径处理逻辑

### 处理流程

```
用户输入路径
    ↓
判断路径类型
    ↓
├─ 绝对路径 → 直接使用
├─ 相对路径 → 基于项目根目录转换
├─ 波浪号路径 → 展开为用户主目录
└─ Windows路径 → 保持格式，验证有效性
    ↓
路径规范化
    ↓
路径验证
    ↓
确保目录存在
    ↓
返回最终路径
```

---

## 🎯 使用场景

### 场景1：开发环境下载

```python
# 开发时下载到项目本地目录
draft_folder = "./downloads/dev"
```

### 场景2：测试环境输出

```python
# 测试时输出到共享目录
draft_folder = "../test_output/drafts"
```

### 场景3：用户个人目录

```python
# 下载到用户文档目录
draft_folder = "~/Documents/CapCut/Projects"
```

### 场景4：生产环境部署

```python
# 生产环境使用绝对路径
draft_folder = "/data/capcut/production/drafts"
```

### 场景5：Windows客户端

```python
# Windows用户的剪映草稿目录
draft_folder = "F:\\jianying\\cgwz\\JianyingPro Drafts"
```

---

## 🔍 路径优先级

系统按以下优先级选择草稿路径：

1. **API传入的 draft_folder 参数**（最高优先级）
2. **用户自定义路径**（path_config.json 配置）
3. **客户端操作系统默认路径**（根据 client_os 参数）
4. **服务器操作系统默认路径**（兜底方案）

示例：

```python
# 优先级1：API参数
requests.post(API_URL, json={
    "draft_id": "xxx",
    "draft_folder": "./my_downloads"  # 最高优先级
})

# 优先级2：配置文件 path_config.json
{
    "custom_download_path": "/home/user/downloads"
}

# 优先级3：client_os参数决定
# 如果未提供draft_folder，根据client_os使用默认路径
```

---

## ⚠️ 注意事项

### 1. 路径权限

确保服务器对目标路径有读写权限：

```bash
# 检查目录权限
ls -ld /path/to/directory

# 设置权限（如需要）
chmod 755 /path/to/directory
```

### 2. 路径安全

- ✅ 系统会验证路径格式
- ✅ 防止路径遍历攻击
- ✅ 自动规范化路径
- ⚠️ 建议在生产环境限制可访问路径范围

### 3. 跨平台注意

- Windows路径使用反斜杠 `\`（但正斜杠 `/` 也支持）
- Linux/macOS路径使用正斜杠 `/`
- 建议使用相对路径以提高跨平台兼容性

### 4. 性能考虑

- 路径转换和验证会有轻微性能开销
- 对于频繁调用，建议缓存转换后的路径
- 首次访问时会自动创建目录

---

## 🐛 问题排查

### 问题1：路径未生效

**症状**：使用相对路径但文件保存在默认位置

**解决方案**：
1. 检查draft_folder参数是否正确传递
2. 查看日志确认路径转换结果
3. 验证路径优先级设置

```bash
# 查看日志
tail -f logs/capcutapi.log | grep "路径"
```

### 问题2：权限不足

**症状**：提示"Permission denied"

**解决方案**：
```bash
# 检查目录所有者和权限
ls -ld /path/to/directory

# 修改所有者（如需要）
sudo chown -R your_user:your_group /path/to/directory

# 修改权限
chmod -R 755 /path/to/directory
```

### 问题3：路径不存在

**症状**：提示"Directory not found"

**解决方案**：
- 系统会自动创建不存在的目录
- 确保上级目录存在且有权限
- 检查路径拼写是否正确

---

## 📚 相关文档

- [README.md](README.md) - 项目主文档
- [path_utils.py](path_utils.py) - 路径工具源码
- [examples/relative_path_example.py](examples/relative_path_example.py) - 使用示例

---

## 🚀 未来计划

- [ ] 支持网络路径（SMB/NFS）
- [ ] 添加路径黑白名单配置
- [ ] 支持路径模板变量（如 `{date}`、`{draft_id}`）
- [ ] 增加路径使用统计和分析
- [ ] 优化大批量路径处理性能

---

## 💬 反馈与支持

如有问题或建议，请通过以下方式联系：

- 📧 Email: business@capcutapi.com
- 🐛 Issues: GitHub Issues
- 📖 文档: 查看README.md和在线文档

---

## 📄 更新日志

### v1.3.0 (2025-11-04)

**新增功能**：
- ✨ 支持相对路径下载
- ✨ 添加路径工具模块 path_utils.py
- ✨ 支持用户主目录展开（~）
- ✨ 自动路径验证和创建

**改进**：
- 🔧 优化save_draft_impl.py路径处理逻辑
- 🔧 增强downloader.py路径规范化
- 🔧 完善错误处理和日志记录

**文档**：
- 📖 更新README.md添加相对路径说明
- 📖 新增RELATIVE_PATH_FEATURE.md详细文档
- 📖 添加使用示例文件

**测试**：
- ✅ 完整的单元测试覆盖
- ✅ 集成测试验证
- ✅ 跨平台兼容性测试

---

**⭐ 如果这个功能对你有帮助，请给项目一个Star！**

**⭐ If this feature helps you, please give the project a Star!**

