#!/usr/bin/env python3
"""
Independent Telegram data validation test script
Test HMAC-SHA256 signature verification for Telegram WebApp initDataRaw
"""

import json
import hmac
import hashlib
from urllib.parse import parse_qsl, urlencode


def validate_telegram_data(init_data_raw, bot_token):
    """Validate Telegram initDataRaw data"""

    # Parse init_data_raw
    data_dict = dict(parse_qsl(init_data_raw))

    # Extract hash
    received_hash = data_dict.pop("hash", None)
    if not received_hash:
        return {"valid": False, "error": "Missing hash parameter"}

    # Extract user data
    user_data_str = data_dict.get("user", "{}")
    try:
        user_data = json.loads(user_data_str)
    except json.JSONDecodeError:
        return {"valid": False, "error": "Invalid user data JSON"}

    # Verify HMAC signature
    # Remove hash parameter, reconstruct data string
    sorted_params = sorted(data_dict.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_params])

    # Calculate HMAC-SHA256
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    # Sort alphabetically
    if received_hash != calculated_hash:
        return {"valid": False, "error": "Invalid signature"}

    return {
        "valid": True,
        "user_data": user_data,
        "auth_date": data_dict.get("auth_date"),
        "query_id": data_dict.get("query_id"),
    }


def test_telegram_validation():
    """Test Telegram data validation"""
    print("=== Testing Telegram Data Validation ===")

    # Test data
    bot_token = "8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"
    user_data = {
        "id": 7498813057,
        "first_name": "Justin",
        "username": "justin_lung",
        "language_code": "zh-hans",
    }

    # Create test initDataRaw
    data_dict = {
        "user": json.dumps(user_data),
        "auth_date": "1717740000",
        "chat_instance": "-1234567890123456789",
        "chat_type": "private",
    }

    # Calculate hash
    data_string = urlencode(sorted(data_dict.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    calculated_hash = hmac.new(
        secret_key, data_string.encode(), hashlib.sha256
    ).hexdigest()

    data_dict["hash"] = calculated_hash
    init_data_raw = urlencode(data_dict)

    print(f"Test initDataRaw: {init_data_raw}")

    # Validate
    result = validate_telegram_data(init_data_raw, bot_token)

    if result["valid"]:
        print("✅ Validation successful")
        print(f"User ID: {result['user_data']['id']}")
        print(f"Username: {result['user_data']['username']}")
        print(f"First Name: {result['user_data']['first_name']}")
    else:
        print(f"❌ Validation failed: {result['error']}")

    return result["valid"]


if __name__ == "__main__":
    success = test_telegram_validation()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Tests failed!")
        exit(1)
