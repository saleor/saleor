#!/usr/bin/env python3
"""
Simplified test script: verify in-memory storage functionality for Telegram email change
"""

import threading
import time
from datetime import datetime, timedelta

# Simulate in-memory storage
_verification_codes = {}
_verification_lock = threading.Lock()


def cleanup_expired_codes():
    """Clean up expired verification codes"""
    current_time = datetime.now()
    expired_keys = []

    with _verification_lock:
        for key, data in _verification_codes.items():
            expires_at_str = data.get("expires_at")
            if expires_at_str:
                try:
                    expires_at = datetime.fromisoformat(
                        expires_at_str.replace("Z", "+00:00")
                    )
                    if current_time > expires_at:
                        expired_keys.append(key)
                except (ValueError, TypeError):
                    expired_keys.append(key)
        # Delete expired codes
        for key in expired_keys:
            del _verification_codes[key]


def store_verification_code(telegram_id, new_email, verification_code):
    """Store verification code in memory"""
    # Clean up expired codes
    cleanup_expired_codes()

    cache_key = f"email_change_verification:{telegram_id}"
    cache_data = {
        "verification_code": verification_code,
        "new_email": new_email,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat(),
    }

    with _verification_lock:
        _verification_codes[cache_key] = cache_data

    return cache_key


def verify_verification_code(telegram_id, verification_code):
    """Verify verification code"""
    # Clean up expired codes
    cleanup_expired_codes()

    cache_key = f"email_change_verification:{telegram_id}"

    with _verification_lock:
        cache_data = _verification_codes.get(cache_key)

    if not cache_data:
        return None, "No pending email change request found"

    # Check if code matches
    stored_code = cache_data.get("verification_code")
    if stored_code != verification_code:
        return None, "Invalid verification code"

    # Check if code expired
    expires_at_str = cache_data.get("expires_at")
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            if datetime.now() > expires_at:
                # Delete expired cache
                with _verification_lock:
                    _verification_codes.pop(cache_key, None)
                return None, "Verification code has expired"
        except (ValueError, TypeError):
            return None, "Invalid expiration time format"

    # Get new email
    new_email = cache_data.get("new_email")
    if not new_email:
        return None, "Invalid verification data"

    # Delete cache after successful verification
    with _verification_lock:
        _verification_codes.pop(cache_key, None)

    return new_email, None


def test_memory_storage():
    """Test in-memory verification code storage functionality"""
    print("=== Test in-memory verification code storage ===")

    # Clean up previous test data
    with _verification_lock:
        _verification_codes.clear()

    # Simulate data
    telegram_id = 123456
    new_email = "test@example.com"
    verification_code = "123456"

    # 1. Store verification code in memory
    cache_key = store_verification_code(telegram_id, new_email, verification_code)
    print(f"Stored verification code in memory, key: {cache_key}")

    # 2. Verify storage success
    with _verification_lock:
        cache_data = _verification_codes.get(cache_key)

    if cache_data:
        print("✓ Verification code stored successfully")
        print(f"  Verification code: {cache_data['verification_code']}")
        print(f"  New email: {cache_data['new_email']}")
        print(f"  Created at: {cache_data['created_at']}")
        print(f"  Expires at: {cache_data['expires_at']}")
    else:
        print("✗ Verification code storage failed")
        return False

    # 3. Test verification code validation
    print("\n=== Test verification code validation ===")

    # Correct code
    result_email, error = verify_verification_code(telegram_id, verification_code)
    if result_email:
        print("✓ Verification code validation successful")
        print(f"  New email: {result_email}")
        # After success, code should be deleted
        with _verification_lock:
            assert _verification_codes.get(cache_key) is None
        print("✓ Verification code deleted from memory")
    else:
        print(f"✗ Verification code validation failed: {error}")
        return False

    # 4. Test wrong code
    print("\n=== Test wrong verification code ===")
    # Store again
    store_verification_code(telegram_id, new_email, verification_code)

    wrong_code = "000000"
    result_email, error = verify_verification_code(telegram_id, wrong_code)
    if not result_email and error == "Invalid verification code":
        print("✓ Wrong code correctly rejected")
    else:
        print("✗ Wrong code validation logic error")
        return False

    # 5. Test expired code
    print("\n=== Test expired verification code ===")
    # Manually create expired code
    expired_cache_key = f"email_change_verification:{telegram_id}"
    expired_data = {
        "verification_code": verification_code,
        "new_email": new_email,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() - timedelta(minutes=1)).isoformat(),  # expired
    }
    with _verification_lock:
        _verification_codes[expired_cache_key] = expired_data

    # Verify expired code is correctly detected
    result_email, error = verify_verification_code(telegram_id, verification_code)
    if not result_email and error == "Verification code has expired":
        print("✓ Expired code correctly detected")
        # Expired cache should be deleted
        with _verification_lock:
            assert _verification_codes.get(expired_cache_key) is None
        print("✓ Expired code deleted from memory")
    else:
        print(f"✗ Expired code detection logic error: {error}")
        return False

    print("\n=== All tests passed ===")
    return True


def test_thread_safety():
    """Test thread safety"""
    print("\n=== Test thread safety ===")

    # Clean up data
    with _verification_lock:
        _verification_codes.clear()

    def worker(thread_id):
        """Worker thread function"""
        telegram_id = 1000 + thread_id
        new_email = f"test{thread_id}@example.com"
        verification_code = f"12345{thread_id}"

        # Store code
        store_verification_code(telegram_id, new_email, verification_code)

        # Verify code
        result_email, error = verify_verification_code(telegram_id, verification_code)

        return result_email == new_email

    # Create multiple threads
    threads = []
    results = []

    for i in range(5):
        thread = threading.Thread(target=lambda i=i: results.append(worker(i)))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Verify results
    if all(results):
        print("✓ Thread safety test passed")
        return True
    else:
        print("✗ Thread safety test failed")
        return False


def test_cleanup_function():
    """Test cleanup function"""
    print("\n=== Test cleanup function ===")

    # Clean up data
    with _verification_lock:
        _verification_codes.clear()

    current_time = datetime.now()

    # Add valid code
    valid_key = "email_change_verification:123"
    valid_data = {
        "verification_code": "123456",
        "new_email": "valid@example.com",
        "created_at": current_time.isoformat(),
        "expires_at": (current_time + timedelta(minutes=10)).isoformat(),
    }
    with _verification_lock:
        _verification_codes[valid_key] = valid_data

    # Add expired code
    expired_key = "email_change_verification:456"
    expired_data = {
        "verification_code": "654321",
        "new_email": "expired@example.com",
        "created_at": (current_time - timedelta(minutes=20)).isoformat(),
        "expires_at": (current_time - timedelta(minutes=10)).isoformat(),
    }
    with _verification_lock:
        _verification_codes[expired_key] = expired_data

    # Run cleanup
    cleanup_expired_codes()

    with _verification_lock:
        assert valid_key in _verification_codes
        assert expired_key not in _verification_codes
    print("✓ Cleanup function works as expected")
    return True


def main():
    """Main test function"""
    print("🚀 Starting memory storage test for Telegram email change...")
    print("=" * 60)

    tests = [
        ("Memory storage functionality", test_memory_storage),
        ("Thread safety", test_thread_safety),
        ("Cleanup function", test_cleanup_function),
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
            "🎉 All tests passed! Memory storage for Telegram email change is working correctly."
        )
    else:
        print("❌ Some tests failed. Please check the implementation.")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
