# 异步保存优化 - 最佳实践方案

## 📋 目录

1. [问题分析](#问题分析)
2. [解决方案架构](#解决方案架构)
3. [后端优化](#后端优化)
4. [前端优化](#前端优化)
5. [实施步骤](#实施步骤)
6. [测试验证](#测试验证)
7. [监控告警](#监控告警)

---

## 🎯 问题分析

### 当前痛点

```
问题：用户在文件未上传完成时就尝试下载 → 404 错误

根本原因：
├─ 后端：异步保存，API 立即返回
├─ 前端：缺少状态轮询机制
├─ 用户：不知道保存进度
└─ 结果：过早下载 → 文件不存在
```

### 关键指标

| 指标 | 当前状态 | 目标状态 |
|------|---------|---------|
| 下载成功率 | ~70% (估计) | >99% |
| 用户等待体验 | 不可知 | 可视化进度 |
| 错误提示 | 404 Generic | 明确原因+建议 |
| 平均保存时间 | 60-120s | 优化到 40-80s |

---

## 🏗️ 解决方案架构

### 整体设计思路

```
┌─────────────────────────────────────────────────────────┐
│                    多层防护机制                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  第1层：前端智能等待                                      │
│  ├─ 实时状态轮询                                         │
│  ├─ 进度可视化                                           │
│  └─ 智能按钮控制                                         │
│                                                          │
│  第2层：后端状态增强                                      │
│  ├─ 细粒度状态管理                                       │
│  ├─ 文件存在性校验                                       │
│  └─ 原子性状态更新                                       │
│                                                          │
│  第3层：下载预检查                                        │
│  ├─ 下载前验证文件                                       │
│  ├─ 自动重试机制                                         │
│  └─ 降级方案                                             │
│                                                          │
│  第4层：监控告警                                          │
│  ├─ 性能监控                                             │
│  ├─ 异常告警                                             │
│  └─ 用户行为分析                                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 后端优化

### 优化1：改进状态管理

#### 当前状态模型（简单）
```python
状态：initialized → processing → completed/failed
进度：0% → 10% → 90% → 100%
```

#### 优化后的状态模型（细粒度）
```python
状态：
├─ initialized (0%)      - 任务已创建
├─ downloading (10-40%)  - 正在下载素材
├─ compressing (40-70%)  - 正在压缩文件
├─ uploading (70-95%)    - 正在上传 OSS
├─ verifying (95-99%)    - 正在验证文件
└─ completed (100%)      - 已完成并验证

额外字段：
├─ oss_uploaded: bool    - OSS 是否上传成功
├─ oss_verified: bool    - OSS 文件是否验证通过
├─ file_size: int        - 文件大小
└─ estimated_time: int   - 预估剩余时间
```

#### 实现代码

**第一步：扩展数据库表**

```python
# database.py

def migrate_drafts_table():
    """迁移 drafts 表，添加新字段"""
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()

    try:
        # 添加新字段
        c.execute("ALTER TABLE drafts ADD COLUMN oss_uploaded INTEGER DEFAULT 0")
        c.execute("ALTER TABLE drafts ADD COLUMN oss_verified INTEGER DEFAULT 0")
        c.execute("ALTER TABLE drafts ADD COLUMN file_size INTEGER DEFAULT 0")
        c.execute("ALTER TABLE drafts ADD COLUMN estimated_time INTEGER DEFAULT 0")
        c.execute("ALTER TABLE drafts ADD COLUMN detailed_status TEXT DEFAULT ''")

        conn.commit()
        print("✅ 数据库迁移成功")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ 字段已存在，跳过迁移")
        else:
            raise
    finally:
        conn.close()


def update_draft_status_enhanced(
    draft_id: str,
    status: str,
    progress: int = 0,
    message: str = '',
    oss_uploaded: bool = False,
    oss_verified: bool = False,
    file_size: int = 0,
    estimated_time: int = 0
):
    """
    增强版状态更新函数

    Args:
        draft_id: 草稿ID
        status: 状态 (initialized, downloading, compressing, uploading, verifying, completed, failed)
        progress: 进度 (0-100)
        message: 消息
        oss_uploaded: OSS 是否上传成功
        oss_verified: OSS 文件是否验证
        file_size: 文件大小（字节）
        estimated_time: 预估剩余时间（秒）
    """
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()

    c.execute("""
        UPDATE drafts
        SET status = ?,
            progress = ?,
            message = ?,
            oss_uploaded = ?,
            oss_verified = ?,
            file_size = ?,
            estimated_time = ?,
            detailed_status = ?,
            last_modified = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        status,
        progress,
        message,
        1 if oss_uploaded else 0,
        1 if oss_verified else 0,
        file_size,
        estimated_time,
        status,  # detailed_status
        draft_id
    ))

    conn.commit()
    conn.close()
```

**第二步：改进保存流程**

```python
# save_draft_impl.py

import time
import os

def save_draft_background_v2(draft_id: str, draft_folder: str, task_id: str, client_os: str = "windows"):
    """
    改进的后台保存函数 - 增加详细状态和时间预估
    """
    start_time = time.time()

    try:
        # 阶段1: 初始化 (0-5%)
        update_draft_status_enhanced(
            draft_id, 'initialized', 0, '正在初始化',
            estimated_time=120  # 预估 2 分钟
        )

        script = get_draft(draft_id)
        if script is None:
            raise Exception(f"Draft {draft_id} does not exist in cache or database")

        # 阶段2: 下载素材 (5-40%)
        materials_count = len(script.materials.audios or []) + len(script.materials.videos or [])
        update_draft_status_enhanced(
            draft_id, 'downloading', 5, f'正在下载 {materials_count} 个素材',
            estimated_time=int(materials_count * 3)  # 每个素材约 3 秒
        )

        # ... 下载素材的代码 ...

        # 阶段3: 压缩文件 (40-70%)
        update_draft_status_enhanced(
            draft_id, 'compressing', 40, '正在压缩草稿文件',
            estimated_time=30
        )

        # ... 压缩文件的代码 ...
        zip_file_path = os.path.join(current_dir, f"{draft_id}.zip")
        file_size = os.path.getsize(zip_file_path)

        # 阶段4: 上传 OSS (70-95%)
        if IS_UPLOAD_DRAFT and not is_custom_download:
            # 根据文件大小预估上传时间（假设 1MB/s）
            estimated_upload_time = int(file_size / 1024 / 1024)

            update_draft_status_enhanced(
                draft_id, 'uploading', 70, '正在上传至云存储',
                file_size=file_size,
                estimated_time=estimated_upload_time
            )

            upload_start = time.time()
            draft_url = upload_to_oss(zip_file_path)
            upload_elapsed = time.time() - upload_start

            logger.info(f"[{draft_id}] OSS 上传完成: {file_size/1024/1024:.2f}MB, 耗时: {upload_elapsed:.2f}s")

            # 🔧 关键改进：上传成功后立即标记
            update_draft_status_enhanced(
                draft_id, 'uploading', 95, 'OSS 上传完成',
                oss_uploaded=True,
                file_size=file_size,
                estimated_time=5
            )

            # 阶段5: 验证文件 (95-99%)
            update_draft_status_enhanced(
                draft_id, 'verifying', 95, '正在验证文件完整性',
                oss_uploaded=True,
                file_size=file_size,
                estimated_time=3
            )

            # 🆕 新增：验证 OSS 文件是否真的存在
            if verify_oss_file(draft_id):
                update_draft_status_enhanced(
                    draft_id, 'verifying', 99, '文件验证通过',
                    oss_uploaded=True,
                    oss_verified=True,
                    file_size=file_size,
                    estimated_time=0
                )
            else:
                raise Exception("OSS 文件验证失败：文件不存在或不完整")

        # 阶段6: 完成 (100%)
        elapsed = time.time() - start_time
        update_draft_status_enhanced(
            draft_id, 'completed', 100, draft_url,
            oss_uploaded=IS_UPLOAD_DRAFT,
            oss_verified=IS_UPLOAD_DRAFT,
            file_size=file_size,
            estimated_time=0
        )

        logger.info(f"[{draft_id}] 保存完成，总耗时: {elapsed:.2f}s")

    except Exception as e:
        logger.error(f"Saving draft {draft_id} failed: {e}", exc_info=True)
        update_draft_status_enhanced(
            draft_id, 'failed', 0, f'保存失败: {str(e)}'
        )


def verify_oss_file(draft_id: str) -> bool:
    """
    验证 OSS 文件是否存在且完整

    Returns:
        bool: 文件存在且完整返回 True
    """
    try:
        from oss import _ensure_bucket

        bucket = _ensure_bucket()
        key = f"{draft_id}.zip"

        # 检查文件是否存在
        if not bucket.object_exists(key):
            logger.error(f"[验证] OSS 文件不存在: {key}")
            return False

        # 获取文件元数据
        meta = bucket.head_object(key)
        file_size = meta.content_length

        logger.info(f"[验证] OSS 文件存在: {key}, 大小: {file_size/1024/1024:.2f}MB")

        # 验证文件大小（至少 1KB）
        if file_size < 1024:
            logger.error(f"[验证] OSS 文件过小，可能损坏: {file_size} bytes")
            return False

        return True

    except Exception as e:
        logger.error(f"[验证] OSS 文件验证失败: {e}")
        return False
```

### 优化2：下载预检查机制

```python
# services/download_service.py

def get_download_url_v2(self, draft_id: str, client_os: str = 'windows',
                        draft_folder: str = '', max_wait: int = 30) -> Dict:
    """
    改进的下载链接生成 - 自动等待保存完成

    Args:
        draft_id: 草稿ID
        client_os: 客户端系统
        draft_folder: 草稿文件夹
        max_wait: 最大等待时间（秒），0表示不等待

    Returns:
        Dict: 下载结果
    """
    try:
        from customize_zip import get_customized_signed_url
        from oss import get_signed_draft_url_if_exists
        from settings.local import IS_UPLOAD_DRAFT
        import time

        # 🆕 步骤1: 检查草稿状态
        status_info = self._check_draft_status(draft_id)

        if status_info['status'] == 'completed' and status_info.get('oss_verified'):
            # 文件已完成并验证，直接生成下载链接
            logger.info(f"[下载] 草稿已完成验证，直接生成链接: {draft_id}")

        elif status_info['status'] in ['downloading', 'compressing', 'uploading', 'verifying']:
            # 🆕 步骤2: 如果正在处理，智能等待
            if max_wait > 0:
                logger.info(f"[下载] 草稿正在处理，等待最多 {max_wait}秒: {draft_id}")

                waited = 0
                while waited < max_wait:
                    time.sleep(2)
                    waited += 2

                    status_info = self._check_draft_status(draft_id)

                    if status_info['status'] == 'completed' and status_info.get('oss_verified'):
                        logger.info(f"[下载] 等待 {waited}秒后草稿完成: {draft_id}")
                        break

                    logger.debug(f"[下载] 等待中... {status_info['status']} {status_info.get('progress', 0)}%")

                if status_info['status'] != 'completed':
                    # 超时仍未完成
                    return {
                        'success': False,
                        'error': f'草稿正在处理中，当前状态: {status_info["status"]}',
                        'status': status_info['status'],
                        'progress': status_info.get('progress', 0),
                        'estimated_time': status_info.get('estimated_time', 0),
                        'suggestion': f'请等待约 {status_info.get("estimated_time", 30)} 秒后重试'
                    }
            else:
                # 不等待，直接返回状态
                return {
                    'success': False,
                    'error': f'草稿正在处理中: {status_info["message"]}',
                    'status': status_info['status'],
                    'progress': status_info.get('progress', 0),
                    'estimated_time': status_info.get('estimated_time', 0),
                    'suggestion': '请稍后重试或使用状态轮询'
                }

        # 🆕 步骤3: 生成下载链接前再次验证
        if IS_UPLOAD_DRAFT:
            signed_url, exists = get_signed_draft_url_if_exists(draft_id)

            if exists and signed_url:
                # 定制化处理
                if draft_folder or client_os != 'windows':
                    try:
                        custom_url = get_customized_signed_url(draft_id, client_os, draft_folder)
                        return {
                            'success': True,
                            'draft_url': custom_url,
                            'storage': 'oss',
                            'file_size': status_info.get('file_size', 0),
                            'verified': True
                        }
                    except FileNotFoundError as e:
                        logger.error(f"基础草稿文件不存在: {e}")
                        return {
                            'success': False,
                            'error': f'基础草稿文件不存在: {draft_id}',
                            'error_type': 'FILE_NOT_FOUND',
                            'suggestion': '文件可能正在上传或已被删除，请重新保存草稿'
                        }

                # 返回基础URL
                return {
                    'success': True,
                    'draft_url': signed_url,
                    'storage': 'oss',
                    'file_size': status_info.get('file_size', 0),
                    'verified': True
                }

        # 本地模式
        from settings.local import DRAFT_DOMAIN, PREVIEW_ROUTER
        from urllib.parse import quote
        safe_id = quote(draft_id, safe='-_.')

        return {
            'success': True,
            'draft_url': f"{DRAFT_DOMAIN}{PREVIEW_ROUTER}?draft_id={safe_id}",
            'storage': 'local'
        }

    except Exception as e:
        logger.error(f"生成下载链接失败: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def _check_draft_status(self, draft_id: str) -> Dict:
    """检查草稿详细状态"""
    import sqlite3

    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()

    c.execute("""
        SELECT status, progress, message, oss_uploaded, oss_verified,
               file_size, estimated_time
        FROM drafts
        WHERE id = ?
    """, (draft_id,))

    result = c.fetchone()
    conn.close()

    if result:
        return {
            'status': result[0],
            'progress': result[1],
            'message': result[2],
            'oss_uploaded': bool(result[3]),
            'oss_verified': bool(result[4]),
            'file_size': result[5] or 0,
            'estimated_time': result[6] or 0
        }

    return {
        'status': 'not_found',
        'progress': 0,
        'message': '草稿不存在'
    }
```

### 优化3：改进 API 端点

```python
# capcut_server.py

@app.route('/api/v2/drafts/<draft_id>/download', methods=['GET'])
def download_draft_v2(draft_id):
    """
    V2 版本下载端点 - 智能等待机制

    查询参数:
        - client_os: 客户端系统 (默认 windows)
        - draft_folder: 草稿文件夹 (可选)
        - wait: 最大等待时间，秒 (默认 30，0表示不等待)

    响应:
        成功: 重定向到下载URL
        处理中: 返回状态和预估时间
        失败: 返回错误信息
    """
    try:
        client_os = request.args.get('client_os', 'windows')
        draft_folder = request.args.get('draft_folder', '')
        max_wait = int(request.args.get('wait', '30'))

        service = get_download_service()
        result = service.get_download_url_v2(
            draft_id=draft_id,
            client_os=client_os,
            draft_folder=draft_folder,
            max_wait=max_wait
        )

        if result['success']:
            # 成功 - 重定向到下载URL
            return redirect(result['draft_url'])
        else:
            # 失败或处理中
            status_code = 202 if result.get('status') in ['downloading', 'compressing', 'uploading', 'verifying'] else 404

            return jsonify(result), status_code

    except Exception as e:
        logger.error(f"[v2] 下载失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/drafts/<draft_id>/status', methods=['GET'])
def get_draft_status_v2(draft_id):
    """
    获取草稿详细状态 - 用于前端轮询

    响应:
        {
            "draft_id": "xxx",
            "status": "uploading",
            "progress": 85,
            "message": "正在上传至云存储",
            "oss_uploaded": false,
            "oss_verified": false,
            "file_size": 25753138,
            "estimated_time": 15,
            "ready_for_download": false
        }
    """
    try:
        service = get_download_service()
        status_info = service._check_draft_status(draft_id)

        # 判断是否可以下载
        ready_for_download = (
            status_info['status'] == 'completed' and
            status_info.get('oss_verified', False)
        )

        return jsonify({
            'draft_id': draft_id,
            'status': status_info['status'],
            'progress': status_info['progress'],
            'message': status_info['message'],
            'oss_uploaded': status_info.get('oss_uploaded', False),
            'oss_verified': status_info.get('oss_verified', False),
            'file_size': status_info.get('file_size', 0),
            'estimated_time': status_info.get('estimated_time', 0),
            'ready_for_download': ready_for_download
        })

    except Exception as e:
        logger.error(f"获取状态失败: {e}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500
```

---

## 🎨 前端优化

### 方案A：原生 JavaScript 实现

```html
<!-- templates/draft_manager.html -->

<!DOCTYPE html>
<html>
<head>
    <title>草稿管理器</title>
    <style>
        .draft-card {
            border: 1px solid #ddd;
            padding: 20px;
            margin: 10px 0;
            border-radius: 8px;
        }

        .progress-container {
            width: 100%;
            background-color: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }

        .progress-bar {
            height: 24px;
            background-color: #4CAF50;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }

        .status-downloading { background-color: #2196F3; color: white; }
        .status-compressing { background-color: #FF9800; color: white; }
        .status-uploading { background-color: #9C27B0; color: white; }
        .status-verifying { background-color: #00BCD4; color: white; }
        .status-completed { background-color: #4CAF50; color: white; }
        .status-failed { background-color: #F44336; color: white; }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin: 5px;
        }

        .btn-primary {
            background-color: #4CAF50;
            color: white;
        }

        .btn-primary:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }

        .btn-secondary {
            background-color: #2196F3;
            color: white;
        }

        .estimated-time {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>草稿管理器</h1>

    <div id="drafts-container"></div>

    <script>
        class DraftManager {
            constructor(draftId, containerId) {
                this.draftId = draftId;
                this.container = document.getElementById(containerId);
                this.statusCheckInterval = null;
                this.isDownloading = false;
            }

            /**
             * 渲染草稿卡片
             */
            render(statusData) {
                const card = document.createElement('div');
                card.className = 'draft-card';
                card.id = `draft-${this.draftId}`;

                card.innerHTML = `
                    <h3>草稿 ID: ${this.draftId}</h3>

                    <div class="status-line">
                        <span class="status-badge status-${statusData.status}">
                            ${this.getStatusText(statusData.status)}
                        </span>
                        <span style="margin-left: 10px;">
                            ${statusData.message}
                        </span>
                    </div>

                    <div class="progress-container">
                        <div class="progress-bar" style="width: ${statusData.progress}%">
                            ${statusData.progress}%
                        </div>
                    </div>

                    ${statusData.estimated_time > 0 ? `
                        <div class="estimated-time">
                            ⏱️ 预计还需 ${statusData.estimated_time} 秒
                        </div>
                    ` : ''}

                    ${statusData.file_size > 0 ? `
                        <div class="file-info">
                            📦 文件大小: ${this.formatFileSize(statusData.file_size)}
                        </div>
                    ` : ''}

                    <div class="actions">
                        <button
                            class="btn btn-primary"
                            id="download-btn-${this.draftId}"
                            ${!statusData.ready_for_download ? 'disabled' : ''}
                            onclick="draftManagers['${this.draftId}'].download()">
                            ${statusData.ready_for_download ? '下载草稿' : '等待保存完成...'}
                        </button>

                        <button
                            class="btn btn-secondary"
                            onclick="draftManagers['${this.draftId}'].checkStatus()">
                            刷新状态
                        </button>
                    </div>
                `;

                // 更新或插入卡片
                const existingCard = document.getElementById(`draft-${this.draftId}`);
                if (existingCard) {
                    existingCard.innerHTML = card.innerHTML;
                } else {
                    this.container.appendChild(card);
                }
            }

            /**
             * 检查草稿状态
             */
            async checkStatus() {
                try {
                    const response = await fetch(`/api/v2/drafts/${this.draftId}/status`);
                    const data = await response.json();

                    this.render(data);

                    return data;
                } catch (error) {
                    console.error('检查状态失败:', error);
                    return null;
                }
            }

            /**
             * 开始状态轮询
             */
            startStatusPolling(interval = 2000) {
                if (this.statusCheckInterval) {
                    return; // 已经在轮询中
                }

                console.log(`开始轮询草稿状态: ${this.draftId}`);

                // 立即检查一次
                this.checkStatus();

                // 定期检查
                this.statusCheckInterval = setInterval(async () => {
                    const status = await this.checkStatus();

                    // 如果已完成，停止轮询
                    if (status && (status.status === 'completed' || status.status === 'failed')) {
                        this.stopStatusPolling();
                    }
                }, interval);
            }

            /**
             * 停止状态轮询
             */
            stopStatusPolling() {
                if (this.statusCheckInterval) {
                    console.log(`停止轮询草稿状态: ${this.draftId}`);
                    clearInterval(this.statusCheckInterval);
                    this.statusCheckInterval = null;
                }
            }

            /**
             * 下载草稿
             */
            async download() {
                if (this.isDownloading) {
                    alert('正在下载中，请稍候...');
                    return;
                }

                try {
                    this.isDownloading = true;

                    // 使用 V2 端点，带智能等待
                    const url = `/api/v2/drafts/${this.draftId}/download?wait=30`;

                    // 直接跳转下载
                    window.location.href = url;

                    // 3秒后重置下载状态
                    setTimeout(() => {
                        this.isDownloading = false;
                    }, 3000);

                } catch (error) {
                    console.error('下载失败:', error);
                    alert('下载失败: ' + error.message);
                    this.isDownloading = false;
                }
            }

            /**
             * 保存草稿
             */
            async save() {
                try {
                    const response = await fetch('/save_draft', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            draft_id: this.draftId
                        })
                    });

                    const result = await response.json();

                    if (result.success) {
                        alert('保存任务已启动');

                        // 开始轮询状态
                        this.startStatusPolling();
                    } else {
                        alert('保存失败: ' + result.error);
                    }

                } catch (error) {
                    console.error('保存失败:', error);
                    alert('保存失败: ' + error.message);
                }
            }

            /**
             * 工具函数
             */
            getStatusText(status) {
                const statusMap = {
                    'initialized': '初始化',
                    'downloading': '下载素材',
                    'compressing': '压缩文件',
                    'uploading': '上传云端',
                    'verifying': '验证文件',
                    'completed': '已完成',
                    'failed': '失败'
                };
                return statusMap[status] || status;
            }

            formatFileSize(bytes) {
                if (bytes < 1024) return bytes + ' B';
                if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
                if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB';
                return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB';
            }
        }

        // 全局管理器实例
        const draftManagers = {};

        /**
         * 初始化示例
         */
        function initExample() {
            // 示例：创建一个草稿管理器
            const draftId = 'dfd_cat_1763436047_920e2b1e';
            const manager = new DraftManager(draftId, 'drafts-container');
            draftManagers[draftId] = manager;

            // 开始轮询状态
            manager.startStatusPolling();
        }

        // 页面加载时初始化
        window.onload = initExample;
    </script>
</body>
</html>
```

### 方案B：React 组件实现

```jsx
// components/DraftCard.jsx

import React, { useState, useEffect, useCallback } from 'react';

const DraftCard = ({ draftId }) => {
    const [status, setStatus] = useState({
        status: 'checking',
        progress: 0,
        message: '检查中...',
        ready_for_download: false,
        file_size: 0,
        estimated_time: 0
    });

    const [isPolling, setIsPolling] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);

    // 检查状态
    const checkStatus = useCallback(async () => {
        try {
            const response = await fetch(`/api/v2/drafts/${draftId}/status`);
            const data = await response.json();
            setStatus(data);
            return data;
        } catch (error) {
            console.error('检查状态失败:', error);
            return null;
        }
    }, [draftId]);

    // 状态轮询
    useEffect(() => {
        if (!isPolling) return;

        const interval = setInterval(async () => {
            const data = await checkStatus();

            // 完成或失败时停止轮询
            if (data && (data.status === 'completed' || data.status === 'failed')) {
                setIsPolling(false);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [isPolling, checkStatus]);

    // 初始检查
    useEffect(() => {
        checkStatus();
    }, [checkStatus]);

    // 下载草稿
    const handleDownload = async () => {
        if (isDownloading) return;

        setIsDownloading(true);

        // 使用 V2 端点
        window.location.href = `/api/v2/drafts/${draftId}/download?wait=30`;

        setTimeout(() => {
            setIsDownloading(false);
        }, 3000);
    };

    // 保存草稿
    const handleSave = async () => {
        try {
            const response = await fetch('/save_draft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ draft_id: draftId })
            });

            const result = await response.json();

            if (result.success) {
                setIsPolling(true);
            } else {
                alert('保存失败: ' + result.error);
            }
        } catch (error) {
            alert('保存失败: ' + error.message);
        }
    };

    // 格式化文件大小
    const formatFileSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
        if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
        return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
    };

    // 状态文本映射
    const statusText = {
        'initialized': '初始化',
        'downloading': '下载素材',
        'compressing': '压缩文件',
        'uploading': '上传云端',
        'verifying': '验证文件',
        'completed': '已完成',
        'failed': '失败'
    };

    return (
        <div className="draft-card">
            <h3>草稿 ID: {draftId}</h3>

            <div className="status-line">
                <span className={`status-badge status-${status.status}`}>
                    {statusText[status.status] || status.status}
                </span>
                <span style={{ marginLeft: '10px' }}>
                    {status.message}
                </span>
            </div>

            <div className="progress-container">
                <div
                    className="progress-bar"
                    style={{ width: `${status.progress}%` }}
                >
                    {status.progress}%
                </div>
            </div>

            {status.estimated_time > 0 && (
                <div className="estimated-time">
                    ⏱️ 预计还需 {status.estimated_time} 秒
                </div>
            )}

            {status.file_size > 0 && (
                <div className="file-info">
                    📦 文件大小: {formatFileSize(status.file_size)}
                </div>
            )}

            <div className="actions">
                <button
                    className="btn btn-primary"
                    disabled={!status.ready_for_download}
                    onClick={handleDownload}
                >
                    {status.ready_for_download ? '下载草稿' : '等待保存完成...'}
                </button>

                <button
                    className="btn btn-secondary"
                    onClick={() => checkStatus()}
                >
                    刷新状态
                </button>

                <button
                    className="btn btn-secondary"
                    onClick={handleSave}
                >
                    重新保存
                </button>
            </div>

            {isPolling && (
                <div className="polling-indicator">
                    🔄 实时监控中...
                </div>
            )}
        </div>
    );
};

export default DraftCard;
```

---

## 📋 实施步骤

### 阶段1：数据库迁移（预计 10分钟）

```bash
# 步骤1：备份数据库
cp capcut.db capcut.db.backup.$(date +%Y%m%d_%H%M%S)

# 步骤2：运行迁移脚本
python3 << 'EOF'
from database import migrate_drafts_table
migrate_drafts_table()
EOF

# 步骤3：验证迁移
sqlite3 capcut.db "PRAGMA table_info(drafts)"
```

### 阶段2：后端代码更新（预计 30分钟）

```bash
# 步骤1：创建新文件
# - database.py 添加迁移函数
# - save_draft_impl.py 添加 save_draft_background_v2
# - services/download_service.py 添加 get_download_url_v2

# 步骤2：更新 capcut_server.py
# - 添加 /api/v2/drafts/<id>/download 端点
# - 添加 /api/v2/drafts/<id>/status 端点

# 步骤3：测试新端点
curl http://localhost:9000/api/v2/drafts/test_id/status
```

### 阶段3：前端页面开发（预计 1小时）

```bash
# 创建新的前端页面
# templates/draft_manager_v2.html

# 或者更新现有页面
# templates/index.html
```

### 阶段4：渐进式迁移（预计 1周）

```python
# 配置文件添加功能开关
# config.json
{
  "features": {
    "use_v2_save": false,      # 是否使用 V2 保存流程
    "use_v2_download": true,   # 是否使用 V2 下载流程
    "auto_status_polling": true # 前端是否自动轮询
  }
}

# 根据开关逐步启用新功能
# 1. 先启用 V2 下载（不影响现有保存）
# 2. 测试稳定后启用 V2 保存
# 3. 最后完全切换到 V2
```

---

## ✅ 测试验证

### 测试用例

```python
# test_async_save_optimization.py

import time
import requests

BASE_URL = "http://localhost:9000"

def test_save_and_download_workflow():
    """测试完整的保存和下载流程"""
    draft_id = "test_draft_" + str(int(time.time()))

    print(f"\n测试草稿: {draft_id}")
    print("=" * 60)

    # 1. 保存草稿
    print("\n步骤1: 保存草稿")
    save_response = requests.post(f"{BASE_URL}/save_draft", json={
        "draft_id": draft_id
    })
    print(f"保存响应: {save_response.json()}")

    # 2. 轮询状态
    print("\n步骤2: 轮询状态")
    max_polls = 60  # 最多轮询 60 次（2分钟）
    poll_count = 0

    while poll_count < max_polls:
        status_response = requests.get(f"{BASE_URL}/api/v2/drafts/{draft_id}/status")
        status_data = status_response.json()

        print(f"  [{poll_count+1}] {status_data['status']} - {status_data['progress']}% - {status_data['message']}")

        if status_data['status'] == 'completed':
            print("  ✅ 保存完成！")
            break

        if status_data['status'] == 'failed':
            print(f"  ❌ 保存失败: {status_data['message']}")
            return False

        time.sleep(2)
        poll_count += 1

    if poll_count >= max_polls:
        print("  ⚠️ 轮询超时")
        return False

    # 3. 下载草稿
    print("\n步骤3: 下载草稿")
    download_response = requests.get(f"{BASE_URL}/api/v2/drafts/{draft_id}/download?wait=30")

    if download_response.status_code == 200:
        print("  ✅ 下载成功！")
        print(f"  文件大小: {len(download_response.content)} 字节")
        return True
    else:
        print(f"  ❌ 下载失败: {download_response.status_code}")
        print(f"  响应: {download_response.text}")
        return False


def test_download_before_complete():
    """测试在保存未完成时下载"""
    draft_id = "test_draft_" + str(int(time.time()))

    print(f"\n测试草稿: {draft_id}")
    print("=" * 60)

    # 1. 保存草稿
    print("\n步骤1: 保存草稿")
    requests.post(f"{BASE_URL}/save_draft", json={"draft_id": draft_id})

    # 2. 立即尝试下载（不等待）
    print("\n步骤2: 立即下载（不等待）")
    download_response = requests.get(f"{BASE_URL}/api/v2/drafts/{draft_id}/download?wait=0")

    if download_response.status_code == 202:
        print("  ✅ 正确返回 202 (处理中)")
        data = download_response.json()
        print(f"  状态: {data['status']}")
        print(f"  进度: {data['progress']}%")
        print(f"  预估时间: {data['estimated_time']}秒")
        return True
    else:
        print(f"  ❌ 意外的状态码: {download_response.status_code}")
        return False


def test_download_with_wait():
    """测试带等待的下载"""
    draft_id = "test_draft_" + str(int(time.time()))

    print(f"\n测试草稿: {draft_id}")
    print("=" * 60)

    # 1. 保存草稿
    print("\n步骤1: 保存草稿")
    requests.post(f"{BASE_URL}/save_draft", json={"draft_id": draft_id})

    # 2. 带等待的下载
    print("\n步骤2: 下载（等待最多 60 秒）")
    start_time = time.time()

    download_response = requests.get(f"{BASE_URL}/api/v2/drafts/{draft_id}/download?wait=60")

    elapsed = time.time() - start_time

    if download_response.status_code == 200:
        print(f"  ✅ 下载成功！等待时间: {elapsed:.2f}秒")
        return True
    elif download_response.status_code == 202:
        print(f"  ⚠️ 超时仍未完成，等待时间: {elapsed:.2f}秒")
        data = download_response.json()
        print(f"  当前状态: {data['status']}")
        return False
    else:
        print(f"  ❌ 下载失败: {download_response.status_code}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("异步保存优化测试套件")
    print("="*60)

    tests = [
        ("完整流程测试", test_save_and_download_workflow),
        ("过早下载测试", test_download_before_complete),
        ("智能等待测试", test_download_with_wait)
    ]

    results = []

    for name, test_func in tests:
        print(f"\n\n{'='*60}")
        print(f"运行测试: {name}")
        print("="*60)

        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            results.append((name, False))

        time.sleep(5)  # 测试间隔

    # 总结
    print("\n\n" + "="*60)
    print("测试总结")
    print("="*60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
```

---

## 📊 监控告警

### Prometheus 指标导出

```python
# monitoring.py

from prometheus_client import Counter, Histogram, Gauge
import time

# 定义指标
draft_save_total = Counter(
    'draft_save_total',
    'Total number of draft saves',
    ['status']  # completed, failed
)

draft_save_duration = Histogram(
    'draft_save_duration_seconds',
    'Draft save duration in seconds',
    buckets=[10, 30, 60, 120, 300, 600]
)

draft_download_total = Counter(
    'draft_download_total',
    'Total number of draft downloads',
    ['status']  # success, not_found, processing
)

draft_processing_gauge = Gauge(
    'draft_processing_current',
    'Current number of drafts being processed'
)

# 使用示例
def save_draft_with_metrics(draft_id):
    start_time = time.time()
    draft_processing_gauge.inc()

    try:
        # 保存逻辑
        result = save_draft_background_v2(draft_id, ...)

        # 记录成功
        draft_save_total.labels(status='completed').inc()

    except Exception as e:
        # 记录失败
        draft_save_total.labels(status='failed').inc()
        raise

    finally:
        # 记录耗时
        elapsed = time.time() - start_time
        draft_save_duration.observe(elapsed)
        draft_processing_gauge.dec()
```

### Grafana 仪表板配置

```json
{
  "dashboard": {
    "title": "CapCutAPI 草稿保存监控",
    "panels": [
      {
        "title": "保存成功率",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(draft_save_total{status=\"completed\"}[5m]) / rate(draft_save_total[5m]) * 100"
          }
        ]
      },
      {
        "title": "平均保存时间",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(draft_save_duration_seconds_sum[5m]) / rate(draft_save_duration_seconds_count[5m])"
          }
        ]
      },
      {
        "title": "正在处理的草稿数",
        "type": "graph",
        "targets": [
          {
            "expr": "draft_processing_current"
          }
        ]
      }
    ]
  }
}
```

---

## 🎯 预期效果

### 优化前 vs 优化后

| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| 下载成功率 | ~70% | >99% | +29% |
| 用户平均等待时间 | 不可知 | 60-90秒 | 透明化 |
| 404 错误率 | ~30% | <1% | -29% |
| 用户满意度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | +2星 |

### 用户体验改进

**优化前**：
```
用户: 点击保存
系统: ✅ 保存成功 (实际还在处理中)
用户: 立即点击下载
系统: ❌ 404 错误
用户: ？？？
```

**优化后**：
```
用户: 点击保存
系统: 🔄 正在保存... 10% (下载素材)
      🔄 正在保存... 50% (压缩文件)
      🔄 正在保存... 85% (上传 OSS，预计 15秒)
      ✅ 保存完成！
用户: 点击下载
系统: ✅ 立即下载
```

---

## 📝 总结

这个最佳实践方案通过以下4层防护机制，彻底解决了异步保存导致的下载失败问题：

1. **前端智能等待** - 用户看到实时进度，知道何时可以下载
2. **后端状态增强** - 细粒度状态管理，精确追踪每个阶段
3. **下载预检查** - 下载前验证文件存在，自动等待或重试
4. **监控告警** - 实时监控系统性能，及时发现问题

**实施建议**：
- ✅ 优先实施后端优化（状态增强 + 下载预检查）
- ✅ 然后实施前端优化（状态轮询 + 进度显示）
- ✅ 最后添加监控告警
- ✅ 渐进式迁移，避免一次性改动太大

**预期收益**：
- ✅ 下载成功率从 70% 提升到 99%+
- ✅ 用户体验显著改善（可视化进度）
- ✅ 系统更加健壮和可维护
- ✅ 问题更容易排查和定位

---

**文档版本**: v1.0
**创建时间**: 2025-11-18
**作者**: AI Assistant
