#!/usr/bin/env python3
"""
Test Gmail SMTP configuration, send verification code from Gmail to QQ mailbox
"""

import os
import sys
import django
from django.core.mail import send_mail
from django.conf import settings
from django.test import override_settings
from django.utils import timezone

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()


def test_email_configuration():
    """Test email configuration"""
    print("🔍 Checking email configuration...")

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
    if all([smtp_host, smtp_user, smtp_password, smtp_port]):
        print("✅ SMTP configuration complete")

        # Test email sending
        test_email_sending(smtp_user)
    else:
        print("❌ SMTP configuration incomplete")
        print("   Please set the following environment variables:")
        print("   - EMAIL_URL=smtp://username:password@host:port/?tls=True")
        print(
            "   - Or set separately: EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_PORT"
        )
        return False

    return True


def test_email_sending(from_email):
    """Test email sending functionality"""
    print("\n📧 Testing email sending...")

    # Test email parameters
    to_email = "test@example.com"
    subject = "Saleor Email Configuration Test"
    message = f"""
Saleor Email Configuration Test

This is a test email to verify the email configuration.

Configuration Information:
- SMTP Server: {getattr(settings, 'EMAIL_HOST', 'Not set')}
- Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}
- Sender: {from_email}
- Time: {timezone.now()}

If you receive this email, the email configuration is correct.
"""

    html_message = f"""
<html>
<body>
    <h1>Saleor Email Configuration Test</h1>
    <p>This is a test email to verify the email configuration.</p>

    <h2>Configuration Information:</h2>
    <ul>
        <li><strong>SMTP Server:</strong> {getattr(settings, 'EMAIL_HOST', 'Not set')}</li>
        <li><strong>Port:</strong> {getattr(settings, 'EMAIL_PORT', 'Not set')}</li>
        <li><strong>Sender:</strong> {from_email}</li>
        <li><strong>Time:</strong> {timezone.now()}</li>
    </ul>

    <p>If you receive this email, the email configuration is correct.</p>
</body>
</html>
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        print("✅ Email sent successfully")
        print(f"   Recipient: {to_email}")
        print(f"   Subject: {subject}")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        print("   Please check your SMTP configuration")
        return False


def show_configuration_help():
    """Show configuration help information"""
    print("\n📝 Configuration Help:")
    print(
        "To enable email sending functionality, please set the following environment variables:"
    )
    print("")
    print("1. Set EMAIL_URL (recommended):")
    print("   export EMAIL_URL='smtp://username:password@host:port/?tls=True'")
    print("")
    print("2. Or set SMTP parameters separately:")
    print("   export EMAIL_HOST='smtp.gmail.com'")
    print("   export EMAIL_HOST_USER='your-email@gmail.com'")
    print("   export EMAIL_HOST_PASSWORD='your-app-password'")
    print("   export EMAIL_PORT='587'")
    print("   export EMAIL_USE_TLS='True'")
    print("")
    print("3. Gmail configuration example:")
    print(
        "   export EMAIL_URL='smtp://your-email@gmail.com:app-password@smtp.gmail.com:587/?tls=True'"
    )
    print("")
    print("4. Restart services to apply new configuration")


def test_gmail_specific_config():
    """Test Gmail specific configuration"""
    print("\n📧 Testing Gmail configuration...")

    # Check if it's a Gmail configuration
    smtp_host = getattr(settings, "EMAIL_HOST", "")
    if "gmail" not in smtp_host.lower():
        print(f"Current configuration is not Gmail: {smtp_host}")
        return True

    print("✅ Detected Gmail configuration")

    # Gmail specific suggestions
    print("\n📝 Gmail configuration suggestions:")
    print("1. Use application-specific password instead of account password")
    print("2. Enable two-step verification")
    print(
        "3. Generate application-specific password: https://myaccount.google.com/apppasswords"
    )
    print(
        "4. Use EMAIL_URL format: smtp://username:app_password@smtp.gmail.com:587/?tls=True"
    )

    return True


def test_gmail_to_qq_email():
    """Test sending verification code from Gmail to QQ mailbox"""
    print("\n=== Testing sending verification code from Gmail to QQ mailbox ===")

    # Get SMTP configuration
    smtp_host = getattr(settings, "EMAIL_HOST", "")
    smtp_user = getattr(settings, "EMAIL_HOST_USER", "")
    smtp_password = getattr(settings, "EMAIL_HOST_PASSWORD", "")
    smtp_port = getattr(settings, "EMAIL_PORT", "")
    smtp_use_tls = getattr(settings, "EMAIL_USE_TLS", False)

    if not all([smtp_host, smtp_user, smtp_password, smtp_port]):
        print("✗ Gmail SMTP configuration incomplete, skip email sending test")
        return False

    # Test email content - simulate Telegram mailbox change verification code
    subject = "Saleor Telegram mailbox change verification code"
    verification_code = "123456"

    message = f"""
Saleor Telegram mailbox change verification code

Your verification code is: {verification_code}

This verification code will expire in 10 minutes.

If you did not request this verification code, please ignore this email.

---
This email is sent automatically by Saleor system
Sender: {smtp_user}
"""

    html_message = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
        <h1 style="color: #2c3e50; margin-bottom: 20px;">Saleor Telegram mailbox change verification code</h1>

        <div style="background-color: #ffffff; padding: 20px; border-radius: 6px; border-left: 4px solid #3498db;">
            <p style="font-size: 16px; color: #2c3e50; margin-bottom: 10px;">Your verification code is:</p>
            <div style="background-color: #ecf0f1; padding: 15px; border-radius: 4px; text-align: center; margin: 15px 0;">
                <span style="font-size: 24px; font-weight: bold; color: #e74c3c; letter-spacing: 3px;">{verification_code}</span>
            </div>
            <p style="font-size: 14px; color: #7f8c8d;">This verification code will expire in 10 minutes.</p>
        </div>

        <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-radius: 4px; border-left: 4px solid #ffc107;">
            <p style="font-size: 14px; color: #856404; margin: 0;">
                <strong>Security reminder:</strong> If you did not request this verification code, please ignore this email.
            </p>
        </div>

        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ecf0f1;">

        <div style="font-size: 12px; color: #95a5a6; text-align: center;">
            <p>This email is sent automatically by Saleor system</p>
            <p>Sender: {smtp_user}</p>
        </div>
    </div>
</body>
</html>
"""

    # Recipient mailbox
    recipient_email = "88888888@qq.com"

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
            f"Please check QQ mailbox {recipient_email} whether you received verification code email"
        )
        print(f"Verification code: {verification_code}")
        return True

    except Exception as e:
        print(f"✗ Email sending failed: {e}")
        print("\nPossible solutions:")
        print("1. Check whether Gmail application-specific password is correct")
        print(
            "2. Confirm whether Gmail has enabled two-step verification and application-specific password"
        )
        print("3. Check network connection")
        print("4. Confirm whether firewall prevents SMTP connection")
        print("5. Check Gmail account security settings")
        return False


def test_telegram_mutation_with_gmail():
    """Test Telegram mutation using Gmail to send email"""
    print("\n=== Testing Telegram Mutation (Gmail configuration) ===")

    try:
        from saleor.graphql.account.mutations.authentication.telegram_email_change_request import (
            TelegramEmailChangeRequest,
        )

        # Simulate Telegram mailbox change request
        new_email = "88888888@qq.com"  # QQ mailbox
        verification_code = "654321"

        # Test email sending method
        result = TelegramEmailChangeRequest.send_verification_email(
            new_email, verification_code, None
        )

        if result:
            print("✓ Telegram mutation using Gmail to send email functionality normal")
            print(f"Verification code {verification_code} sent to {new_email}")
            return True
        else:
            print("✗ Telegram mutation email sending functionality abnormal")
            return False

    except Exception as e:
        print(f"✗ Telegram mutation test failed: {e}")
        return False


def test_email_content_preview():
    """Preview email content"""
    print("\n=== Email content preview ===")

    verification_code = "123456"
    smtp_user = getattr(settings, "EMAIL_HOST_USER", "ikun.ldea@gmail.com")
    recipient_email = "88888888@qq.com"

    print(f"Sender: {smtp_user}")
    print(f"Recipient: {recipient_email}")
    print(f"Subject: Saleor Telegram mailbox change verification code")
    print(f"Verification code: {verification_code}")
    print(f"Validity period: 10 minutes")

    print("\nPure text content preview:")
    print("-" * 50)
    print(
        f"""
Saleor Telegram mailbox change verification code

Your verification code is: {verification_code}

This verification code will expire in 10 minutes.

If you did not request this verification code, please ignore this email.

---
This email is sent automatically by Saleor system
Sender: {smtp_user}
""".strip()
    )
    print("-" * 50)

    print("✓ Email content preview completed")
    return True


def main():
    """Main test function"""
    print("🚀 Starting Gmail SMTP configuration test...\n")

    # Test configuration
    success = test_email_configuration()

    # Show configuration help
    show_configuration_help()

    if success:
        print("\n✨ Test completed successfully!")
    else:
        print("\n❌ Test failed. Please check your configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
