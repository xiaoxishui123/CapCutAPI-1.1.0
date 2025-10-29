import os
import subprocess
import time
import requests
import shutil
from requests.exceptions import RequestException, Timeout
from urllib.parse import urlparse, unquote, urlunparse
from settings.local import DOWNLOAD_HEADERS, FILE_SERVER_PUBLIC_HOST, FILE_SERVER_INTERNAL_BASE

def download_video(video_url, draft_name, material_name):
    """
    Download video to specified directory
    :param video_url: Video URL
    :param draft_name: Draft name
    :param material_name: Material name
    :return: Local video path
    """
    # Ensure directory exists
    video_dir = f"{draft_name}/assets/video"
    os.makedirs(video_dir, exist_ok=True)
    
    # Generate local filename
    local_path = f"{video_dir}/{material_name}"
    
    # Check if file already exists
    if os.path.exists(local_path):
        print(f"Video file already exists: {local_path}")
        return local_path
    
    try:
        # Use ffmpeg to download video
        command = [
            '/usr/bin/ffmpeg',
            '-i', video_url,
            '-c', 'copy',  # Direct copy, no re-encoding
            local_path
        ]
        subprocess.run(command, check=True, capture_output=True)
        return local_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to download video: {e.stderr.decode('utf-8')}")

def download_image(image_url, draft_name, material_name):
    """
    Download image to specified directory, and convert to PNG format
    :param image_url: Image URL
    :param draft_name: Draft name
    :param material_name: Material name
    :return: Local image path
    """
    # Ensure directory exists
    image_dir = f"{draft_name}/assets/image"
    os.makedirs(image_dir, exist_ok=True)
    
    # Uniformly use png format
    local_path = f"{image_dir}/{material_name}"
    
    # Check if file already exists
    if os.path.exists(local_path):
        print(f"Image file already exists: {local_path}")
        return local_path
    
    try:
        # Use ffmpeg to download and convert image to PNG format
        command = [
            '/usr/bin/ffmpeg',
            '-headers', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36\r\nReferer: https://www.163.com/\r\n',
            '-i', image_url,
            '-vf', 'format=rgba',  # Convert to RGBA format to support transparency
            '-frames:v', '1',      # Ensure only one frame is processed
            '-y',                  # Overwrite existing files
            local_path
        ]
        subprocess.run(command, check=True, capture_output=True)
        return local_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to download image: {e.stderr.decode('utf-8')}")

def download_audio(audio_url, draft_name, material_name, max_retries=3):
    """
    Download audio using requests (more reliable than ffmpeg for remote URLs)
    :param audio_url: Audio URL  
    :param draft_name: Draft name
    :param material_name: Material name
    :param max_retries: Maximum retry attempts
    :return: Local audio path
    """
    # Ensure directory exists
    audio_dir = f"{draft_name}/assets/audio"
    os.makedirs(audio_dir, exist_ok=True)
    
    # Generate local filename (keep .mp3 extension)
    local_path = f"{audio_dir}/{material_name}"
    
    # Check if file already exists and is not empty
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        print(f"Audio file already exists: {local_path}")
        return local_path
    
    # 🔧 修复：使用requests替代ffmpeg，更稳定可靠
    import requests
    import time
    
    last_error = None
    for attempt in range(max_retries):
        try:
            print(f"Downloading audio (attempt {attempt+1}/{max_retries}): {audio_url[:80]}...")
            
            # 使用requests下载，支持重定向和各种HTTP特性
            response = requests.get(
                audio_url, 
                timeout=60,  # 60秒超时
                stream=True,  # 流式下载，节省内存
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            response.raise_for_status()  # 检查HTTP错误
            
            # 写入文件
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 验证文件已下载且不为空
            if not os.path.exists(local_path):
                raise Exception(f"File was not created: {local_path}")
            
            file_size = os.path.getsize(local_path)
            if file_size == 0:
                raise Exception(f"Downloaded file is empty: {local_path}")
            
            print(f"✅ Audio downloaded successfully: {material_name} ({file_size} bytes)")
            return local_path
            
        except requests.Timeout:
            last_error = f"Download timeout after 60 seconds"
            print(f"⚠️  {last_error}")
        except requests.RequestException as e:
            last_error = f"HTTP error: {str(e)}"
            print(f"⚠️  {last_error}")
        except Exception as e:
            last_error = f"Download error: {str(e)}"
            print(f"⚠️  {last_error}")
        
        # 重试前等待（指数退避）
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1s, 2s, 4s...
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    # 所有重试都失败
    raise Exception(f"Failed to download audio after {max_retries} attempts: {last_error}")

def download_file(url:str, local_filename, max_retries=3, timeout=180):
    # 检查是否是本地文件路径
    if os.path.exists(url) and os.path.isfile(url):
        # 是本地文件，直接复制
        directory = os.path.dirname(local_filename)
        
        # 创建目标目录（如果不存在）
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
        
        print(f"Copying local file: {url} to {local_filename}")
        start_time = time.time()
        
        # 复制文件
        shutil.copy2(url, local_filename)
        
        print(f"Copy completed in {time.time()-start_time:.2f} seconds")
        print(f"File saved as: {os.path.abspath(local_filename)}")
        return local_filename
    
    # 原有的下载逻辑
    # Extract directory part
    directory = os.path.dirname(local_filename)

    retries = 0
    while retries < max_retries:
        try:
            if retries > 0:
                wait_time = 2 ** retries  # Exponential backoff strategy
                print(f"Retrying in {wait_time} seconds... (Attempt {retries+1}/{max_retries})")
                time.sleep(wait_time)
            
            print(f"Downloading file: {local_filename}")
            start_time = time.time()
            
            # Create directory (if it doesn't exist)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"Created directory: {directory}")

            # Build headers dynamically; avoid hardcoded Referer which may cause 403
            parsed = urlparse(url)
            # Optional host rewrite to internal base
            try:
                if FILE_SERVER_PUBLIC_HOST and FILE_SERVER_INTERNAL_BASE and parsed.netloc == FILE_SERVER_PUBLIC_HOST:
                    internal = urlparse(FILE_SERVER_INTERNAL_BASE)
                    parsed = parsed._replace(scheme=internal.scheme or parsed.scheme,
                                             netloc=internal.netloc or parsed.netloc)
                    url = urlunparse(parsed)
            except Exception:
                pass
            origin = f"{parsed.scheme}://{parsed.netloc}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            # Only set Referer when origin is http(s)
            if parsed.scheme in ('http', 'https'):
                headers['Referer'] = origin

            # Merge custom headers from config (take precedence)
            if isinstance(DOWNLOAD_HEADERS, dict) and DOWNLOAD_HEADERS:
                headers.update(DOWNLOAD_HEADERS)
            with requests.get(url, stream=True, timeout=timeout, headers=headers) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024
                
                with open(local_filename, 'wb') as file:
                    bytes_written = 0
                    for chunk in response.iter_content(block_size):
                        if chunk:
                            file.write(chunk)
                            bytes_written += len(chunk)
                            
                            if total_size > 0:
                                progress = bytes_written / total_size * 100
                                # For frequently updated progress, consider using logger.debug or more granular control to avoid large log files
                                # Or only output progress to console, not write to file
                                print(f"\r[PROGRESS] {progress:.2f}% ({bytes_written/1024:.2f}KB/{total_size/1024:.2f}KB)", end='')
                                pass # Avoid printing too much progress information in log files
                
                if total_size > 0:
                    # print() # Original newline
                    pass
                print(f"Download completed in {time.time()-start_time:.2f} seconds")
                print(f"File saved as: {os.path.abspath(local_filename)}")
                return local_filename
                
        except Timeout:
            print(f"Download timed out after {timeout} seconds")
        except RequestException as e:
            print(f"Request failed: {e}")
        except Exception as e:
            print(f"Unexpected error during download: {e}")
        
        retries += 1
    
    print(f"Download failed after {max_retries} attempts for URL: {url}")
    return False

