
import oss2
import os
from settings.local import OSS_CONFIG, MP4_OSS_CONFIG


def _ensure_bucket():
    auth = oss2.AuthV4(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
    endpoint = OSS_CONFIG['endpoint']
    if not endpoint.startswith('http'):
        endpoint = 'https://' + endpoint
    return oss2.Bucket(auth, endpoint, OSS_CONFIG['bucket_name'], region=OSS_CONFIG['region'])

    
def upload_to_oss(path):
    # Create OSS client with v4 authentication and region
    bucket = _ensure_bucket()
    
    # Upload file
    object_name = os.path.basename(path)
    bucket.put_object_from_file(object_name, path)
    
    # Generate public URL (since bucket is public-read-write)
    url = f"https://{OSS_CONFIG['bucket_name']}.{OSS_CONFIG['endpoint']}/{object_name}"
    
    # Clean up temporary file
    os.remove(path)
    
    return url


def upload_mp4_to_oss(path):
    """Special method for uploading MP4 files, using custom domain and v4 signature"""
    # Directly use credentials from the configuration file
    auth = oss2.AuthV4(MP4_OSS_CONFIG['access_key_id'], MP4_OSS_CONFIG['access_key_secret'])
    
    # Use the correct OSS endpoint for bucket operations
    oss_endpoint = f"https://oss-{MP4_OSS_CONFIG['region']}.aliyuncs.com"
    
    # Create bucket instance with region
    bucket = oss2.Bucket(auth, oss_endpoint, MP4_OSS_CONFIG['bucket_name'], region=MP4_OSS_CONFIG['region'])
    
    # Upload file
    object_name = os.path.basename(path)
    bucket.put_object_from_file(object_name, path)
    
    # Generate custom domain URL (use the configured endpoint for public access)
    custom_domain = MP4_OSS_CONFIG['endpoint']
    url = f"{custom_domain}/{object_name}"
    
    return url


def get_signed_draft_url_if_exists(draft_id: str, expires_seconds: int = 24*60*60):
    """Return signed URL for <draft_id>.zip if exists in OSS. Otherwise return ("", False)."""
    bucket = _ensure_bucket()
    key = f"{draft_id}.zip"
    try:
        if bucket.object_exists(key):
            url = f"https://{OSS_CONFIG['bucket_name']}.{OSS_CONFIG['endpoint']}/{key}"
            return url, True
        return "", False
    except Exception:
        # Do not raise; let caller handle errors uniformly
        return "", False