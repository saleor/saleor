#!/usr/bin/env python3
"""
集成测试：测试使用python-telegram-bot的GraphQL mutation接口
"""

import os
import sys
import django
import asyncio
import json
from urllib.parse import parse_qs

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from django.test import TestCase
from django.test.utils import override_settings
from saleor.graphql.account.mutations.authentication.telegram_token_create import (
    TelegramTokenCreate,
    validate_telegram_data,
    validate_telegram_data_async,
)
from saleor.account.models import User


class TelegramMutationIntegrationTest(TestCase):
    """Telegram GraphQL mutation集成测试"""

    def setUp(self):
        """测试设置"""
        self.bot_token = "8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"
        self.init_data_raw = (
            "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
            "&chat_instance=6755980278051609308"
            "&chat_type=sender"
            "&auth_date=1738051266"
            "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
            "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
        )

    @override_settings(
        TELEGRAM_BOT_TOKEN="8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"
    )
    def test_validate_telegram_data_async(self):
        """测试异步验证函数"""
        print("🧪 Testing async validation function...")

        try:
            # 运行异步验证
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                validate_telegram_data_async(self.init_data_raw, self.bot_token)
            )
            loop.close()

            # 验证结果
            self.assertIsNotNone(result)
            self.assertIn("user", result)
            self.assertIn("bot_info", result)

            user_info = result["user"]
            self.assertEqual(user_info["id"], 7498813057)
            self.assertEqual(user_info["first_name"], "Justin")
            self.assertEqual(user_info["last_name"], "Lung")
            self.assertEqual(user_info["username"], "justin_lung")

            bot_info = result["bot_info"]
            self.assertIn("id", bot_info)
            self.assertIn("first_name", bot_info)
            self.assertIn("username", bot_info)

            print("✅ Async validation passed!")
            return True

        except Exception as e:
            print(f"❌ Async validation failed: {e}")
            return False

    @override_settings(
        TELEGRAM_BOT_TOKEN="8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"
    )
    def test_validate_telegram_data_sync(self):
        """测试同步验证函数"""
        print("🧪 Testing sync validation function...")

        try:
            result = validate_telegram_data(self.init_data_raw)

            # 验证结果
            self.assertIsNotNone(result)
            self.assertIn("user", result)
            self.assertIn("bot_info", result)

            user_info = result["user"]
            self.assertEqual(user_info["id"], 7498813057)
            self.assertEqual(user_info["first_name"], "Justin")
            self.assertEqual(user_info["last_name"], "Lung")

            print("✅ Sync validation passed!")
            return True

        except Exception as e:
            print(f"❌ Sync validation failed: {e}")
            return False

    @override_settings(
        TELEGRAM_BOT_TOKEN="8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"
    )
    def test_get_or_create_user(self):
        """测试用户创建/获取功能"""
        print("🧪 Testing user creation/retrieval...")

        try:
            # 先验证数据
            telegram_data = validate_telegram_data(self.init_data_raw)

            # 获取或创建用户
            user = TelegramTokenCreate.get_or_create_user(telegram_data)

            # 验证用户信息
            self.assertIsNotNone(user)
            self.assertEqual(user.email, "telegram_7498813057@telegram.local")
            self.assertEqual(user.first_name, "Justin")
            self.assertEqual(user.last_name, "Lung")
            self.assertTrue(user.is_active)
            self.assertTrue(user.is_confirmed)

            # 验证元数据
            metadata = user.private_metadata
            self.assertEqual(metadata.get("telegram_id"), 7498813057)
            self.assertEqual(metadata.get("telegram_username"), "justin_lung")
            self.assertEqual(metadata.get("telegram_language_code"), "zh-hans")
            self.assertIn("bot_info", metadata)

            print("✅ User creation/retrieval passed!")
            return True

        except Exception as e:
            print(f"❌ User creation/retrieval failed: {e}")
            return False

    @override_settings(
        TELEGRAM_BOT_TOKEN="8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"
    )
    def test_telegram_mutation_integration(self):
        """测试完整的GraphQL mutation"""
        print("🧪 Testing complete GraphQL mutation...")

        try:
            # 模拟GraphQL请求
            from django.test import RequestFactory
            from django.contrib.auth.models import AnonymousUser

            factory = RequestFactory()
            request = factory.post("/graphql/")
            request.user = AnonymousUser()

            # 执行mutation
            result = TelegramTokenCreate.perform_mutation(
                root=None,
                info=type("ResolveInfo", (), {"context": request})(),
                init_data_raw=self.init_data_raw,
            )

            # 验证结果
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.token)
            self.assertIsNotNone(result.refresh_token)
            self.assertIsNotNone(result.csrf_token)
            self.assertIsNotNone(result.user)
            self.assertEqual(len(result.errors), 0)

            # 验证用户信息
            user = result.user
            self.assertEqual(user.email, "telegram_7498813057@telegram.local")
            self.assertEqual(user.first_name, "Justin")
            self.assertEqual(user.last_name, "Lung")

            print("✅ Complete GraphQL mutation passed!")
            print(f"   Token: {result.token[:20]}...")
            print(f"   User: {user.email}")
            return True

        except Exception as e:
            print(f"❌ Complete GraphQL mutation failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    def test_wrong_bot_token(self):
        """测试错误的bot token"""
        print("🧪 Testing wrong bot token...")

        try:
            with self.assertRaises(Exception):
                validate_telegram_data_async(self.init_data_raw, "wrong_token")
            print("✅ Wrong bot token correctly rejected!")
            return True
        except Exception as e:
            print(f"❌ Wrong bot token test failed: {e}")
            return False

    def test_missing_init_data(self):
        """测试缺少init_data的情况"""
        print("🧪 Testing missing init_data...")

        try:
            with self.assertRaises(Exception):
                TelegramTokenCreate.perform_mutation(
                    root=None,
                    info=type("ResolveInfo", (), {"context": None})(),
                    init_data_raw="",
                )
            print("✅ Missing init_data correctly rejected!")
            return True
        except Exception as e:
            print(f"❌ Missing init_data test failed: {e}")
            return False


def run_integration_tests():
    """运行集成测试"""
    print("🚀 Telegram GraphQL Mutation Integration Tests")
    print("=" * 70)

    # 创建测试实例
    test_instance = TelegramMutationIntegrationTest()
    test_instance.setUp()

    # 运行所有测试
    tests = [
        ("Async Validation", test_instance.test_validate_telegram_data_async),
        ("Sync Validation", test_instance.test_validate_telegram_data_sync),
        ("User Creation", test_instance.test_get_or_create_user),
        ("Complete Mutation", test_instance.test_telegram_mutation_integration),
        ("Wrong Bot Token", test_instance.test_wrong_bot_token),
        ("Missing Init Data", test_instance.test_missing_init_data),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))

    # 输出结果
    print("\n📊 Integration Test Results:")
    print("=" * 70)
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print(
            "🎉 All integration tests passed! Telegram mutation is ready for production."
        )
    else:
        print("❌ Some integration tests failed. Please check the implementation.")

    return all_passed


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
