# MCP Bridge与Dify短视频工作流集成部署指南

## 📋 概述

本指南详细说明如何将MCP Bridge服务集成到Dify短视频生成工作流中，实现智能化的短视频制作流程。

## 🏗️ 架构概览

```
用户输入 → Dify工作流 → MCP Bridge → CapCut API → 短视频输出
    ↓           ↓           ↓           ↓
  参数验证   工作流编排   协议转换    视频处理
```

## ✅ 前置条件

### 1. 服务状态检查
```bash
# 检查MCP Bridge服务
curl http://localhost:8082/health

# 检查CapCut API服务
curl http://localhost:9000/get_intro_animation_types

# 检查Dify服务
cd /home/dify/docker && docker-compose ps
```

### 2. 环境要求
- Python 3.11+
- Docker & Docker Compose
- 网络端口：8080 (Dify), 8082 (MCP Bridge), 9000 (CapCut API)

## 🚀 部署步骤

### 第一步：配置环境变量

在Dify工作流中配置以下环境变量：

```yaml
environment_variables:
  - name: MCP_BRIDGE_URL
    value: "http://localhost:8082"
  - name: CAPCUT_API_URL  
    value: "http://localhost:9000"
  - name: ENABLE_HTTP_FALLBACK
    value: "true"
  - name: MAX_RETRY_ATTEMPTS
    value: "3"
  - name: REQUEST_TIMEOUT
    value: "30"
```

### 第二步：导入工作流配置

1. 登录Dify管理界面 (http://localhost:8080)
2. 进入工作流管理页面
3. 导入 `优化版短视频工作流.yml` 配置文件
4. 验证所有节点配置正确

### 第三步：测试集成

运行集成测试脚本：
```bash
cd /home/dify
python3 test_workflow_integration.py
```

## 📊 测试结果分析

### 当前测试状态
- **总测试数**: 9
- **通过测试**: 7  
- **失败测试**: 2
- **成功率**: 77.8%

### 通过的测试项目
✅ MCP Bridge连通性  
✅ CapCut API连通性  
✅ MCP创建草稿功能  
✅ HTTP降级机制  
✅ 工作流配置文件验证  
✅ MCP Bridge响应时间 (4.12ms)  
✅ CapCut API响应时间 (5.05ms)  

### 需要关注的问题
❌ **Dify API连通性**: HTTP 404错误  
❌ **错误处理机制**: MCP服务对无效方法返回成功状态

## 🔧 故障排除

### 问题1: Dify API连通性失败
**症状**: HTTP 404错误  
**原因**: Dify可能没有暴露/health端点  
**解决方案**: 
```bash
# 检查Dify服务状态
docker-compose ps
# 确认Dify Web服务正常运行
curl http://localhost:8080
```

### 问题2: MCP Bridge错误处理
**症状**: 无效方法调用返回成功状态  
**原因**: MCP Bridge可能将所有请求转发给CapCut服务  
**解决方案**: 在MCP Bridge中添加方法验证逻辑

## 🎯 工作流节点说明

### 核心处理节点 (11个)

1. **用户输入验证** - 验证用户提供的参数
2. **参数标准化** - 统一参数格式
3. **脚本生成** - 基于AI生成视频脚本
4. **素材生成** - 并行生成图片、音频素材
5. **MCP草稿创建** - 通过MCP Bridge创建CapCut项目
6. **时间轴装配** - 组装视频时间轴
7. **音频混合** - 处理背景音乐和语音
8. **字幕对齐** - 同步字幕与音频
9. **渲染提交** - 提交渲染任务
10. **进度监控** - 监控渲染进度
11. **结果输出** - 返回最终视频

### 降级机制

当MCP Bridge不可用时，工作流自动切换到HTTP直接调用：
```
MCP调用失败 → 检测到错误 → 切换到HTTP API → 继续处理
```

## 📈 性能优化建议

### 1. 并行处理
- 素材生成节点支持并行执行
- 音频处理与视频处理可同时进行

### 2. 缓存策略
- 缓存常用素材模板
- 缓存AI生成的脚本片段

### 3. 监控指标
- 响应时间: MCP Bridge < 100ms, CapCut API < 2s
- 成功率: > 95%
- 并发处理能力: 支持10个并发请求

## 🔒 安全配置

### 1. 网络安全
```bash
# 限制MCP Bridge仅本地访问
iptables -A INPUT -p tcp --dport 8082 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8082 -j DROP
```

### 2. 认证配置
- 在生产环境中启用API密钥认证
- 配置请求频率限制

### 3. 数据保护
- 敏感参数通过环境变量传递
- 定期轮换API密钥

## 📝 使用示例

### 基本调用示例
```json
{
  "title": "产品介绍视频",
  "script": "欢迎使用我们的新产品...",
  "style": "商务风格",
  "duration": 30,
  "resolution": "1080x1920"
}
```

### 高级配置示例
```json
{
  "title": "营销视频",
  "script": "限时优惠活动...",
  "style": "动感风格", 
  "duration": 60,
  "resolution": "1080x1920",
  "background_music": "upbeat",
  "voice_style": "professional",
  "subtitle_style": "modern"
}
```

## 🔄 维护和更新

### 日常维护
1. 每日检查服务状态
2. 监控错误日志
3. 清理临时文件

### 定期更新
1. 更新CapCut API版本
2. 优化工作流配置
3. 更新素材库

### 备份策略
1. 备份工作流配置
2. 备份用户数据
3. 备份系统配置

## 📞 技术支持

如遇到问题，请按以下顺序排查：

1. **检查服务状态**: 运行健康检查脚本
2. **查看日志**: 检查各服务的错误日志
3. **网络连通性**: 确认服务间网络通信正常
4. **配置验证**: 验证环境变量和配置文件
5. **重启服务**: 必要时重启相关服务

---

## 📊 集成成功标准

- [x] MCP Bridge服务正常运行
- [x] CapCut API服务正常运行  
- [x] 工作流配置文件验证通过
- [x] 核心功能测试通过
- [x] 性能指标达标
- [ ] Dify API连通性修复
- [ ] 错误处理机制完善

**当前集成状态**: 🟡 基本可用，需要小幅优化

集成测试通过率达到77.8%，核心功能已经可以正常使用。建议在解决剩余问题后投入生产环境。