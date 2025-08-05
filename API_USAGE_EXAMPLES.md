# CapCutAPI 使用示例

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

### 8. 保存草稿

```python
import requests

# 保存草稿
response = requests.post("http://8.148.70.18:9000/save_draft", json={
    "draft_id": "my_draft_001",
    "draft_folder": "/path/to/capcut/drafts"
})

print(response.json())
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

1. **草稿ID**: 每个草稿必须有唯一的ID
2. **时间参数**: start和end参数表示秒数
3. **坐标系统**: position_x和position_y使用0-1的相对坐标
4. **文件格式**: 支持常见的视频、音频、图片格式
5. **网络资源**: 确保视频、音频、图片URL可以正常访问

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