#!/usr/bin/env python3
"""列出所有注册的Flask路由"""

import sys
sys.path.insert(0, '/home/CapCutAPI-1.1.0')

from capcut_server import app

print("已注册的路由：\n")
for rule in app.url_map.iter_rules():
    print(f"{rule.rule:60s} {','.join(rule.methods):20s} {rule.endpoint}")

# 专门检查 v2 路由
print("\n\n/api/v2 路由：\n")
v2_routes = [rule for rule in app.url_map.iter_rules() if '/api/v2' in rule.rule]
if v2_routes:
    for rule in v2_routes:
        print(f"{rule.rule:60s} {','.join(rule.methods):20s} {rule.endpoint}")
else:
    print("未找到任何 /api/v2 路由！")
