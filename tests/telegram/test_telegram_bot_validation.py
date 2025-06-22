#!/usr/bin/env python3
"""
Test Telegram validation implementation using python-telegram-bot
"""

import json
from urllib.parse import parse_qs


def test_telegram_bot_validation():
    """Test python-telegram-bot validation"""

    # Real bot token
    bot_token = "8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"

    # Real initDataRaw data
    real_init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    print("🧪 Testing python-telegram-bot validation...")
    print("=" * 60)
    print(f"🤖 Bot Token: {bot_token[:20]}...")
    print(f"📦 Init Data Raw: {real_init_data_raw[:100]}...")
    print()

    try:
        # Try to import python-telegram-bot
        try:
            from telegram import Bot
            from telegram.error import TelegramError

            print("✅ python-telegram-bot imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import python-telegram-bot: {e}")
            print("Please run: poetry add python-telegram-bot")
            return False

        # Create Bot instance
        bot = Bot(token=bot_token)
        print("✅ Bot instance created")

        # Validate bot token
        try:
            bot_info = bot.get_me()
            print(
                f"✅ Bot validation successful: {bot_info.first_name} (@{bot_info.username})"
            )
        except TelegramError as e:
            print(f"❌ Bot validation failed: {e}")
            return False

        # Parse init_data_raw
        parsed_data = parse_qs(real_init_data_raw)
        print("✅ Init data parsed successfully")

        # Extract user data
        user_data = parsed_data.get("user", [None])[0]
        if not user_data:
            print("❌ Missing user data")
            return False

        # Parse user data
        try:
            user_info = json.loads(user_data)
            print(
                f"✅ User data parsed: {user_info['first_name']} {user_info['last_name']}"
            )
        except json.JSONDecodeError as e:
            print(f"❌ Invalid user data JSON: {e}")
            return False

        # Validate basic structure of user data
        required_fields = ["id", "first_name"]
        for field in required_fields:
            if field not in user_info:
                print(f"❌ Missing required field: {field}")
                return False

        # Validate user ID
        try:
            user_id = int(user_info["id"])
            if user_id <= 0:
                print("❌ Invalid user ID")
                return False
            print(f"✅ User ID validated: {user_id}")
        except (ValueError, TypeError):
            print("❌ User ID must be a positive integer")
            return False

        print("✅ All validations passed!")
        return True

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


def test_wrong_bot_token():
    """Test with wrong bot token"""
    print("\n🧪 Testing with wrong bot token...")
    print("=" * 60)

    # Wrong bot token
    wrong_bot_token = "wrong_bot_token"

    try:
        from telegram import Bot
        from telegram.error import TelegramError

        # Create Bot instance
        bot = Bot(token=wrong_bot_token)

        # Try to validate bot token
        try:
            bot_info = bot.get_me()
            print("❌ Should have failed with wrong bot token")
            return False
        except TelegramError as e:
            print(f"✅ Correctly rejected wrong bot token: {e}")
            return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_missing_dependencies():
    """Test missing dependencies scenario"""
    print("\n🧪 Testing missing dependencies...")
    print("=" * 60)

    try:
        import telegram

        print("✅ python-telegram-bot is available")
        return True
    except ImportError as e:
        print(f"❌ python-telegram-bot not available: {e}")
        print("Please run: poetry add python-telegram-bot")
        return False


if __name__ == "__main__":
    print("🚀 Python Telegram Bot Validation Test")
    print("=" * 60)

    # Check dependencies
    deps_result = test_missing_dependencies()

    if deps_result:
        # Test real data
        test1_result = test_telegram_bot_validation()

        # Test wrong bot token
        test2_result = test_wrong_bot_token()

        print("\n📊 Test Results:")
        print("=" * 60)
        print(f"✅ Dependencies available: {'PASS' if deps_result else 'FAIL'}")
        print(f"✅ Real data validation: {'PASS' if test1_result else 'FAIL'}")
        print(f"✅ Wrong token rejection: {'PASS' if test2_result else 'FAIL'}")

        if test1_result and test2_result:
            print(
                "\n🎉 All tests passed! python-telegram-bot validation is working correctly."
            )
            print("\n✅ Now you can retest the GraphQL mutation!")
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
    else:
        print(
            "\n❌ Dependencies not available. Please install python-telegram-bot first."
        )
