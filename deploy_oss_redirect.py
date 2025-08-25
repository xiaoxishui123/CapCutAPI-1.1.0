import oss2
from settings.local import OSS_CONFIG


def get_bucket():
    auth = oss2.AuthV4(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
    endpoint = OSS_CONFIG['endpoint']
    if not endpoint.startswith('http'):
        endpoint = 'https://' + endpoint
    return oss2.Bucket(auth, endpoint, OSS_CONFIG['bucket_name'], region=OSS_CONFIG['region'])

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>CapCut 草稿下载</title>
<meta name="referrer" content="no-referrer" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body{font-family:system-ui,Segoe UI,Roboto,Arial;margin:0;padding:24px;background:#f8fafc;color:#0f172a}
  .card{max-width:720px;margin:0 auto;background:#fff;padding:24px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.06)}
  h1{margin:0 0 12px}
  .id{font-family:ui-monospace,Menlo,monospace;color:#4f46e5}
  .btn{background:#4f46e5;color:#fff;border:none;padding:12px 18px;border-radius:10px;cursor:pointer}
  .btn:hover{background:#4338ca}
  .tip{color:#475569;margin-top:10px}
  .link{color:#2563eb;text-decoration:none}
</style>
<script>
(function(){
  function getId(){
    var q = window.location.search || "";
    var p = new URLSearchParams(q);
    var id = p.get('draft_id');
    if(!id){
      var s = q.replace(/^\?/,'');
      if(s.startsWith('=')) id = decodeURIComponent(s.slice(1));
    }
    return id ? id.trim() : '';
  }
  window.addEventListener('DOMContentLoaded', function(){
    var id = getId();
    var idEl = document.getElementById('draftId');
    var btn = document.getElementById('openBtn');
    if(idEl) idEl.textContent = id || '(未提供)';
    btn.addEventListener('click', function(){
      if(!id){ alert('缺少 draft_id'); return; }
      var target = 'http://8.148.70.18:9000/draft/downloader?draft_id=' + encodeURIComponent(id);
      window.location.href = target;
    });
    var a = document.getElementById('openLink');
    if(a){ a.href = 'http://8.148.70.18:9000/draft/downloader?draft_id=' + encodeURIComponent(id); }
  });
})();
</script>
</head>
<body>
  <div class="card">
    <h1>草稿下载入口</h1>
    <p>草稿 ID：<span class="id" id="draftId"></span></p>
    <p class="tip">这是一个兼容旧链接的提示页。点击下面按钮将打开下载页面，系统会在需要时自动保存并上传草稿，然后跳转到 OSS 签名下载链接。</p>
    <p><button id="openBtn" class="btn">打开下载页面（推荐）</button></p>
    <p class="tip">如果按钮无法点击，可复制此链接在新标签页打开：<br/>
      <a id="openLink" class="link" href="#">打开下载页面</a></p>
  </div>
</body>
</html>
"""

if __name__ == '__main__':
    bucket = get_bucket()
    key = 'draft/downloader'
    # 上传并设置为内联展示、禁止强制下载，避免浏览器直接下载HTML
    bucket.put_object(key, HTML.encode('utf-8'), headers={
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-cache',
        'x-oss-force-download': 'false',
        'Content-Disposition': 'inline'
    })
    # 再通过复制明确替换所有元数据
    headers = {
        'x-oss-metadata-directive': 'REPLACE',
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-cache',
        'x-oss-force-download': 'false',
        'Content-Disposition': 'inline'
    }
    bucket.copy_object(bucket.bucket_name, key, key, headers=headers)
    print('Deployed friendly page with inline rendering at oss key:', key)
