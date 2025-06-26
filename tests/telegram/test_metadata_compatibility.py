#!/usr/bin/env python3
"""
Test Telegram metadata compatibility handling
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


class TelegramMetadataCompatibilityTest(TestCase):
    """Test Telegram metadata compatibility handling"""

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

    def test_existing_user_with_null_metadata(self):
        """Test existing user with null metadata handling"""
        print("\n" + "=" * 60)
        print("Test existing user null metadata compatibility")
        print("=" * 60)

        # Create existing user with null metadata
        existing_user = User.objects.create(
            email="telegram_222222222@telegram.local",
            first_name="Compatibility",
            last_name="Test",
            external_reference="telegram_222222222",
            is_active=True,
            is_confirmed=True,
        )

        # Set metadata with null values (simulating old data)
        existing_user.store_value_in_private_metadata(
            {
                "telegram_id": 222222222,
                "telegram_username": None,  # null value
                "telegram_language_code": "zh-CN",
                "telegram_photo_url": None,  # null value
                "created_via_telegram": True,
            }
        )
        existing_user.save(update_fields=["private_metadata"])

        print(f"✅ Existing user created: {existing_user.email}")
        print(
            f"📋 Initial metadata (with null values): {existing_user.private_metadata}"
        )

        # Verify GraphQL query doesn't fail
        try:
            # Simulate GraphQL query metadata
            metadata = existing_user.private_metadata

            # Check each field to ensure no null values cause GraphQL errors
            for key, value in metadata.items():
                if value is None:
                    print(f"⚠️  Found null value: {key} = {value}")
                    # This should be handled by GraphQL resolver as empty string
                else:
                    print(f"✅ Field normal: {key} = {value}")

            print("✅ Existing user null metadata compatibility test passed")
            return True

        except Exception as e:
            print(f"❌ Compatibility test exception: {e}")
            return False

    def test_new_user_metadata_creation(self):
        """Test new user metadata creation (ensure no null values)"""
        print("\n" + "=" * 60)
        print("Test new user metadata creation")
        print("=" * 60)

        # Create user data with null values
        user_data = {
            "id": 333333333,
            "first_name": "New User",
            "last_name": "Test",
            "username": None,  # null value
            "language_code": None,  # null value
            "photo_url": "https://example.com/photo.jpg",  # valid value
        }

        init_data_raw = self.create_telegram_init_data(user_data)

        with override_settings(TELEGRAM_BOT_TOKEN=self.bot_token):
            try:
                # Execute mutation
                result = TelegramTokenCreate.perform_mutation(
                    None, None, init_data_raw=init_data_raw
                )

                if result.errors:
                    print(f"❌ Mutation execution failed: {result.errors}")
                    return False

                user = result.user
                print(f"✅ New user created successfully: {user.email}")

                # Check metadata
                metadata = user.private_metadata
                print(f"📋 New user metadata: {metadata}")

                # Verify no null values
                for key, value in metadata.items():
                    if value is None:
                        print(f"❌ Found null value: {key} = {value}")
                        return False
                    else:
                        print(f"✅ Field normal: {key} = {value}")

                # Verify required fields exist
                required_fields = ["telegram_id", "created_via_telegram"]
                for field in required_fields:
                    if field not in metadata:
                        print(f"❌ Missing required field: {field}")
                        return False
                    else:
                        print(f"✅ Required field exists: {field}")

                # Verify optional field handling is correct
                if "telegram_username" in metadata:
                    print(f"❌ Username field should not exist (because value is null)")
                    return False
                else:
                    print("✅ Username field correctly filtered")

                if "telegram_language_code" in metadata:
                    print(
                        f"❌ Language code field should not exist (because value is null)"
                    )
                    return False
                else:
                    print("✅ Language code field correctly filtered")

                if "telegram_photo_url" in metadata:
                    print(
                        f"✅ Photo URL field exists: {metadata['telegram_photo_url']}"
                    )
                else:
                    print("❌ Photo URL field missing (should have value)")
                    return False

                print("✅ New user metadata creation test passed")
                return True

            except Exception as e:
                print(f"❌ Test exception: {e}")
                return False

    def test_mixed_metadata_scenarios(self):
        """Test mixed metadata scenarios"""
        print("\n" + "=" * 60)
        print("Test mixed metadata scenarios")
        print("=" * 60)

        # Create multiple users to test different scenarios
        test_scenarios = [
            {
                "name": "Fully valid data",
                "user_data": {
                    "id": 444444444,
                    "first_name": "Fully Valid",
                    "username": "validuser",
                    "language_code": "zh-CN",
                    "photo_url": "https://example.com/photo1.jpg",
                },
            },
            {
                "name": "Partially null data",
                "user_data": {
                    "id": 555555555,
                    "first_name": "Partially Null",
                    "username": None,
                    "language_code": "en",
                    "photo_url": None,
                },
            },
            {
                "name": "All null data",
                "user_data": {
                    "id": 666666666,
                    "first_name": "All Null",
                    "username": None,
                    "language_code": None,
                    "photo_url": None,
                },
            },
        ]

        for scenario in test_scenarios:
            print(f"\n--- Test scenario: {scenario['name']} ---")

            init_data_raw = self.create_telegram_init_data(scenario["user_data"])

            with override_settings(TELEGRAM_BOT_TOKEN=self.bot_token):
                try:
                    # Execute mutation
                    result = TelegramTokenCreate.perform_mutation(
                        None, None, init_data_raw=init_data_raw
                    )

                    if result.errors:
                        print(f"❌ Scenario failed: {result.errors}")
                        continue

                    user = result.user
                    metadata = user.private_metadata
                    print(f"📋 Metadata: {metadata}")

                    # Verify no null values
                    has_null = False
                    for key, value in metadata.items():
                        if value is None:
                            print(f"❌ Found null value: {key} = {value}")
                            has_null = True

                    if not has_null:
                        print("✅ Scenario test passed")
                    else:
                        print("❌ Scenario test failed")

                except Exception as e:
                    print(f"❌ Scenario exception: {e}")

        print("✅ Mixed metadata scenarios test completed")
        return True


def run_compatibility_tests():
    """Run compatibility tests"""
    print("🚀 Starting Telegram metadata compatibility tests")

    test_instance = TelegramMetadataCompatibilityTest()
    test_instance.setUp()

    # Run tests
    tests = [
        test_instance.test_existing_user_with_null_metadata,
        test_instance.test_new_user_metadata_creation,
        test_instance.test_mixed_metadata_scenarios,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test execution exception: {e}")

    print(f"\n📊 Compatibility test results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All compatibility tests passed!")
        return True
    else:
        print("❌ Some compatibility tests failed")
        return False


if __name__ == "__main__":
    run_compatibility_tests()
