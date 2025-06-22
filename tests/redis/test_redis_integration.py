#!/usr/bin/env python3
"""
Redis integration test script
Test functionality to get Redis instance from backend.env configuration
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "saleor"))


def test_redis_connection():
    """Test Redis connection"""
    print("🔍 Testing Redis connection...")

    try:
        # Simulate Django settings
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

        import django

        django.setup()

        from django.core.cache import cache
        from django.conf import settings

        # Get Redis configuration
        celery_broker_url = getattr(
            settings, "CELERY_BROKER_URL", "redis://redis:6379/1"
        )
        print(f"✅ Redis configuration: {celery_broker_url}")

        # Test Redis connection
        test_key = "test_redis_connection"
        test_value = {
            "message": "Hello Redis!",
            "timestamp": datetime.now().isoformat(),
            "test": True,
        }

        # Store test data
        cache.set(test_key, test_value, timeout=60)
        print(f"✅ Test data stored: {test_key}")

        # Read test data
        retrieved_value = cache.get(test_key)
        if retrieved_value == test_value:
            print(f"✅ Test data read successfully: {retrieved_value}")
        else:
            print(
                f"❌ Test data read failed: expected={test_value}, actual={retrieved_value}"
            )
            return False

        # Clean up test data
        cache.delete(test_key)
        print(f"✅ Test data cleaned up")

        return True

    except Exception as e:
        print(f"❌ Redis connection test failed: {e}")
        return False


def test_verification_code_storage():
    """Test verification code storage functionality"""
    print("\n🔍 Testing verification code storage functionality...")

    try:
        import django

        django.setup()

        from django.core.cache import cache
        from django.utils import timezone

        # Simulate verification code data
        telegram_id = 123456789
        verification_code = "123456"
        old_email = f"telegram_{telegram_id}@telegram.local"
        new_email = "test@example.com"

        cache_key = f"email_change_verification:{telegram_id}"
        cache_data = {
            "verification_code": verification_code,
            "old_email": old_email,
            "new_email": new_email,
            "created_at": timezone.now().isoformat(),
        }

        # Store verification code
        cache.set(cache_key, cache_data, timeout=600)  # 10 minutes
        print(f"✅ Verification code stored: {cache_key}")
        print(f"   Verification code: {verification_code}")
        print(f"   Old email: {old_email}")
        print(f"   New email: {new_email}")

        # Read verification code
        retrieved_data = cache.get(cache_key)
        if (
            retrieved_data
            and retrieved_data.get("verification_code") == verification_code
        ):
            print(f"✅ Verification code read successfully")
        else:
            print(f"❌ Verification code read failed")
            return False

        # Verify verification code
        input_code = "123456"
        if retrieved_data.get("verification_code") == input_code:
            print(f"✅ Verification code validation successful")
        else:
            print(f"❌ Verification code validation failed")
            return False

        # Clean up verification code
        cache.delete(cache_key)
        print(f"✅ Verification code cleaned up")

        return True

    except Exception as e:
        print(f"❌ Verification code storage test failed: {e}")
        return False


def test_expiration_handling():
    """Test expiration handling functionality"""
    print("\n🔍 Testing expiration handling functionality...")

    try:
        import django

        django.setup()

        from django.core.cache import cache
        from django.utils import timezone

        # Simulate expired verification code
        telegram_id = 987654321
        cache_key = f"email_change_verification:{telegram_id}"

        # Store a short-term expired verification code (5 seconds)
        cache_data = {
            "verification_code": "999999",
            "old_email": f"telegram_{telegram_id}@telegram.local",
            "new_email": "expired@example.com",
            "created_at": timezone.now().isoformat(),
        }

        cache.set(cache_key, cache_data, timeout=5)  # 5 seconds expiration
        print(f"✅ Short-term verification code stored: {cache_key}")

        # Read immediately (should exist)
        immediate_data = cache.get(cache_key)
        if immediate_data:
            print(f"✅ Immediate read successful")
        else:
            print(f"❌ Immediate read failed")
            return False

        # Wait 6 seconds then read (should be expired)
        print("⏳ Waiting 6 seconds for verification code to expire...")
        import time

        time.sleep(6)

        expired_data = cache.get(cache_key)
        if expired_data is None:
            print(f"✅ Expired verification code automatically cleaned up")
        else:
            print(f"❌ Expired verification code not cleaned up: {expired_data}")
            return False

        return True

    except Exception as e:
        print(f"❌ Expiration handling test failed: {e}")
        return False


def test_backend_env_config():
    """Test backend.env configuration reading"""
    print("\n🔍 Testing backend.env configuration reading...")

    try:
        # Read backend.env file
        backend_env_path = ".devcontainer/backend.env"
        if os.path.exists(backend_env_path):
            with open(backend_env_path, "r") as f:
                content = f.read()

            print(f"✅ backend.env file exists")
            print(f"File content:")
            for line in content.strip().split("\n"):
                if line.strip():
                    if "CELERY_BROKER_URL" in line:
                        print(f"   🔗 {line}")
                    elif "EMAIL_URL" in line:
                        print(f"   📧 {line}")
                    else:
                        print(f"   📝 {line}")

            # Check Redis configuration
            if "CELERY_BROKER_URL=redis://" in content:
                print(f"✅ Redis configuration found")
                return True
            else:
                print(f"❌ Redis configuration not found")
                return False
        else:
            print(f"❌ backend.env file does not exist: {backend_env_path}")
            return False

    except Exception as e:
        print(f"❌ backend.env configuration test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting Redis integration test...")
    print("=" * 50)

    tests = [
        ("backend.env configuration reading", test_backend_env_config),
        ("Redis connection", test_redis_connection),
        ("Verification code storage", test_verification_code_storage),
        ("Expiration handling", test_expiration_handling),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        print("-" * 30)

        try:
            result = test_func()
            results.append((test_name, result))

            if result:
                print(f"✅ {test_name} - Passed")
            else:
                print(f"❌ {test_name} - Failed")

        except Exception as e:
            print(f"❌ {test_name} - Exception: {e}")
            results.append((test_name, False))

    # Output test summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ Passed" if result else "❌ Failed"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Redis integration is working correctly.")
    else:
        print("❌ Some tests failed. Please check the configuration.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
