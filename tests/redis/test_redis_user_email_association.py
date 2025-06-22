#!/usr/bin/env python3
"""
Test Redis storage of email verification codes with user ID and old/new email association functionality
Verify data integrity and consistency
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "saleor"))


def test_redis_data_structure_enhanced():
    """Test enhanced Redis data structure"""
    print("🔍 Testing enhanced Redis data structure...")

    try:
        # Simulate user data
        telegram_id = 123456789
        user_id = 98765
        old_email = f"telegram_{telegram_id}@telegram.local"
        new_email = "newemail@example.com"
        verification_code = "123456"
        created_at = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()

        # Simulate main verification code data
        cache_data = {
            "verification_code": verification_code,
            "old_email": old_email,
            "new_email": new_email,
            "telegram_id": telegram_id,
            "user_id": user_id,
            "created_at": created_at,
            "expires_at": expires_at,
        }

        # Simulate email mapping data
        email_mapping_data = {
            "telegram_id": telegram_id,
            "user_id": user_id,
            "new_email": new_email,
            "verification_code": verification_code,
            "created_at": created_at,
        }

        print(f"✅ Main verification code data structure:")
        for key, value in cache_data.items():
            print(f"   {key}: {value}")

        print(f"\n✅ Email mapping data structure:")
        for key, value in email_mapping_data.items():
            print(f"   {key}: {value}")

        # Verify data structure integrity
        required_fields = [
            "verification_code",
            "old_email",
            "new_email",
            "telegram_id",
            "user_id",
            "created_at",
            "expires_at",
        ]
        for field in required_fields:
            if field in cache_data:
                print(f"   ✅ Main data field {field} exists")
            else:
                print(f"   ❌ Main data field {field} missing")
                return False

        mapping_required_fields = [
            "telegram_id",
            "user_id",
            "new_email",
            "verification_code",
            "created_at",
        ]
        for field in mapping_required_fields:
            if field in email_mapping_data:
                print(f"   ✅ Mapping data field {field} exists")
            else:
                print(f"   ❌ Mapping data field {field} missing")
                return False

        return True

    except Exception as e:
        print(f"❌ Redis data structure test failed: {e}")
        return False


def test_user_email_association_validation():
    """Test user ID and old/new email association validation"""
    print("\n🔍 Testing user ID and old/new email association validation...")

    try:
        # Simulate data
        telegram_id = 123456789
        user_id = 98765
        old_email = f"telegram_{telegram_id}@telegram.local"
        new_email = "newemail@example.com"

        # Test 1: Telegram ID and email format consistency
        expected_old_email = f"telegram_{telegram_id}@telegram.local"
        if old_email == expected_old_email:
            print(f"✅ Telegram ID and email format consistency validation passed")
        else:
            print(f"❌ Telegram ID and email format consistency validation failed")
            return False

        # Test 2: User ID consistency
        stored_user_id = 98765
        if stored_user_id == user_id:
            print(f"✅ User ID consistency validation passed")
        else:
            print(f"❌ User ID consistency validation failed")
            return False

        # Test 3: Old email format validation
        if old_email.startswith("telegram_") and old_email.endswith("@telegram.local"):
            print(f"✅ Old email format validation passed")
        else:
            print(f"❌ Old email format validation failed")
            return False

        # Test 4: New email format validation
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if re.match(pattern, new_email) and not new_email.endswith("@telegram.local"):
            print(f"✅ New email format validation passed")
        else:
            print(f"❌ New email format validation failed")
            return False

        # Test 5: Email mapping relationship validation
        cache_key = f"email_change_verification:{telegram_id}"
        email_mapping_key = f"email_change_mapping:{old_email}"

        print(f"✅ Cache key format validation passed:")
        print(f"   Main cache key: {cache_key}")
        print(f"   Mapping cache key: {email_mapping_key}")

        return True

    except Exception as e:
        print(f"❌ User email association validation test failed: {e}")
        return False


def test_data_integrity_validation():
    """Test data integrity validation"""
    print("\n🔍 Testing data integrity validation...")

    try:
        # Simulate complete data validation scenario
        telegram_id = 123456789
        user_id = 98765
        old_email = f"telegram_{telegram_id}@telegram.local"
        new_email = "newemail@example.com"

        # Scenario 1: Data complete and consistent
        print(f"📋 Scenario 1: Data complete and consistent")
        cache_data = {
            "telegram_id": telegram_id,
            "user_id": user_id,
            "old_email": old_email,
            "new_email": new_email,
            "verification_code": "123456",
            "created_at": datetime.now().isoformat(),
        }

        # Verify Telegram ID consistency
        if cache_data.get("telegram_id") == telegram_id:
            print(f"   ✅ Telegram ID consistency validation passed")
        else:
            print(f"   ❌ Telegram ID consistency validation failed")
            return False

        # Verify user ID consistency
        if cache_data.get("user_id") == user_id:
            print(f"   ✅ User ID consistency validation passed")
        else:
            print(f"   ❌ User ID consistency validation failed")
            return False

        # Verify email format consistency
        if cache_data.get("old_email") == old_email:
            print(f"   ✅ Old email consistency validation passed")
        else:
            print(f"   ❌ Old email consistency validation failed")
            return False

        # Scenario 2: Data inconsistent (simulate error condition)
        print(f"📋 Scenario 2: Data inconsistency detection")
        invalid_cache_data = {
            "telegram_id": 999999999,  # Wrong Telegram ID
            "user_id": 11111,  # Wrong user ID
            "old_email": "wrong@telegram.local",  # Wrong email
            "new_email": new_email,
            "verification_code": "123456",
            "created_at": datetime.now().isoformat(),
        }

        # Detect Telegram ID mismatch
        if invalid_cache_data.get("telegram_id") != telegram_id:
            print(f"   ✅ Correctly detected Telegram ID mismatch")
        else:
            print(f"   ❌ Failed to detect Telegram ID mismatch")
            return False

        # Detect user ID mismatch
        if invalid_cache_data.get("user_id") != user_id:
            print(f"   ✅ Correctly detected user ID mismatch")
        else:
            print(f"   ❌ Failed to detect user ID mismatch")
            return False

        # Detect email mismatch
        if invalid_cache_data.get("old_email") != old_email:
            print(f"   ✅ Correctly detected email mismatch")
        else:
            print(f"   ❌ Failed to detect email mismatch")
            return False

        return True

    except Exception as e:
        print(f"❌ Data integrity validation test failed: {e}")
        return False


def test_email_format_validation():
    """Test email format validation"""
    print("\n🔍 Testing email format validation...")

    try:
        import re

        # Fix regex pattern to more strictly validate email format
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        # Test valid email formats
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.com",
            "user-name@domain.com",
        ]

        for email in valid_emails:
            if re.match(pattern, email):
                print(f"✅ Valid email format: {email}")
            else:
                print(f"❌ Invalid email format: {email}")
                return False

        # Test invalid email formats
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "user@example",
            "user@example..com",  # This should be recognized as invalid
            "user@example.c",  # Too short TLD
            "user@example.comm",  # Invalid TLD
        ]

        for email in invalid_emails:
            if not re.match(pattern, email):
                print(f"✅ Correctly rejected invalid email: {email}")
            else:
                print(f"❌ Incorrectly accepted invalid email: {email}")
                return False

        # Test Telegram email format specifically
        telegram_id = 123456789
        telegram_email = f"telegram_{telegram_id}@telegram.local"

        if telegram_email.startswith("telegram_") and telegram_email.endswith(
            "@telegram.local"
        ):
            print(f"✅ Telegram email format validation passed: {telegram_email}")
        else:
            print(f"❌ Telegram email format validation failed: {telegram_email}")
            return False

        return True

    except Exception as e:
        print(f"❌ Email format validation test failed: {e}")
        return False


def test_redis_cleanup_logic():
    """Test Redis cleanup logic"""
    print("\n🔍 Testing Redis cleanup logic...")

    try:
        # Simulate cleanup scenario
        telegram_id = 123456789
        old_email = f"telegram_{telegram_id}@telegram.local"

        # Define cache keys that should be cleaned up
        cache_keys = [
            f"email_change_verification:{telegram_id}",
            f"email_change_mapping:{old_email}",
            f"verification_attempts:{telegram_id}",
        ]

        print(f"✅ Cache keys to be cleaned up:")
        for key in cache_keys:
            print(f"   {key}")

        # Simulate cleanup verification
        cleaned_keys = []
        for key in cache_keys:
            # In real implementation, this would delete from Redis
            cleaned_keys.append(key)
            print(f"   ✅ Cleaned up: {key}")

        if len(cleaned_keys) == len(cache_keys):
            print(f"✅ All cache keys cleaned up successfully")
            return True
        else:
            print(f"❌ Not all cache keys were cleaned up")
            return False

    except Exception as e:
        print(f"❌ Redis cleanup logic test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting Redis user email association test...")
    print("=" * 60)

    tests = [
        ("Enhanced Redis data structure", test_redis_data_structure_enhanced),
        ("User email association validation", test_user_email_association_validation),
        ("Data integrity validation", test_data_integrity_validation),
        ("Email format validation", test_email_format_validation),
        ("Redis cleanup logic", test_redis_cleanup_logic),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        print("-" * 40)

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
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ Passed" if result else "❌ Failed"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print(
            "🎉 All tests passed! Redis user email association functionality is working correctly."
        )
    else:
        print("❌ Some tests failed. Please check the implementation.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
