# Pattern 模板库 - 快速启动指南

欢迎使用 CapCutAPI Pattern 模板库！本指南将帮助您在 5 分钟内开始使用视频编辑模板。

---

## 📚 什么是 Pattern？

Pattern 是预先编写好的视频编辑脚本模板，包含完整的视频创作流程：
- 🎨 自动素材下载
- ✨ AI 内容生成
- 🎬 视频合成和特效
- 📝 字幕和文本添加

---

## 🚀 5 分钟快速开始

### 步骤 1: 查看可用模板

```bash
curl http://localhost:9000/api/patterns/list | jq
```

**输出示例**:
```json
{
  "success": true,
  "patterns": [
    {
      "id": "001-words",
      "name": "文字滚动效果",
      "type": "python",
      "video_url": "https://www.youtube.com/watch?v=HLSHaJuNtBw"
    }
  ],
  "count": 3
}
```

### 步骤 2: 下载模板

```bash
# 下载文字滚动效果模板
curl -O http://localhost:9000/api/patterns/download/001-words
```

### 步骤 3: 配置 API 密钥

编辑下载的 Python 文件，配置您的 API 密钥：

```python
# 设置 API 密钥
QWEN_API_KEY = "your qwen api key"        # 通义千问 API
PEXELS_API_KEY = "your pexels api key"    # Pexels 图片 API
CAPCUT_API_KEY = "your capcut api key"    # CapCut API（如需要）
LICENSE_KEY = "your license key"          # License Key（如需要）
```

**获取 API 密钥**:
- 通义千问: https://dashscope.console.aliyun.com/
- Pexels: https://www.pexels.com/api/

### 步骤 4: 修改配置参数

根据您的环境修改配置：

```python
PORT = 9000  # CapCutAPI 服务端口
BASE_URL = f"http://localhost:{PORT}"

# 草稿保存路径（Windows 示例）
draft_folder = "C:\\Users\\YourName\\JianyingPro\\User Data\\Projects\\com.lveditor.draft"

# 或 macOS 示例
draft_folder = "/Users/yourname/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
```

### 步骤 5: 运行模板

```bash
python 001-words.py
```

**执行流程**:
1. 调用 AI 生成文字内容
2. 自动下载背景音频和图片
3. 识别音频生成字幕
4. 合成视频草稿
5. 保存到剪映/CapCut

**完成！** 🎉 打开剪映/CapCut 查看生成的草稿

---

## 📖 可用模板详解

### 🎬 001-words - 文字滚动效果

**功能**: 自动生成带字幕的文字滚动效果视频

**适用场景**:
- 情感金句视频
- 知识分享短视频
- 励志语录视频

**所需 API**:
- 通义千问 API（文字生成）
- Pexels API（背景图片）
- CapCut API（视频合成）

**效果演示**: [观看视频](https://www.youtube.com/watch?v=HLSHaJuNtBw)

**核心特点**:
- ✅ AI 自动生成文字内容
- ✅ 自动识别音频生成字幕
- ✅ 支持彩色高亮关键词
- ✅ 背景图片自动适配

### 💑 002-relationship - 情侣关系主题

**功能**: 生成情侣关系建议短视频

**适用场景**:
- 情感类短视频
- 恋爱技巧分享
- 情侣互动内容

**所需 API**:
- 通义千问 API（内容生成）
- Pexels API（素材图片）
- CapCut API（视频合成）

**效果演示**: [观看视频](https://www.youtube.com/watch?v=f2Q1OI_SQZo)

**核心特点**:
- ✅ AI 生成情感建议
- ✅ 自动素材搜索下载
- ✅ 专业的视觉效果
- ✅ 完整的视频流程

### 📋 001-words-coze - 扣子工作流

**功能**: 扣子（Coze）平台工作流配置

**适用场景**:
- 在扣子平台使用 CapCut MCP 插件
- 自动化视频生成工作流

**使用方式**:
1. 复制 MD 文件中的 JSON 配置
2. 在扣子平台创建工作流
3. 粘贴配置并调整参数

---

## 🔧 常见问题

### Q1: 模板运行报错 "API key not found"
**A**: 请检查是否正确配置了所有必需的 API 密钥。

### Q2: 草稿保存路径找不到
**A**: 确认草稿路径是否正确：
- Windows: 在剪映设置中查看草稿位置
- macOS: 通常在 `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft`

### Q3: 生成的视频没有出现在剪映中
**A**:
1. 检查 `draft_folder` 路径是否正确
2. 确认剪映是否已关闭（部分版本需要重启）
3. 检查日志输出是否有错误信息

### Q4: API 调用失败
**A**:
1. 检查 CapCutAPI 服务是否运行：`curl http://localhost:9000/health`
2. 检查网络连接是否正常
3. 查看 CapCutAPI 日志：`tail -f logs/capcutapi.log`

### Q5: 如何自定义模板内容？
**A**:
1. 下载模板文件
2. 编辑 Python 脚本修改参数
3. 参考 CapCutAPI 文档了解更多 API 用法

---

## 💡 进阶使用

### 创建自定义模板

基于现有模板创建您自己的模板：

```python
# 1. 下载现有模板作为基础
curl -O http://localhost:9000/api/patterns/download/001-words

# 2. 重命名并修改
mv 001-words.py my-custom-template.py

# 3. 编辑模板，修改以下部分：
# - AI 提示词
# - 素材选择逻辑
# - 视觉效果参数
# - 文本样式

# 4. 运行您的自定义模板
python my-custom-template.py
```

### 批量生成视频

```python
# 循环生成多个视频
for i in range(10):
    os.system(f"python 001-words.py")
    print(f"生成第 {i+1} 个视频")
```

### 与 AI 工具集成

在 Coze、Dify 等平台中使用 Pattern 模板：

1. 使用 CapCut MCP 插件
2. 调用 Pattern API 获取模板
3. 在工作流中应用模板逻辑

---

## 📚 更多资源

- **API 文档**: [API_USAGE_EXAMPLES.md](../docs/API_USAGE_EXAMPLES.md)
- **项目文档**: [CLAUDE.md](../CLAUDE.md)
- **集成报告**: [PATTERN_INTEGRATION_REPORT.md](../docs/PATTERN_INTEGRATION_REPORT.md)
- **视频演示**:
  - [文字滚动效果](https://www.youtube.com/watch?v=HLSHaJuNtBw)
  - [情侣关系主题](https://www.youtube.com/watch?v=f2Q1OI_SQZo)

---

## 🎓 学习路径

### 初级（第 1 周）
1. ✅ 成功运行一个模板
2. ✅ 理解模板的基本结构
3. ✅ 修改简单参数（颜色、字体等）

### 中级（第 2-3 周）
1. ✅ 修改 AI 提示词生成不同内容
2. ✅ 调整视觉效果和动画
3. ✅ 集成不同的素材来源

### 高级（第 4 周+）
1. ✅ 创建完全自定义的模板
2. ✅ 与 AI 工作流平台集成
3. ✅ 开发批量生成脚本

---

## 💬 获取帮助

遇到问题？有建议？

- **GitHub Issues**: [提交问题](https://github.com/sun-guannan/CapCutAPI/issues)
- **Email**: abelchrisnic@gmail.com
- **在线文档**: [CapCutAPI Docs](https://www.capcutapi.top)

---

**祝您使用愉快！** 🚀

如果这个项目对您有帮助，欢迎 Star ⭐ 项目仓库！
