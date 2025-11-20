# Validators 使用指南

> **快速参考文档 - 输入验证函数使用说明**

---

## 📦 导入方式

```python
from validators import (
    validate_draft_id,
    validate_url,
    validate_text_content,
    validate_numeric_range,
    validate_color,
    validate_duration,
    validate_material_type,
    validate_resolution,
    validate_file_path,
    validate_required_fields
)
```

---

## 🎯 核心验证函数

### 1. validate_draft_id()

**功能**: 验证草稿ID格式

**参数**:
- `draft_id` (str): 草稿ID字符串

**返回**: `(bool, str)` - (是否有效, 错误信息)

**规则**:
- 只允许字母、数字、下划线、连字符
- 长度: 3-100字符

**示例**:
```python
is_valid, error = validate_draft_id("dfd_cat_abc123")
if not is_valid:
    return jsonify({'success': False, 'error': error}), 400
```

---

### 2. validate_url()

**功能**: 验证URL格式并防止SSRF攻击

**参数**:
- `url` (str): URL字符串
- `allow_internal` (bool): 是否允许访问内网地址（默认False）

**返回**: `(bool, str)` - (是否有效, 错误信息)

**规则**:
- 只支持 http 和 https 协议
- 默认禁止 localhost、127.0.0.1、内网地址

**示例**:
```python
# 禁止内网访问（默认）
is_valid, error = validate_url(video_url)

# 允许内网访问（用于本地文件服务器）
is_valid, error = validate_url(video_url, allow_internal=True)

if not is_valid:
    return jsonify({'success': False, 'error': error}), 400
```

---

### 3. validate_text_content()

**功能**: 验证文本内容长度

**参数**:
- `text` (str): 文本内容
- `max_length` (int): 最大长度（默认10000）
- `min_length` (int): 最小长度（默认0）

**返回**: `(bool, str)` - (是否有效, 错误信息)

**示例**:
```python
is_valid, error = validate_text_content(text, max_length=10000)
if not is_valid:
    return jsonify({'success': False, 'error': error}), 400
```

---

### 4. validate_color()

**功能**: 验证颜色格式

**参数**:
- `color` (str): 颜色字符串

**返回**: `(bool, str)` - (是否有效, 错误信息)

**支持格式**:
- HEX: `#FF5733`, `#F57`, `#FF5733AA`
- RGB: `rgb(255, 87, 51)`
- RGBA: `rgba(255, 87, 51, 0.5)`

**示例**:
```python
is_valid, error = validate_color(font_color)
if not is_valid:
    return jsonify({'success': False, 'error': error}), 400
```

---

### 5. validate_duration()

**功能**: 验证时长参数

**参数**:
- `start` (float): 开始时间（秒）
- `end` (float): 结束时间（秒）
- `max_duration` (float): 最大时长（秒，可选）

**返回**: `(bool, str)` - (是否有效, 错误信息)

**规则**:
- start >= 0
- end > start

**示例**:
```python
is_valid, error = validate_duration(start, end)
if not is_valid:
    return jsonify({'success': False, 'error': error}), 400
```

---

### 6. validate_resolution()

**功能**: 验证分辨率

**参数**:
- `width` (int): 宽度（像素）
- `height` (int): 高度（像素）

**返回**: `(bool, str)` - (是否有效, 错误信息)

**规则**:
- 宽度: 1-7680 (8K)
- 高度: 1-4320 (8K)

**示例**:
```python
is_valid, error = validate_resolution(int(width), int(height))
if not is_valid:
    return jsonify({'success': False, 'error': error}), 400
```

---

### 7. validate_required_fields()

**功能**: 验证必填字段

**参数**:
- `data` (dict): 数据字典
- `required_fields` (list): 必填字段列表

**返回**: `(bool, str)` - (是否有效, 错误信息)

**示例**:
```python
is_valid, error = validate_required_fields(data, ['text', 'draft_id'])
if not is_valid:
    return jsonify({'success': False, 'error': error}), 400
```

---

### 8. validate_numeric_range()

**功能**: 验证数值范围

**参数**:
- `value`: 数值（int、float或字符串）
- `min_val` (float): 最小值（可选）
- `max_val` (float): 最大值（可选）
- `field_name` (str): 字段名称（用于错误信息）

**返回**: `(bool, str)` - (是否有效, 错误信息)

**示例**:
```python
is_valid, error = validate_numeric_range(volume, 0, 1, "音量")
if not is_valid:
    return jsonify({'success': False, 'error': error}), 400
```

---

## 📋 完整使用示例

### 示例1: 创建草稿端点

```python
@app.route('/create_draft', methods=['POST'])
def create_draft_service():
    try:
        data = request.get_json()
        draft_id = data.get('draft_id')
        width = data.get('width', 1080)
        height = data.get('height', 1920)

        # 验证draft_id（如果指定）
        if draft_id:
            is_valid, error_msg = validate_draft_id(draft_id)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': f'draft_id验证失败: {error_msg}'
                }), 400

        # 验证分辨率
        is_valid, error_msg = validate_resolution(int(width), int(height))
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'分辨率验证失败: {error_msg}'
            }), 400

        # 继续处理...
        draft_id, script = get_or_create_draft(draft_id, width, height)

        return jsonify({
            'success': True,
            'output': {'draft_id': draft_id}
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

### 示例2: 添加文本端点

```python
@app.route('/add_text', methods=['POST'])
def add_text():
    try:
        data = request.get_json()

        # 1. 验证必填字段
        is_valid, error_msg = validate_required_fields(data, ['text'])
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        text = data.get('text')
        draft_id = data.get('draft_id')
        start = data.get('start', 0)
        end = data.get('end', 5)
        font_color = data.get('color', '#FF0000')

        # 2. 验证文本内容
        is_valid, error_msg = validate_text_content(text, max_length=10000)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'文本内容验证失败: {error_msg}'
            }), 400

        # 3. 验证draft_id
        if draft_id:
            is_valid, error_msg = validate_draft_id(draft_id)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': f'draft_id验证失败: {error_msg}'
                }), 400

        # 4. 验证时长
        is_valid, error_msg = validate_duration(start, end)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'时长验证失败: {error_msg}'
            }), 400

        # 5. 验证颜色
        is_valid, error_msg = validate_color(font_color)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'字体颜色验证失败: {error_msg}'
            }), 400

        # 继续处理...
        result = add_text_impl(text, start, end, draft_id, font_color)

        return jsonify({'success': True, 'output': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 🛡️ 安全最佳实践

### 1. 验证顺序

推荐按以下顺序进行验证:

```python
# 1️⃣ 必填字段验证（最先）
is_valid, error = validate_required_fields(data, ['field1', 'field2'])

# 2️⃣ 格式验证（ID、URL等）
is_valid, error = validate_draft_id(draft_id)
is_valid, error = validate_url(video_url)

# 3️⃣ 范围验证（数值、长度等）
is_valid, error = validate_numeric_range(volume, 0, 1)
is_valid, error = validate_text_content(text, max_length=10000)

# 4️⃣ 业务逻辑验证（数据库查询等）
if draft_id not in draft_cache:
    return error_response('草稿不存在')
```

---

### 2. 错误响应格式

统一使用以下错误响应格式:

```python
# ✅ 推荐
return jsonify({
    'success': False,
    'error': f'{字段名}验证失败: {error_msg}'
}), 400

# 示例
return jsonify({
    'success': False,
    'error': 'draft_id验证失败: 草稿ID长度不能少于3字符'
}), 400
```

---

### 3. 内网地址处理

对于需要访问本地文件服务器的场景:

```python
# ✅ 允许内网访问
is_valid, error = validate_url(video_url, allow_internal=True)

# ❌ 不推荐：直接跳过URL验证
# if video_url:  # 没有验证
```

---

### 4. 空值处理

```python
# ✅ 推荐：先检查字段是否存在
draft_id = data.get('draft_id')
if draft_id:  # 只在用户提供了draft_id时才验证
    is_valid, error = validate_draft_id(draft_id)
    if not is_valid:
        return error_response(error)

# ❌ 不推荐：直接验证可能为None的值
is_valid, error = validate_draft_id(data.get('draft_id'))  # 可能报错
```

---

## 🧪 测试验证

### 运行内置测试

```bash
# 运行validators模块的内置测试
python3 validators.py
```

### 编写自定义测试

```python
import pytest
from validators import validate_draft_id, validate_url

def test_draft_id_valid():
    is_valid, error = validate_draft_id("dfd_cat_abc123")
    assert is_valid == True
    assert error == ""

def test_draft_id_too_short():
    is_valid, error = validate_draft_id("ab")
    assert is_valid == False
    assert "长度不能少于" in error

def test_url_localhost_blocked():
    is_valid, error = validate_url("http://localhost:8080/test")
    assert is_valid == False
    assert "禁止访问本地地址" in error

def test_url_localhost_allowed():
    is_valid, error = validate_url("http://localhost:8080/test", allow_internal=True)
    assert is_valid == True
```

---

## 📚 参考文档

- [输入验证功能实施总结](./输入验证功能实施总结.md) - 完整的实施报告
- [待优化任务清单](./待优化任务清单.md) - 项目优化计划
- [CapCutAPI架构分析与优化建议](./CapCutAPI_架构分析与优化建议.md) - 架构优化指南

---

**文档版本**: v1.0
**最后更新**: 2025-11-11
**维护人**: AI Assistant
