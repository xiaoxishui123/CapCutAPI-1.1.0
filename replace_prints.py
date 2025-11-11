#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量替换print语句为logger调用的工具脚本
"""

import re

def replace_prints_in_file(filepath):
    """替换文件中的print语句为logger调用"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 保存原始内容用于对比
    original_content = content

    # 替换模式1: print(f"...: {error}") -> logger.error(f"...", exc_info=True)
    # 处理包含error, exception, e, err等错误变量的print语句
    patterns = [
        # 匹配 print(f"...失败: {e}") 或 print(f"...错误: {e}")
        (r'print\(f"([^"]*(?:失败|错误)[^"]*:\s*\{(?:e|error|err|exception)[^}]*\}[^"]*)"\)',
         r'logger.error(f"\1", exc_info=True)'),

        # 匹配 print(f"...异常: {e}") 或包含traceback的
        (r'print\(f"([^"]*异常[^"]*)"\)',
         r'logger.error(f"\1", exc_info=True)'),

        # 匹配 print(f"开始...: ...") -> logger.info(f"开始...: ...")
        (r'print\(f"(开始[^"]*)"\)',
         r'logger.info(f"\1")'),

        # 匹配 print(f"..成功: ...") -> logger.info(f"..成功: ...")
        (r'print\(f"([^"]*成功[^"]*)"\)',
         r'logger.info(f"\1")'),

        # 匹配 print(f"检测到...") or print(f"跳过...") -> logger.debug(f"...")
        (r'print\(f"((?:检测到|跳过)[^"]*)"\)',
         r'logger.debug(f"\1")'),

        # 匹配 print(f"保存...") -> logger.info(f"...")
        (r'print\(f"(保存[^"]*)"\)',
         r'logger.info(f"\1")'),

        # 匹配 print(f"使用...") -> logger.debug(f"...")
        (r'print\(f"(使用[^"]*)"\)',
         r'logger.debug(f"\1")'),

        # 匹配 print(f"原始...") -> logger.debug(f"...")
        (r'print\(f"(原始[^"]*)"\)',
         r'logger.debug(f"\1")'),

        # 匹配 print(f"代理下载...") -> logger.info(f"...")
        (r'print\(f"(代理下载[^"]*)"\)',
         r'logger.info(f"\1")'),

        # 匹配 print(f"生成...失败") -> logger.error(f"...", exc_info=False)
        (r'print\(f"(生成[^"]*失败[^"]*)"\)',
         r'logger.error(f"\1")'),

        # 匹配其他所有 print(f"...") -> logger.info(f"...")
        (r'print\(f"([^"]*)"\)',
         r'logger.info(f"\1")'),

        # 匹配 print("...") (不带f) -> logger.info("...")
        (r'print\("([^"]*)"\)',
         r'logger.info("\1")')
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    # 统计替换数量
    replaced_count = original_content.count('print(') - content.count('print(')

    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return replaced_count

if __name__ == '__main__':
    filepath = '/home/CapCutAPI-1.1.0/capcut_server.py'
    count = replace_prints_in_file(filepath)
    print(f"成功替换 {count} 个print语句为logger调用")
