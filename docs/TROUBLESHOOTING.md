# CapCutAPI 故障排除指南

## 🚨 常见访问问题

### 问题1: "连接被拒绝" 或 "无法访问localhost:9000"

**症状**: 
- 浏览器显示 "连接被拒绝"
- 无法打开 `localhost:9000` 或 `127.0.0.1:9000`
- API调用失败

**原因**: 
您试图在本地机器上访问 `localhost:9000`，但服务实际运行在远程服务器上。

**解决方案**: 
✅ 使用正确的服务器地址：`http://8.148.70.18:9000`

```bash
# 错误的访问方式
curl http://localhost:9000/
curl http://127.0.0.1:9000/

# 正确的访问方式
curl http://8.148.70.18:9000/
```

### 问题2: 草稿预览页面无法打开

**症状**: 
- 草稿预览链接无法访问
- 显示404错误
- 浏览器显示 "ERR_ABORTED" 错误
- 页面加载失败或显示空白

**解决方案**: 
1. 确保使用正确的服务器地址
2. 检查草稿ID是否正确
3. 确认草稿已经创建完成
4. **检查模板渲染问题**（常见原因）

```bash
# 正确的草稿预览URL格式
http://8.148.70.18:9000/draft/preview/[草稿ID]

# 示例
http://8.148.70.18:9000/draft/preview/dfd_cat_1756464075_cf9e91a5

# 如果出现ERR_ABORTED错误，检查服务器日志
sudo journalctl -u capcutapi.service -n 20

# 测试预览页面是否返回正确的HTML
curl -v http://8.148.70.18:9000/draft/preview/[草稿ID]
```

### 问题2.1: 预览页面模板渲染失败

**症状**: 
- 浏览器显示 "ERR_ABORTED" 错误
- 服务器日志显示模板渲染异常
- 页面无法正常加载

**原因**: 
模板文件缺少必需的变量，导致Jinja2模板渲染失败

**解决方案**: 
1. 检查 `preview.html` 模板所需的变量
2. 确保 `render_template_with_official_style` 函数传递所有必需参数
3. 检查 `draft_info` 变量是否正确传递

```bash
# 检查模板中使用的变量
grep -n "{{\|{%" /home/CapCutAPI-1.1.0/templates/preview.html

# 重启服务应用修复
./service_manager.sh restart

# 验证修复效果
curl -I http://8.148.70.18:9000/draft/preview/[草稿ID]
```

### 问题3: API调用返回错误

**症状**: 
- API返回500错误
- 请求超时

**解决方案**: 
1. 检查请求URL是否正确
2. 确认请求方法（GET/POST）
3. 检查请求参数格式

```bash
# 测试API连接
curl -v http://8.148.70.18:9000/get_intro_animation_types

# 测试服务状态
curl -H "Accept: application/json" http://8.148.70.18:9000/
```

## 🔧 服务器端检查

### 检查服务状态

```bash
# 检查服务是否运行
sudo systemctl status capcutapi.service

# 检查端口监听
netstat -tlnp | grep 9000

# 查看服务日志
sudo journalctl -u capcutapi.service -f
```

### 重启服务

```bash
# 使用服务管理脚本（推荐）
./service_manager.sh restart

# 或者使用systemctl
sudo systemctl restart capcutapi.service
```

## 🚀 服务启动和配置问题

### 问题4: 服务启动失败

**症状**: 
- `systemctl status capcutapi.service` 显示失败状态
- 服务无法启动或立即退出
- 端口9000没有被监听

**常见原因和解决方案**: 

1. **Python依赖缺失**
```bash
# 检查虚拟环境
source /home/CapCutAPI-1.1.0/venv/bin/activate
pip list | grep -E "flask|requests|oss2|imageio|psutil"

# 重新安装依赖
pip install -r requirements.txt
```

2. **配置文件问题**
```bash
# 检查配置文件是否存在
ls -la /home/CapCutAPI-1.1.0/config.json

# 验证配置文件格式
python3 -c "import json; print(json.load(open('config.json')))"
```

3. **权限问题**
```bash
# 检查文件权限
ls -la /home/CapCutAPI-1.1.0/capcut_server.py

# 修复权限
chmod +x /home/CapCutAPI-1.1.0/capcut_server.py
chown -R $(whoami):$(whoami) /home/CapCutAPI-1.1.0/
```

4. **端口被占用**
```bash
# 检查端口占用
sudo lsof -i :9000

# 杀死占用进程（如果需要）
sudo kill -9 <PID>
```

### 问题5: 模板和静态文件问题

**症状**: 
- 页面显示不正常
- 缺少样式或脚本
- 模板渲染错误

**解决方案**: 
```bash
# 检查模板目录结构
ls -la /home/CapCutAPI-1.1.0/templates/

# 检查静态文件目录
ls -la /home/CapCutAPI-1.1.0/static/

# 验证模板文件语法
python3 -c "from jinja2 import Template; Template(open('templates/preview.html').read())"
```

## 🌐 网络连接测试

### 从本地测试服务器连接

```bash
# Windows (命令提示符)
telnet 8.148.70.18 9000

# Windows (PowerShell)
Test-NetConnection -ComputerName 8.148.70.18 -Port 9000

# Linux/macOS
nc -zv 8.148.70.18 9000
```

### 防火墙检查

```bash
# 检查防火墙状态
sudo firewall-cmd --list-ports

# 如果需要开放端口
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --reload
```

## 📝 日志分析

### 应用日志位置

```bash
# 系统服务日志
sudo journalctl -u capcutapi.service -n 50

# 应用日志（如果配置了）
tail -f /home/CapCutAPI-1.1.0/logs/capcutapi.log
```

### 常见错误信息

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|----------|
| Connection refused | 服务未启动或端口未开放 | 检查服务状态，重启服务 |
| 404 Not Found | URL路径错误 | 检查API端点是否正确 |
| 500 Internal Server Error | 服务器内部错误 | 查看服务日志，检查配置 |
| Timeout | 网络连接问题 | 检查网络连接和防火墙 |
| ERR_ABORTED | 模板渲染失败 | 检查模板变量，重启服务 |
| TemplateNotFound | 模板文件缺失 | 检查templates目录和文件 |
| UndefinedError | 模板变量未定义 | 检查函数参数传递 |
| ModuleNotFoundError | Python依赖缺失 | 重新安装依赖包 |

## 🆘 获取帮助

### 收集诊断信息

```bash
# 服务状态
sudo systemctl status capcutapi.service

# 端口监听
netstat -tlnp | grep 9000

# 最近的日志
sudo journalctl -u capcutapi.service -n 20

# 系统信息
uname -a
python3 --version
```

### 快速测试脚本

```bash
#!/bin/bash
echo "=== CapCutAPI 诊断测试 ==="
echo "1. 检查服务状态..."
sudo systemctl is-active capcutapi.service

echo "2. 检查端口监听..."
netstat -tlnp | grep 9000

echo "3. 测试本地连接..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/ || echo "本地连接失败"

echo "4. 测试外部连接..."
curl -s -o /dev/null -w "%{http_code}" http://8.148.70.18:9000/ || echo "外部连接失败"

echo "=== 诊断完成 ==="
```

## 🔄 故障排除流程

### 快速诊断流程

```
1. 检查服务状态
   ↓
2. 服务运行正常？
   ├─ 否 → 检查启动问题（问题4）
   └─ 是 → 继续
   ↓
3. 端口监听正常？
   ├─ 否 → 检查端口占用
   └─ 是 → 继续
   ↓
4. 网络连接正常？
   ├─ 否 → 检查防火墙设置
   └─ 是 → 继续
   ↓
5. API响应正常？
   ├─ 否 → 检查日志错误
   └─ 是 → 继续
   ↓
6. 预览页面正常？
   ├─ 否 → 检查模板渲染（问题2.1）
   └─ 是 → 问题解决
```

### 一键诊断脚本

创建并运行以下诊断脚本：

```bash
#!/bin/bash
# 保存为 diagnose.sh
echo "=== CapCutAPI 完整诊断 ==="
echo "时间: $(date)"
echo ""

echo "1. 检查服务状态..."
sudo systemctl is-active capcutapi.service
sudo systemctl status capcutapi.service --no-pager -l
echo ""

echo "2. 检查端口监听..."
netstat -tlnp | grep 9000
echo ""

echo "3. 检查进程..."
ps aux | grep capcut_server
echo ""

echo "4. 检查配置文件..."
if [ -f "config.json" ]; then
    echo "✅ config.json 存在"
    python3 -c "import json; json.load(open('config.json'))" && echo "✅ 配置文件格式正确" || echo "❌ 配置文件格式错误"
else
    echo "❌ config.json 不存在"
fi
echo ""

echo "5. 检查依赖..."
source venv/bin/activate 2>/dev/null || echo "⚠️  虚拟环境未激活"
pip list | grep -E "flask|requests|oss2|imageio|psutil" || echo "❌ 缺少关键依赖"
echo ""

echo "6. 测试API连接..."
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:9000/ 2>/dev/null || echo "❌ 本地连接失败"
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://8.148.70.18:9000/ 2>/dev/null || echo "❌ 外部连接失败"
echo ""

echo "7. 检查最近日志..."
sudo journalctl -u capcutapi.service -n 10 --no-pager
echo ""

echo "=== 诊断完成 ==="
```

## 📞 联系支持

如果以上解决方案都无法解决您的问题，请提供以下信息：

1. 错误的具体描述和截图
2. 您使用的操作系统和版本
3. 访问的完整URL
4. 完整的错误日志
5. 诊断脚本的输出结果
6. 问题出现的具体步骤

---

**最后更新**: 2025年1月19日  
**版本**: v1.1  
**适用于**: CapCutAPI v1.2.0+  
**更新内容**: 添加预览页面模板渲染问题、服务启动问题、完整诊断流程