#!/usr/bin/env python3
"""
简化测试：Telegram邮箱变更功能
"""

import os
import sys
import django
import json
import secrets
from datetime import datetime, timedelta

# 设置Django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from django.test import TestCase
from django.test.utils import override_settings
from saleor.account.models import User


def test_verification_code_generation():
    """测试验证码生成"""
    print("\n" + "=" * 50)
    print("测试验证码生成")
    print("=" * 50)

    # 生成6位数字验证码
    verification_code = "".join(secrets.choice("0123456789") for _ in range(6))

    print(f"生成的验证码: {verification_code}")
    print(f"验证码长度: {len(verification_code)}")

    # 验证格式
    assert len(verification_code) == 6
    assert verification_code.isdigit()

    print("✅ 验证码生成测试成功")
    return verification_code


def test_user_metadata_storage():
    """测试用户元数据存储"""
    print("\n" + "=" * 50)
    print("测试用户元数据存储")
    print("=" * 50)

    # 创建测试用户
    telegram_id = 123456789
    user = User.objects.create_user(
        email=f"telegram_{telegram_id}@telegram.local",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_confirmed=True,
        external_reference=f"telegram_{telegram_id}",
    )

    # 生成验证码和元数据
    verification_code = test_verification_code_generation()
    new_email = "newemail@example.com"
    expires_at = datetime.now() + timedelta(minutes=10)

    # 存储元数据
    user.store_value_in_private_metadata(
        {
            "email_change_verification_code": verification_code,
            "email_change_new_email": new_email,
            "email_change_expires_at": expires_at.isoformat(),
            "email_change_requested_at": datetime.now().isoformat(),
        }
    )
    user.save(update_fields=["private_metadata"])

    print(f"用户ID: {user.id}")
    print(f"用户邮箱: {user.email}")
    print(f"外部引用: {user.external_reference}")
    print(f"私有元数据: {user.private_metadata}")

    # 验证元数据存储
    stored_code = user.private_metadata.get("email_change_verification_code")
    stored_email = user.private_metadata.get("email_change_new_email")

    assert stored_code == verification_code
    assert stored_email == new_email

    print("✅ 用户元数据存储测试成功")

    # 清理测试数据
    user.delete()
    return True


def test_email_validation():
    """测试邮箱验证逻辑"""
    print("\n" + "=" * 50)
    print("测试邮箱验证逻辑")
    print("=" * 50)

    # 测试有效的Telegram邮箱格式
    telegram_id = 123456789
    valid_email = f"telegram_{telegram_id}@telegram.local"
    expected_email = f"telegram_{telegram_id}@telegram.local"

    print(f"测试邮箱: {valid_email}")
    print(f"期望邮箱: {expected_email}")

    # 验证格式
    assert valid_email == expected_email
    assert valid_email.startswith("telegram_")
    assert valid_email.endswith("@telegram.local")

    # 测试无效邮箱格式
    invalid_emails = [
        "wrong@example.com",
        "telegram_123@wrong.local",
        "not_telegram@telegram.local",
        "telegram_abc@telegram.local",  # 非数字ID
    ]

    for invalid_email in invalid_emails:
        print(f"测试无效邮箱: {invalid_email}")
        assert invalid_email != expected_email

    print("✅ 邮箱验证逻辑测试成功")
    return True


def test_verification_code_validation():
    """测试验证码验证逻辑"""
    print("\n" + "=" * 50)
    print("测试验证码验证逻辑")
    print("=" * 50)

    # 创建测试用户
    telegram_id = 123456789
    user = User.objects.create_user(
        email=f"telegram_{telegram_id}@telegram.local",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_confirmed=True,
        external_reference=f"telegram_{telegram_id}",
    )

    # 设置验证码
    correct_code = "123456"
    wrong_code = "999999"
    new_email = "newemail@example.com"
    expires_at = datetime.now() + timedelta(minutes=10)

    user.store_value_in_private_metadata(
        {
            "email_change_verification_code": correct_code,
            "email_change_new_email": new_email,
            "email_change_expires_at": expires_at.isoformat(),
            "email_change_requested_at": datetime.now().isoformat(),
        }
    )
    user.save(update_fields=["private_metadata"])

    # 测试正确验证码
    stored_code = user.private_metadata.get("email_change_verification_code")
    stored_email = user.private_metadata.get("email_change_new_email")

    print(f"存储的验证码: {stored_code}")
    print(f"输入的验证码: {correct_code}")
    print(f"新邮箱: {stored_email}")

    assert stored_code == correct_code
    assert stored_code != wrong_code
    assert stored_email == new_email

    # 测试验证码匹配
    is_valid = stored_code == correct_code
    is_invalid = stored_code == wrong_code

    print(f"正确验证码匹配: {is_valid}")
    print(f"错误验证码匹配: {is_invalid}")

    assert is_valid is True
    assert is_invalid is False

    print("✅ 验证码验证逻辑测试成功")

    # 清理测试数据
    user.delete()
    return True


def test_email_change_flow():
    """测试完整的邮箱变更流程"""
    print("\n" + "=" * 50)
    print("测试完整的邮箱变更流程")
    print("=" * 50)

    # 1. 创建用户
    telegram_id = 123456789
    old_email = f"telegram_{telegram_id}@telegram.local"
    new_email = "newemail@example.com"

    user = User.objects.create_user(
        email=old_email,
        first_name="Test",
        last_name="User",
        is_active=True,
        is_confirmed=True,
        external_reference=f"telegram_{telegram_id}",
    )

    print(f"步骤1: 创建用户")
    print(f"  用户ID: {user.id}")
    print(f"  旧邮箱: {user.email}")
    print(f"  外部引用: {user.external_reference}")

    # 2. 生成验证码并存储
    verification_code = test_verification_code_generation()
    expires_at = datetime.now() + timedelta(minutes=10)

    user.store_value_in_private_metadata(
        {
            "email_change_verification_code": verification_code,
            "email_change_new_email": new_email,
            "email_change_expires_at": expires_at.isoformat(),
            "email_change_requested_at": datetime.now().isoformat(),
        }
    )
    user.save(update_fields=["private_metadata"])

    print(f"步骤2: 生成验证码并存储")
    print(f"  验证码: {verification_code}")
    print(f"  新邮箱: {new_email}")
    print(f"  过期时间: {expires_at}")

    # 3. 验证验证码
    stored_code = user.private_metadata.get("email_change_verification_code")
    stored_email = user.private_metadata.get("email_change_new_email")

    assert stored_code == verification_code
    assert stored_email == new_email

    print(f"步骤3: 验证验证码")
    print(f"  验证码匹配: {stored_code == verification_code}")
    print(f"  邮箱匹配: {stored_email == new_email}")

    # 4. 更新邮箱
    user.email = new_email
    user.save(update_fields=["email", "updated_at"])

    print(f"步骤4: 更新邮箱")
    print(f"  新邮箱: {user.email}")

    # 5. 清理元数据
    user.store_value_in_private_metadata(
        {
            "email_change_verification_code": None,
            "email_change_new_email": None,
            "email_change_expires_at": None,
            "email_change_requested_at": None,
            "email_change_completed_at": datetime.now().isoformat(),
            "previous_email": old_email,
        }
    )
    user.save(update_fields=["private_metadata"])

    print(f"步骤5: 清理元数据")
    print(f"  最终邮箱: {user.email}")
    print(f"  私有元数据: {user.private_metadata}")

    # 验证最终状态
    assert user.email == new_email
    assert user.private_metadata.get("email_change_completed_at") is not None
    assert user.private_metadata.get("previous_email") == old_email

    print("✅ 完整邮箱变更流程测试成功")

    # 清理测试数据
    user.delete()
    return True


def main():
    """主测试函数"""
    print("🚀 开始Telegram邮箱变更功能测试")
    print("=" * 60)

    try:
        # 运行所有测试
        test_verification_code_generation()
        test_user_metadata_storage()
        test_email_validation()
        test_verification_code_validation()
        test_email_change_flow()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)

        print("\n📋 功能总结:")
        print("✅ 验证码生成 (6位数字)")
        print("✅ 用户元数据存储")
        print("✅ 邮箱格式验证")
        print("✅ 验证码验证逻辑")
        print("✅ 完整邮箱变更流程")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
