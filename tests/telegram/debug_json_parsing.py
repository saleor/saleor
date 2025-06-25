#!/usr/bin/env python3
"""
Debug JSON parsing issues
"""

import json
import sys
import os
from urllib.parse import parse_qs, unquote

# Add project root directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Set Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

import django

django.setup()


def debug_json_parsing():
    """Debug JSON parsing issues"""

    # Your provided new initDataRaw data
    init_data_raw = "auth_date=1750788564&hash=b2b555fa093ec89146d0b2c1096a0e3de43b6eda505be078a86d2b915e6d644b&signature=&start_param=&user=%7B%22added_to_attachment_menu%22%3Afalse%2C%22allows_write_to_pm%22%3Afalse%2C%22first_name%22%3A%221682845821%22%2C%22id%22%3A1682845821%2C%22is_bot%22%3Afalse%2C%22is_premium%22%3Afalse%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22kenmy_android%22%2C%22language_code%22%3A%22zh-CN%22%2C%22photo_url%22%3A%22https%3A%2F%2Fmt.social%2F_matrix%2Fmedia%2Fv3%2Fthumbnail%2Fmt.social%2FnaNAHDnDBDqEaDvgoeAfbibm%3Fwidth%3D384%26height%3D384%26method%3Dcrop%26allow_redirect%3Dtrue%22%2C%22provider%22%3A%22matrix%22%2C%22extra%22%3A%7B%22hs%22%3A%22mt.social%22%7D%7D"

    print("=" * 60)
    print("Debug JSON Parsing Issues")
    print("=" * 60)
    print(f"Original data: {init_data_raw}")
    print()

    # URL decode
    decoded_data = unquote(init_data_raw)
    print(f"Decoded data: {decoded_data}")
    print()

    # Parse parameters
    parsed_data = parse_qs(decoded_data)
    print("Parsed parameters:")
    for key, values in parsed_data.items():
        print(f"  {key}: {values[0] if values else 'None'}")
    print()

    # Extract user data
    user_data = parsed_data.get("user", [None])[0]
    if user_data:
        print(f"User data string: {user_data}")
        print()

        # Try to parse JSON
        try:
            user_info = json.loads(user_data)
            print("✅ JSON parsing successful!")
            print(f"User info: {json.dumps(user_info, indent=2, ensure_ascii=False)}")

            # Check required fields
            required_fields = ["id", "first_name"]
            for field in required_fields:
                if field in user_info:
                    print(f"✅ Required field {field}: {user_info[field]}")
                else:
                    print(f"❌ Missing required field: {field}")

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {str(e)}")
            print(f"Error position: Line {e.lineno}, Column {e.colno}")
            print(f"Error message: {e.msg}")

            # Try to locate the problem
            print("\nTrying to locate the problem:")
            lines = user_data.split("\n")
            if e.lineno <= len(lines):
                problem_line = lines[e.lineno - 1]
                print(f"Problem line: {problem_line}")
                if e.colno <= len(problem_line):
                    print(f"Problem position: {' ' * (e.colno - 1)}^")

    else:
        print("❌ User data not found")


def test_telegram_validation():
    """Test Telegram validation"""
    from django.test import override_settings
    from saleor.graphql.account.mutations.authentication.telegram_token_create import (
        validate_telegram_data,
    )

    init_data_raw = "auth_date=1750788564&hash=b2b555fa093ec89146d0b2c1096a0e3de43b6eda505be078a86d2b915e6d644b&signature=&start_param=&user=%7B%22added_to_attachment_menu%22%3Afalse%2C%22allows_write_to_pm%22%3Afalse%2C%22first_name%22%3A%221682845821%22%2C%22id%22%3A1682845821%2C%22is_bot%22%3Afalse%2C%22is_premium%22%3Afalse%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22kenmy_android%22%2C%22language_code%22%3A%22zh-CN%22%2C%22photo_url%22%3A%22https%3A%2F%2Fmt.social%2F_matrix%2Fmedia%2Fv3%2Fthumbnail%2Fmt.social%2FnaNAHDnDBDqEaDvgoeAfbibm%3Fwidth%3D384%26height%3D384%26method%3Dcrop%26allow_redirect%3Dtrue%22%2C%22provider%22%3A%22matrix%22%2C%22extra%22%3A%7B%22hs%22%3A%22mt.social%22%7D%7D"

    print("=" * 60)
    print("Test Telegram Validation")
    print("=" * 60)

    try:
        with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_for_validation"):
            result = validate_telegram_data(init_data_raw)
            print("✅ Validation successful!")
            print(
                f"User info: {json.dumps(result['user'], indent=2, ensure_ascii=False)}"
            )

    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")

        # If it's a ValidationError, show detailed information
        if hasattr(e, "message_dict"):
            print("Detailed error information:")
            for field, errors in e.message_dict.items():
                print(f"  {field}: {errors}")
        elif hasattr(e, "message"):
            print(f"Error message: {e.message}")


if __name__ == "__main__":
    print("Starting JSON parsing debug...")
    print()

    debug_json_parsing()
    print()
    test_telegram_validation()

    print()
    print("=" * 60)
    print("Debug completed")
    print("=" * 60)
