#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小化“草稿封面”功能测试（不依赖启动 Web 服务）

测试点：
- update_draft_cover_metadata 会把:
  - draft_meta_info.json 的 draft_cover 设置为 draft_cover.jpg
  - draft_info.json 的 static_cover_image_path 设置为 draft_cover.jpg（如果字段存在）
"""

import json
import os
import tempfile

from draft_cover import update_draft_cover_metadata


def main() -> None:
    with tempfile.TemporaryDirectory() as d:
        # 准备最小草稿文件
        meta = {"draft_cover": "", "draft_name": "test"}
        info = {"cover": None, "static_cover_image_path": ""}

        with open(os.path.join(d, "draft_meta_info.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, separators=(",", ":"))
        with open(os.path.join(d, "draft_info.json"), "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, separators=(",", ":"))

        # 写入封面文件
        cover_path = os.path.join(d, "draft_cover.jpg")
        with open(cover_path, "wb") as f:
            # 这里不要求图片内容真实可预览；我们只验证“元数据更新逻辑”
            # 真正的封面图片生成由 ffmpeg/download 逻辑负责（在 save_draft 阶段执行）
            f.write(b"TEST_COVER")

        # 更新元数据
        update_draft_cover_metadata(d, "draft_cover.jpg")

        # 断言
        with open(os.path.join(d, "draft_meta_info.json"), "r", encoding="utf-8") as f:
            meta2 = json.load(f)
        with open(os.path.join(d, "draft_info.json"), "r", encoding="utf-8") as f:
            info2 = json.load(f)

        assert meta2.get("draft_cover") == "draft_cover.jpg", meta2
        assert info2.get("static_cover_image_path") == "draft_cover.jpg", info2

    print("OK: draft cover metadata updated")


if __name__ == "__main__":
    main()


