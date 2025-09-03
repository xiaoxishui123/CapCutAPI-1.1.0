# CapCutAPI 跨平台素材识别问题解决方案

## 📋 **问题概述**

### 问题现象
- **环境**: Linux服务器生成草稿 → Windows剪映打开
- **症状**: 剪映显示"素材丢失，点击重新链接"
- **表现**: 草稿能正常打开，但无法识别视频素材

### 影响范围
- 所有通过CapCutAPI生成的草稿
- 跨平台使用场景（Linux服务器 + Windows客户端）
- 视频、音频素材的元数据获取

---

## 🔍 **问题诊断过程**

### 第一阶段：表面现象分析
```bash
# 检查文件结构完整性
ls -la draft_folder/assets/
# 结果：✅ 文件存在，大小正常

# 检查路径格式
# 结果：✅ Windows路径格式正确
```

**初步结论**: 文件和路径都正确，问题在其他地方。

### 第二阶段：深入元数据分析
```python
# 检查draft_info.json中的视频元数据
{
    "duration": 0,  # ❌ 关键问题：时长为0！
    "width": 1920,
    "height": 1080,
    "path": "F:\\...\\video.mp4",  # ✅ 路径正确
    "media_path": "F:\\...\\video.mp4"  # ✅ 路径正确
}
```

**关键发现**: 视频时长为0微秒，这是剪映无法识别的根本原因。

### 第三阶段：追踪元数据生成过程
```bash
# 查看日志中的ffprobe调用
tail -f logs/capcutapi.log

# 发现关键错误：
Error: ffprobe command not found, please check installation.
FileNotFoundError: [Errno 2] No such file or directory: 'ffprobe'
```

**根因定位**: ffprobe命令无法找到，导致视频元数据获取失败。

---

## 🎯 **根因分析**

### 问题根源
| **层面** | **具体问题** | **影响** |
|---------|-------------|---------|
| **环境依赖** | ffprobe命令路径问题 | 无法获取视频元数据 |
| **代码实现** | 硬编码命令名称 | 依赖系统PATH环境变量 |
| **进程环境** | 虚拟环境vs系统环境差异 | 不同启动方式PATH不同 |

### 关键代码位置
```python
# 问题代码 (pyJianYingDraft/local_materials.py:155)
command = [
    'ffprobe',  # ❌ 硬编码，依赖PATH
    '-v', 'error',
    # ...
]
```

### 技术原理
1. **ffprobe作用**: 获取视频文件的时长、分辨率等元数据
2. **调用方式**: Python subprocess.check_output()
3. **失败机制**: 找不到命令 → 异常处理 → 使用默认值(0)
4. **后果链条**: 时长=0 → 剪映认为无效 → 显示素材丢失

---

## 🔧 **解决方案**

### 核心修复策略
**将相对命令路径改为绝对路径**，消除对环境变量的依赖。

### 具体修复位置

#### 1. pyJianYingDraft/local_materials.py
```python
# 修复前
command = ['ffprobe', '-v', 'error', ...]

# 修复后  
command = ['/usr/bin/ffprobe', '-v', 'error', ...]
```
**涉及行数**: 第155、333、353行

#### 2. save_draft_impl.py
```python
# 修复前
command = ['ffprobe', '-v', 'error', ...]

# 修复后
command = ['/usr/bin/ffprobe', '-v', 'error', ...]
```
**涉及行数**: 第315、408行

#### 3. get_duration_impl.py
```python
# 修复前
command = ['ffprobe', '-v', 'error', ...]

# 修复后
command = ['/usr/bin/ffprobe', '-v', 'error', ...]
```
**涉及行数**: 第23行

### 修复验证
```bash
# 重启服务器
pkill -f capcut_server && python3 capcut_server.py &

# 测试修复效果
curl -X POST http://server:9000/create_draft ...
# 结果：✅ 视频时长正确获取 (125.93秒)
```

---

## ✅ **验证过程**

### 技术验证
```python
# 验证视频元数据
{
    "duration": 125933333,  # ✅ 正确：125.93秒
    "width": 320,           # ✅ 正确：实际分辨率
    "height": 240,          # ✅ 正确：实际分辨率
    "path": "F:\\...\\video.mp4",      # ✅ Windows格式
    "media_path": "F:\\...\\video.mp4" # ✅ Windows格式
}
```

### 用户验证
- ✅ 剪映能正确识别视频素材
- ✅ 预览窗口正常显示视频内容
- ✅ 时间轴显示完整的视频长度
- ✅ 所有编辑功能正常工作

---

## 📚 **经验总结**

### 关键教训
1. **环境依赖管理**: 不要假设所有环境都有相同的PATH
2. **错误处理完善**: 关键依赖失败时应该有明显的错误提示
3. **跨平台兼容**: 充分考虑不同OS和启动方式的差异
4. **调试策略**: 从表面现象到深层原因的系统化分析

### 最佳实践
1. **使用绝对路径**: 对于系统工具调用，优先使用完整路径
2. **环境检查**: 在服务启动时检查关键依赖的可用性
3. **详细日志**: 记录每个关键步骤的执行状态
4. **分层验证**: 从文件 → 元数据 → 用户界面逐层验证

---

## 🛠️ **预防措施**

### 代码改进建议
```python
# 建议的健壮性改进
import shutil

def get_ffprobe_path():
    """获取ffprobe的可用路径"""
    paths = ['/usr/bin/ffprobe', '/usr/local/bin/ffprobe', 'ffprobe']
    for path in paths:
        if shutil.which(path):
            return path
    raise FileNotFoundError("ffprobe not found in system")

# 使用示例
ffprobe_cmd = get_ffprobe_path()
command = [ffprobe_cmd, '-v', 'error', ...]
```

### 部署检查清单
- [ ] 确认ffmpeg/ffprobe已安装
- [ ] 验证虚拟环境中的PATH设置
- [ ] 测试各种启动方式下的命令可用性
- [ ] 检查不同用户权限下的执行情况

---

## 🚀 **标准使用流程**

### 正确的API调用模式
```bash
# 1. 创建草稿
curl -X POST http://server:9000/create_draft \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "project_name",
    "width": 1080,
    "height": 1920
  }'

# 2. 添加视频素材
curl -X POST http://server:9000/add_video \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "project_name",
    "video_url": "https://example.com/video.mp4",
    "start": 0,
    "end": 10,
    "track_name": "main_video"
  }'

# 3. 保存草稿（关键：Windows路径格式）
curl -X POST http://server:9000/save_draft \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "project_name",
    "draft_folder": "F:\\\\jianyin\\\\cgwz\\\\JianyingPro Drafts"
  }'
```

### Windows本地部署步骤
1. **下载**: `scp server:project_name.tar.gz ./`
2. **解压**: 到 `F:\jianyin\cgwz\JianyingPro Drafts\`
3. **验证**: 确保assets文件夹和素材文件完整
4. **打开**: 在剪映中导入项目

---

## 📊 **问题分类与处理矩阵**

| **症状** | **可能原因** | **诊断方法** | **解决方案** |
|---------|-------------|-------------|-------------|
| 素材丢失 | 文件不存在 | `ls -la assets/` | 重新下载 |
| 素材丢失 | 路径格式错误 | 检查draft_info.json路径 | 修正路径格式 |
| 素材丢失 | 时长为0 | 检查duration字段 | 修复ffprobe调用 |
| 素材丢失 | 权限问题 | 检查文件权限 | 修改文件权限 |

---

## 🎯 **成功标准**

### 技术指标
- ✅ 视频duration > 0
- ✅ 分辨率与实际文件匹配
- ✅ 路径格式符合目标OS
- ✅ 所有素材文件完整下载

### 用户体验指标  
- ✅ 剪映能正常识别所有素材
- ✅ 预览功能正常工作
- ✅ 编辑操作无异常
- ✅ 导出功能正常

---

## 📞 **支持信息**

### 常见问题排查
```bash
# 检查ffprobe是否可用
/usr/bin/ffprobe -version

# 检查草稿文件完整性  
ls -la draft_folder/assets/*/

# 验证视频元数据
grep -A 5 -B 5 "duration" draft_folder/draft_info.json
```

### 联系方式
- **技术文档**: 本文档
- **代码仓库**: `/home/CapCutAPI-1.1.0/`
- **日志位置**: `logs/capcutapi.log`

---

**文档版本**: v1.0  
**最后更新**: 2025年8月5日  
**验证状态**: ✅ 已通过完整测试验证 