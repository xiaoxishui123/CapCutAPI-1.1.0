# CapCutAPI 使用示例

> 建议先阅读 `CapCutAPI_快速使用指南.md` 了解标准流程与路径规范。以下示例聚焦接口调用。

## 服务器信息

- **服务器地址**: http://8.148.70.18:9000
- **部署状态**: ✅ 已部署并运行中
- **服务管理**: 使用 `./service_manager.sh` 脚本

## 快速开始

### 1. 创建草稿

```python
import requests

# 创建新草稿
response = requests.post("http://8.148.70.18:9000/create_draft", json={
    "draft_id": "my_draft_001",
    "width": 1080,
    "height": 1920
})

print(response.json())
```

### 2. 添加视频

```python
import requests

# 添加视频到草稿
response = requests.post("http://8.148.70.18:9000/add_video", json={
    "draft_id": "my_draft_001",
    "video_url": "http://example.com/video.mp4",
    "start": 0,
    "end": 10,
    "width": 1080,
    "height": 1920,
    "speed": 1.0,
    "volume": 1.0
})

print(response.json())
```

### 3. 添加文本

```python
import requests

# 添加文本到草稿
response = requests.post("http://8.148.70.18:9000/add_text", json={
    "draft_id": "my_draft_001",
    "text": "Hello, World!",
    "start": 0,
    "end": 3,
    "font": "ZY_Courage",
    "font_color": "#FF0000",
    "font_size": 30.0,
    "position_x": 0.5,
    "position_y": 0.5
})

print(response.json())
```

### 4. 添加音频

```python
import requests

# 添加音频到草稿
response = requests.post("http://8.148.70.18:9000/add_audio", json={
    "draft_id": "my_draft_001",
    "audio_url": "http://example.com/audio.mp3",
    "start": 0,
    "end": 10,
    "volume": 1.0
})

print(response.json())
```

### 5. 添加图片

```python
import requests

# 添加图片到草稿
response = requests.post("http://8.148.70.18:9000/add_image", json={
    "draft_id": "my_draft_001",
    "image_url": "http://example.com/image.jpg",
    "start": 0,
    "end": 5,
    "width": 1080,
    "height": 1920
})

print(response.json())
```

### 6. 添加字幕

```python
import requests

# 添加字幕到草稿
response = requests.post("http://8.148.70.18:9000/add_subtitle", json={
    "draft_id": "my_draft_001",
    "subtitle_text": "这是字幕内容",
    "start": 0,
    "end": 3,
    "font": "ZY_Courage",
    "font_color": "#FFFFFF",
    "font_size": 24.0
})

print(response.json())
```

### 7. 添加特效

```python
import requests

# 添加特效到草稿
response = requests.post("http://8.148.70.18:9000/add_effect", json={
    "draft_id": "my_draft_001",
    "effect_type": "Transition",
    "effect_name": "Fade",
    "start": 0,
    "end": 1
})

print(response.json())
```

### 8. 保存草稿与生成下载链接（派生zip）

```python
import requests

# 保存草稿（可选：本地保存时传 draft_folder）
requests.post("http://8.148.70.18:9000/save_draft", json={
    "draft_id": "my_draft_001"
})

# 生成下载链接：标准直链（存在则直接返回）
r = requests.post("http://8.148.70.18:9000/generate_draft_url", json={
    "draft_id": "my_draft_001"
}).json()
print(r)

# 生成定制化下载链接：按客户端改写并缓存派生zip
r2 = requests.post("http://8.148.70.18:9000/generate_draft_url", json={
    "draft_id": "my_draft_001",
    "client_os": "windows",           # 或 linux
    "draft_folder": "F:/jianyin/cgwz/JianyingPro Drafts"
}).json()
print(r2)

# 未上传时一键触发
requests.post("http://8.148.70.18:9000/generate_draft_url?force_save=true", json={
    "draft_id": "my_draft_001",
    "force_save": True
})
```

## 获取支持的选项

### 获取动画类型

```python
import requests

# 获取入场动画类型
response = requests.get("http://8.148.70.18:9000/get_intro_animation_types")
print(response.json())

# 获取出场动画类型
response = requests.get("http://8.148.70.18:9000/get_outro_animation_types")
print(response.json())

# 获取转场类型
response = requests.get("http://8.148.70.18:9000/get_transition_types")
print(response.json())

# 获取遮罩类型
response = requests.get("http://8.148.70.18:9000/get_mask_types")
print(response.json())

# 获取字体类型
response = requests.get("http://8.148.70.18:9000/get_font_types")
print(response.json())
```

## 完整示例

```python
import requests
import time

# 服务器地址
BASE_URL = "http://8.148.70.18:9000"

def create_video_project():
    """创建完整的视频项目示例"""
    
    # 1. 创建草稿
    print("创建草稿...")
    response = requests.post(f"{BASE_URL}/create_draft", json={
        "draft_id": "demo_project_001",
        "width": 1080,
        "height": 1920
    })
    print(response.json())
    
    # 2. 添加视频
    print("添加视频...")
    response = requests.post(f"{BASE_URL}/add_video", json={
        "draft_id": "demo_project_001",
        "video_url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "start": 0,
        "end": 10,
        "width": 1080,
        "height": 1920
    })
    print(response.json())
    
    # 3. 添加文本
    print("添加文本...")
    response = requests.post(f"{BASE_URL}/add_text", json={
        "draft_id": "demo_project_001",
        "text": "欢迎使用CapCutAPI!",
        "start": 0,
        "end": 5,
        "font": "ZY_Courage",
        "font_color": "#FF0000",
        "font_size": 40.0,
        "position_x": 0.5,
        "position_y": 0.8
    })
    print(response.json())
    
    # 4. 添加字幕
    print("添加字幕...")
    response = requests.post(f"{BASE_URL}/add_subtitle", json={
        "draft_id": "demo_project_001",
        "subtitle_text": "这是一个演示项目",
        "start": 2,
        "end": 7,
        "font": "ZY_Courage",
        "font_color": "#FFFFFF",
        "font_size": 28.0
    })
    print(response.json())
    
    # 5. 保存草稿
    print("保存草稿...")
    response = requests.post(f"{BASE_URL}/save_draft", json={
        "draft_id": "demo_project_001"
    })
    print(response.json())
    
    print("项目创建完成！")

if __name__ == "__main__":
    create_video_project()
```

## 新增功能示例

### 1. 草稿列表查询

```python
# 获取所有草稿列表
response = requests.get(f"{BASE_URL}/api/drafts/list")
print(f"草稿列表: {response.json()}")
```

### 2. 批量下载草稿

```python
# 批量下载多个草稿
response = requests.post(f"{BASE_URL}/api/drafts/batch-download", json={
    "draft_ids": ["draft1", "draft2", "draft3"],
    "client_os": "windows",
    "draft_folder": "F:/jianyin/cgwz/JianyingPro Drafts"
})
print(f"批量下载结果: {response.json()}")
```

### 3. 生成定制化下载链接

```python
# 生成Windows平台的下载链接
response = requests.post(f"{BASE_URL}/generate_draft_url", json={
    "draft_id": "my_draft",
    "client_os": "windows",
    "draft_folder": "F:/jianyin/cgwz/JianyingPro Drafts"
})
print(f"下载链接: {response.json()}")
```

### 4. 草稿缓存调试

```python
# 查看草稿缓存信息
response = requests.get(f"{BASE_URL}/debug/cache/my_draft")
print(f"缓存信息: {response.json()}")
```

## Pattern 模板库 API (NEW! 🎨)

Pattern 模板库提供开箱即用的视频编辑模板，帮助您快速创建专业视频。

### 1. 列出所有可用模板

**请求**:
```python
import requests

BASE_URL = "http://8.148.70.18:9000"

# 获取所有模板列表
response = requests.get(f"{BASE_URL}/api/patterns/list")
data = response.json()

print(f"成功: {data['success']}")
print(f"模板数量: {data['count']}")
print(f"\n可用模板:")
for pattern in data['patterns']:
    print(f"  - ID: {pattern['id']}")
    print(f"    名称: {pattern['name']}")
    print(f"    类型: {pattern['type']}")
    print(f"    描述: {pattern['description']}")
    if pattern.get('video_url'):
        print(f"    演示: {pattern['video_url']}")
    print()
```

**响应示例**:
```json
{
  "success": true,
  "patterns": [
    {
      "id": "001-words",
      "name": "文字滚动效果",
      "description": "文字滚动效果视频模板，支持 AI 生成文字内容",
      "file": "001-words.py",
      "type": "python",
      "video_url": "https://www.youtube.com/watch?v=HLSHaJuNtBw"
    },
    {
      "id": "002-relationship",
      "name": "情侣关系主题",
      "description": "生成情侣关系主题的短视频",
      "file": "002-relationship.py",
      "type": "python",
      "video_url": "https://www.youtube.com/watch?v=f2Q1OI_SQZo"
    },
    {
      "id": "001-words-coze",
      "name": "文字滚动效果（扣子工作流）",
      "description": "扣子平台工作流配置文件",
      "file": "001-words-coze.md",
      "type": "workflow"
    }
  ],
  "count": 3
}
```

### 2. 获取模板详情和内容

**请求**:
```python
import requests

BASE_URL = "http://8.148.70.18:9000"
pattern_id = "001-words"

# 获取模板详情
response = requests.get(f"{BASE_URL}/api/patterns/get/{pattern_id}")
data = response.json()

if data['success']:
    pattern = data['pattern']
    print(f"模板名称: {pattern['name']}")
    print(f"模板类型: {pattern['type']}")
    print(f"模板描述: {pattern['description']}")
    print(f"内容长度: {len(pattern['content'])} 字符")

    # 保存模板内容到本地
    file_ext = ".py" if pattern['type'] == "python" else ".md"
    filename = f"{pattern_id}{file_ext}"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(pattern['content'])

    print(f"\n✅ 模板已保存到: {filename}")
else:
    print(f"❌ 错误: {data['error']}")
```

**响应示例**:
```json
{
  "success": true,
  "pattern": {
    "id": "001-words",
    "name": "文字滚动效果",
    "description": "文字滚动效果视频模板",
    "file": "001-words.py",
    "type": "python",
    "video_url": "https://www.youtube.com/watch?v=HLSHaJuNtBw",
    "content": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n...(完整的模板代码)..."
  }
}
```

### 3. 直接下载模板文件

**请求**:
```python
import requests

BASE_URL = "http://8.148.70.18:9000"
pattern_id = "001-words"

# 下载模板文件
response = requests.get(f"{BASE_URL}/api/patterns/download/{pattern_id}")

if response.status_code == 200:
    # 从 Content-Disposition 头获取文件名
    filename = f"{pattern_id}.py"  # 根据模板类型调整扩展名

    with open(filename, 'wb') as f:
        f.write(response.content)

    print(f"✅ 模板已下载: {filename}")
    print(f"文件大小: {len(response.content)} 字节")
else:
    print(f"❌ 下载失败: {response.status_code}")
    print(response.text)
```

**使用 curl 下载**:
```bash
# 下载 Python 模板
curl -O http://8.148.70.18:9000/api/patterns/download/001-words

# 下载工作流配置
curl -O http://8.148.70.18:9000/api/patterns/download/001-words-coze
```

### 4. 完整的 Pattern 使用流程

```python
import requests
import json

BASE_URL = "http://8.148.70.18:9000"

def use_pattern_workflow():
    """完整的 Pattern 使用流程示例"""

    print("=" * 60)
    print("Pattern 模板库使用流程")
    print("=" * 60)

    # 步骤 1: 浏览可用模板
    print("\n📋 步骤 1: 获取模板列表...")
    response = requests.get(f"{BASE_URL}/api/patterns/list")
    patterns = response.json()['patterns']

    print(f"找到 {len(patterns)} 个可用模板:")
    for i, pattern in enumerate(patterns, 1):
        print(f"{i}. {pattern['name']} ({pattern['id']})")
        print(f"   类型: {pattern['type']}")
        print(f"   {pattern['description']}")

    # 步骤 2: 选择并下载模板
    pattern_id = "001-words"  # 选择文字滚动效果模板
    print(f"\n📥 步骤 2: 下载模板 '{pattern_id}'...")

    response = requests.get(f"{BASE_URL}/api/patterns/get/{pattern_id}")
    pattern_data = response.json()['pattern']

    # 保存到本地
    filename = f"{pattern_id}.py"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(pattern_data['content'])

    print(f"✅ 模板已保存: {filename}")

    # 步骤 3: 配置和使用
    print(f"\n⚙️ 步骤 3: 配置说明")
    print("请按照以下步骤使用模板:")
    print(f"1. 打开 {filename} 查看配置要求")
    print("2. 配置必要的 API 密钥 (如: Qwen API Key, Pexels API Key)")
    print("3. 根据需要调整模板参数")
    print(f"4. 运行模板: python3 {filename}")

    # 步骤 4: 查看演示
    if pattern_data.get('video_url'):
        print(f"\n🎬 步骤 4: 查看演示效果")
        print(f"演示视频: {pattern_data['video_url']}")

    print("\n" + "=" * 60)
    print("✅ Pattern 使用流程完成！")
    print("=" * 60)

if __name__ == "__main__":
    use_pattern_workflow()
```

### 5. 错误处理示例

```python
import requests

BASE_URL = "http://8.148.70.18:9000"

def get_pattern_safely(pattern_id):
    """安全地获取 Pattern 模板"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/patterns/get/{pattern_id}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data['success']:
                return data['pattern']
            else:
                print(f"❌ API 错误: {data.get('error', '未知错误')}")
                return None

        elif response.status_code == 404:
            print(f"❌ 模板不存在: {pattern_id}")
            print("提示: 使用 /api/patterns/list 查看可用模板")
            return None

        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print("❌ 请求超时，请检查网络连接")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {str(e)}")
        return None

    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        return None

# 使用示例
pattern = get_pattern_safely("001-words")
if pattern:
    print(f"✅ 成功获取模板: {pattern['name']}")
else:
    print("获取模板失败")
```

### 6. Pattern 与草稿 API 结合使用

```python
import requests

BASE_URL = "http://8.148.70.18:9000"

def create_video_from_pattern():
    """使用 Pattern 模板创建视频项目"""

    # 1. 获取模板内容作为参考
    print("📋 获取模板参考...")
    response = requests.get(f"{BASE_URL}/api/patterns/get/001-words")
    pattern = response.json()['pattern']
    print(f"使用模板: {pattern['name']}")

    # 2. 创建草稿
    print("\n📝 创建草稿...")
    draft_id = "pattern_demo_001"
    requests.post(f"{BASE_URL}/create_draft", json={
        "draft_id": draft_id,
        "width": 1080,
        "height": 1920
    })

    # 3. 根据模板逻辑添加素材
    print("🎬 添加视频素材...")
    requests.post(f"{BASE_URL}/add_video", json={
        "draft_id": draft_id,
        "video_url": "http://example.com/background.mp4",
        "start": 0,
        "end": 10
    })

    print("✍️ 添加文字效果...")
    requests.post(f"{BASE_URL}/add_text", json={
        "draft_id": draft_id,
        "text": "这是使用 Pattern 创建的视频",
        "start": 0,
        "end": 10,
        "font": "ZY_Courage",
        "font_color": "#FF0000",
        "font_size": 40.0
    })

    # 4. 保存草稿
    print("\n💾 保存草稿...")
    response = requests.post(f"{BASE_URL}/save_draft", json={
        "draft_id": draft_id
    })

    print(f"✅ 草稿创建完成: {draft_id}")
    print(f"预览地址: {BASE_URL}/draft/preview/{draft_id}")

if __name__ == "__main__":
    create_video_from_pattern()
```

## Web界面访问

### 核心页面

#### 1. 主页
- **地址**: http://8.148.70.18:9000
- **功能**: 欢迎页面，显示 API 基本信息

#### 2. 草稿管理仪表板
- **地址**: http://8.148.70.18:9000/api/drafts/dashboard
- **功能**: 管理所有草稿，支持批量操作

#### 3. 草稿预览
- **地址**: http://8.148.70.18:9000/draft/preview/[草稿ID]
- **功能**: 可视化预览草稿内容和时间轴
- **示例**: http://8.148.70.18:9000/draft/preview/dfd_cat_1756104121_cb774809

#### 4. 草稿下载
- **地址**: http://8.148.70.18:9000/draft/downloader?draft_id=[草稿ID]
- **功能**: 下载草稿文件到本地

### Pattern 相关接口 (API Only)

Pattern 模板库通过 API 端点提供服务，没有专门的 Web 页面，但可以通过浏览器访问：

#### 5. Pattern 列表 (JSON)
- **地址**: http://8.148.70.18:9000/api/patterns/list
- **功能**: 返回所有可用模板的 JSON 列表
- **格式**: JSON

#### 6. Pattern 详情 (JSON)
- **地址**: http://8.148.70.18:9000/api/patterns/get/[模板ID]
- **示例**: http://8.148.70.18:9000/api/patterns/get/001-words
- **功能**: 返回模板的完整信息和代码内容
- **格式**: JSON

#### 7. Pattern 下载 (文件)
- **地址**: http://8.148.70.18:9000/api/patterns/download/[模板ID]
- **示例**: http://8.148.70.18:9000/api/patterns/download/001-words
- **功能**: 直接下载模板文件
- **格式**: Python 脚本 (.py) 或 Markdown (.md)

## 错误处理

```python
import requests

def safe_api_call(url, data=None):
    """安全的API调用函数"""
    try:
        if data:
            response = requests.post(url, json=data, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                return result
            else:
                print(f"API错误: {result.get('error', '未知错误')}")
                return None
        else:
            print(f"HTTP错误: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"网络错误: {str(e)}")
        return None
    except Exception as e:
        print(f"未知错误: {str(e)}")
        return None

# 使用示例
result = safe_api_call("http://8.148.70.18:9000/get_intro_animation_types")
if result:
    print("API调用成功")
else:
    print("API调用失败")
```

## 服务管理

### 查看服务状态
```bash
./service_manager.sh status
```

### 重启服务
```bash
./service_manager.sh restart
```

### 查看日志
```bash
./service_manager.sh logs
```

### 测试API
```bash
./service_manager.sh test
```

## 注意事项

### 基础 API 使用

1. **草稿ID**: 每个草稿必须有唯一的ID
2. **时间参数**: start和end参数表示秒数
3. **坐标系统**: position_x和position_y使用0-1的相对坐标
4. **文件格式**: 支持常见的视频、音频、图片格式
5. **网络资源**: 确保视频、音频、图片URL可以正常访问

### Pattern 模板使用

6. **模板类型**: 支持 Python 脚本 (`.py`) 和工作流配置 (`.md`)
7. **API 密钥**: Python 模板可能需要配置第三方 API 密钥（如 Qwen、Pexels）
8. **演示视频**: 大多数模板都有演示视频链接，建议先查看效果
9. **模板修改**: 下载后可以根据需求自由修改模板代码
10. **错误处理**: 使用 404 状态码表示模板不存在，使用 `/api/patterns/list` 查看可用模板

### 最佳实践

11. **超时设置**: API 调用建议设置 10-30 秒超时
12. **错误处理**: 始终检查响应的 `success` 字段和 HTTP 状态码
13. **文件编码**: 模板内容使用 UTF-8 编码
14. **并发控制**: 批量操作时注意控制并发数量，避免服务器过载

## 故障排除

### 服务无法启动
```bash
# 查看详细错误信息
sudo journalctl -u capcutapi.service -n 50

# 检查端口占用
netstat -tlnp | grep 9000

# 检查防火墙
firewall-cmd --list-ports
```

### API调用失败
```bash
# 测试网络连接
curl -v http://8.148.70.18:9000/get_intro_animation_types

# 检查服务状态
./service_manager.sh status
```

### 权限问题
```bash
# 确保脚本有执行权限
chmod +x service_manager.sh
chmod +x deploy.sh

# 检查文件权限
ls -la *.sh
```