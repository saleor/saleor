#!/usr/bin/env python3
"""
Script to diagnose Redis verification code data
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "saleor"))


def decode_init_data(init_data_raw):
    """Decode initDataRaw to get Telegram user information"""
    try:
        import urllib.parse

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


def check_redis_connection():
    """Check Redis connection"""
    try:
        from django.core.cache import cache

        # Test Redis connection
        test_key = "test_connection"
        test_value = "test_value"

        cache.set(test_key, test_value, 60)
        retrieved_value = cache.get(test_key)

        if retrieved_value == test_value:
            print(f"✅ Redis connection normal")
            cache.delete(test_key)
            return True
        else:
            print(f"❌ Redis connection abnormal: written and read values don't match")
            return False

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def check_verification_data(telegram_id):
    """Check verification code data in Redis"""
    try:
        from django.core.cache import cache

        cache_key = f"email_change_verification:{telegram_id}"
        print(f"🔍 Checking Redis key: {cache_key}")

        # Get data
        cache_data = cache.get(cache_key)

        if cache_data:
            print(f"✅ Found verification code data:")
            print(f"   Telegram ID: {cache_data.get('telegram_id')}")
            print(f"   User ID: {cache_data.get('user_id')}")
            print(f"   Old email: {cache_data.get('old_email')}")
            print(f"   New email: {cache_data.get('new_email')}")
            print(f"   Verification code: {cache_data.get('verification_code')}")
            print(f"   Created at: {cache_data.get('created_at')}")
            print(f"   Expires at: {cache_data.get('expires_at')}")

            # Check if expired
            if cache_data.get("expires_at"):
                try:
                    expires_at = datetime.fromisoformat(
                        cache_data.get("expires_at").replace("Z", "+00:00")
                    )
                    current_time = datetime.now()

                    if current_time > expires_at:
                        print(f"❌ Verification code expired")
                        return False
                    else:
                        time_left = expires_at - current_time
                        print(
                            f"✅ Verification code not expired, time remaining: {time_left}"
                        )
                        return True
                except Exception as e:
                    print(f"❌ Time parsing failed: {e}")
                    return False
            else:
                print(f"⚠️ No expiration time information found")
                return True
        else:
            print(f"❌ No verification code data found")
            return False

    except Exception as e:
        print(f"❌ Failed to check verification code data: {e}")
        return False


def check_user_exists(telegram_id):
    """Check if user exists"""
    try:
        from saleor.account import models

        external_ref = f"telegram_{telegram_id}"
        print(f"🔍 Looking for user: {external_ref}")

        try:
            user = models.User.objects.get(external_reference=external_ref)
            print(f"✅ User exists:")
            print(f"   User ID: {user.pk}")
            print(f"   Email: {user.email}")
            print(f"   Name: {user.first_name} {user.last_name}")
            return user
        except models.User.DoesNotExist:
            print(f"❌ User does not exist")
            return None

    except Exception as e:
        print(f"❌ Failed to check user: {e}")
        return None


def check_all_redis_keys():
    """Check all related Redis keys"""
    try:
        from django.core.cache import cache

        # Note: This requires Redis to support keys command, production environment may not support it
        print(f"🔍 Checking all Redis keys...")

        # Try to get some possible key patterns
        possible_keys = [
            "email_change_verification:*",
            "email_change_mapping:*",
            "verification:*",
        ]

        for pattern in possible_keys:
            print(f"   Checking pattern: {pattern}")
            # This is just an example, actual implementation may need to be adjusted based on Redis configuration

    except Exception as e:
        print(f"❌ Failed to check Redis keys: {e}")


def simulate_verification_request(telegram_id, old_email, new_email):
    """Simulate creating verification code request"""
    try:
        from django.core.cache import cache
        from datetime import datetime, timedelta
        import random

        # Generate 6-digit verification code
        verification_code = str(random.randint(100000, 999999))

        # Create time
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=10)

        # Simulate user ID
        user_id = 12345  # This should be the actual user ID

        # Create cache data
        cache_data = {
            "telegram_id": telegram_id,
            "user_id": user_id,
            "old_email": old_email,
            "new_email": new_email,
            "verification_code": verification_code,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        # Store in Redis
        cache_key = f"email_change_verification:{telegram_id}"
        cache.set(cache_key, cache_data, 600)  # 10 minutes expiration

        print(f"✅ Simulated verification code request creation:")
        print(f"   Verification code: {verification_code}")
        print(f"   Expiration time: {expires_at}")
        print(f"   Redis key: {cache_key}")

        return verification_code

    except Exception as e:
        print(f"❌ Failed to simulate verification code creation: {e}")
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

    # 2. Check Redis connection
    print(f"\n🔍 Step 2: Check Redis connection")
    print("-" * 50)
    redis_ok = check_redis_connection()

    if not redis_ok:
        print("❌ Redis connection failed, please check Redis configuration")
        return

    # 3. Check if user exists
    print(f"\n🔍 Step 3: Check if user exists")
    print("-" * 50)
    user = check_user_exists(telegram_id)

    if user:
        # 4. Check verification code data
        print(f"\n🔍 Step 4: Check verification code data")
        print("-" * 50)
        verification_ok = check_verification_data(telegram_id)

        if verification_ok:
            print(f"✅ Verification code data is valid")
        else:
            print(f"❌ Verification code data is invalid")
    else:
        print(f"❌ User does not exist, verification code data check skipped")

    # 5. Check all related Redis keys
    print(f"\n🔍 Step 5: Check all related Redis keys")
    print("-" * 50)
    check_all_redis_keys()

    # 6. Simulate verification request
    print(f"\n🔍 Step 6: Simulate verification request")
    print("-" * 50)
    simulated_verification_code = simulate_verification_request(
        telegram_id, old_email, new_email
    )

    if simulated_verification_code:
        print(f"✅ Simulated verification code request created successfully")
    else:
        print(f"❌ Failed to simulate verification code request")


if __name__ == "__main__":
    main()
