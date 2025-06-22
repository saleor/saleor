#!/usr/bin/env python3
"""
Test the modified Python native Telegram validation implementation
"""

import os
import sys
import django
from django.conf import settings

# Set Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

# Import our validation function
from saleor.graphql.account.mutations.authentication.telegram_token_create import (
    validate_telegram_data,
)


def test_telegram_validation():
    """
    Test Telegram data validation
    """

    # Set bot token
    settings.TELEGRAM_BOT_TOKEN = "8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"

    # Real initDataRaw data
    real_init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    print("🧪 Testing Python native Telegram validation...")
    print("=" * 60)
    print(f"🤖 Bot Token: {settings.TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"📦 Init Data Raw: {real_init_data_raw[:100]}...")
    print()

    try:
        # Validate data
        result = validate_telegram_data(real_init_data_raw)
        print("✅ Validation successful!")
        print(f"📋 User ID: {result['user']['id']}")
        print(
            f"📋 User Name: {result['user']['first_name']} {result['user']['last_name']}"
        )
        print(f"📋 Username: {result['user']['username']}")
        return True
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


def test_wrong_bot_token():
    """
    Test with wrong bot token
    """
    print("\n🧪 Testing with wrong bot token...")
    print("=" * 60)

    # Set wrong bot token
    settings.TELEGRAM_BOT_TOKEN = "wrong_bot_token"

    # Real initDataRaw data
    real_init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    try:
        result = validate_telegram_data(real_init_data_raw)
        print("❌ Should have failed with wrong bot token")
        return False
    except Exception as e:
        print(f"✅ Correctly rejected wrong bot token: {e}")
        return True


def test_no_bot_token():
    """
    Test with no bot token configured
    """
    print("\n🧪 Testing with no bot token...")
    print("=" * 60)

    # Remove bot token
    if hasattr(settings, "TELEGRAM_BOT_TOKEN"):
        delattr(settings, "TELEGRAM_BOT_TOKEN")

    # Real initDataRaw data
    real_init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    try:
        result = validate_telegram_data(real_init_data_raw)
        print("❌ Should have failed with no bot token")
        return False
    except Exception as e:
        print(f"✅ Correctly rejected with no bot token: {e}")
        return True


if __name__ == "__main__":
    print("🚀 Python Native Telegram Validation Test")
    print("=" * 60)

    # Test real data
    test1_result = test_telegram_validation()

    # Test wrong bot token
    test2_result = test_wrong_bot_token()

    # Test no bot token
    test3_result = test_no_bot_token()

    print("\n📊 Test Results:")
    print("=" * 60)
    print(f"✅ Real data validation: {'PASS' if test1_result else 'FAIL'}")
    print(f"✅ Wrong token rejection: {'PASS' if test2_result else 'FAIL'}")
    print(f"✅ No token rejection: {'PASS' if test3_result else 'FAIL'}")

    if test1_result and test2_result and test3_result:
        print("\n🎉 All tests passed! Python native validation is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
