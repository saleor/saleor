#!/usr/bin/env python3
"""
Compare current Telegram validation implementation with official standards
"""

import json
import hmac
import hashlib
from urllib.parse import parse_qsl, urlencode
import subprocess
import sys
import os


def current_implementation_validate(init_data_raw, bot_token):
    """Current implementation in Saleor"""
    try:
        # Parse init_data_raw
        data_dict = dict(parse_qsl(init_data_raw))

        # Extract hash
        received_hash = data_dict.pop("hash", None)
        if not received_hash:
            return {"valid": False, "error": "Missing hash parameter"}

        # Sort parameters and create check string
        sorted_params = sorted(data_dict.items())
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_params])

        # Calculate HMAC-SHA256
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        # Verify hash
        if received_hash != calculated_hash:
            return {"valid": False, "error": "Invalid signature"}

        # Parse user data
        user_data = json.loads(data_dict.get("user", "{}"))

        return {
            "valid": True,
            "user_data": user_data,
            "auth_date": data_dict.get("auth_date"),
            "query_id": data_dict.get("query_id"),
        }

    except Exception as e:
        return {"valid": False, "error": str(e)}


def official_telegram_validation(init_data_raw, bot_token):
    """Official Telegram validation using @telegram-apps/sdk"""
    try:
        # Create Node.js script for validation
        node_script = f"""
const {{ validate }} = require('@telegram-apps/sdk');

const initDataRaw = '{init_data_raw}';
const botToken = '{bot_token}';

try {{
    const result = validate(initDataRaw, botToken);
    console.log(JSON.stringify({{ success: true, result }}));
}} catch (error) {{
    console.log(JSON.stringify({{ success: false, error: error.message }}));
}}
"""

        # Write script to temporary file
        script_path = "/tmp/telegram_validation.js"
        with open(script_path, "w") as f:
            f.write(node_script)

        # Run Node.js script
        result = subprocess.run(
            ["node", script_path], capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return {"valid": False, "error": f"Node.js error: {result.stderr}"}

        # Parse result
        try:
            data = json.loads(result.stdout.strip())
            if data.get("success"):
                return {"valid": True, "result": data.get("result")}
            else:
                return {"valid": False, "error": data.get("error")}
        except json.JSONDecodeError:
            return {"valid": False, "error": f"Invalid JSON response: {result.stdout}"}

    except subprocess.TimeoutExpired:
        return {"valid": False, "error": "Node.js validation timeout"}
    except FileNotFoundError:
        return {"valid": False, "error": "Node.js not found"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def test_validation_comparison():
    """Test and compare validation methods"""
    print("🔍 Comparing Telegram validation implementations")
    print("=" * 60)

    # Test data
    bot_token = "8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"

    # Real initDataRaw data
    real_init_data_raw = (
        "user=%7B%22id%22%3A7498813057%2C%22first_name%22%3A%22Justin%22%2C%22last_name%22%3A%22Lung%22%2C%22username%22%3A%22justin_lung%22%2C%22language_code%22%3A%22zh-hans%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FrGKW6Lt09BFrz7VflVuUhEs6QKCzwcYRig4tOJajh48XbQ6wjxfYBorP5x7116lJ.svg%22%7D"
        "&chat_instance=6755980278051609308"
        "&chat_type=sender"
        "&auth_date=1738051266"
        "&signature=7lnXe6LFLx7RSFUNuoJzWocQmIppy3vHs44gIKO-k8Atz78aORr2h7p3EyswVzywkGkdAxrAYXzgUL7_Cjf6AQ"
        "&hash=53414351f3b4ed4bba75ca16f1704c2b186b319e15124c4702e989d1841a262c"
    )

    print(f"🤖 Bot Token: {bot_token[:20]}...")
    print(f"📦 Init Data Raw: {real_init_data_raw[:100]}...")
    print()

    # Test current implementation
    print("1️⃣ Testing Current Implementation:")
    current_result = current_implementation_validate(real_init_data_raw, bot_token)
    print(f"   Result: {current_result}")
    print()

    # Test official implementation
    print("2️⃣ Testing Official Implementation:")
    official_result = official_telegram_validation(real_init_data_raw, bot_token)
    print(f"   Result: {official_result}")
    print()

    # Compare results
    print("3️⃣ Comparison:")
    if current_result.get("valid") == official_result.get("valid"):
        print("   ✅ Both implementations agree on validation result")
        if current_result.get("valid"):
            print("   ✅ Both implementations validate successfully")
        else:
            print("   ❌ Both implementations reject the data")
    else:
        print("   ❌ Implementations disagree on validation result")
        print(f"   Current: {current_result.get('valid')}")
        print(f"   Official: {official_result.get('valid')}")

    return current_result, official_result


def test_with_manual_verification():
    """Test with manual HMAC verification according to official docs"""
    print("\n🔧 Manual HMAC Verification Test")
    print("=" * 60)

    bot_token = "8014119913:AAFyzp17QSynAxUmo51_oZrpypiKWckiFBA"

    # Test data
    user_data = {
        "id": 7498813057,
        "first_name": "Justin",
        "username": "justin_lung",
        "language_code": "zh-hans",
    }

    data_dict = {
        "user": json.dumps(user_data),
        "auth_date": "1717740000",
        "chat_instance": "-1234567890123456789",
        "chat_type": "private",
    }

    # According to official docs:
    # 1. Sort parameters alphabetically
    sorted_params = sorted(data_dict.items())

    # 2. Create data check string with newlines
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_params])

    print(f"📝 Data check string:")
    print(f"   {data_check_string}")
    print()

    # 3. Calculate HMAC-SHA256
    # Secret key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    # 4. Calculate hash = HMAC-SHA256(secret_key, data_check_string)
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    print(f"🔐 Calculated hash: {calculated_hash}")

    # 5. Add hash to data and create initDataRaw
    data_dict["hash"] = calculated_hash
    init_data_raw = urlencode(data_dict)

    print(f"📦 Generated initDataRaw: {init_data_raw}")
    print()

    # 6. Test our validation
    result = current_implementation_validate(init_data_raw, bot_token)
    print(f"✅ Validation result: {result}")

    return result


if __name__ == "__main__":
    print("🚀 Telegram Validation Implementation Comparison")
    print("=" * 60)

    # Test comparison
    current, official = test_validation_comparison()

    # Test manual verification
    manual_result = test_with_manual_verification()

    print("\n📊 Summary:")
    print(
        f"   Current implementation: {'✅ Working' if current.get('valid') else '❌ Failed'}"
    )
    print(
        f"   Official implementation: {'✅ Working' if official.get('valid') else '❌ Failed'}"
    )
    print(
        f"   Manual verification: {'✅ Working' if manual_result.get('valid') else '❌ Failed'}"
    )

    if current.get("valid") and manual_result.get("valid"):
        print("\n🎉 Current implementation appears to be correct!")
    else:
        print("\n⚠️  There may be issues with the current implementation")
