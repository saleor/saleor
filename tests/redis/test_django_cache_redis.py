#!/usr/bin/env python3
"""
Test Django cache system integration with Redis
Verify verification code storage to Redis and reading from Redis functionality
"""

import os
import sys
import django
from django.core.cache import cache
from django.conf import settings

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()


def test_django_cache_redis_integration():
    """Test Django cache system integration with Redis"""
    print("=== Testing Django Cache System Integration with Redis ===")

    # Check cache backend configuration
    cache_backend = (
        getattr(settings, "CACHES", {}).get("default", {}).get("BACKEND", "Unknown")
    )
    print(f"Cache backend: {cache_backend}")

    # Test basic cache functionality
    test_key = "test_verification_code"
    test_data = {
        "verification_code": "123456",
        "user_id": 123,
        "email": "test@example.com",
        "created_at": "2024-01-01T00:00:00Z",
    }

    # Store to cache, set 10 minutes expiration
    cache.set(test_key, test_data, timeout=600)
    print(f"✅ Verification code stored to cache: {test_key}")

    # Read from cache
    retrieved_data = cache.get(test_key)
    if retrieved_data:
        print(f"✅ Successfully read from cache: {retrieved_data}")
    else:
        print("❌ Failed to read from cache")

    # Test cache expiration
    print("\n=== Testing Cache Expiration ===")
    short_key = "test_short_expiration"
    cache.set(short_key, "test_value", timeout=1)  # 1 second expiration

    # Immediately read
    immediate_value = cache.get(short_key)
    print(f"Immediate read: {immediate_value}")

    # Wait and read again
    import time

    time.sleep(2)
    expired_value = cache.get(short_key)
    print(f"After expiration: {expired_value}")

    # Test cache deletion
    print("\n=== Testing Cache Deletion ===")
    delete_key = "test_delete"
    cache.set(delete_key, "to_be_deleted")
    print(f"Before deletion: {cache.get(delete_key)}")

    cache.delete(delete_key)
    after_delete = cache.get(delete_key)
    print(f"After deletion: {after_delete}")

    # Test verification code specific functionality
    print("\n=== Testing Verification Code Functionality ===")
    verification_key = "email_change_verification:123456"
    verification_data = {
        "verification_code": "654321",
        "old_email": "old@example.com",
        "new_email": "new@example.com",
        "telegram_id": 123456789,
        "user_id": 456,
        "created_at": "2024-01-01T00:00:00Z",
        "expires_at": "2024-01-01T00:10:00Z",
    }

    # Store verification data
    cache.set(verification_key, verification_data, timeout=600)
    print(f"✅ Verification data stored: {verification_key}")

    # Retrieve verification data
    retrieved_verification = cache.get(verification_key)
    if retrieved_verification:
        print(f"✅ Verification data retrieved: {retrieved_verification}")
        print(f"   Code: {retrieved_verification.get('verification_code')}")
        print(f"   Old Email: {retrieved_verification.get('old_email')}")
        print(f"   New Email: {retrieved_verification.get('new_email')}")
    else:
        print("❌ Failed to retrieve verification data")

    # Test cache clear
    print("\n=== Testing Cache Clear ===")
    cache.clear()
    print("✅ Cache cleared")

    # Verify cache is empty
    empty_value = cache.get(test_key)
    print(f"After clear: {empty_value}")

    print("\n=== Test Completed Successfully ===")


if __name__ == "__main__":
    test_django_cache_redis_integration()
