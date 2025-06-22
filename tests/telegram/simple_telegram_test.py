#!/usr/bin/env python3
"""
Simple Telegram validation test, no Django environment dependency
Test HMAC-SHA256 signature verification for Telegram WebApp initDataRaw
"""

import json
import hmac
import hashlib
from urllib.parse import parse_qs, unquote


def validate_telegram_data(init_data_raw, bot_token):
    """Simple Telegram data validation function"""
    try:
        # Parse init_data_raw
        parsed_data = parse_qs(init_data_raw)

        # Extract hash
        data_hash = parsed_data.get("hash", [None])[0]
        if not data_hash:
            print("❌ Missing hash in Telegram init data")
            return False

        # Extract user data
        user_data = parsed_data.get("user", [None])[0]
        if not user_data:
            print("❌ Missing user data in Telegram init data")
            return False

        print(f"📋 Parsed data keys: {list(parsed_data.keys())}")
        print(f"🔑 Data hash: {data_hash}")
        print(f"👤 User data: {user_data[:100]}...")

        # Verify HMAC signature
        # Remove hash parameter, reconstruct data string
        data_check_string_parts = []
        for key, values in parsed_data.items():
            if key != "hash":
                for value in values:
                    data_check_string_parts.append(f"{key}={value}")

        # Sort alphabetically
        data_check_string_parts.sort()
        data_check_string = "\n".join(data_check_string_parts)

        print(f"📝 Data check string: {data_check_string}")

        # Use HMAC-SHA256 to verify signature
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        print(f"🔐 Calculated hash: {calculated_hash}")
        print(f"📊 Hash match: {calculated_hash == data_hash}")

        # Verify hash match
        if calculated_hash != data_hash:
            print("❌ Invalid Telegram data signature")
            return False

        print("✅ Telegram data validation successful!")
        return True

    except Exception as e:
        print(f"❌ Telegram validation failed: {str(e)}")
        return False


def test_real_data():
    """Test with real Telegram data"""
    print("🧪 Testing with real Telegram data...")
    print("=" * 60)

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

    print(f"🤖 Bot Token: {bot_token[:20]}...")
    print(f"📦 Init Data Raw: {real_init_data_raw[:100]}...")
    print()

    # Validate data
    result = validate_telegram_data(real_init_data_raw, bot_token)

    if result:
        # Parse user data
        parsed_data = parse_qs(real_init_data_raw)
        user_data = parsed_data.get("user", [None])[0]
        if user_data:
            user_info = json.loads(user_data)
            print(f"✅ User Info:")
            print(f"   ID: {user_info.get('id')}")
            print(
                f"   Name: {user_info.get('first_name')} {user_info.get('last_name')}"
            )
            print(f"   Username: {user_info.get('username')}")
            print(f"   Language: {user_info.get('language_code')}")

    return result


def test_wrong_bot_token():
    """Test with wrong bot token"""
    print("\n🧪 Testing with wrong bot token...")
    print("=" * 60)

    # Wrong bot token
    wrong_bot_token = "wrong_bot_token"

    # Real initDataRaw data
    real_init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    result = validate_telegram_data(real_init_data_raw, wrong_bot_token)
    print(f"Expected to fail with wrong bot token: {not result}")
    return not result


if __name__ == "__main__":
    print("🚀 Telegram Data Validation Test")
    print("=" * 60)

    # Test real data
    test1_result = test_real_data()

    # Test wrong bot token
    test2_result = test_wrong_bot_token()

    print("\n📊 Test Results:")
    print(f"✅ Real data validation: {'PASS' if test1_result else 'FAIL'}")
    print(f"✅ Wrong token rejection: {'PASS' if test2_result else 'FAIL'}")

    if test1_result and test2_result:
        print("\n🎉 All tests passed! Telegram validation is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
