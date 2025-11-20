# OSS 配置诊断报告

生成时间：2025-11-13
项目：CapCutAPI-1.1.0

---

## 📊 诊断总结

| 检查项 | 状态 | 说明 |
|--------|------|------|
| ✅ .env 文件存在 | 正常 | 环境变量文件已找到 |
| ✅ config.json 配置 | 正常 | 配置文件加载成功 |
| ⚠️ OSS 环境变量 | **需要修复** | endpoint 和 region 使用占位符 |
| ⚠️ MP4 OSS 配置 | 未配置 | 使用默认值，未实际配置 |
| ❌ OSS 连接测试 | **失败** | 无法解析 OSS 域名 |

**结论**：OSS 配置存在问题，需要修复后才能正常使用。

---

## 🔍 问题详情

### 1. OSS 主要问题：Region 配置错误

**当前配置**（.env 文件）：
```bash
OSS_ENDPOINT=oss-cn-region.aliyuncs.com
OSS_REGION=cn-region
```

**问题分析**：
- `oss-cn-region.aliyuncs.com` 是占位符，不是真实的阿里云 OSS 地域
- `cn-region` 也是占位符，需要替换为实际的区域代码
- 导致无法解析域名，连接失败

**错误信息**：
```
Failed to resolve 'zdaigfpt.oss-cn-region.aliyuncs.com'
[Errno -2] Name or service not known
```

### 2. MP4 OSS 配置：完全未配置

**当前配置**（.env 文件）：
```bash
MP4_OSS_BUCKET_NAME=your-bucket-name
MP4_OSS_ACCESS_KEY_ID=your-access-key-id
MP4_OSS_ACCESS_KEY_SECRET=your-access-key-secret
MP4_OSS_ENDPOINT=https://your-bucket-name.oss-cn-region.aliyuncs.com
MP4_OSS_REGION=cn-region
```

**问题分析**：
- 所有配置项都是默认值/占位符
- 如果不使用 MP4 视频直链功能，可以忽略
- 如果需要使用，需要配置实际的 OSS 信息

### 3. 当前 OSS 功能状态

**config.json 配置**：
```json
{
  "is_upload_draft": true
}
```

**说明**：
- OSS 上传功能已启用（`is_upload_draft: true`）
- 但由于配置错误，无法正常工作
- 启动时可能会因为配置验证失败而报错

---

## 🛠️ 修复方案

### 方案 1：查找实际的 OSS Region（推荐）

#### 步骤 1：登录阿里云控制台

1. 访问 https://oss.console.aliyun.com
2. 登录你的阿里云账号
3. 找到 Bucket 列表

#### 步骤 2：查看 Bucket 信息

1. 找到名为 `zdaigfpt` 的 Bucket
2. 点击 Bucket 名称进入详情页
3. 在「概览」页面查看「Endpoint（地域节点）」信息

示例信息：
```
外网访问 Endpoint: zdaigfpt.oss-cn-hangzhou.aliyuncs.com
地域节点: 华东1（杭州）
Region ID: cn-hangzhou
```

#### 步骤 3：修改 .env 文件

根据实际信息修改：

```bash
# 假设你的 Bucket 在杭州区域
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_REGION=cn-hangzhou
```

或者其他区域（根据实际情况）：

```bash
# 上海区域
OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
OSS_REGION=cn-shanghai

# 北京区域
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_REGION=cn-beijing

# 深圳区域
OSS_ENDPOINT=oss-cn-shenzhen.aliyuncs.com
OSS_REGION=cn-shenzhen
```

### 方案 2：使用 OSS CLI 工具查询

如果已安装阿里云 CLI：

```bash
# 列出所有 Bucket
aliyun oss ls

# 查看特定 Bucket 信息
aliyun oss bucket-info oss://zdaigfpt
```

### 方案 3：尝试常见区域（不推荐）

如果无法查看控制台，可以尝试常见区域：

```bash
# 1. 尝试杭州（最常用）
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_REGION=cn-hangzhou

# 2. 尝试上海
OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
OSS_REGION=cn-shanghai

# 3. 尝试北京
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_REGION=cn-beijing
```

**验证方法**：
修改后运行测试：
```bash
python test_oss_config.py
```

如果看到「✅ OSS 连接测试成功」说明配置正确。

---

## 📝 完整的 .env 配置示例

### 示例 1：OSS 在杭州区域

```bash
# CapCutAPI 环境变量配置
# 警告：此文件包含敏感信息，不要提交到Git！

# ===== OSS配置（草稿上传） =====
OSS_BUCKET_NAME=your-bucket-name
OSS_ACCESS_KEY_ID=your-access-key-id
OSS_ACCESS_KEY_SECRET=your-access-key-secret
OSS_ENDPOINT=oss-cn-wuhan-lr.aliyuncs.com
OSS_REGION=cn-wuhan-lr

# ===== MP4 OSS配置（视频直链域名） =====
# 如果不使用视频直链功能，可以保持默认值或删除这些配置
# 如果使用，请填入实际的 OSS 信息
MP4_OSS_BUCKET_NAME=your-bucket-name
MP4_OSS_ACCESS_KEY_ID=your-access-key-id
MP4_OSS_ACCESS_KEY_SECRET=your-access-key-secret
MP4_OSS_ENDPOINT=https://your-bucket-name.oss-cn-hangzhou.aliyuncs.com
MP4_OSS_REGION=cn-hangzhou
```

### 示例 2：OSS 和 MP4 使用相同配置

如果草稿和视频使用同一个 OSS Bucket：

```bash
# ===== OSS配置（草稿上传） =====
OSS_BUCKET_NAME=your-bucket-name
OSS_ACCESS_KEY_ID=your-access-key-id
OSS_ACCESS_KEY_SECRET=your-access-key-secret
OSS_ENDPOINT=oss-cn-wuhan-lr.aliyuncs.com
OSS_REGION=cn-wuhan-lr

# ===== MP4 OSS配置（使用与草稿相同的配置） =====
MP4_OSS_BUCKET_NAME=your-bucket-name
MP4_OSS_ACCESS_KEY_ID=your-access-key-id
MP4_OSS_ACCESS_KEY_SECRET=your-access-key-secret
MP4_OSS_ENDPOINT=https://your-bucket-name.oss-cn-wuhan-lr.aliyuncs.com
MP4_OSS_REGION=cn-wuhan-lr
```

---

## 🧪 验证步骤

### 1. 修改配置后，运行测试脚本

```bash
python test_oss_config.py
```

### 2. 预期成功输出

```
============================================================
  3. 测试 OSS 连接
============================================================

🔗 正在连接 OSS...
  - Endpoint: https://oss-cn-hangzhou.aliyuncs.com
  - Bucket: zdaigfpt
  - Region: cn-hangzhou

📊 测试：获取 Bucket 信息...
  ✅ Bucket 名称: zdaigfpt
  ✅ 存储类型: Standard
  ✅ 创建时间: 2024-xx-xx
  ✅ 访问权限: public-read

📊 测试：列出 Bucket 中的对象（最多10个）...
  ℹ️  Bucket 为空

✅ OSS 连接测试成功！

============================================================
  4. 测试 OSS 上传功能
============================================================

📝 创建测试文件...
  ✅ 测试文件创建成功

📤 上传文件到 OSS: capcut_api_test_file.txt
  ✅ 上传成功
  - ETag: "xxxxx"

🔗 文件访问地址:
  https://zdaigfpt.oss-cn-hangzhou.aliyuncs.com/capcut_api_test_file.txt

✅ OSS 上传功能测试成功！
```

### 3. 检查主服务启动

配置修复后，尝试启动主服务：

```bash
# 方式 1：使用管理脚本
./service_manager.sh restart

# 方式 2：直接运行
python capcut_server.py
```

应该能看到服务正常启动，不再报 OSS 配置错误。

---

## 📚 阿里云 OSS 区域列表

| 区域名称 | Region ID | Endpoint |
|---------|-----------|----------|
| 华东1（杭州） | cn-hangzhou | oss-cn-hangzhou.aliyuncs.com |
| 华东2（上海） | cn-shanghai | oss-cn-shanghai.aliyuncs.com |
| 华北1（青岛） | cn-qingdao | oss-cn-qingdao.aliyuncs.com |
| 华北2（北京） | cn-beijing | oss-cn-beijing.aliyuncs.com |
| 华北3（张家口） | cn-zhangjiakou | oss-cn-zhangjiakou.aliyuncs.com |
| 华北5（呼和浩特） | cn-huhehaote | oss-cn-huhehaote.aliyuncs.com |
| 华北6（乌兰察布） | cn-wulanchabu | oss-cn-wulanchabu.aliyuncs.com |
| 华南1（深圳） | cn-shenzhen | oss-cn-shenzhen.aliyuncs.com |
| 华南2（河源） | cn-heyuan | oss-cn-heyuan.aliyuncs.com |
| 华南3（广州） | cn-guangzhou | oss-cn-guangzhou.aliyuncs.com |
| 西南1（成都） | cn-chengdu | oss-cn-chengdu.aliyuncs.com |
| 中国香港 | cn-hongkong | oss-cn-hongkong.aliyuncs.com |

完整列表：https://help.aliyun.com/document_detail/31837.html

---

## 🔒 安全建议

1. **不要提交 .env 到 Git**
   ```bash
   # 确保 .gitignore 包含
   echo ".env" >> .gitignore
   ```

2. **定期轮换 Access Key**
   - 建议每 90 天更换一次
   - 在阿里云控制台 RAM 访问控制中管理

3. **使用最小权限原则**
   - 仅授予必需的 OSS 权限
   - 不要使用主账号的 Access Key

4. **监控 OSS 使用量**
   - 定期检查存储用量和流量
   - 设置费用告警

---

## ❓ 常见问题

### Q1: 修改配置后还是连接失败？

**可能原因**：
1. Region 还是不对，尝试其他常见区域
2. Access Key 过期或被禁用
3. Bucket 不存在或已删除
4. 网络问题（防火墙、代理）

**调试方法**：
```bash
# 使用 curl 测试 OSS endpoint
curl -I https://zdaigfpt.oss-cn-hangzhou.aliyuncs.com
```

### Q2: 是否需要配置 MP4_OSS？

**回答**：取决于使用场景
- **需要配置**：如果使用独立的 OSS Bucket 存储视频素材，并需要自定义域名访问
- **不需要配置**：如果只使用草稿上传功能，或视频和草稿使用同一个 Bucket

### Q3: OSS 配置错误会影响哪些功能？

**影响范围**：
- ❌ 草稿保存到云端（`/save_draft` API）
- ❌ 草稿下载和预览
- ❌ 视频素材上传（如果使用 OSS 存储）
- ✅ 本地草稿创建（不受影响）
- ✅ API 其他功能（不受影响）

### Q4: 可以禁用 OSS 上传吗？

**可以**，修改 `config.json`：
```json
{
  "is_upload_draft": false
}
```

这样草稿将保存到本地，不使用 OSS。

---

## 📞 技术支持

- **项目文档**：`/home/CapCutAPI-1.1.0/CLAUDE.md`
- **API 文档**：`/home/CapCutAPI-1.1.0/docs/API_USAGE_EXAMPLES.md`
- **故障排除**：`/home/CapCutAPI-1.1.0/docs/TROUBLESHOOTING.md`

---

**生成工具**：`test_oss_config.py`
**下次检查**：修改配置后重新运行 `python test_oss_config.py`
