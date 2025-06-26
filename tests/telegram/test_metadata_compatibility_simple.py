#!/usr/bin/env python3
"""
Simple test for Telegram metadata compatibility handling
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from django.test import TestCase
from saleor.account.models import User
from saleor.graphql.meta.resolvers import resolve_metadata


class SimpleMetadataCompatibilityTest(TestCase):
    """Simple metadata compatibility test"""

    def test_resolve_metadata_null_handling(self):
        """Test resolve_metadata handling null values"""
        print("\n" + "=" * 50)
        print("Test null value handling")
        print("=" * 50)

        # Create metadata with null values
        metadata_with_nulls = {
            "telegram_id": 123456789,
            "telegram_username": None,  # null value
            "telegram_language_code": "zh-CN",
            "telegram_photo_url": None,  # null value
            "created_via_telegram": True,
        }

        print(f"📋 Original metadata: {metadata_with_nulls}")

        # Use resolve_metadata to process
        result = resolve_metadata(metadata_with_nulls)
        print(f"📋 Processed metadata: {result}")

        # Verify result
        if not result:
            print("❌ Processing result is empty")
            return False

        # Verify no None values
        for item in result:
            if item["value"] is None:
                print(f"❌ Found None value: {item}")
                return False
            else:
                print(f"✅ Field normal: {item['key']} = {item['value']}")

        # Verify null values are converted to empty strings
        for item in result:
            if item["key"] in ["telegram_username", "telegram_photo_url"]:
                if item["value"] != "":
                    print(
                        f"❌ Null value not correctly converted: {item['key']} = {item['value']}"
                    )
                    return False
                else:
                    print(
                        f"✅ Null value correctly converted to empty string: {item['key']}"
                    )

        print("✅ Null value handling test passed")
        return True

    def test_resolve_metadata_valid_values(self):
        """Test resolve_metadata handling valid values"""
        print("\n" + "=" * 50)
        print("Test valid value handling")
        print("=" * 50)

        # Create metadata with valid values
        metadata_with_values = {
            "telegram_id": 987654321,
            "telegram_username": "validuser",
            "telegram_language_code": "zh-CN",
            "telegram_photo_url": "https://example.com/photo.jpg",
            "created_via_telegram": True,
        }

        print(f"📋 Original metadata: {metadata_with_values}")

        # Use resolve_metadata to process
        result = resolve_metadata(metadata_with_values)
        print(f"📋 Processed metadata: {result}")

        # Verify result
        if not result:
            print("❌ Processing result is empty")
            return False

        # Verify all values are correctly preserved
        expected_items = {
            "telegram_id": "987654321",
            "telegram_username": "validuser",
            "telegram_language_code": "zh-CN",
            "telegram_photo_url": "https://example.com/photo.jpg",
            "created_via_telegram": "True",
        }

        for item in result:
            key = item["key"]
            value = item["value"]
            if key in expected_items:
                if str(value) != expected_items[key]:
                    print(
                        f"❌ Value mismatch: {key}, expected: {expected_items[key]}, actual: {value}"
                    )
                    return False
                else:
                    print(f"✅ Value correct: {key} = {value}")
            else:
                print(f"⚠️  Unexpected field: {key} = {value}")

        print("✅ Valid value handling test passed")
        return True

    def test_user_with_null_metadata(self):
        """Test user with null metadata"""
        print("\n" + "=" * 50)
        print("Test user null metadata")
        print("=" * 50)

        # Create user
        user = User.objects.create(
            email="test_null@example.com",
            first_name="Test",
            last_name="User",
            is_active=True,
            is_confirmed=True,
        )

        # Set metadata with null values (simulating pre-fix data)
        user.store_value_in_private_metadata(
            {
                "telegram_id": 123456789,
                "telegram_username": None,  # null value
                "telegram_language_code": "zh-CN",
                "telegram_photo_url": None,  # null value
                "created_via_telegram": True,
            }
        )
        user.save(update_fields=["private_metadata"])

        print(f"✅ User created: {user.email}")
        print(f"📋 Stored metadata: {user.private_metadata}")

        # Simulate GraphQL query processing
        try:
            # Use resolve_metadata to process
            result = resolve_metadata(user.private_metadata)
            print(f"📋 GraphQL processing result: {result}")

            # Verify no None values
            for item in result:
                if item["value"] is None:
                    print(f"❌ Found None value: {item}")
                    return False
                else:
                    print(f"✅ Field normal: {item['key']} = {item['value']}")

            # Verify null values are converted to empty strings
            for item in result:
                if item["key"] in ["telegram_username", "telegram_photo_url"]:
                    if item["value"] != "":
                        print(
                            f"❌ Null value not correctly converted: {item['key']} = {item['value']}"
                        )
                        return False
                    else:
                        print(
                            f"✅ Null value correctly converted to empty string: {item['key']}"
                        )

            print("✅ User null metadata test passed")
            return True

        except Exception as e:
            print(f"❌ Processing exception: {e}")
            return False


def run_simple_compatibility_tests():
    """Run simple compatibility tests"""
    print("🚀 Starting simple metadata compatibility tests")

    test_instance = SimpleMetadataCompatibilityTest()

    # Run tests
    tests = [
        test_instance.test_resolve_metadata_null_handling,
        test_instance.test_resolve_metadata_valid_values,
        test_instance.test_user_with_null_metadata,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test execution exception: {e}")

    print(f"\n📊 Simple compatibility test results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All simple compatibility tests passed!")
        return True
    else:
        print("❌ Some simple compatibility tests failed")
        return False


if __name__ == "__main__":
    run_simple_compatibility_tests()
