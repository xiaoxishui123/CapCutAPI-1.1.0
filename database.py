import sqlite3
import json

def init_db():
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'initialized',
            progress INTEGER DEFAULT 0,
            message TEXT,
            script_data TEXT,
            width INTEGER DEFAULT 1920,
            height INTEGER DEFAULT 1080,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id TEXT PRIMARY KEY,
            draft_id TEXT,
            data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (draft_id) REFERENCES drafts (id)
        )
    ''')
    conn.commit()
    conn.close()

def get_draft_materials(draft_id):
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("SELECT data FROM materials WHERE draft_id = ?", (draft_id,))
    materials = [json.loads(row[0]) for row in c.fetchall()]
    conn.close()
    return materials

def add_material_to_db(draft_id, material_id, material_data):
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO drafts (id) VALUES (?)", (draft_id,))
    c.execute("INSERT OR REPLACE INTO materials (id, draft_id, data) VALUES (?, ?, ?)",
              (material_id, draft_id, json.dumps(material_data)))
    conn.commit()
    conn.close()

def update_material_in_db(material_id, material_data):
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("UPDATE materials SET data = ? WHERE id = ?", (json.dumps(material_data), material_id))
    conn.commit()
    conn.close()

def delete_material_from_db(material_id):
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()

def get_all_drafts():
    """获取所有草稿信息，返回字典格式列表"""
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("""
        SELECT 
            d.id, 
            d.status,
            d.progress,
            d.message,
            d.created_at,
            d.last_modified,
            COUNT(m.id) as materials_count
        FROM drafts d
        LEFT JOIN materials m ON d.id = m.draft_id
        GROUP BY d.id
        ORDER BY d.last_modified DESC
    """)
    
    drafts = []
    for row in c.fetchall():
        draft = {
            'id': row[0],
            'name': row[0],  # 使用ID作为名称
            'status': row[1] or 'initialized',
            'progress': row[2] or 0,
            'message': row[3] or '',
            'created_time': row[4] or '未知',
            'modified_time': row[5] or '未知',
            'materials_count': row[6] or 0,
            'duration': '00:00'  # 默认时长
        }
        drafts.append(draft)
    
    conn.close()
    return drafts

def update_draft_status(draft_id, status, progress=None, message=None):
    """更新草稿状态和进度信息"""
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    # 确保草稿存在
    c.execute("INSERT OR IGNORE INTO drafts (id, status) VALUES (?, ?)", (draft_id, status))
    # 更新状态
    c.execute("UPDATE drafts SET status = ?, progress = ?, message = ?, last_modified = CURRENT_TIMESTAMP WHERE id = ?", 
              (status, progress, message, draft_id))
    conn.commit()
    conn.close()

def get_draft_status(draft_id):
    """获取草稿状态和进度信息"""
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("SELECT status, progress, message, last_modified FROM drafts WHERE id = ?", (draft_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'status': result[0],
            'progress': result[1] or 0,
            'message': result[2] or '',
            'last_modified': result[3]
        }
    else:
        return {
            'status': 'not_found',
            'progress': 0,
            'message': '草稿不存在',
            'last_modified': None
        }

def save_draft_to_db(draft_id, script_data, width=1920, height=1080):
    """保存草稿完整数据到数据库"""
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO drafts 
        (id, script_data, width, height, status, last_modified) 
        VALUES (?, ?, ?, ?, 'saved', CURRENT_TIMESTAMP)
    """, (draft_id, script_data, width, height))
    conn.commit()
    conn.close()

def get_draft_from_db(draft_id):
    """从数据库获取草稿完整数据"""
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("SELECT script_data, width, height FROM drafts WHERE id = ?", (draft_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'script_data': result[0],
            'width': result[1] or 1920,
            'height': result[2] or 1080
        }
    return None

def draft_exists_in_db(draft_id):
    """检查草稿是否存在于数据库中"""
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM drafts WHERE id = ? AND script_data IS NOT NULL", (draft_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_all_draft_ids_from_db():
    """获取数据库中所有草稿的ID列表"""
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("SELECT id FROM drafts WHERE script_data IS NOT NULL")
    draft_ids = [row[0] for row in c.fetchall()]
    conn.close()
    return draft_ids

def get_draft_by_id(draft_id):
    """根据ID获取草稿基本信息"""
    conn = sqlite3.connect('capcut.db')
    c = conn.cursor()
    c.execute("SELECT id, status, last_modified, script_data FROM drafts WHERE id = ?", (draft_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'name': f'Draft_{result[0]}',  # 默认名称
            'status': result[1] or 'created',
            'created_at': result[2],
            'script_data': json.loads(result[3]) if result[3] else None
        }
    return None

