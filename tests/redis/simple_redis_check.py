#!/usr/bin/env python3
"""
Simple Redis check script
"""

import redis
import json
import urllib.parse
from datetime import datetime


def decode_init_data(init_data_raw):
    """Decode initDataRaw to get Telegram user information"""
    try:
        # URL decode
        decoded = urllib.parse.unquote(init_data_raw)
        print(f"✅ URL decode successful")
        print(f"   Decoded length: {len(decoded)}")

        # Parse parameters
        params = {}
        for param in decoded.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value

        # Parse user parameter
        if "user" in params:
            user_str = urllib.parse.unquote(params["user"])
            print(f"✅ Parsed user parameter: {user_str}")

            # Try to parse JSON
            try:
                user_data = json.loads(user_str)
                telegram_id = user_data.get("id")
                print(f"✅ Got Telegram ID: {telegram_id}")
                return telegram_id
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                return None
        else:
            print(f"❌ User parameter not found")
            return None

    except Exception as e:
        print(f"❌ Decoding failed: {e}")
        return None


def check_redis_data(telegram_id):
    """Check verification code data in Redis"""
    try:
        # Try to connect to Redis
        # Default connection parameters, may need to adjust based on actual configuration
        redis_client = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )

        # Test connection
        redis_client.ping()
        print(f"✅ Redis connection successful")

        # Check verification code data
        cache_key = f"email_change_verification:{telegram_id}"
        print(f"🔍 Checking Redis key: {cache_key}")

        # Get data
        cache_data = redis_client.get(cache_key)

        if cache_data:
            try:
                data = json.loads(cache_data)
                print(f"✅ Found verification code data:")
                print(f"   Telegram ID: {data.get('telegram_id')}")
                print(f"   User ID: {data.get('user_id')}")
                print(f"   Old email: {data.get('old_email')}")
                print(f"   New email: {data.get('new_email')}")
                print(f"   Verification code: {data.get('verification_code')}")
                print(f"   Created at: {data.get('created_at')}")
                print(f"   Expires at: {data.get('expires_at')}")

                # Check if expired
                if data.get("expires_at"):
                    try:
                        expires_at = datetime.fromisoformat(
                            data.get("expires_at").replace("Z", "+00:00")
                        )
                        current_time = datetime.now()

                        if current_time > expires_at:
                            print(f"❌ Verification code expired")
                            return False, data
                        else:
                            time_left = expires_at - current_time
                            print(
                                f"✅ Verification code not expired, time remaining: {time_left}"
                            )
                            return True, data
                    except Exception as e:
                        print(f"❌ Time parsing failed: {e}")
                        return True, data
                else:
                    print(f"⚠️ No expiration time information found")
                    return True, data
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"   Raw data: {cache_data}")
                return False, None
        else:
            print(f"❌ No verification code data found")
            return False, None

    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        print(f"   Please check if Redis is running, or adjust connection parameters")
        return False, None
    except Exception as e:
        print(f"❌ Failed to check verification code data: {e}")
        return False, None


def check_all_verification_keys():
    """Check all verification-related keys"""
    try:
        redis_client = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )

        print(f"🔍 Checking all verification-related keys...")

        # Get all keys
        all_keys = redis_client.keys("*")
        verification_keys = [
            key for key in all_keys if "verification" in key or "email_change" in key
        ]

        if verification_keys:
            print(f"✅ Found {len(verification_keys)} related keys:")
            for key in verification_keys:
                print(f"   {key}")

                # Try to get value
                try:
                    value = redis_client.get(key)
                    if value:
                        try:
                            data = json.loads(value)
                            if isinstance(data, dict):
                                print(f"      Telegram ID: {data.get('telegram_id')}")
                                print(
                                    f"      Verification code: {data.get('verification_code')}"
                                )
                                print(f"      New email: {data.get('new_email')}")
                        except:
                            print(f"      Value: {value[:100]}...")
                except Exception as e:
                    print(f"      Failed to get value: {e}")
        else:
            print(f"❌ No verification-related keys found")

    except Exception as e:
        print(f"❌ Failed to check Redis keys: {e}")


def create_test_verification(telegram_id, old_email, new_email):
    """Create test verification code data"""
    try:
        redis_client = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )

        import random
        from datetime import datetime, timedelta

        # Generate 6-digit verification code
        verification_code = str(random.randint(100000, 999999))

        # Create time
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=10)

        # Create cache data
        cache_data = {
            "telegram_id": telegram_id,
            "user_id": 12345,  # Simulate user ID
            "old_email": old_email,
            "new_email": new_email,
            "verification_code": verification_code,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        # Store in Redis
        cache_key = f"email_change_verification:{telegram_id}"
        redis_client.setex(
            cache_key, 600, json.dumps(cache_data)
        )  # 10 minutes expiration

        print(f"✅ Created test verification code data:")
        print(f"   Verification code: {verification_code}")
        print(f"   Expiration time: {expires_at}")
        print(f"   Redis key: {cache_key}")

        return verification_code

    except Exception as e:
        print(f"❌ Failed to create test verification code: {e}")
        return None


def main():
    """Main diagnostic function"""
    print("🔍 Starting Redis verification code data diagnosis...")
    print("=" * 70)

    # Test parameters
    init_data_raw = "user%3D%257B%2522id%2522%253A5861990984%252C%2522first_name%2522%253A%2522King%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522username%2522%253A%2522Svenlai666%2522%252C%2522language_code%2522%253A%2522zh-hans%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FfOso4OMYHXqI0CdCO2hxaqi5A23cXtUBjFLnUoRJa_aPy1E8DABF_Hm179IT0QOn.svg%2522%257D%26chat_instance%3D3930809717662463213%26chat_type%3Dprivate%26auth_date%3D1745999001%26signature%3DCVuFy8jWC8PNwkWdbA7tPueIbNqkUNxtillFjZQGL2yY47BhtAhh6QGqc3UwLwq9QYG6eMBSf-pcNibA49YUCA%26hash%3D5fb2ea078b8265c57271590e5a41f7a050f9892c25defd98fb7b380e3305d228&tgWebAppVersion=8.0&tgWebAppPlatform=macos&tgWebAppThemeParams=%7B%22secondary_bg_color%22%3A%22%23131415%22%2C%22subtitle_text_color%22%3A%22%23b1c3d5%22%2C%22text_color%22%3A%22%23ffffff%22%2C%22section_header_text_color%22%3A%22%23b1c3d5%22%2C%22destructive_text_color%22%3A%22%23ef5b5b%22%2C%22bottom_bar_bg_color%22%3A%22%23213040%22%2C%22section_bg_color%22%3A%22%2318222d%22%2C%22button_text_color%22%3A%22%23ffffff%22%2C%22accent_text_color%22%3A%22%232ea6ff%22%2C%22button_color%22%3A%22%232ea6ff%22%2C%22link_color%22%3A%22%2362bcf9%22%2C%22bg_color%22%3A%22%2318222d%22%2C%22hint_color%22%3A%22%23b1c3d5%22%2C%22header_bg_color%22%3A%22%23131415%22%2C%22section_separator_color%22%3A%22%23213040%22%7D"
    verification_code = "251404"
    old_email = "telegram_5861990984@telegram.local"
    new_email = "88888888@qq.com"

    print(f"📋 Diagnostic parameters:")
    print(f"   Verification code: {verification_code}")
    print(f"   Old email: {old_email}")
    print(f"   New email: {new_email}")

    # 1. Decode initDataRaw
    print(f"\n🔍 Step 1: Decode initDataRaw")
    print("-" * 50)
    telegram_id = decode_init_data(init_data_raw)

    if not telegram_id:
        print("❌ Cannot get Telegram ID, diagnosis terminated")
        return

    # 2. Check Redis data
    print(f"\n🔍 Step 2: Check Redis verification code data")
    print("-" * 50)
    verification_exists, data = check_redis_data(telegram_id)

    if verification_exists and data:
        print(f"\n✅ Verification code data exists and is valid")
        stored_code = data.get("verification_code")
        if stored_code == verification_code:
            print(f"✅ Verification code matches")
        else:
            print(f"❌ Verification code does not match:")
            print(f"   Stored verification code: {stored_code}")
            print(f"   Input verification code: {verification_code}")
    else:
        print(f"\n⚠️ Verification code data does not exist or has expired")
        print(f"   Possible reasons:")
        print(f"   1. Verification code has expired (10-minute validity)")
        print(f"   2. Verification code has been used and cleared")
        print(f"   3. Need to resend verification code")

        # 3. Create test verification data
        print(f"\n🔍 Step 3: Create test verification data")
        print("-" * 50)
        test_code = create_test_verification(telegram_id, old_email, new_email)

        if test_code:
            print(f"✅ Test verification code created successfully")
            print(f"   You can now test with verification code: {test_code}")
        else:
            print(f"❌ Failed to create test verification code")

    # 4. Check all verification keys
    print(f"\n🔍 Step 4: Check all verification keys")
    print("-" * 50)
    check_all_verification_keys()


if __name__ == "__main__":
    main()
