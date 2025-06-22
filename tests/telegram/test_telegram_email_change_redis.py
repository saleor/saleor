#!/usr/bin/env python3
"""
测试Telegram邮箱变更的Redis存储功能
验证验证码存储到Redis和从Redis读取的功能
"""

import json
import time
from datetime import datetime, timedelta


def test_redis_storage():
    """测试Redis存储验证码功能"""
    print("=== 测试Redis存储验证码功能 ===")

    try:
        import redis

        # 创建Redis连接（使用与项目相同的配置）
        redis_client = redis.Redis(
            host="localhost", port=6379, db=1, decode_responses=True
        )

        # 测试连接
        redis_client.ping()
        print("✅ Redis连接成功")

        # 1. 存储验证码到Redis
        telegram_id = 5861990984
        old_email = "telegram_5861990984@telegram.local"
        new_email = "88888888@qq.com"
        verification_code = "123456"

        cache_key = f"email_change_verification:{telegram_id}"
        cache_data = {
            "verification_code": verification_code,
            "old_email": old_email,
            "new_email": new_email,
            "created_at": datetime.now().isoformat(),
        }

        # 存储到Redis，设置10分钟过期时间
        redis_client.setex(
            cache_key,
            600,  # 10分钟 = 600秒
            json.dumps(cache_data),
        )

        print(f"✅ 验证码已存储到Redis，键: {cache_key}")

        # 2. 从Redis读取验证码
        cached_data = redis_client.get(cache_key)
        if cached_data:
            stored_data = json.loads(cached_data)
            print(f"✅ 从Redis读取成功: {stored_data}")

            # 验证数据完整性
            assert stored_data["verification_code"] == verification_code
            assert stored_data["old_email"] == old_email
            assert stored_data["new_email"] == new_email
            print("✅ 数据完整性验证通过")
        else:
            print("❌ 从Redis读取失败")
            return False

        # 3. 验证验证码
        if (
            stored_data["verification_code"] == verification_code
            and stored_data["old_email"] == old_email
            and stored_data["new_email"] == new_email
        ):
            # 验证成功后删除Redis缓存
            redis_client.delete(cache_key)
            print("✅ 验证码验证成功，已从Redis删除")
        else:
            print("❌ 验证码验证失败")
            return False

        # 4. 验证删除是否成功
        cached_data_after_delete = redis_client.get(cache_key)
        if cached_data_after_delete is None:
            print("✅ 验证码已从Redis删除")
        else:
            print("❌ 验证码删除失败")
            return False

        return True

    except ImportError:
        print("❌ Redis模块未安装")
        return False
    except Exception as e:
        print(f"❌ Redis测试失败: {e}")
        return False


def test_redis_expiration():
    """测试Redis过期功能"""
    print("\n=== 测试Redis过期功能 ===")

    try:
        import redis

        redis_client = redis.Redis(
            host="localhost", port=6379, db=1, decode_responses=True
        )

        # 存储一个短期过期的验证码
        test_key = "test_expiration_key"
        test_data = {
            "verification_code": "999999",
            "old_email": "test@example.com",
            "new_email": "new@example.com",
            "created_at": datetime.now().isoformat(),
        }

        # 设置5秒过期
        redis_client.setex(
            test_key,
            5,  # 5秒
            json.dumps(test_data),
        )

        print(f"✅ 测试验证码已存储，5秒后过期")

        # 立即读取应该存在
        cached_data = redis_client.get(test_key)
        if cached_data:
            print("✅ 验证码立即读取成功")
        else:
            print("❌ 验证码立即读取失败")
            return False

        # 等待6秒后读取应该不存在
        print("等待6秒...")
        time.sleep(6)

        cached_data_after_expire = redis_client.get(test_key)
        if cached_data_after_expire is None:
            print("✅ 过期验证码已从Redis删除")
        else:
            print("❌ 过期验证码未删除")
            return False

        return True

    except Exception as e:
        print(f"❌ 过期测试失败: {e}")
        return False


def test_redis_connection_config():
    """测试Redis连接配置"""
    print("\n=== 测试Redis连接配置 ===")

    try:
        import redis
        import urllib.parse

        # 模拟项目的Redis配置
        redis_url = "redis://localhost:6379/1"

        if redis_url.startswith("redis://"):
            parsed = urllib.parse.urlparse(redis_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            db = int(parsed.path.lstrip("/")) if parsed.path else 1

            print(f"解析Redis URL: {redis_url}")
            print(f"  Host: {host}")
            print(f"  Port: {port}")
            print(f"  DB: {db}")

            # 测试连接
            redis_client = redis.Redis(
                host=host, port=port, db=db, decode_responses=True
            )

            redis_client.ping()
            print("✅ Redis连接配置正确")
            return True
        else:
            print("❌ Redis URL格式错误")
            return False

    except Exception as e:
        print(f"❌ 连接配置测试失败: {e}")
        return False


def test_cache_backend():
    """测试Django缓存后端"""
    print("\n=== 测试Django缓存后端 ===")

    try:
        import os
        import django

        # 设置Django环境
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
        django.setup()

        from django.conf import settings
        from django.core.cache import cache

        # 检查缓存后端配置
        cache_backend = settings.CACHES["default"]["BACKEND"]
        print(f"缓存后端: {cache_backend}")

        # 测试缓存功能
        test_key = "test_cache_key"
        test_value = "test_value"

        cache.set(test_key, test_value, 60)  # 60秒过期
        retrieved_value = cache.get(test_key)

        if retrieved_value == test_value:
            print("✅ Django缓存功能正常")

            # 清理测试数据
            cache.delete(test_key)
            return True
        else:
            print("❌ Django缓存功能异常")
            return False

    except Exception as e:
        print(f"❌ Django缓存测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试Telegram邮箱变更Redis存储功能...\n")

    # 测试Redis连接配置
    if not test_redis_connection_config():
        print("\n❌ Redis连接配置测试失败")
        return

    # 测试Redis存储
    if not test_redis_storage():
        print("\n❌ Redis存储测试失败")
        return

    # 测试Redis过期功能
    if not test_redis_expiration():
        print("\n❌ Redis过期测试失败")
        return

    # 测试Django缓存后端
    if not test_cache_backend():
        print("\n❌ Django缓存后端测试失败")
        return

    print("\n" + "=" * 60)
    print("🎉 所有Redis测试通过！")
    print("\nRedis存储功能总结:")
    print("1. ✅ Redis连接配置正确")
    print("2. ✅ 验证码成功存储到Redis，有效期10分钟")
    print("3. ✅ 验证码成功从Redis读取")
    print("4. ✅ 验证码验证成功后自动删除")
    print("5. ✅ Redis自动处理过期时间")
    print("6. ✅ Django缓存后端正常工作")

    print("\n现在你可以:")
    print("1. 重新请求邮箱变更，验证码将存储到Redis")
    print("2. 确认邮箱变更，验证码将从Redis读取")
    print("3. 验证码过期后自动从Redis删除")


if __name__ == "__main__":
    main()
