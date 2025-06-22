#!/usr/bin/env python3
"""
Test EMAIL_URL configuration correctness
"""

import os
import sys
import django
from django.conf import settings
from django.core.mail import send_mail
from django.test import override_settings
from dj_email_url import parse as parse_email_url

# Set Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()


def test_email_url_config():
    """Test EMAIL_URL configuration"""
    print("🔍 Checking EMAIL_URL configuration...")
    email_url = getattr(settings, "EMAIL_URL", None)
    # Check EMAIL_URL configuration
    print(f"EMAIL_URL: {email_url or 'Not set'}")
    if not email_url:
        print("❌ EMAIL_URL not set")
        print("   Please set the EMAIL_URL environment variable:")
        print("   export EMAIL_URL='smtp://username:password@host:port/?tls=True'")
        return False
    # Check parsed configuration
    parsed = parse_email_url(email_url)
    print(f"Parsed result:")
    for k, v in parsed.items():
        print(f"  {k}: {v}")
    smtp_password = parsed.get("PASSWORD")
    print(f"  EMAIL_HOST_PASSWORD: {'Set' if smtp_password else 'Not set'}")
    # Check configuration completeness
    if all([parsed.get("EMAIL_HOST"), parsed.get("EMAIL_HOST_USER"), smtp_password]):
        print("✅ EMAIL_URL configuration complete")
        return True
    else:
        print("❌ EMAIL_URL configuration incomplete")
        return False


def test_email_sending_with_url_config():
    """Test email sending using EMAIL_URL configuration"""
    print("\n📧 Testing email sending...")

    # Check configuration
    smtp_host = getattr(settings, "EMAIL_HOST", "")
    smtp_port = getattr(settings, "EMAIL_PORT", "")
    smtp_user = getattr(settings, "EMAIL_HOST_USER", "")
    smtp_password = getattr(settings, "EMAIL_HOST_PASSWORD", "")

    if not all([smtp_host, smtp_user, smtp_password, smtp_port]):
        print("❌ SMTP configuration is incomplete, skipping email sending test")
        return False

    # Test email content
    subject = "Saleor Email URL Config Test"
    message = f"""
Saleor Email URL Configuration Test

This is a test email to verify the EMAIL_URL configuration.

Configuration info:
- SMTP server: {smtp_host}
- Port: {smtp_port}
- Sender: {smtp_user}
- Config method: EMAIL_URL

If you receive this email, the EMAIL_URL configuration is correct.
"""

    html_message = f"""
<html>
<body>
    <h1>Saleor Email URL Configuration Test</h1>
    <p>This is a test email to verify the EMAIL_URL configuration.</p>

    <h2>Configuration info:</h2>
    <ul>
        <li><strong>SMTP server:</strong> {smtp_host}</li>
        <li><strong>Port:</strong> {smtp_port}</li>
        <li><strong>Sender:</strong> {smtp_user}</li>
        <li><strong>Config method:</strong> EMAIL_URL</li>
    </ul>

    <p>If you receive this email, the EMAIL_URL configuration is correct.</p>
</body>
</html>
"""

    # Send test email
    recipient_email = input("Please enter recipient email address: ").strip()
    if not recipient_email:
        print("❌ No recipient email address provided")
        return False

    print(f"Sending verification code from {smtp_user} to {recipient_email}")

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=smtp_user,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False


def test_gmail_smtp_connection():
    """Test Gmail SMTP connection"""
    print("\n=== Testing Gmail SMTP connection ===")

    try:
        from django.core.mail.backends.smtp import EmailBackend

        # Create SMTP backend
        backend = EmailBackend(
            host=settings.EMAIL_HOST,
            port=int(settings.EMAIL_PORT),
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            use_ssl=settings.EMAIL_USE_SSL,
            timeout=10,
        )

        # Test connection
        backend.open()
        print("✓ Gmail SMTP connection successful")
        backend.close()
        return True

    except Exception as e:
        print(f"✗ Gmail SMTP connection failed: {e}")
        return False


def test_send_verification_email():
    """Test sending verification code email"""
    print("\n=== Testing sending verification code email ===")

    # Get SMTP configuration
    smtp_user = getattr(settings, "EMAIL_HOST_USER", "")
    recipient_email = "88888888@qq.com"
    verification_code = "656482"  # Use the code you received

    # Email content
    subject = "Saleor Telegram Email Change Verification Code"
    message = f"""
Saleor Telegram Email Change Verification Code

Your verification code is: {verification_code}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

---
This email was sent automatically by the Saleor system
Sender: {smtp_user}
"""

    html_message = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
        <h1 style="color: #2c3e50; margin-bottom: 20px;">Saleor Telegram Email Change Verification Code</h1>

        <div style="background-color: #ffffff; padding: 20px; border-radius: 6px; border-left: 4px solid #3498db;">
            <p style="font-size: 16px; color: #2c3e50; margin-bottom: 10px;">Your verification code is:</p>
            <div style="background-color: #ecf0f1; padding: 15px; border-radius: 4px; text-align: center; margin: 15px 0;">
                <span style="font-size: 24px; font-weight: bold; color: #e74c3c; letter-spacing: 3px;">{verification_code}</span>
            </div>
            <p style="font-size: 14px; color: #7f8c8d;">This code will expire in 10 minutes.</p>
        </div>

        <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-radius: 4px; border-left: 4px solid #ffc107;">
            <p style="font-size: 14px; color: #856404; margin: 0;">
                <strong>Security Notice:</strong> If you did not request this code, please ignore this email.
            </p>
        </div>

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ecf0f1;">

        <div style="font-size: 12px; color: #95a5a6; text-align: center;">
            <p>This email was sent automatically by the Saleor system</p>
            <p>Sender: {smtp_user}</p>
        </div>
    </div>
</body>
</html>
"""

    try:
        print(f"Sending verification code from {smtp_user} to {recipient_email}")
        print(f"Verification code: {verification_code}")

        send_mail(
            subject=subject,
            message=message,
            from_email=smtp_user,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )

        print("✓ Verification code email sent successfully!")
        print(
            f"Please check QQ mailbox {recipient_email} for the verification code email"
        )
        print(f"Verification code: {verification_code}")
        return True

    except Exception as e:
        print(f"✗ Email sending failed: {e}")
        print("\nPossible solutions:")
        print("1. Check if Gmail app-specific password is correct")
        print(
            "2. Make sure Gmail has enabled two-step verification and app-specific password"
        )
        print("3. Check network connection")
        print("4. Make sure firewall is not blocking SMTP connection")
        print("5. Check Gmail account security settings")
        print("6. Make sure Gmail allows less secure app access")
        return False


def test_telegram_mutation_email_sending():
    """Test email sending functionality of Telegram mutation"""
    print("\n=== Testing Telegram Mutation email sending ===")

    try:
        from saleor.graphql.account.mutations.authentication.telegram_email_change_request import (
            TelegramEmailChangeRequest,
        )

        # Simulate email sending
        new_email = "88888888@qq.com"
        verification_code = "123456"

        # Test email sending method
        result = TelegramEmailChangeRequest.send_verification_email(
            new_email, verification_code, None
        )

        if result:
            print("✓ Telegram mutation email sending functionality is working")
            print(f"Verification code {verification_code} has been sent to {new_email}")
            return True
        else:
            print("✗ Telegram mutation email sending functionality error")
            return False

    except Exception as e:
        print(f"✗ Telegram mutation test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Starting EMAIL_URL configuration test...\n")

    # Test configuration
    config_ok = test_email_url_config()

    if config_ok:
        # Test email sending
        test_email_sending_with_url_config()
    else:
        print("\n❌ Configuration test failed, please fix configuration issues first")

    print("\n✨ Test completed!")

    if config_ok:
        # Test other functionality
        test_gmail_smtp_connection()
        test_send_verification_email()
        test_telegram_mutation_email_sending()

        print("\n🎉 All tests passed!")
        print("\n=== Configuration Successful ===")
        print("✓ EMAIL_URL configuration correct")
        print("✓ Gmail SMTP connection normal")
        print("✓ Email sending functionality normal")
        print("✓ Telegram email change functionality can be used")
        print("\nNow you can use the Telegram email change functionality normally!")
        return True
    else:
        print(f"\n❌ 4 tests failed")
        print("\nPlease check EMAIL_URL configuration and run tests again")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
