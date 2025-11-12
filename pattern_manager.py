#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pattern 管理模块
负责管理和提供视频编辑模板（Pattern）

作者: CapCutAPI Team
版本: 1.0.0
创建时间: 2025-01-11
"""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class PatternManager:
    """Pattern 模板管理器"""

    def __init__(self, pattern_dir: str = None):
        """
        初始化 Pattern 管理器

        Args:
            pattern_dir: Pattern 目录路径，默认为项目根目录下的 pattern/
        """
        if pattern_dir is None:
            # 获取项目根目录
            project_root = Path(__file__).parent
            pattern_dir = project_root / "pattern"

        self.pattern_dir = Path(pattern_dir)
        logger.info(f"Pattern 目录: {self.pattern_dir}")

        # 检查目录是否存在
        if not self.pattern_dir.exists():
            logger.warning(f"Pattern 目录不存在: {self.pattern_dir}")
            self.pattern_dir.mkdir(parents=True, exist_ok=True)

    def list_patterns(self) -> List[Dict]:
        """
        列出所有可用的 Pattern

        Returns:
            Pattern 列表，每个 Pattern 包含：
            - id: Pattern ID
            - name: Pattern 名称
            - description: 描述信息
            - file: 文件路径
            - type: 类型 (python/markdown)
            - video_url: 演示视频链接（如果有）
        """
        patterns = []

        if not self.pattern_dir.exists():
            logger.warning(f"Pattern 目录不存在: {self.pattern_dir}")
            return patterns

        # 读取 README.md 获取视频链接
        video_urls = self._parse_readme()

        # 遍历 pattern 目录
        for file_path in sorted(self.pattern_dir.glob("*")):
            if file_path.is_file() and file_path.name != "README.md":
                pattern_id = file_path.stem

                # 根据文件扩展名确定类型
                file_ext = file_path.suffix
                if file_ext == ".py":
                    pattern_type = "python"
                    description = self._extract_python_description(file_path)
                elif file_ext == ".md":
                    pattern_type = "markdown"
                    description = "扣子工作流配置"
                else:
                    continue

                pattern_info = {
                    "id": pattern_id,
                    "name": self._generate_pattern_name(pattern_id),
                    "description": description,
                    "file": str(file_path.name),
                    "type": pattern_type,
                    "video_url": video_urls.get(pattern_id, "")
                }

                patterns.append(pattern_info)

        logger.info(f"找到 {len(patterns)} 个 Pattern")
        return patterns

    def get_pattern_content(self, pattern_id: str) -> Optional[str]:
        """
        获取 Pattern 的内容

        Args:
            pattern_id: Pattern ID

        Returns:
            Pattern 文件内容，如果不存在返回 None
        """
        # 尝试查找 .py 或 .md 文件
        for ext in [".py", ".md"]:
            file_path = self.pattern_dir / f"{pattern_id}{ext}"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    logger.info(f"读取 Pattern 内容: {file_path.name}")
                    return content
                except Exception as e:
                    logger.error(f"读取 Pattern 失败: {e}")
                    return None

        logger.warning(f"Pattern 不存在: {pattern_id}")
        return None

    def get_pattern_info(self, pattern_id: str) -> Optional[Dict]:
        """
        获取单个 Pattern 的详细信息

        Args:
            pattern_id: Pattern ID

        Returns:
            Pattern 信息字典，如果不存在返回 None
        """
        patterns = self.list_patterns()
        for pattern in patterns:
            if pattern["id"] == pattern_id:
                return pattern
        return None

    def _parse_readme(self) -> Dict[str, str]:
        """
        解析 README.md 获取视频链接

        Returns:
            Pattern ID 到视频 URL 的映射
        """
        video_urls = {}
        readme_path = self.pattern_dir / "README.md"

        if not readme_path.exists():
            return video_urls

        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 简单解析 Markdown 中的视频链接
            # 格式: [![Words](https://img.youtube.com/vi/VIDEO_ID/hqdefault.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)
            import re
            pattern = r'\[!\[.*?\]\(.*?\)\]\((https://www\.youtube\.com/watch\?v=.*?)\)'
            matches = re.finditer(pattern, content)

            # 根据出现顺序匹配 Pattern ID
            pattern_files = sorted([f.stem for f in self.pattern_dir.glob("*.py")])
            for idx, match in enumerate(matches):
                if idx < len(pattern_files):
                    video_urls[pattern_files[idx]] = match.group(1)

        except Exception as e:
            logger.error(f"解析 README.md 失败: {e}")

        return video_urls

    def _extract_python_description(self, file_path: Path) -> str:
        """
        从 Python 文件中提取描述信息

        Args:
            file_path: Python 文件路径

        Returns:
            描述信息
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 读取前几行查找注释或文档字符串
                lines = f.readlines()[:20]

                # 查找包含 "def " 的行来推断功能
                for line in lines:
                    if "def " in line and "main" in line:
                        # 尝试从文件名推断
                        if "words" in file_path.name:
                            return "文字滚动效果视频模板"
                        elif "relationship" in file_path.name:
                            return "情侣关系主题视频模板"

                return "视频编辑模板"
        except Exception as e:
            logger.error(f"提取描述失败: {e}")
            return "视频编辑模板"

    def _generate_pattern_name(self, pattern_id: str) -> str:
        """
        根据 Pattern ID 生成友好的名称

        Args:
            pattern_id: Pattern ID

        Returns:
            友好的名称
        """
        # 从文件名推断名称
        if "words" in pattern_id:
            return "文字滚动效果"
        elif "relationship" in pattern_id:
            return "情侣关系主题"
        else:
            # 默认使用 ID
            return pattern_id.replace("-", " ").replace("_", " ").title()


# 全局 Pattern 管理器实例
_pattern_manager = None

def get_pattern_manager() -> PatternManager:
    """获取全局 Pattern 管理器实例"""
    global _pattern_manager
    if _pattern_manager is None:
        _pattern_manager = PatternManager()
    return _pattern_manager
