#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OSS 配置和功能测试脚本
用于验证阿里云 OSS 配置是否有效
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

def print_section(title):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_env_variables():
    """测试环境变量是否加载"""
    print_section("1. 检查环境变量")

    oss_vars = {
        "OSS_BUCKET_NAME": os.getenv("OSS_BUCKET_NAME"),
        "OSS_ACCESS_KEY_ID": os.getenv("OSS_ACCESS_KEY_ID"),
        "OSS_ACCESS_KEY_SECRET": os.getenv("OSS_ACCESS_KEY_SECRET"),
        "OSS_ENDPOINT": os.getenv("OSS_ENDPOINT"),
        "OSS_REGION": os.getenv("OSS_REGION"),
    }

    mp4_oss_vars = {
        "MP4_OSS_BUCKET_NAME": os.getenv("MP4_OSS_BUCKET_NAME"),
        "MP4_OSS_ACCESS_KEY_ID": os.getenv("MP4_OSS_ACCESS_KEY_ID"),
        "MP4_OSS_ACCESS_KEY_SECRET": os.getenv("MP4_OSS_ACCESS_KEY_SECRET"),
        "MP4_OSS_ENDPOINT": os.getenv("MP4_OSS_ENDPOINT"),
        "MP4_OSS_REGION": os.getenv("MP4_OSS_REGION"),
    }

    print("\n📋 OSS 配置（草稿上传）:")
    all_oss_ok = True
    for key, value in oss_vars.items():
        if value:
            # 敏感信息脱敏显示
            if "SECRET" in key or "KEY_ID" in key:
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display_value = value

            # 检查是否为占位符
            if "region" in value.lower() and value == "oss-cn-region.aliyuncs.com":
                print(f"  ⚠️  {key}: {display_value} (占位符，需要修改为实际区域)")
                all_oss_ok = False
            elif "region" in value.lower() and value == "cn-region":
                print(f"  ⚠️  {key}: {display_value} (占位符，需要修改为实际区域)")
                all_oss_ok = False
            else:
                print(f"  ✅ {key}: {display_value}")
        else:
            print(f"  ❌ {key}: 未配置")
            all_oss_ok = False

    print("\n📋 MP4 OSS 配置（视频直链）:")
    all_mp4_ok = True
    for key, value in mp4_oss_vars.items():
        if value:
            # 检查是否为默认值
            if "your-" in value.lower():
                print(f"  ⚠️  {key}: {value} (默认值，未配置)")
                all_mp4_ok = False
            else:
                if "SECRET" in key or "KEY_ID" in key:
                    display_value = value[:8] + "..." if len(value) > 8 else "***"
                else:
                    display_value = value
                print(f"  ✅ {key}: {display_value}")
        else:
            print(f"  ⚠️  {key}: 未配置")
            all_mp4_ok = False

    return all_oss_ok, all_mp4_ok

def test_config_loading():
    """测试配置加载"""
    print_section("2. 检查配置模块加载")

    try:
        from settings.local import OSS_CONFIG, MP4_OSS_CONFIG, IS_UPLOAD_DRAFT

        print(f"\n📋 IS_UPLOAD_DRAFT: {IS_UPLOAD_DRAFT}")

        print("\n📋 OSS_CONFIG 加载结果:")
        if OSS_CONFIG:
            for key, value in OSS_CONFIG.items():
                if "secret" in key.lower() or "key_id" in key.lower():
                    display_value = value[:8] + "..." if len(value) > 8 else "***"
                else:
                    display_value = value
                print(f"  {key}: {display_value}")
        else:
            print("  ⚠️  配置为空")

        print("\n📋 MP4_OSS_CONFIG 加载结果:")
        if MP4_OSS_CONFIG:
            for key, value in MP4_OSS_CONFIG.items():
                if "secret" in key.lower() or "key_id" in key.lower():
                    display_value = value[:8] + "..." if len(value) > 8 else "***"
                else:
                    display_value = value
                print(f"  {key}: {display_value}")
        else:
            print("  ⚠️  配置为空")

        return True, OSS_CONFIG, MP4_OSS_CONFIG, IS_UPLOAD_DRAFT
    except Exception as e:
        print(f"\n❌ 配置加载失败: {str(e)}")
        return False, None, None, None

def test_oss_connection(oss_config):
    """测试 OSS 连接"""
    print_section("3. 测试 OSS 连接")

    if not oss_config:
        print("\n⚠️  跳过测试：OSS 配置为空")
        return False

    required_fields = ['bucket_name', 'access_key_id', 'access_key_secret', 'endpoint', 'region']
    missing = [f for f in required_fields if not oss_config.get(f)]

    if missing:
        print(f"\n❌ 配置不完整，缺少字段: {', '.join(missing)}")
        return False

    try:
        import oss2

        print("\n🔗 正在连接 OSS...")

        # 创建认证对象
        auth = oss2.AuthV4(
            oss_config['access_key_id'],
            oss_config['access_key_secret']
        )

        # 构造 endpoint
        endpoint = oss_config['endpoint']
        if not endpoint.startswith('http'):
            endpoint = 'https://' + endpoint

        print(f"  - Endpoint: {endpoint}")
        print(f"  - Bucket: {oss_config['bucket_name']}")
        print(f"  - Region: {oss_config['region']}")

        # 创建 Bucket 对象
        bucket = oss2.Bucket(
            auth,
            endpoint,
            oss_config['bucket_name'],
            region=oss_config['region']
        )

        # 测试：获取 Bucket 信息
        print("\n📊 测试：获取 Bucket 信息...")
        bucket_info = bucket.get_bucket_info()
        print(f"  ✅ Bucket 名称: {bucket_info.name}")
        print(f"  ✅ 存储类型: {bucket_info.storage_class}")
        print(f"  ✅ 创建时间: {bucket_info.creation_date}")
        print(f"  ✅ 访问权限: {bucket_info.acl.grant}")

        # 测试：列出对象
        print("\n📊 测试：列出 Bucket 中的对象（最多10个）...")
        count = 0
        for obj in oss2.ObjectIterator(bucket, max_keys=10):
            count += 1
            print(f"  {count}. {obj.key} ({obj.size} bytes, {obj.last_modified})")

        if count == 0:
            print("  ℹ️  Bucket 为空")
        else:
            print(f"\n  ✅ 共找到 {count} 个对象")

        print("\n✅ OSS 连接测试成功！")
        return True

    except ImportError:
        print("\n❌ 未安装 oss2 库，请运行: pip install oss2")
        return False
    except oss2.exceptions.NoSuchBucket:
        print(f"\n❌ Bucket 不存在: {oss_config['bucket_name']}")
        return False
    except oss2.exceptions.AccessDenied:
        print("\n❌ 访问被拒绝：请检查 Access Key ID 和 Secret 是否正确")
        return False
    except oss2.exceptions.RequestError as e:
        error_msg = str(e)
        if "Name or service not known" in error_msg or "Failed to resolve" in error_msg:
            print(f"\n❌ 无法解析 OSS 域名：{oss_config['endpoint']}")
            print("   这通常是因为 OSS_ENDPOINT 或 OSS_REGION 配置不正确")
            print("   请检查 .env 文件中的配置是否为实际的阿里云区域")
        else:
            print(f"\n❌ OSS 请求错误: {error_msg}")
        return False
    except Exception as e:
        print(f"\n❌ OSS 连接失败: {type(e).__name__}: {str(e)}")
        return False

def test_oss_upload(oss_config):
    """测试 OSS 上传功能"""
    print_section("4. 测试 OSS 上传功能")

    if not oss_config or not all(oss_config.get(k) for k in ['bucket_name', 'access_key_id', 'access_key_secret', 'endpoint', 'region']):
        print("\n⚠️  跳过测试：OSS 配置不完整")
        return False

    try:
        import oss2
        import tempfile

        # 创建测试文件
        print("\n📝 创建测试文件...")
        test_content = "CapCutAPI OSS 测试文件\n这是一个测试文件，用于验证 OSS 上传功能。"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            test_file_path = f.name

        print(f"  ✅ 测试文件创建成功: {test_file_path}")

        # 连接 OSS
        auth = oss2.AuthV4(oss_config['access_key_id'], oss_config['access_key_secret'])
        endpoint = oss_config['endpoint']
        if not endpoint.startswith('http'):
            endpoint = 'https://' + endpoint

        bucket = oss2.Bucket(auth, endpoint, oss_config['bucket_name'], region=oss_config['region'])

        # 上传测试文件
        test_object_name = 'capcut_api_test_file.txt'
        print(f"\n📤 上传文件到 OSS: {test_object_name}")

        result = bucket.put_object_from_file(test_object_name, test_file_path)
        print(f"  ✅ 上传成功")
        print(f"  - ETag: {result.etag}")
        print(f"  - Request ID: {result.request_id}")

        # 生成访问 URL
        url = f"https://{oss_config['bucket_name']}.{oss_config['endpoint']}/{test_object_name}"
        print(f"\n🔗 文件访问地址:")
        print(f"  {url}")

        # 验证文件是否存在
        print(f"\n🔍 验证文件是否存在...")
        exists = bucket.object_exists(test_object_name)
        if exists:
            print(f"  ✅ 文件存在于 OSS")
        else:
            print(f"  ❌ 文件不存在于 OSS")

        # 下载并验证内容
        print(f"\n📥 下载并验证文件内容...")
        downloaded_content = bucket.get_object(test_object_name).read().decode('utf-8')
        if downloaded_content == test_content:
            print(f"  ✅ 文件内容验证成功")
        else:
            print(f"  ❌ 文件内容不匹配")

        # 清理测试文件
        print(f"\n🧹 清理测试文件...")
        bucket.delete_object(test_object_name)
        os.unlink(test_file_path)
        print(f"  ✅ 测试文件已删除")

        print("\n✅ OSS 上传功能测试成功！")
        return True

    except Exception as e:
        print(f"\n❌ OSS 上传测试失败: {type(e).__name__}: {str(e)}")
        # 清理临时文件
        try:
            if 'test_file_path' in locals() and os.path.exists(test_file_path):
                os.unlink(test_file_path)
        except:
            pass
        return False

def main():
    """主函数"""
    print("\n🚀 CapCutAPI OSS 配置和功能测试")
    print("="*60)

    # 测试环境变量
    oss_env_ok, mp4_env_ok = test_env_variables()

    # 测试配置加载
    config_ok, oss_config, mp4_oss_config, is_upload_draft = test_config_loading()

    if not config_ok:
        print("\n❌ 配置加载失败，无法继续测试")
        sys.exit(1)

    # 测试 OSS 连接
    oss_conn_ok = False
    if is_upload_draft:
        oss_conn_ok = test_oss_connection(oss_config)

        # 测试 OSS 上传
        if oss_conn_ok:
            test_oss_upload(oss_config)
    else:
        print_section("3. OSS 功能未启用")
        print("\n⚠️  IS_UPLOAD_DRAFT = False，OSS 功能未启用")
        print("   如需测试 OSS 功能，请在 config.json 中设置 is_upload_draft = true")

    # 总结
    print_section("测试总结")

    print("\n📊 测试结果:")
    print(f"  {'✅' if oss_env_ok else '⚠️ '} OSS 环境变量配置")
    print(f"  {'✅' if mp4_env_ok else '⚠️ '} MP4 OSS 环境变量配置")
    print(f"  {'✅' if config_ok else '❌'} 配置模块加载")
    if is_upload_draft:
        print(f"  {'✅' if oss_conn_ok else '❌'} OSS 连接测试")
    else:
        print(f"  ⏭️  OSS 连接测试（功能未启用）")

    # 提供修复建议
    if not oss_env_ok:
        print("\n💡 修复建议 - OSS 配置:")
        print("  1. 编辑 .env 文件")
        print("  2. 将 OSS_ENDPOINT 和 OSS_REGION 修改为实际区域")
        print("     例如：OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com")
        print("           OSS_REGION=cn-hangzhou")
        print("  3. 可用区域列表：")
        print("     - 华东1（杭州）: cn-hangzhou")
        print("     - 华东2（上海）: cn-shanghai")
        print("     - 华北1（青岛）: cn-qingdao")
        print("     - 华北2（北京）: cn-beijing")
        print("     - 华北3（张家口）: cn-zhangjiakou")
        print("     - 华南1（深圳）: cn-shenzhen")

    if not mp4_env_ok:
        print("\n💡 修复建议 - MP4 OSS 配置:")
        print("  如需使用 MP4 视频直链功能，请在 .env 文件中配置 MP4_OSS_* 环境变量")

if __name__ == "__main__":
    main()
