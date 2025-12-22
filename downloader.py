import os
import subprocess
import time
import requests
import shutil
from requests.exceptions import RequestException, Timeout
from urllib.parse import urlparse, unquote, urlunparse, parse_qs, urlencode
from settings.local import DOWNLOAD_HEADERS, FILE_SERVER_PUBLIC_HOST, FILE_SERVER_INTERNAL_BASE
# 导入路径工具模块以支持相对路径
from path_utils import normalize_path, ensure_directory_exists

def strip_oss_signature(url):
    """
    去掉 OSS 签名参数，返回无签名的 URL
    阿里云 OSS 签名参数以 x-oss- 开头
    """
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        
        # 解析查询参数
        params = parse_qs(parsed.query, keep_blank_values=True)
        
        # 检查是否有 OSS 签名参数
        oss_params = [k for k in params.keys() if k.lower().startswith('x-oss-')]
        if not oss_params:
            return url
        
        # 移除所有 OSS 签名参数
        clean_params = {k: v for k, v in params.items() if not k.lower().startswith('x-oss-')}
        
        # 重建 URL
        new_query = urlencode(clean_params, doseq=True) if clean_params else ''
        new_parsed = parsed._replace(query=new_query)
        clean_url = urlunparse(new_parsed)
        
        print(f"🔧 Stripped OSS signature from URL: {url[:60]}... -> {clean_url[:60]}...")
        return clean_url
    except Exception as e:
        print(f"⚠️ Failed to strip OSS signature: {e}")
        return url

def download_video(video_url, draft_name, material_name, max_retries=3):
    """
    Download video to specified directory
    支持相对路径和绝对路径
    使用 requests 下载以支持重试和 Headers，更稳定
    
    :param video_url: Video URL
    :param draft_name: Draft name (支持相对路径)
    :param material_name: Material name
    :param max_retries: Maximum retry attempts
    :return: Local video path
    """
    # 🆕 支持相对路径：规范化draft_name
    draft_name = normalize_path(draft_name)
    
    # Ensure directory exists
    video_dir = f"{draft_name}/assets/video"
    ensure_directory_exists(video_dir)
    
    # Generate local filename
    local_path = f"{video_dir}/{material_name}"
    
    # Check if file already exists
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        print(f"Video file already exists: {local_path}")
        return local_path
    
    import requests
    import time
    
    last_error = None
    for attempt in range(max_retries):
        try:
            print(f"Downloading video (attempt {attempt+1}/{max_retries}): {video_url[:80]}...")
            
            # 自动设置 Referer
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            try:
                parsed = urlparse(video_url)
                if parsed.scheme in ('http', 'https'):
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                    headers['Referer'] = origin
            except:
                pass

            response = requests.get(
                video_url, 
                timeout=120,  # 视频通常较大，增加超时时间
                stream=True, 
                allow_redirects=True,
                headers=headers
            )
            response.raise_for_status()
            
            # 写入文件
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192 * 4):
                    if chunk:
                        f.write(chunk)
            
            # 验证
            if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
                raise Exception("File download failed or empty")
                
            print(f"✅ Video downloaded successfully: {material_name}")
            return local_path
            
        except Exception as e:
            last_error = str(e)
            print(f"⚠️ Video download error: {last_error}")
            
            # 清理失败的文件
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except:
                    pass
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    # 如果所有重试都失败，尝试使用 ffmpeg 作为备选方案
    print(f"⚠️ Requests download failed, falling back to ffmpeg for: {video_url}")
    try:
        command = [
            '/usr/bin/ffmpeg',
            '-i', video_url,
            '-c', 'copy',
            '-y',
            '-v', 'error',
            local_path
        ]
        subprocess.run(command, check=True, capture_output=True)
        return local_path
    except Exception as e:
        raise Exception(f"Failed to download video (both requests and ffmpeg failed): {str(e)}. Last error: {last_error}")

def download_image(image_url, draft_name, material_name, max_retries=3):
    """
    Download image to specified directory, and convert to PNG format
    支持相对路径和绝对路径
    
    :param image_url: Image URL
    :param draft_name: Draft name (支持相对路径)
    :param material_name: Material name
    :param max_retries: Maximum retry attempts
    :return: Local image path
    """
    # 🆕 支持相对路径：规范化draft_name
    draft_name = normalize_path(draft_name)
    
    # Ensure directory exists
    image_dir = f"{draft_name}/assets/image"
    ensure_directory_exists(image_dir)
    
    # Uniformly use png format
    local_path = f"{image_dir}/{material_name}"
    
    # Check if file already exists
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        print(f"Image file already exists: {local_path}")
        return local_path
    
    import requests
    import uuid
    import time
    
    # 临时文件路径
    temp_filename = f"temp_{uuid.uuid4().hex}"
    temp_path = os.path.join(image_dir, temp_filename)
    
    last_error = None
    
    # 🆕 准备 URL 列表：先尝试原始 URL，如果失败再尝试去掉签名的 URL
    urls_to_try = [image_url]
    clean_url = strip_oss_signature(image_url)
    if clean_url != image_url:
        urls_to_try.append(clean_url)
    
    for url_index, current_url in enumerate(urls_to_try):
        url_desc = "signed URL" if url_index == 0 else "clean URL (no signature)"
        
        for attempt in range(max_retries):
            try:
                # 1. 使用 requests 下载原图（更稳定，支持重试和Headers控制）
                print(f"Downloading image [{url_desc}] (attempt {attempt+1}/{max_retries}): {current_url[:80]}...")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
                }
                
                # 🆕 注意：OSS 可能设置了 Referer 防盗链
                # 只对非 OSS URL 设置 Referer，避免触发 403
                try:
                    parsed = urlparse(current_url)
                    is_oss_url = 'aliyuncs.com' in parsed.netloc or 'oss' in parsed.netloc.lower()
                    if parsed.scheme in ('http', 'https') and not is_oss_url:
                        origin = f"{parsed.scheme}://{parsed.netloc}"
                        headers['Referer'] = origin
                except:
                    pass
                    
                response = requests.get(current_url, headers=headers, timeout=60, stream=True)
                response.raise_for_status()
                
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            
                # 2. 使用 ffmpeg 转换为 PNG
                command = [
                    '/usr/bin/ffmpeg',
                    '-i', temp_path,
                    '-vf', 'format=rgba',  # Convert to RGBA format to support transparency
                    '-frames:v', '1',      # Ensure only one frame is processed
                    '-y',                  # Overwrite existing files
                    '-v', 'error',         # 只显示错误信息
                    local_path
                ]
                subprocess.run(command, check=True, capture_output=True)
                
                print(f"✅ Image downloaded and converted: {material_name}")
                return local_path
                
            except Exception as e:
                last_error = str(e)
                print(f"⚠️ Image download error: {last_error}")
                
                # 🆕 如果是 403 错误且还有其他 URL 可以尝试，跳过剩余重试直接尝试下一个 URL
                if '403' in last_error and url_index < len(urls_to_try) - 1:
                    print(f"🔄 403 Forbidden with {url_desc}, will try clean URL...")
                    break
                    
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            finally:
                # 清理临时文件
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
    
    raise Exception(f"Failed to download image after {max_retries} attempts: {last_error}")

def download_audio(audio_url, draft_name, material_name, max_retries=3):
    """
    Download audio using requests (more reliable than ffmpeg for remote URLs)
    支持相对路径和绝对路径
    
    :param audio_url: Audio URL  
    :param draft_name: Draft name (支持相对路径)
    :param material_name: Material name
    :param max_retries: Maximum retry attempts
    :return: Local audio path
    """
    # 🆕 支持相对路径：规范化draft_name
    draft_name = normalize_path(draft_name)
    
    # Ensure directory exists
    audio_dir = f"{draft_name}/assets/audio"
    ensure_directory_exists(audio_dir)
    
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
            
            # 🔧 改进：使用requests下载，支持重定向和各种HTTP特性，增强请求头
            response = requests.get(
                audio_url, 
                timeout=60,  # 60秒超时
                stream=True,  # 流式下载，节省内存
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'identity'  # 避免压缩，直接下载原始音频
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
    """
    通用文件下载函数
    支持相对路径和绝对路径
    
    :param url: 文件URL或本地路径
    :param local_filename: 本地保存路径 (支持相对路径)
    :param max_retries: 最大重试次数
    :param timeout: 超时时间（秒）
    :return: 本地文件路径
    """
    # 🆕 支持相对路径：规范化local_filename
    local_filename = normalize_path(local_filename)
    
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

