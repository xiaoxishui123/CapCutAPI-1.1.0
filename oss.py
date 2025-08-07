
import oss2
import os
from settings.local import OSS_CONFIG, MP4_OSS_CONFIG

def upload_to_oss(path):
    # Create OSS client with v4 authentication and region
    auth = oss2.AuthV4(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
    
    # Ensure endpoint has proper format
    endpoint = OSS_CONFIG['endpoint']
    if not endpoint.startswith('http'):
        endpoint = 'https://' + endpoint
    
    bucket = oss2.Bucket(auth, endpoint, OSS_CONFIG['bucket_name'], region=OSS_CONFIG['region'])
    
    # Upload file
    object_name = os.path.basename(path)
    bucket.put_object_from_file(object_name, path)
    
    # Generate signed URL (valid for 24 hours) with v4 signature
    url = bucket.sign_url('GET', object_name, 24 * 60 * 60, slash_safe=True)
    
    # Clean up temporary file
    os.remove(path)
    
    return url

def upload_mp4_to_oss(path):
    """Special method for uploading MP4 files, using custom domain and v4 signature"""
    # Directly use credentials from the configuration file
    auth = oss2.AuthV4(MP4_OSS_CONFIG['access_key_id'], MP4_OSS_CONFIG['access_key_secret'])
    
    # Create bucket instance with region
    bucket = oss2.Bucket(auth, MP4_OSS_CONFIG['endpoint'], MP4_OSS_CONFIG['bucket_name'], region=MP4_OSS_CONFIG['region'])
    
    # Upload file
    object_name = os.path.basename(path)
    bucket.put_object_from_file(object_name, path)
    
    # Generate custom domain URL
    custom_domain = MP4_OSS_CONFIG['endpoint']
    url = f"{custom_domain}/{object_name}"
    
    return url