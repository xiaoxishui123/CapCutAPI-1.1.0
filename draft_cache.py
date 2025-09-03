from collections import OrderedDict
import pyJianYingDraft as draft
from typing import Dict, Optional
import pickle
import json

# Modify global variable, use OrderedDict to implement LRU cache, limit the maximum number to 10000
DRAFT_CACHE: Dict[str, 'draft.Script_file'] = OrderedDict()  # Use Dict for type hinting
MAX_CACHE_SIZE = 10000

def serialize_script(script: draft.Script_file) -> str:
    """
    序列化Script_file对象为JSON字符串
    :param script: Script_file对象
    :return: JSON字符串
    """
    try:
        # 使用pickle序列化，然后base64编码
        import base64
        pickled_data = pickle.dumps(script)
        return base64.b64encode(pickled_data).decode('utf-8')
    except Exception as e:
        print(f"序列化草稿失败: {e}")
        return None

def deserialize_script(script_data: str) -> Optional[draft.Script_file]:
    """
    从JSON字符串反序列化Script_file对象
    :param script_data: JSON字符串
    :return: Script_file对象或None
    """
    try:
        import base64
        pickled_data = base64.b64decode(script_data.encode('utf-8'))
        return pickle.loads(pickled_data)
    except Exception as e:
        print(f"反序列化草稿失败: {e}")
        return None

def update_cache(key: str, value: draft.Script_file, sync_to_db: bool = True) -> None:
    """
    更新LRU缓存并可选择同步到数据库
    :param key: 草稿ID
    :param value: Script_file对象
    :param sync_to_db: 是否同步到数据库
    """
    if key in DRAFT_CACHE:
        # If the key exists, delete the old item
        DRAFT_CACHE.pop(key)
    elif len(DRAFT_CACHE) >= MAX_CACHE_SIZE:
        print(f"{key}, Cache is full, deleting the least recently used item")
        # If the cache is full, delete the least recently used item (the first item)
        DRAFT_CACHE.popitem(last=False)
    
    # Add new item to the end (most recently used)
    DRAFT_CACHE[key] = value
    
    # 同步到数据库
    if sync_to_db:
        try:
            from database import save_draft_to_db
            script_data = serialize_script(value)
            if script_data:
                save_draft_to_db(key, script_data, value.width, value.height)
                print(f"草稿 {key} 已同步到数据库")
        except Exception as e:
            print(f"同步草稿到数据库失败: {e}")

def get_draft(draft_id: str) -> Optional[draft.Script_file]:
    """
    获取草稿，优先从缓存获取，缓存未命中时从数据库获取
    :param draft_id: 草稿ID
    :return: Script_file对象或None
    """
    # 首先尝试从缓存获取
    if draft_id in DRAFT_CACHE:
        # 更新LRU顺序
        script = DRAFT_CACHE.pop(draft_id)
        DRAFT_CACHE[draft_id] = script
        print(f"从缓存获取草稿: {draft_id}")
        return script
    
    # 缓存未命中，尝试从数据库获取
    try:
        from database import get_draft_from_db
        result = get_draft_from_db(draft_id)
        if result:
            script_data = result['script_data']
            width = result['width']
            height = result['height']
            script = deserialize_script(script_data)
            if script:
                # 加载到缓存中（不再次同步到数据库）
                update_cache(draft_id, script, sync_to_db=False)
                print(f"从数据库加载草稿到缓存: {draft_id}")
                return script
    except Exception as e:
        print(f"从数据库获取草稿失败: {e}")
    
    return None

def draft_exists(draft_id: str) -> bool:
    """
    检查草稿是否存在（缓存或数据库）
    :param draft_id: 草稿ID
    :return: bool
    """
    # 检查缓存
    if draft_id in DRAFT_CACHE:
        return True
    
    # 检查数据库
    try:
        from database import draft_exists_in_db
        return draft_exists_in_db(draft_id)
    except Exception as e:
        print(f"检查数据库草稿存在性失败: {e}")
        return False