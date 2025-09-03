#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
草稿迁移脚本 - 将缓存中的草稿迁移到数据库
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from draft_cache import DRAFT_CACHE, serialize_script
from database import save_draft_to_db, draft_exists_in_db, init_db
import sqlite3

def migrate_cache_to_database():
    """
    将缓存中的所有草稿迁移到数据库
    """
    print("开始迁移草稿从缓存到数据库...")
    
    # 确保数据库已初始化
    init_db()
    
    if not DRAFT_CACHE:
        print("缓存中没有草稿需要迁移")
        return
    
    migrated_count = 0
    failed_count = 0
    skipped_count = 0
    
    for draft_id, script in DRAFT_CACHE.items():
        try:
            # 检查数据库中是否已存在该草稿
            if draft_exists_in_db(draft_id):
                print(f"草稿 {draft_id} 已存在于数据库中，跳过")
                skipped_count += 1
                continue
            
            # 序列化草稿数据
            script_data = serialize_script(script)
            if not script_data:
                print(f"序列化草稿 {draft_id} 失败，跳过")
                failed_count += 1
                continue
            
            # 保存到数据库
            save_draft_to_db(draft_id, script_data, script.width, script.height)
            print(f"成功迁移草稿: {draft_id}")
            migrated_count += 1
            
        except Exception as e:
            print(f"迁移草稿 {draft_id} 失败: {e}")
            failed_count += 1
    
    print(f"\n迁移完成:")
    print(f"  成功迁移: {migrated_count} 个草稿")
    print(f"  跳过已存在: {skipped_count} 个草稿")
    print(f"  迁移失败: {failed_count} 个草稿")
    print(f"  总计处理: {len(DRAFT_CACHE)} 个草稿")

def verify_migration():
    """
    验证迁移结果
    """
    print("\n验证迁移结果...")
    
    from database import get_all_draft_ids_from_db
    
    try:
        db_draft_ids = get_all_draft_ids_from_db()
        cache_draft_ids = set(DRAFT_CACHE.keys())
        
        print(f"缓存中的草稿数量: {len(cache_draft_ids)}")
        print(f"数据库中的草稿数量: {len(db_draft_ids)}")
        
        # 检查缓存中的草稿是否都在数据库中
        missing_in_db = cache_draft_ids - set(db_draft_ids)
        if missing_in_db:
            print(f"警告: 以下草稿在缓存中但不在数据库中: {missing_in_db}")
        else:
            print("✅ 所有缓存草稿都已成功迁移到数据库")
        
        # 检查数据库中是否有额外的草稿
        extra_in_db = set(db_draft_ids) - cache_draft_ids
        if extra_in_db:
            print(f"信息: 数据库中有额外的草稿（可能是之前创建的）: {len(extra_in_db)} 个")
        
    except Exception as e:
        print(f"验证过程中出错: {e}")

def show_migration_status():
    """
    显示迁移状态
    """
    print("=" * 50)
    print("草稿迁移状态检查")
    print("=" * 50)
    
    try:
        from database import get_all_draft_ids_from_db
        
        cache_count = len(DRAFT_CACHE)
        db_draft_ids = get_all_draft_ids_from_db()
        db_count = len(db_draft_ids)
        
        print(f"缓存中的草稿数量: {cache_count}")
        print(f"数据库中的草稿数量: {db_count}")
        
        if cache_count == 0:
            print("✅ 缓存为空，无需迁移")
        elif db_count >= cache_count:
            print("✅ 数据库中的草稿数量 >= 缓存数量，可能已完成迁移")
        else:
            print("⚠️  建议执行迁移操作")
        
    except Exception as e:
        print(f"检查状态时出错: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='草稿迁移工具')
    parser.add_argument('--migrate', action='store_true', help='执行迁移操作')
    parser.add_argument('--verify', action='store_true', help='验证迁移结果')
    parser.add_argument('--status', action='store_true', help='显示迁移状态')
    
    args = parser.parse_args()
    
    if args.status or (not args.migrate and not args.verify):
        show_migration_status()
    
    if args.migrate:
        migrate_cache_to_database()
        verify_migration()
    
    if args.verify:
        verify_migration()