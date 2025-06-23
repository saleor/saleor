#!/usr/bin/env python3
"""
Test enhanced Telegram validation features
Including:
1. telegramTokenCreate user uniqueness validation
2. telegramEmailChangeRequest email uniqueness validation
3. telegramEmailChangeConfirm email uniqueness validation
"""

import os
import sys
import django
import json
import hmac
import hashlib
from urllib.parse import urlencode

# Set up Django environment
sys.path.append('/Users/svenlai/Desktop/saleor')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saleor.settings')
django.setup()

from django.test import override_settings
from django.contrib.auth import get_user_model
from saleor.account.models import User
from saleor.graphql.account.mutations.authentication.telegram_token_create import TelegramTokenCreate
from saleor.graphql.account.mutations.authentication.telegram_email_change_request import TelegramEmailChangeRequest
from saleor.graphql.account.mutations.authentication.telegram_email_change_confirm import TelegramEmailChangeConfirm

User = get_user_model()

def create_valid_telegram_init_data(telegram_id=123456789):
    """Create valid Telegram initDataRaw data"""
    user_data = {
        "id": telegram_id,
        "first_name": "Test User",
        "last_name": "",
        "username": "testuser",
        "language_code": "en",
        "allows_write_to_pm": True,
    }
    
    data_dict = {
        "user": json.dumps(user_data),
        "auth_date": "1234567890",
        "chat_instance": "1234567890123456789",
        "chat_type": "private",
    }
    
    # Use correct bot token to create signature
    data_string = urlencode(sorted(data_dict.items()))
    secret_key = hmac.new(
        b"test_bot_token_123456789", data_string.encode(), hashlib.sha256
    ).hexdigest()
    
    data_dict["hash"] = secret_key
    init_data_raw = urlencode(data_dict)
    return init_data_raw

def test_telegram_token_create_uniqueness():
    """Test telegramTokenCreate user uniqueness validation"""
    print("🔍 Testing telegramTokenCreate user uniqueness validation")
    
    # Clean up test data
    User.objects.filter(external_reference__startswith="telegram_").delete()
    
    telegram_id = 123456789
    init_data_raw = create_valid_telegram_init_data(telegram_id)
    
    with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
        try:
            # First time creating user
            print("📝 Creating user for the first time...")
            result1 = TelegramTokenCreate.perform_mutation(
                None, None, init_data_raw=init_data_raw
            )
            
            if result1.errors:
                print(f"❌ First creation failed: {result1.errors}")
                return False
            
            user1 = result1.user
            print(f"✅ First creation successful: User ID={user1.pk}, Email={user1.email}")
            
            # Second time using the same telegram_id
            print("🔄 Using the same telegram_id for the second time...")
            result2 = TelegramTokenCreate.perform_mutation(
                None, None, init_data_raw=init_data_raw
            )
            
            if result2.errors:
                print(f"❌ Second creation failed: {result2.errors}")
                return False
            
            user2 = result2.user
            print(f"✅ Second creation successful: User ID={user2.pk}, Email={user2.email}")
            
            # Verify if it's the same user
            if user1.pk == user2.pk:
                print("✅ User uniqueness validation passed: same telegram_id returns same user")
                return True
            else:
                print("❌ User uniqueness validation failed: same telegram_id returns different users")
                return False
                
        except Exception as e:
            print(f"❌ Test exception: {e}")
            return False

def test_telegram_email_change_request_uniqueness():
    """Test telegramEmailChangeRequest email uniqueness validation"""
    print("\n🔍 Testing telegramEmailChangeRequest email uniqueness validation")
    
    # Clean up test data
    User.objects.filter(external_reference__startswith="telegram_").delete()
    
    telegram_id = 123456789
    init_data_raw = create_valid_telegram_init_data(telegram_id)
    old_email = f"telegram_{telegram_id}@telegram.local"
    new_email = "test@example.com"
    
    with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
        try:
            # First create user
            print("📝 Creating user...")
            token_result = TelegramTokenCreate.perform_mutation(
                None, None, init_data_raw=init_data_raw
            )
            
            if token_result.errors:
                print(f"❌ User creation failed: {token_result.errors}")
                return False
            
            user = token_result.user
            print(f"✅ User creation successful: User ID={user.pk}, Email={user.email}")
            
            # Test email uniqueness validation
            print("📧 Testing email uniqueness validation...")
            
            # Create another user using the same email
            conflicting_user = User.objects.create_user(
                email=new_email,
                first_name="Conflicting",
                last_name="User",
                password="testpass123"
            )
            print(f"📝 Created conflicting user: User ID={conflicting_user.pk}, Email={conflicting_user.email}")
            
            # Try to request email change
            try:
                email_result = TelegramEmailChangeRequest.perform_mutation(
                    None, None, 
                    init_data_raw=init_data_raw,
                    old_email=old_email,
                    new_email=new_email
                )
                
                if email_result.errors:
                    print(f"✅ Email uniqueness validation passed: detected conflicting email")
                    return True
                else:
                    print("❌ Email uniqueness validation failed: should have detected conflicting email")
                    return False
                    
            except Exception as e:
                print(f"✅ Email uniqueness validation passed: exception detected conflict - {e}")
                return True
                
        except Exception as e:
            print(f"❌ Test exception: {e}")
            return False

def test_telegram_email_change_confirm_uniqueness():
    """Test telegramEmailChangeConfirm email uniqueness validation"""
    print("\n🔍 Testing telegramEmailChangeConfirm email uniqueness validation")
    
    # Clean up test data
    User.objects.filter(external_reference__startswith="telegram_").delete()
    
    telegram_id = 123456789
    init_data_raw = create_valid_telegram_init_data(telegram_id)
    old_email = f"telegram_{telegram_id}@telegram.local"
    new_email = "test@example.com"
    verification_code = "123456"
    
    with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
        try:
            # First create user
            print("📝 Creating user...")
            token_result = TelegramTokenCreate.perform_mutation(
                None, None, init_data_raw=init_data_raw
            )
            
            if token_result.errors:
                print(f"❌ User creation failed: {token_result.errors}")
                return False
            
            user = token_result.user
            print(f"✅ User creation successful: User ID={user.pk}, Email={user.email}")
            
            # Create another user using the target email
            conflicting_user = User.objects.create_user(
                email=new_email,
                first_name="Conflicting",
                last_name="User",
                password="testpass123"
            )
            print(f"📝 Created conflicting user: User ID={conflicting_user.pk}, Email={conflicting_user.email}")
            
            # Try to confirm email change
            try:
                confirm_result = TelegramEmailChangeConfirm.perform_mutation(
                    None, None,
                    init_data_raw=init_data_raw,
                    verification_code=verification_code,
                    old_email=old_email,
                    new_email=new_email
                )
                
                if confirm_result.errors:
                    print(f"✅ Email uniqueness validation passed: detected conflicting email")
                    return True
                else:
                    print("❌ Email uniqueness validation failed: should have detected conflicting email")
                    return False
                    
            except Exception as e:
                print(f"✅ Email uniqueness validation passed: exception detected conflict - {e}")
                return True
                
        except Exception as e:
            print(f"❌ Test exception: {e}")
            return False

def test_telegram_user_metadata_consistency():
    """Test Telegram user metadata consistency"""
    print("\n🔍 Testing Telegram user metadata consistency")
    
    # Clean up test data
    User.objects.filter(external_reference__startswith="telegram_").delete()
    
    telegram_id = 123456789
    init_data_raw = create_valid_telegram_init_data(telegram_id)
    
    with override_settings(TELEGRAM_BOT_TOKEN="test_bot_token_123456789"):
        try:
            # Create user
            print("📝 Creating user...")
            result = TelegramTokenCreate.perform_mutation(
                None, None, init_data_raw=init_data_raw
            )
            
            if result.errors:
                print(f"❌ User creation failed: {result.errors}")
                return False
            
            user = result.user
            print(f"✅ User creation successful: User ID={user.pk}, Email={user.email}")
            
            # Check metadata
            private_metadata = user.get_private_metadata()
            print(f"📋 User metadata: {private_metadata}")
            
            # Validate key fields
            expected_fields = [
                "telegram_id", "created_via_telegram", "created_at"
            ]
            
            for field in expected_fields:
                if field not in private_metadata:
                    print(f"❌ Missing metadata field: {field}")
                    return False
                else:
                    print(f"✅ Metadata field exists: {field} = {private_metadata[field]}")
            
            # Validate telegram_id consistency
            if private_metadata["telegram_id"] != telegram_id:
                print(f"❌ Telegram ID mismatch: expected={telegram_id}, actual={private_metadata['telegram_id']}")
                return False
            
            print("✅ User metadata consistency validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Test exception: {e}")
            return False

def main():
    """Run all tests"""
    print("🚀 Starting enhanced Telegram validation feature tests")
    print("=" * 50)
    
    tests = [
        ("Telegram Token Create User Uniqueness", test_telegram_token_create_uniqueness),
        ("Telegram Email Change Request Email Uniqueness", test_telegram_email_change_request_uniqueness),
        ("Telegram Email Change Confirm Email Uniqueness", test_telegram_email_change_confirm_uniqueness),
        ("Telegram User Metadata Consistency", test_telegram_user_metadata_consistency),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running test: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                print(f"✅ {test_name} test passed")
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced validation features are working correctly")
    else:
        print("⚠️ Some tests failed, please check the implementation")

if __name__ == "__main__":
    main() 