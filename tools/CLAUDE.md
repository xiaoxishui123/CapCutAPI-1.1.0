[根目录](../CLAUDE.md) > **tools**

---

# tools 工具脚本模块文档

> 最后更新时间：2025-11-11 22:43:46

## 变更记录 (Changelog)

### 2025-11-11 22:43:46
- 初始化 tools 工具脚本模块文档
- 完成模块架构和功能分析

---

## 模块职责

`tools` 模块是 CapCutAPI 项目的辅助工具脚本目录，包含用于草稿维护、数据修复和调试的实用工具。

**核心功能**：
- 草稿 ID 刷新和修复
- 数据迁移和清理
- 调试和诊断工具

**使用场景**：
- 数据库维护
- 草稿文件修复
- 开发调试

---

## 文件清单

### 1. refresh_draft_id.py
**功能**: 刷新和修复草稿 ID

**使用场景**:
- 草稿 ID 冲突修复
- 批量重命名草稿
- 数据库与文件系统同步

**使用方法**:
```bash
# 刷新单个草稿 ID
python tools/refresh_draft_id.py --draft-id dfd_cat_123456_abc

# 批量刷新所有草稿
python tools/refresh_draft_id.py --all

# 预览模式（不实际修改）
python tools/refresh_draft_id.py --draft-id dfd_cat_123456_abc --dry-run
```

**功能详情**:
1. 读取草稿 `draft_meta_info.json`
2. 生成新的草稿 ID（时间戳 + UUID）
3. 更新文件夹名称和内部引用
4. 同步数据库记录
5. 验证修改正确性

**输出示例**:
```
[INFO] 正在处理草稿: dfd_cat_1234567890_abc123
[INFO] 旧 ID: dfd_cat_1234567890_abc123
[INFO] 新 ID: dfd_cat_1762219273_240addca
[INFO] 更新文件夹名称...
[INFO] 更新 draft_meta_info.json...
[INFO] 更新数据库记录...
[SUCCESS] 草稿 ID 刷新完成！
```

**注意事项**:
- ⚠️ 运行前建议备份草稿文件
- ⚠️ 确保草稿未被剪映应用锁定
- ⚠️ 使用 `--dry-run` 先预览修改

---

## 常见使用场景

### 场景 1: 修复草稿 ID 冲突
**问题**: 两个草稿 ID 相同，导致剪映无法识别

**解决方案**:
```bash
# 1. 查看冲突的草稿
ls -la drafts/

# 2. 刷新其中一个草稿的 ID
python tools/refresh_draft_id.py --draft-id dfd_cat_123456_abc

# 3. 验证修复结果
ls -la drafts/
```

### 场景 2: 批量重置所有草稿
**使用场景**: 清理测试数据，重新生成草稿 ID

**步骤**:
```bash
# 1. 备份草稿目录
cp -r drafts/ drafts_backup/

# 2. 批量刷新（预览）
python tools/refresh_draft_id.py --all --dry-run

# 3. 确认无误后执行
python tools/refresh_draft_id.py --all

# 4. 验证数据库同步
sqlite3 capcut.db "SELECT * FROM drafts;"
```

### 场景 3: 数据迁移
**场景**: 从旧服务器迁移草稿到新服务器

**步骤**:
```bash
# 1. 复制草稿文件到新服务器
rsync -av user@old-server:/data/drafts/ ./drafts/

# 2. 刷新所有草稿 ID（避免冲突）
python tools/refresh_draft_id.py --all

# 3. 重建数据库索引
python tools/rebuild_db.py  # 需要额外创建此工具
```

---

## 工具开发指南

### 新增工具脚本规范
如需添加新的工具脚本，遵循以下规范：

**1. 文件命名**:
```
<功能描述>_<对象>.py
```
示例: `cleanup_drafts.py`, `export_materials.py`

**2. 脚本结构**:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具名称: 草稿清理工具
功能描述: 清理过期的草稿文件和数据库记录
使用方法: python tools/cleanup_drafts.py --days 30
"""

import argparse
import logging
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='草稿清理工具')
    parser.add_argument('--days', type=int, default=30, help='清理多少天前的草稿')
    parser.add_argument('--dry-run', action='store_true', help='预览模式')
    args = parser.parse_args()

    logger.info(f'开始清理 {args.days} 天前的草稿...')

    # 实现清理逻辑
    # ...

    logger.info('清理完成！')

if __name__ == '__main__':
    main()
```

**3. 命令行参数**:
- `--dry-run`: 预览模式（不实际修改）
- `--verbose`: 详细日志
- `--help`: 帮助信息

**4. 错误处理**:
```python
try:
    # 危险操作
    os.remove(file_path)
except Exception as e:
    logger.error(f'删除失败: {e}')
    continue
```

**5. 确认提示**:
```python
if not args.dry_run:
    confirm = input('确认执行操作？(yes/no): ')
    if confirm.lower() != 'yes':
        logger.info('操作已取消')
        return
```

---

## 常见问题 (FAQ)

### Q1: refresh_draft_id.py 报错"找不到草稿"？
**解决方案**:
1. 检查草稿 ID 是否正确：
   ```bash
   ls drafts/ | grep dfd_cat
   ```
2. 确保在项目根目录运行：
   ```bash
   cd /home/CapCutAPI-1.1.0
   python tools/refresh_draft_id.py --draft-id xxx
   ```

### Q2: 刷新后草稿无法在剪映中打开？
**可能原因**:
1. 草稿文件损坏
2. 路径引用未更新
3. 数据库记录不一致

**解决方案**:
```bash
# 1. 验证草稿文件完整性
unzip -t drafts/dfd_cat_xxx/draft_content.data

# 2. 重新生成草稿
curl -X POST http://localhost:9000/api/drafts/rebuild/xxx

# 3. 检查日志
tail -f logs/capcutapi.log
```

### Q3: 如何批量操作特定条件的草稿？
**示例**: 只刷新 7 天前创建的草稿

**解决方案**（需扩展脚本）:
```python
# 在 refresh_draft_id.py 中添加
import os
from datetime import datetime, timedelta

def filter_old_drafts(days=7):
    """筛选旧草稿"""
    cutoff = datetime.now() - timedelta(days=days)
    old_drafts = []

    for draft_dir in os.listdir('drafts/'):
        meta_file = f'drafts/{draft_dir}/draft_meta_info.json'
        if os.path.exists(meta_file):
            mtime = os.path.getmtime(meta_file)
            if datetime.fromtimestamp(mtime) < cutoff:
                old_drafts.append(draft_dir)

    return old_drafts
```

---

## 扩展建议

### 推荐新增工具
1. **cleanup_drafts.py**: 清理过期草稿
2. **export_materials.py**: 导出草稿中的素材清单
3. **validate_drafts.py**: 验证草稿文件完整性
4. **migrate_drafts.py**: 草稿数据迁移工具
5. **stats_drafts.py**: 草稿统计分析工具

### 示例: cleanup_drafts.py
```python
#!/usr/bin/env python3
"""清理过期草稿工具"""
import os
import shutil
from datetime import datetime, timedelta

def cleanup_old_drafts(days=30, dry_run=False):
    """清理超过指定天数的草稿"""
    cutoff = datetime.now() - timedelta(days=days)
    removed = 0

    for draft_dir in os.listdir('drafts/'):
        draft_path = f'drafts/{draft_dir}'
        if os.path.isdir(draft_path):
            mtime = os.path.getmtime(draft_path)
            if datetime.fromtimestamp(mtime) < cutoff:
                if dry_run:
                    print(f'[DRY-RUN] 将删除: {draft_dir}')
                else:
                    shutil.rmtree(draft_path)
                    print(f'[DELETED] {draft_dir}')
                removed += 1

    print(f'共清理 {removed} 个草稿')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    cleanup_old_drafts(args.days, args.dry_run)
```

---

## 相关模块
- [根目录](../CLAUDE.md) - 项目总览
- [database.py](../database.py) - 数据库操作
- [draft_cache.py](../draft_cache.py) - 草稿缓存管理

---

**提示**: tools 目录的脚本主要用于维护和调试，不应在生产环境频繁使用。建议在测试环境验证后再应用到生产。
