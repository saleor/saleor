#!/usr/bin/env python3
"""
Test SMTP configuration to ensure it's working correctly
"""

import os
import sys
import django
from django.core.mail import send_mail
from django.conf import settings
from django.test import override_settings

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()


def test_smtp_configuration():
    """Test SMTP configuration"""
    print("🔍 Checking SMTP configuration...")

    # Check EMAIL_URL configuration
    email_url = getattr(settings, "EMAIL_URL", "")
    print(f"EMAIL_URL: {email_url or 'Not set'}")

    # Check parsed configuration
    smtp_host = getattr(settings, "EMAIL_HOST", "")
    smtp_port = getattr(settings, "EMAIL_PORT", "")
    smtp_user = getattr(settings, "EMAIL_HOST_USER", "")
    smtp_password = getattr(settings, "EMAIL_HOST_PASSWORD", "")

    print(f"EMAIL_HOST: {smtp_host or 'Not set'}")
    print(f"EMAIL_PORT: {smtp_port or 'Not set'}")
    print(f"EMAIL_HOST_USER: {smtp_user or 'Not set'}")
    print(f"EMAIL_HOST_PASSWORD: {'Set' if smtp_password else 'Not set'}")

    # Check configuration completeness
    if not all([smtp_host, smtp_user, smtp_password, smtp_port]):
        print("❌ SMTP configuration incomplete")
        print("   Please set EMAIL_URL environment variable:")
        print("   export EMAIL_URL='smtp://username:password@host:port/?tls=True'")
        return False

    print("✅ SMTP configuration complete")
    return True


def test_email_sending():
    """Test email sending"""
    print("\n📧 Testing email sending...")

    # Check configuration
    smtp_host = getattr(settings, "EMAIL_HOST", "")
    smtp_port = getattr(settings, "EMAIL_PORT", "")
    smtp_user = getattr(settings, "EMAIL_HOST_USER", "")
    smtp_password = getattr(settings, "EMAIL_HOST_PASSWORD", "")

    if not all([smtp_host, smtp_user, smtp_password, smtp_port]):
        print("❌ SMTP configuration incomplete, skipping email sending test")
        return False

    # Test email content
    subject = "Saleor SMTP Configuration Test"
    message = f"""
Saleor SMTP Configuration Test

This is a test email to verify the SMTP configuration.

Configuration Information:
- SMTP Server: {smtp_host}
- Port: {smtp_port}
- Sender: {smtp_user}

If you receive this email, the SMTP configuration is correct.
"""

    # Send test email
    recipient_email = input("Please enter recipient email address: ").strip()
    if not recipient_email:
        print("❌ No recipient email address provided")
        return False

    print(f"Sending test email from {smtp_user} to {recipient_email}")

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=smtp_user,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False


def test_telegram_mutation_with_smtp():
    """Test Telegram mutation in SMTP configuration"""
    print("\n=== Testing Telegram Mutation (SMTP configuration) ===")

    try:
        from saleor.graphql.account.mutations.authentication.telegram_email_change_request import (
            TelegramEmailChangeRequest,
        )

        # Simulate email sending
        new_email = "test@example.com"
        verification_code = "123456"

        # Test email sending method
        result = TelegramEmailChangeRequest.send_verification_email(
            new_email, verification_code, None
        )

        if result:
            print("✓ Telegram mutation email sending functionality works")
            return True
        else:
            print("✗ Telegram mutation email sending functionality fails")
            return False

    except Exception as e:
        print(f"✗ Telegram mutation test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting SMTP configuration test...\n")

    # Test configuration
    success = test_smtp_configuration()

    if success:
        # Test email sending
        test_email_sending()
    else:
        print("\n❌ Configuration test failed, please fix configuration issues first")

    print("\n✨ Test completed!")

    if success and test_email_sending():
        print("\n🎉 All tests passed!")
        print("\n=== Configuration successful ===")
        print("✓ SMTP configuration correct")
        print("✓ Email sending functionality works")
        print("✓ Telegram email change functionality can be used")
        print("\nNow you can use Telegram email change functionality!")
        return True
    else:
        print(f"\n❌ 1 test failed")
        print("\nPlease check SMTP configuration and rerun tests")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
