# 下载API端点删除计划

## 执行日期
2025-11-17

## 删除的端点列表

### 1. 重复的 generate_draft_url_api (行3847-3983)
**位置**: capcut_server.py:3847
**原因**: 与第1423行的 generate_draft_url() 重复，Flask只会使用后面定义的
**影响**: 低，实际上没有被使用
**删除**: ✅ 完全删除

### 2. /api/drafts/download/<draft_id> (行2878-2947)
**位置**: capcut_server.py:2878
**函数**: download_draft_file()
**原因**: 只是内部调用 generate_draft_url_api，多此一举
**影响**: 中，需要检查是否有外部调用
**删除**: ✅ 完全删除

### 3. /api/draft/download/proxy/<draft_id> (行4013-4074)
**位置**: capcut_server.py:4013
**函数**: download_proxy()
**原因**: 与 /api/drafts/download/proxy/ 功能完全重复
**影响**: 中，需要检查使用日志
**删除**: ✅ 完全删除

### 4. /api/draft/download/progress/<task_id> (行3493-3513)
**位置**: capcut_server.py:3493
**函数**: get_download_progress()
**原因**: 只返回模拟数据，未实际实现
**影响**: 低，功能未完成
**删除**: ✅ 完全删除

### 5. /api/draft/download (行3519-3662)
**位置**: capcut_server.py:3519
**函数**: draft_download_api()
**原因**: 功能与其他端点重叠，逻辑混乱
**影响**: 需要验证，检查日志
**删除**: ⚠️ 先添加废弃警告，观察1周后删除

## 保留的端点

### ✅ 核心端点（不删除）

1. **generate_draft_url** (行1423)
   - 路由: POST /generate_draft_url
   - 功能: 智能生成下载链接
   - 状态: 保留并优化

2. **download_draft_proxy** (行3013)
   - 路由: GET /api/drafts/download/proxy/<draft_id>
   - 功能: 代理下载，支持自动修复
   - 状态: 保留并作为核心

3. **batch_download_drafts** (行3302)
   - 路由: POST /api/drafts/batch-download
   - 功能: 批量下载
   - 状态: 保留（高价值功能）

4. **check_draft_exists** (行5091)
   - 路由: GET /api/drafts/check/<draft_id>
   - 功能: 诊断草稿状态
   - 状态: 新增，保留

### ⚠️ 待评估端点

1. **download_draft_to_custom_path** (行3149)
   - 路由: POST /api/drafts/download/custom/<draft_id>
   - 功能: 下载到自定义路径
   - 状态: 检查使用率后决定

## 删除顺序

1. 先删除明确重复的（1, 3, 4）
2. 添加日志监控（2, 5）
3. 观察1周后删除未使用的（2, 5）
4. 评估待定端点使用率

## 回滚方案

如果删除导致问题：
```bash
git checkout refactor/download-api-optimization -- capcut_server.py
```

## 验证步骤

删除后需要验证：
1. ✅ 服务启动无错误
2. ✅ 核心下载功能正常
3. ✅ API文档更新
4. ✅ 日志监控1周无异常
