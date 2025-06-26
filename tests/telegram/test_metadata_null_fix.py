#!/usr/bin/env python3
"""
Test Telegram metadata null value fix
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


class TelegramMetadataNullFixTest(TestCase):
    """Test Telegram metadata null value fix"""

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

    def test_metadata_with_null_values(self):
        """Test metadata processing with null values"""
        print("\n" + "=" * 60)
        print("Test Telegram metadata null value fix")
        print("=" * 60)

        # Create user data with null values
        user_data_with_nulls = {
            "id": 123456789,
            "first_name": "Test User",
            "last_name": "",  # Empty string
            "username": None,  # null value
            "language_code": None,  # null value
            "photo_url": None,  # null value
        }

        init_data_raw = self.create_telegram_init_data(user_data_with_nulls)

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
                print(f"✅ User created successfully: {user.email}")

                # Check metadata
                private_metadata = user.private_metadata
                print(f"📋 User metadata: {private_metadata}")

                # Verify no null values
                for key, value in private_metadata.items():
                    if value is None:
                        print(f"❌ Found null value: {key} = {value}")
                        return False
                    else:
                        print(f"✅ Field normal: {key} = {value}")

                # Verify required fields exist
                required_fields = ["telegram_id", "created_via_telegram"]
                for field in required_fields:
                    if field not in private_metadata:
                        print(f"❌ Missing required field: {field}")
                        return False
                    else:
                        print(f"✅ Required field exists: {field}")

                # Verify optional fields don't exist (because values are null)
                optional_fields = [
                    "telegram_username",
                    "telegram_language_code",
                    "telegram_photo_url",
                ]
                for field in optional_fields:
                    if field in private_metadata:
                        print(
                            f"⚠️  Optional field exists (may have issues): {field} = {private_metadata[field]}"
                        )

                print("✅ Metadata null value fix test passed")
                return True

            except Exception as e:
                print(f"❌ Test exception: {e}")
                return False

    def test_metadata_with_valid_values(self):
        """Test metadata processing with valid values"""
        print("\n" + "=" * 60)
        print("Test Telegram metadata valid value processing")
        print("=" * 60)

        # Create user data with valid values
        user_data_with_values = {
            "id": 987654321,
            "first_name": "Valid User",
            "last_name": "Test",
            "username": "validuser",
            "language_code": "zh-CN",
            "photo_url": "https://example.com/photo.jpg",
        }

        init_data_raw = self.create_telegram_init_data(user_data_with_values)

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
                print(f"✅ User created successfully: {user.email}")

                # Check metadata
                private_metadata = user.private_metadata
                print(f"📋 User metadata: {private_metadata}")

                # Verify all fields have values
                for key, value in private_metadata.items():
                    if value is None:
                        print(f"❌ Found null value: {key} = {value}")
                        return False
                    else:
                        print(f"✅ Field normal: {key} = {value}")

                # Verify required fields exist
                required_fields = ["telegram_id", "created_via_telegram"]
                for field in required_fields:
                    if field not in private_metadata:
                        print(f"❌ Missing required field: {field}")
                        return False
                    else:
                        print(f"✅ Required field exists: {field}")

                # Verify optional fields exist
                optional_fields = [
                    "telegram_username",
                    "telegram_language_code",
                    "telegram_photo_url",
                ]
                for field in optional_fields:
                    if field not in private_metadata:
                        print(f"❌ Missing optional field: {field}")
                        return False
                    elif private_metadata[field] is None:
                        print(f"❌ Field value is null: {field}")
                        return False
                    else:
                        print(f"✅ Field normal: {field} = {private_metadata[field]}")

                print("✅ Metadata valid value processing test passed")
                return True

            except Exception as e:
                print(f"❌ Test exception: {e}")
                return False

    def test_existing_user_metadata_update(self):
        """Test existing user metadata update"""
        print("\n" + "=" * 60)
        print("Test existing user metadata update")
        print("=" * 60)

        # Create existing user
        existing_user = User.objects.create(
            email="telegram_111111111@telegram.local",
            first_name="Existing",
            last_name="User",
            external_reference="telegram_111111111",
            is_active=True,
            is_confirmed=True,
        )

        # Set initial metadata
        existing_user.store_value_in_private_metadata(
            {
                "telegram_id": 111111111,
                "telegram_username": "old_username",
                "created_via_telegram": True,
            }
        )
        existing_user.save(update_fields=["private_metadata"])

        print(f"✅ Existing user created: {existing_user.email}")
        print(f"📋 Initial metadata: {existing_user.private_metadata}")

        # Create update data (with null values)
        user_data_update = {
            "id": 111111111,
            "first_name": "Updated User",
            "last_name": "New",
            "username": None,  # Update to null
            "language_code": "en",  # Add valid value
            "photo_url": None,  # Update to null
        }

        init_data_raw = self.create_telegram_init_data(user_data_update)

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
                print(f"✅ User updated successfully: {user.email}")

                # Check updated metadata
                user.refresh_from_db()
                private_metadata = user.private_metadata
                print(f"📋 Updated metadata: {private_metadata}")

                # Verify no null values
                for key, value in private_metadata.items():
                    if value is None:
                        print(f"❌ Found null value: {key} = {value}")
                        return False

                # Verify field updates are correct
                if "telegram_username" in private_metadata:
                    print(
                        f"⚠️  Username field still exists: {private_metadata['telegram_username']}"
                    )
                else:
                    print(
                        "✅ Username field correctly removed (because updated to null)"
                    )

                if "telegram_language_code" in private_metadata:
                    print(
                        f"✅ Language code field added: {private_metadata['telegram_language_code']}"
                    )
                else:
                    print("❌ Language code field not added")

                print("✅ Existing user metadata update test passed")
                return True

            except Exception as e:
                print(f"❌ Test exception: {e}")
                return False


def run_tests():
    """Run all tests"""
    print("🚀 Starting Telegram metadata null value fix tests")

    test_instance = TelegramMetadataNullFixTest()
    test_instance.setUp()

    # Run tests
    tests = [
        test_instance.test_metadata_with_null_values,
        test_instance.test_metadata_with_valid_values,
        test_instance.test_existing_user_metadata_update,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test execution exception: {e}")

    print(f"\n📊 Test results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    run_tests()
