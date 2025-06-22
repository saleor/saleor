#!/usr/bin/env python3
"""
Check current running Saleor service email configuration
"""

import os
import sys
import django
from django.conf import settings
from django.core.mail import send_mail
from django.test import override_settings

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)


def check_email_configuration():
    """Check Saleor email configuration"""
    print("🔍 Checking Saleor email configuration...")

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
        print("✅ Saleor email configuration complete")
        return True
    else:
        print("❌ Saleor email configuration incomplete")
        print("   Please set EMAIL_URL environment variable:")
        print("   export EMAIL_URL='smtp://username:password@host:port/?tls=True'")
        return False


def test_email_sending():
    """Test email sending functionality"""
    print("\n📧 Testing email sending functionality...")

    smtp_user = getattr(settings, "EMAIL_HOST_USER", "")
    recipient_email = input("Please enter recipient email address: ").strip()
    if not recipient_email:
        print("❌ No recipient email address provided")
        return False

    subject = "Saleor Email Configuration Test"
    message = "This is a test email to verify the Saleor email configuration."

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


if __name__ == "__main__":
    print("🚀 Starting Saleor email configuration check...\n")

    # Check configuration
    success = check_email_configuration()

    if success:
        # Test email sending
        test_email_sending()

    # Show configuration help
    show_configuration_help()

    if success:
        print("\n✨ Test completed successfully!")
    else:
        print("\n❌ Test failed. Please check your configuration.")
        sys.exit(1)
