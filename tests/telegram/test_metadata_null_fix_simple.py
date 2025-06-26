#!/usr/bin/env python3
"""
Simple test for Telegram metadata null value fix
"""

import os
import sys
import django
import json
import hmac
import hashlib
from urllib.parse import urlencode

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from django.test import TestCase
from django.test.utils import override_settings
from saleor.account.models import User
from saleor.graphql.account.mutations.authentication.telegram_token_create import (
    TelegramTokenCreate,
    validate_telegram_data,
)


class SimpleTelegramMetadataTest(TestCase):
    """Simple Telegram metadata test"""

    def setUp(self):
        """Test setup"""
        self.bot_token = "test_bot_token_123456789"

    def create_telegram_init_data(self, user_data):
        """Create Telegram initDataRaw data"""
        data_dict = {
            "user": json.dumps(user_data),
            "auth_date": "1234567890",
            "chat_instance": "1234567890123456789",
            "chat_type": "private",
        }

        # Calculate HMAC signature
        data_string = urlencode(sorted(data_dict.items()))
        secret_key = hmac.new(
            self.bot_token.encode(), data_string.encode(), hashlib.sha256
        ).hexdigest()

        data_dict["hash"] = secret_key
        return urlencode(data_dict)

    def test_null_values_filtered(self):
        """Test that null values are correctly filtered"""
        print("\n" + "=" * 50)
        print("Test null value filtering")
        print("=" * 50)

        # Create user data with null values
        user_data = {
            "id": 123456789,
            "first_name": "Test User",
            "username": None,  # null value
            "language_code": None,  # null value
        }

        init_data_raw = self.create_telegram_init_data(user_data)

        with override_settings(TELEGRAM_BOT_TOKEN=self.bot_token):
            try:
                # Execute mutation
                result = TelegramTokenCreate.perform_mutation(
                    None, None, init_data_raw=init_data_raw
                )

                if result.errors:
                    print(f"❌ Execution failed: {result.errors}")
                    return False

                user = result.user
                print(f"✅ User created: {user.email}")

                # Check metadata
                metadata = user.private_metadata
                print(f"📋 Metadata: {metadata}")

                # Verify null values are filtered
                if "telegram_username" in metadata:
                    print(
                        f"❌ Username field should not exist: {metadata['telegram_username']}"
                    )
                    return False
                else:
                    print("✅ Username field correctly filtered")

                if "telegram_language_code" in metadata:
                    print(
                        f"❌ Language code field should not exist: {metadata['telegram_language_code']}"
                    )
                    return False
                else:
                    print("✅ Language code field correctly filtered")

                # Verify required fields exist
                if "telegram_id" in metadata and "created_via_telegram" in metadata:
                    print("✅ Required fields exist")
                else:
                    print("❌ Required fields missing")
                    return False

                print("✅ Null value filtering test passed")
                return True

            except Exception as e:
                print(f"❌ Test exception: {e}")
                return False


def run_simple_test():
    """Run simple test"""
    print("🚀 Starting simple Telegram metadata test")

    test_instance = SimpleTelegramMetadataTest()
    test_instance.setUp()

    if test_instance.test_null_values_filtered():
        print("🎉 Simple test passed!")
        return True
    else:
        print("❌ Simple test failed")
        return False


if __name__ == "__main__":
    run_simple_test()
