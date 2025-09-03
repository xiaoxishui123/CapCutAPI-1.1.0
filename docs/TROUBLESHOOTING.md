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

**解决方案**: 
1. 确保使用正确的服务器地址
2. 检查草稿ID是否正确
3. 确认草稿已经创建完成

```bash
# 正确的草稿预览URL格式
http://8.148.70.18:9000/draft/preview/[草稿ID]

# 示例
http://8.148.70.18:9000/draft/preview/dfd_cat_1756464075_cf9e91a5
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
# 使用服务管理脚本
./service_manager.sh restart

# 或者使用systemctl
sudo systemctl restart capcutapi.service
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

## 📞 联系支持

如果以上解决方案都无法解决您的问题，请提供以下信息：

1. 错误的具体描述
2. 您使用的操作系统
3. 访问的完整URL
4. 错误截图或日志
5. 诊断脚本的输出结果

---

**最后更新**: 2025年1月19日  
**版本**: v1.0  
**适用于**: CapCutAPI v1.2.0+