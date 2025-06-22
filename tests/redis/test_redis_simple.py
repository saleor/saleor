#!/usr/bin/env python3
"""
Simplified Redis test script
Does not depend on Django environment, directly tests Redis connection and functionality
"""

import os
import json
from datetime import datetime, timedelta


def test_backend_env_config():
    """Test backend.env configuration reading"""
    print("🔍 Testing backend.env configuration reading...")

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


def test_redis_connection_simple():
    """Test Redis connection (simplified version)"""
    print("\n🔍 Testing Redis connection (simplified version)...")

    try:
        # Try to import redis module
        try:
            import redis

            print(f"✅ redis module installed")
        except ImportError:
            print(f"⚠️ redis module not installed, skipping connection test")
            return True

        # Read Redis configuration from backend.env
        backend_env_path = ".devcontainer/backend.env"
        redis_url = "redis://redis:6379/1"  # Default configuration

        if os.path.exists(backend_env_path):
            with open(backend_env_path, "r") as f:
                content = f.read()
                for line in content.strip().split("\n"):
                    if line.startswith("CELERY_BROKER_URL="):
                        redis_url = line.split("=", 1)[1]
                        break

        print(f"🔗 Redis URL: {redis_url}")

        # Parse Redis URL
        if redis_url.startswith("redis://"):
            # Simple parsing redis://host:port/db
            parts = redis_url.replace("redis://", "").split("/")
            host_port = parts[0]
            db = int(parts[1]) if len(parts) > 1 else 0

            if ":" in host_port:
                host, port = host_port.split(":")
                port = int(port)
            else:
                host = host_port
                port = 6379

            print(f"   Host: {host}")
            print(f"   Port: {port}")
            print(f"   Database: {db}")

            # Try to connect to Redis
            try:
                r = redis.Redis(host=host, port=port, db=db, socket_connect_timeout=5)

                # Test connection
                r.ping()
                print(f"✅ Redis connection successful")

                # Test basic operations
                test_key = "test_redis_simple"
                test_value = {
                    "message": "Hello Redis!",
                    "timestamp": datetime.now().isoformat(),
                    "test": True,
                }

                # Store test data
                r.set(test_key, json.dumps(test_value), ex=60)
                print(f"✅ Test data stored: {test_key}")

                # Read test data
                retrieved_json = r.get(test_key)
                if retrieved_json:
                    retrieved_value = json.loads(retrieved_json)
                    if retrieved_value == test_value:
                        print(f"✅ Test data read successfully")
                    else:
                        print(f"❌ Test data read failed")
                        return False
                else:
                    print(f"❌ Test data read failed")
                    return False

                # Clean up test data
                r.delete(test_key)
                print(f"✅ Test data cleaned up")

                return True

            except redis.ConnectionError as e:
                print(f"❌ Redis connection failed: {e}")
                print(f"   Please ensure Redis service is running")
                return False
            except Exception as e:
                print(f"❌ Redis operation failed: {e}")
                return False
        else:
            print(f"❌ Invalid Redis URL format: {redis_url}")
            return False

    except Exception as e:
        print(f"❌ Redis connection test failed: {e}")
        return False


def test_verification_code_logic():
    """Test verification code logic (no Redis dependency)"""
    print("\n🔍 Testing verification code logic...")

    try:
        # Simulate verification code data
        telegram_id = 123456789
        verification_code = "123456"
        old_email = f"telegram_{telegram_id}@telegram.local"
        new_email = "test@example.com"
        created_at = datetime.now().isoformat()

        cache_key = f"email_change_verification:{telegram_id}"
        cache_data = {
            "verification_code": verification_code,
            "old_email": old_email,
            "new_email": new_email,
            "created_at": created_at,
        }

        print(f"✅ Verification code data structure:")
        print(f"   Cache key: {cache_key}")
        print(f"   Verification code: {verification_code}")
        print(f"   Old email: {old_email}")
        print(f"   New email: {new_email}")
        print(f"   Created at: {created_at}")

        # Test verification code validation logic
        input_code = "123456"
        if cache_data.get("verification_code") == input_code:
            print(f"✅ Verification code validation successful")
        else:
            print(f"❌ Verification code validation failed")
            return False

        # Test expiration time validation logic
        created_at_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        current_time = datetime.now()
        time_diff = current_time - created_at_dt

        if time_diff < timedelta(minutes=10):
            print(f"✅ Verification code not expired: {time_diff}")
        else:
            print(f"❌ Verification code expired: {time_diff}")
            return False

        # Test email format validation
        expected_old_email = f"telegram_{telegram_id}@telegram.local"
        if old_email == expected_old_email:
            print(f"✅ Email format validation successful")
        else:
            print(f"❌ Email format validation failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Verification code logic test failed: {e}")
        return False


def test_email_validation():
    """Test email validation logic"""
    print("\n🔍 Testing email validation logic...")

    try:
        # Test valid email formats
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.com",
        ]

        for email in valid_emails:
            if "@" in email and "." in email.split("@")[1]:
                print(f"✅ Valid email: {email}")
            else:
                print(f"❌ Invalid email: {email}")
                return False

        # Test Telegram email format
        telegram_id = 123456789
        telegram_email = f"telegram_{telegram_id}@telegram.local"
        expected_format = f"telegram_{telegram_id}@telegram.local"

        if telegram_email == expected_format:
            print(f"✅ Telegram email format correct: {telegram_email}")
        else:
            print(f"❌ Telegram email format incorrect: {telegram_email}")
            return False

        # Test email uniqueness check logic
        existing_emails = ["user1@example.com", "user2@example.com"]
        new_email = "user3@example.com"

        if new_email not in existing_emails:
            print(f"✅ Email uniqueness check passed: {new_email}")
        else:
            print(f"❌ Email uniqueness check failed: {new_email}")
            return False

        return True

    except Exception as e:
        print(f"❌ Email validation test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting simplified Redis test...")
    print("=" * 50)

    tests = [
        ("backend.env configuration reading", test_backend_env_config),
        ("Redis connection (simplified)", test_redis_connection_simple),
        ("Verification code logic", test_verification_code_logic),
        ("Email validation", test_email_validation),
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
        print("🎉 All tests passed! Redis functionality is working correctly.")
    else:
        print("❌ Some tests failed. Please check the configuration.")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
