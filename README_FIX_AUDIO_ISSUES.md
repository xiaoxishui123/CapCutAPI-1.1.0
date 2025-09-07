# 音频文件识别问题修复指南

## 问题描述

在使用 CapCutAPI 生成草稿文件时，可能会遇到剪映客户端无法识别音频文件的问题。这通常是由于路径配置不正确导致的。

## 问题原因

1. **路径格式问题**：在 OSS 模式下，如果未正确设置自定义路径，系统可能使用相对路径而非绝对路径
2. **路径配置不一致**：[draft_meta_info.json](file:///home/CapCutAPI-1.1.0/template/draft_meta_info.json) 中的 [draft_fold_path](file:///home/CapCutAPI-1.1.0/pyJianYingDraft/draft.py#L101-L101) 和 [draft_root_path](file:///home/CapCutAPI-1.1.0/pyJianYingDraft/draft.py#L100-L100) 与实际下载路径不匹配
3. **音频路径字段问题**：[draft_info.json](file:///home/CapCutAPI-1.1.0/template/draft_info.json) 中音频素材的 `replace_path` 字段可能导致识别问题

## 解决方案

### 1. 配置检查

首先验证配置文件是否正确：

```bash
python fix_audio_recognition_issues.py --check
```

### 2. 修复单个草稿

```bash
python fix_audio_recognition_issues.py /path/to/draft_folder [客户端OS]
```

例如：
```bash
python fix_audio_recognition_issues.py "/home/CapCutAPI-1.1.0/my_draft" windows
```

### 3. 批量修复草稿

```bash
python fix_audio_recognition_issues.py --batch /path/to/drafts_directory [客户端OS]
```

例如：
```bash
python fix_audio_recognition_issues.py --batch "/home/CapCutAPI-1.1.0/drafts" windows
```

## 配置文件说明

### path_config.json
```json
{
  "custom_download_path": "F:\\jianyin\\cgwz\\JianyingPro Drafts"
}
```

### config.json
确保 `draft_paths` 配置正确：
```json
"draft_paths": {
  "windows": "F:\\jianyin\\cgwz\\JianyingPro Drafts",
  "linux": "/data/jianying/drafts",
  "darwin": "/Users/Shared/JianyingPro Drafts"
}
```

## 修复内容

1. **更新元数据路径**：修复 [draft_meta_info.json](file:///home/CapCutAPI-1.1.0/template/draft_meta_info.json) 中的 [draft_fold_path](file:///home/CapCutAPI-1.1.0/pyJianYingDraft/draft.py#L101-L101) 和 [draft_root_path](file:///home/CapCutAPI-1.1.0/pyJianYingDraft/draft.py#L100-L100)
2. **修复音频路径**：移除 [draft_info.json](file:///home/CapCutAPI-1.1.0/template/draft_info.json) 中音频素材的 `replace_path` 字段
3. **路径格式标准化**：确保所有路径使用正确的 Windows 格式

## 验证修复结果

修复完成后，可以在剪映客户端中打开草稿，确认音频文件能够正常识别和播放。

## 常见问题

### 1. 路径格式错误
确保使用 Windows 格式的绝对路径，包含盘符（如 `F:\jianyin\cgwz\JianyingPro Drafts`）

### 2. 权限问题
确保草稿目录具有读写权限

### 3. 路径不存在
确保配置的路径在系统中实际存在

## 日志查看

修复过程中的详细日志会记录在 `fix_audio_issues.log` 文件中，可用于问题排查。