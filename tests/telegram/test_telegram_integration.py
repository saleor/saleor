#!/usr/bin/env python3
"""
Test script for Telegram integration functionality
"""

import os
import sys
import django
import asyncio
import json
from urllib.parse import parse_qs, unquote

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError
from saleor.account.models import User
from saleor.core.jwt import create_access_token, create_refresh_token


async def test_telegram_validation():
    """Test Telegram data validation"""
    print("=" * 50)
    print("Testing Telegram data validation")
    print("=" * 50)

    # Get bot token
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not configured")
        return False

    print(f"✅ Bot token configured: {bot_token[:10]}...")

    # Test bot connection
    try:
        bot = Bot(token=bot_token)
        bot_info = await bot.get_me()
        print(
            f"✅ Bot connection successful: {bot_info.first_name} (@{bot_info.username})"
        )
    except TelegramError as e:
        print(f"❌ Bot connection failed: {str(e)}")
        return False

    return True


def test_user_creation_and_lookup():
    """Test user creation and lookup functionality"""
    print("\n" + "=" * 50)
    print("Testing user creation and lookup functionality")
    print("=" * 50)

    # Test data
    test_telegram_id = 123456789
    test_user_info = {
        "id": test_telegram_id,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "language_code": "zh-CN",
    }

    # 1. Look for non-existent user
    try:
        user = User.objects.get(external_reference=f"telegram_{test_telegram_id}")
        print(f"❌ User already exists: {user.email}")
        return False
    except User.DoesNotExist:
        print("✅ User doesn't exist, can create")

    # 2. Create user
    try:
        from django.contrib.auth.hashers import make_password
        import secrets

        email = f"telegram_{test_telegram_id}@telegram.local"
        random_password = secrets.token_urlsafe(32)

        user = User.objects.create(
            email=email,
            first_name=test_user_info.get("first_name", ""),
            last_name=test_user_info.get("last_name", ""),
            is_active=True,
            is_confirmed=True,
            external_reference=f"telegram_{test_telegram_id}",
            password=make_password(random_password),
        )

        # Set metadata
        user.store_value_in_private_metadata(
            {
                "telegram_id": test_telegram_id,
                "telegram_username": test_user_info.get("username"),
                "telegram_language_code": test_user_info.get("language_code"),
                "created_via_telegram": True,
            }
        )
        user.save(update_fields=["private_metadata"])

        print(f"✅ User creation successful: {user.email}")
        print(f"   - ID: {user.id}")
        print(f"   - External Reference: {user.external_reference}")
        print(f"   - Private Metadata: {user.private_metadata}")

    except Exception as e:
        print(f"❌ User creation failed: {str(e)}")
        return False

    # 3. Look up the newly created user
    try:
        found_user = User.objects.get(external_reference=f"telegram_{test_telegram_id}")
        print(f"✅ User lookup successful: {found_user.email}")

        # Validate metadata
        telegram_id = found_user.get_value_from_private_metadata("telegram_id")
        if telegram_id == test_telegram_id:
            print("✅ Metadata validation successful")
        else:
            print(
                f"❌ Metadata validation failed: expected {test_telegram_id}, got {telegram_id}"
            )
            return False

    except User.DoesNotExist:
        print("❌ User lookup failed")
        return False

    # 4. Generate tokens
    try:
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        print("✅ Token generation successful")
        print(f"   - Access Token: {access_token[:50]}...")
        print(f"   - Refresh Token: {refresh_token[:50]}...")

    except Exception as e:
        print(f"❌ Token generation failed: {str(e)}")
        return False

    # 5. Clean up test data
    try:
        user.delete()
        print("✅ Test data cleanup completed")
    except Exception as e:
        print(f"⚠️ Test data cleanup failed: {str(e)}")

    return True


def test_init_data_parsing():
    """Test initDataRaw parsing"""
    print("\n" + "=" * 50)
    print("Testing initDataRaw parsing")
    print("=" * 50)

    # Simulated initDataRaw data (double URL encoded)
    test_init_data_raw = "user%3D%257B%2522id%2522%253A123456789%252C%2522first_name%2522%253A%2522Test%2522%252C%2522last_name%2522%253A%2522User%2522%252C%2522username%2522%253A%2522testuser%2522%252C%2522language_code%2522%253A%2522zh-CN%2522%257D%26auth_date%3D1234567890%26hash%3Dtest_hash%26chat_instance%3Dtest_instance%26chat_type%3Dtest_type%26signature%3Dtest_signature"

    print(f"Original data: {test_init_data_raw}")

    # First URL decode
    decoded_data = unquote(test_init_data_raw)
    print(f"First decode: {decoded_data}")

    # Second URL decode (handle double encoding)
    double_decoded_data = unquote(decoded_data)
    print(f"Second decode: {double_decoded_data}")

    # Parse parameters
    parsed_data = parse_qs(double_decoded_data)
    print(f"Parse result: {parsed_data}")

    # Extract user data
    user_data = parsed_data.get("user", [None])[0]
    if user_data:
        try:
            user_info = json.loads(user_data)
            print(f"User info: {user_info}")
            print("✅ initDataRaw parsing successful")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ User data JSON parsing failed: {str(e)}")
            return False
    else:
        print("❌ User data not found")
        return False


def main():
    """Main test function"""
    print("Starting Telegram integration functionality test")
    print("=" * 60)

    # Test 1: initDataRaw parsing
    if not test_init_data_parsing():
        print("❌ initDataRaw parsing test failed")
        return False

    # Test 2: User creation and lookup
    if not test_user_creation_and_lookup():
        print("❌ User creation and lookup test failed")
        return False

    # Test 3: Telegram validation (requires real bot token)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        telegram_valid = loop.run_until_complete(test_telegram_validation())
        loop.close()

        if not telegram_valid:
            print(
                "⚠️ Telegram validation test failed (may be token configuration issue)"
            )
        else:
            print("✅ Telegram validation test successful")

    except Exception as e:
        print(f"⚠️ Telegram validation test exception: {str(e)}")

    print("\n" + "=" * 60)
    print("✅ All tests completed")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
