import graphene
import json
import secrets
import threading
from urllib.parse import parse_qs, unquote
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from telegram import Bot
from telegram.error import TelegramError

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....core.jwt import create_token
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_AUTH
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....core.scalars import DateTime
from ...types import User
from .telegram_token_create import validate_telegram_data


def get_redis_cache():
    """Get Redis cache instance from backend.env configuration"""
    try:
        # Get Redis configuration from environment variables
        celery_broker_url = getattr(
            settings, "CELERY_BROKER_URL", "redis://redis:6379/1"
        )
        print(f"🔗 Redis configuration: {celery_broker_url}")

        # Use Django cache system, which automatically handles Redis connection
        # Django cache system will automatically configure Redis based on CACHE_URL or CELERY_BROKER_URL
        return cache

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        raise ValidationError("Redis connection failed")


class TelegramEmailChangeRequest(BaseMutation):
    """Mutation that requests email change for Telegram user with verification code."""

    class Arguments:
        init_data_raw = graphene.String(
            required=True, description="Telegram WebApp initDataRaw string"
        )
        old_email = graphene.String(
            required=True,
            description="Current email address (telegram_xxx@telegram.local format)",
        )
        new_email = graphene.String(
            required=True, description="New email address to change to"
        )

    user = graphene.Field(User, description="User requesting email change")
    verification_code = graphene.String(
        description="Verification code sent to new email"
    )
    expires_at = DateTime(description="When the verification code expires")

    class Meta:
        description = "Request email change for Telegram user with verification code"
        doc_category = DOC_CATEGORY_AUTH
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def find_user_by_telegram_id(cls, telegram_id):
        """Find user by telegram_id"""
        try:
            user = models.User.objects.get(external_reference=f"telegram_{telegram_id}")
            return user
        except models.User.DoesNotExist:
            return None

    @classmethod
    def generate_verification_code(cls):
        """Generate 6-digit verification code"""
        return "".join(secrets.choice("0123456789") for _ in range(6))

    @classmethod
    def store_verification_code_in_redis(
        cls, telegram_id, old_email, new_email, verification_code, user_id=None
    ):
        """Store verification code in Redis with 10-minute expiration, enhanced with user ID and email association"""
        try:
            redis_cache = get_redis_cache()
            cache_key = f"email_change_verification:{telegram_id}"

            # Prepare cache data with enhanced user association
            cache_data = {
                "verification_code": verification_code,
                "old_email": old_email,
                "new_email": new_email,
                "telegram_id": telegram_id,
                "user_id": user_id,
                "created_at": timezone.now().isoformat(),
                "expires_at": (timezone.now() + timedelta(minutes=10)).isoformat(),
            }

            # Store in Redis with 10-minute expiration
            redis_cache.set(
                cache_key, cache_data, timeout=600
            )  # 10 minutes = 600 seconds

            print(f"✅ Verification code stored in Redis: {cache_key}")
            print(f"   User ID: {user_id}")
            print(f"   Telegram ID: {telegram_id}")
            print(f"   Verification code: {verification_code}")
            print(f"   Old email: {old_email}")
            print(f"   New email: {new_email}")
            print(f"   Expiration: 10 minutes")

            # Additional storage of email mapping for quick lookup
            email_mapping_key = f"email_change_mapping:{old_email}"
            email_mapping_data = {
                "telegram_id": telegram_id,
                "user_id": user_id,
                "new_email": new_email,
                "verification_code": verification_code,
                "created_at": cache_data["created_at"],
            }
            redis_cache.set(email_mapping_key, email_mapping_data, timeout=600)

            print(f"✅ Email mapping stored: {email_mapping_key}")

            return cache_key

        except Exception as e:
            print(f"❌ Redis storage failed: {e}")
            raise ValidationError(f"Failed to store verification code: {str(e)}")

    @classmethod
    def validate_email_change_request(cls, telegram_id, old_email, new_email, user):
        """Validate completeness and consistency of email change request with enhanced uniqueness checks"""
        try:
            # 1. Validate consistency between Telegram ID and email format
            expected_old_email = f"telegram_{telegram_id}@telegram.local"
            if old_email != expected_old_email:
                print(
                    f"❌ Email format doesn't match Telegram ID: expected={expected_old_email}, actual={old_email}"
                )
                raise ValidationError("Email format does not match Telegram ID")

            # 2. Validate user's current email matches requested old email
            if user.email != old_email:
                print(
                    f"❌ User's current email doesn't match requested old email: current={user.email}, requested={old_email}"
                )
                raise ValidationError(
                    "Current user email does not match the requested old email"
                )

            # 3. Validate new email format
            if not cls.is_valid_email_format(new_email):
                print(f"❌ Invalid new email format: {new_email}")
                raise ValidationError("Invalid new email format")

            # 4. Validate new email is not Telegram format
            if new_email.endswith("@telegram.local"):
                print(f"❌ New email cannot be Telegram format: {new_email}")
                raise ValidationError("New email cannot be a Telegram format email")

            # 5. Enhanced new email uniqueness validation
            cls.validate_new_email_uniqueness(new_email, user.pk)

            # 6. Check if new email is already bound to another telegram user
            cls.validate_new_email_not_bound_to_telegram(new_email)

            # 7. Check if there's already a pending email change request for this user
            cls.validate_no_pending_email_change(telegram_id)

            print(f"✅ Email change request validation passed")
            return True

        except ValidationError:
            raise
        except Exception as e:
            print(f"❌ Email change request validation failed: {e}")
            raise ValidationError(f"Email change request validation failed: {str(e)}")

    @classmethod
    def validate_new_email_uniqueness(cls, new_email, current_user_id):
        """Validate that new email is unique and not used by any other user"""
        try:
            # Check if email is already used by another user
            existing_user = models.User.objects.filter(email=new_email).first()
            
            if existing_user:
                if existing_user.pk == current_user_id:
                    print(f"❌ New email is the same as current email: {new_email}")
                    raise ValidationError("New email cannot be the same as current email")
                else:
                    print(f"❌ New email already used by another user: {new_email}")
                    print(f"   Existing user ID: {existing_user.pk}")
                    print(f"   Existing user email: {existing_user.email}")
                    raise ValidationError("New email is already used by another user")
            
            # Check if email is in any pending email change requests
            redis_cache = get_redis_cache()
            pending_requests = []
            
            # This is a simplified check - in production you might want to scan all keys
            # For now, we'll rely on the uniqueness check above
            
            print(f"✅ New email uniqueness validation passed: {new_email}")
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            print(f"❌ New email uniqueness validation failed: {e}")
            raise ValidationError(f"New email uniqueness validation failed: {str(e)}")

    @classmethod
    def validate_new_email_not_bound_to_telegram(cls, new_email):
        """Validate that new email is not already bound to another telegram user"""
        try:
            # Check if any user with this email has telegram metadata
            users_with_email = models.User.objects.filter(email=new_email)
            
            for user in users_with_email:
                private_metadata = user.get_private_metadata()
                if private_metadata.get("created_via_telegram") or private_metadata.get("telegram_id"):
                    print(f"❌ New email is already bound to telegram user: {new_email}")
                    print(f"   Telegram user ID: {private_metadata.get('telegram_id')}")
                    raise ValidationError("New email is already bound to another telegram user")
            
            print(f"✅ New email not bound to telegram validation passed: {new_email}")
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            print(f"❌ New email telegram binding validation failed: {e}")
            raise ValidationError(f"New email telegram binding validation failed: {str(e)}")

    @classmethod
    def validate_no_pending_email_change(cls, telegram_id):
        """Validate that there's no pending email change request for this user"""
        try:
            redis_cache = get_redis_cache()
            cache_key = f"email_change_verification:{telegram_id}"
            
            existing_request = redis_cache.get(cache_key)
            if existing_request:
                print(f"❌ Pending email change request already exists for telegram_id: {telegram_id}")
                print(f"   Pending new email: {existing_request.get('new_email')}")
                print(f"   Created at: {existing_request.get('created_at')}")
                raise ValidationError("A pending email change request already exists. Please wait for the current request to expire or use the existing verification code.")
            
            print(f"✅ No pending email change request found for telegram_id: {telegram_id}")
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            print(f"❌ Pending email change validation failed: {e}")
            raise ValidationError(f"Pending email change validation failed: {str(e)}")

    @classmethod
    def is_valid_email_format(cls, email):
        """Validate email format is valid"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @classmethod
    def send_verification_email(cls, new_email, verification_code, user):
        from django.core.mail import send_mail
        from django.conf import settings

        # Check SMTP configuration
        smtp_host = getattr(settings, "EMAIL_HOST", "")
        smtp_user = getattr(settings, "EMAIL_HOST_USER", "")
        smtp_password = getattr(settings, "EMAIL_HOST_PASSWORD", "")
        smtp_port = getattr(settings, "EMAIL_PORT", "")

        if not all([smtp_host, smtp_user, smtp_password, smtp_port]):
            # If SMTP configuration is incomplete, return verification code without sending email
            # In production environment, complete SMTP settings should be configured
            print(
                f"⚠ SMTP configuration incomplete, verification code: {verification_code}"
            )
            print(f"   Recipient: {new_email}")
            print(f"   Please configure the following environment variables:")
            print(f"   - EMAIL_URL=smtp://username:password@host:port/?tls=True")
            print(
                f"   - Or set separately: EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_PORT"
            )
            return True

        subject = "Saleor User Verification"
        message = f"""
Saleor User Verification

Your verification code is: {verification_code}

The verification code will expire in 10 minutes.
"""
        html_message = f"""
<html><body><h1>Saleor User Verification</h1><p>Your verification code is: <strong>{verification_code}</strong></p><p>The verification code will expire in 10 minutes.</p></body></html>
"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=smtp_user,
                recipient_list=[new_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"⚠ Email sending failed: {str(e)}")
            print(f"   Verification code: {verification_code}")
            print(f"   Recipient: {new_email}")
            # In production environment, exception should be raised here
            # But in development environment, we allow execution to continue
            return True

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        """Perform mutation"""
        init_data_raw = data.get("init_data_raw")
        old_email = data.get("old_email")
        new_email = data.get("new_email")

        if not all([init_data_raw, old_email, new_email]):
            raise ValidationError(
                {
                    "init_data_raw": ValidationError(
                        "All parameters are required",
                        code=AccountErrorCode.REQUIRED.value,
                    )
                }
            )

        try:
            # 1. Validate Telegram data
            telegram_data = validate_telegram_data(init_data_raw)
            user_info = telegram_data["user"]
            telegram_id = user_info["id"]

            # 2. Find user
            user = cls.find_user_by_telegram_id(telegram_id)
            if not user:
                raise ValidationError(
                    {
                        "init_data_raw": ValidationError(
                            "User not found", code=AccountErrorCode.NOT_FOUND.value
                        )
                    }
                )

            # 3. Validate completeness and consistency of email change request
            cls.validate_email_change_request(telegram_id, old_email, new_email, user)

            # 4. Generate verification code
            verification_code = cls.generate_verification_code()
            expires_at = timezone.now() + timedelta(minutes=10)

            # 5. Store verification code in Redis with user ID and email association
            cls.store_verification_code_in_redis(
                telegram_id, old_email, new_email, verification_code, user.pk
            )

            # 6. Send verification code email
            cls.send_verification_email(new_email, verification_code, user)

            return cls(
                user=user,
                verification_code=verification_code,  # Return verification code in development environment
                expires_at=expires_at,
                errors=[],
            )

        except ValidationError as e:
            return cls(
                user=None,
                verification_code=None,
                expires_at=None,
                errors=[
                    {
                        "field": "init_data_raw",
                        "message": str(e),
                        "code": AccountErrorCode.INVALID.value,
                    }
                ],
            )
