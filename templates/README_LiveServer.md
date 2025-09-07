# 📋 Live Server 预览说明

## 🔍 **问题说明**

当您使用VS Code的Live Server扩展预览`dashboard.html`时遇到问题，这是因为：

### 为什么原始dashboard.html不能直接预览：
1. **Flask模板语法**: 使用了`{{ }}`等Jinja2模板语法，需要Flask服务器解析
2. **API依赖**: 页面需要从后端API (`/api/drafts/list`) 获取真实数据
3. **相对路径**: 模板中的路径需要Flask路由系统来正确解析

## ✅ **解决方案**

### 方案1: 使用静态预览版本 (推荐用于界面设计)
```bash
# 在VS Code中打开这个文件，然后右键 "Open with Live Server"
templates/dashboard_static_preview.html
```

**特点**:
- ✅ 可以在Live Server中正常预览
- ✅ 显示完整的界面设计效果
- ✅ 包含示例数据和交互提示
- ⚠️ 功能是模拟的，不连接真实API

### 方案2: 使用真实服务器 (推荐用于功能测试)
```bash
# 在浏览器中直接访问
http://8.148.70.18:9000/api/drafts/dashboard
```

**特点**:
- ✅ 完整的功能实现
- ✅ 真实的数据展示
- ✅ 所有交互功能可用
- ✅ 连接后端API服务

## 🛠️ **VS Code Live Server 配置**

### 如果要预览静态版本：
1. 右键点击 `dashboard_static_preview.html`
2. 选择 "Open with Live Server"
3. 或使用快捷键 `Alt+L Alt+O`

### 如果要预览真实功能：
1. 确保CapCutAPI服务正在运行
2. 在浏览器中访问: `http://8.148.70.18:9000/api/drafts/dashboard`

## 📂 **文件说明**

| 文件 | 用途 | Live Server支持 |
|------|------|----------------|
| `dashboard.html` | Flask模板文件 | ❌ 需要Flask服务器 |
| `dashboard_static_preview.html` | 静态预览版本 | ✅ 完全支持 |
| `preview.html` | 草稿预览模板 | ❌ 需要Flask服务器 |
| `index.html` | 主页模板 | ❌ 需要Flask服务器 |

## 💡 **开发建议**

### 用于界面设计和样式调试：
- 使用 `dashboard_static_preview.html` + Live Server
- 快速查看CSS效果和响应式设计
- 测试交互动画和布局

### 用于功能测试：
- 使用真实服务器地址
- 测试API调用和数据展示
- 验证业务逻辑和用户流程

## 🔧 **常见问题解决**

### Q: Live Server显示空白页面？
A: 检查是否使用了Flask模板语法，使用静态预览版本

### Q: 数据无法加载？
A: 静态预览版本使用示例数据，真实数据需要访问服务器

### Q: 按钮点击没有反应？
A: 静态版本只有提示功能，真实功能需要后端支持

### Q: 路径错误？
A: 确保Live Server的根目录设置正确，或使用绝对路径

## 🌟 **最佳实践**

1. **界面开发**: 使用静态预览版本快速迭代设计
2. **功能测试**: 使用真实服务器验证完整流程  
3. **版本控制**: 保持两个版本同步更新
4. **文档维护**: 及时更新静态版本的示例数据


