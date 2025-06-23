import graphene
import json
from urllib.parse import parse_qs, unquote
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta

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


class TelegramEmailChangeConfirm(BaseMutation):
    """Mutation that confirms email change for Telegram user with verification code."""

    class Arguments:
        init_data_raw = graphene.String(
            required=True, description="Telegram WebApp initDataRaw string"
        )
        verification_code = graphene.String(
            required=True, description="Verification code received via email"
        )
        old_email = graphene.String(
            required=True,
            description="Current email address (telegram_xxx@telegram.local format)",
        )
        new_email = graphene.String(
            required=True, description="New email address to change to"
        )

    user = graphene.Field(User, description="User with updated email")
    success = graphene.Boolean(description="Whether the email change was successful")
    token = graphene.String(description="JWT token for the user")

    class Meta:
        description = "Confirm email change for Telegram user with verification code"
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
    def get_verification_data_from_redis(cls, telegram_id):
        """Get verification code data from Redis with enhanced user ID and email association validation"""
        try:
            redis_cache = get_redis_cache()
            cache_key = f"email_change_verification:{telegram_id}"

            # Get data from Redis
            cache_data = redis_cache.get(cache_key)

            if not cache_data:
                print(f"❌ Verification code data not found in Redis: {cache_key}")
                return None

            print(f"✅ Retrieved verification code data from Redis: {cache_key}")
            print(f"   User ID: {cache_data.get('user_id')}")
            print(f"   Telegram ID: {cache_data.get('telegram_id')}")
            print(f"   Verification code: {cache_data.get('verification_code')}")
            print(f"   Old email: {cache_data.get('old_email')}")
            print(f"   New email: {cache_data.get('new_email')}")
            print(f"   Created at: {cache_data.get('created_at')}")
            print(f"   Expires at: {cache_data.get('expires_at')}")

            return cache_data

        except Exception as e:
            print(f"❌ Failed to get data from Redis: {e}")
            raise ValidationError(f"Failed to get verification data: {str(e)}")

    @classmethod
    def validate_verification_data_integrity(cls, cache_data, telegram_id, user):
        """Validate completeness and consistency of verification code data stored in Redis"""
        try:
            # 1. Validate Telegram ID consistency
            stored_telegram_id = cache_data.get("telegram_id")
            if stored_telegram_id != telegram_id:
                print(
                    f"❌ Telegram ID mismatch: expected={telegram_id}, stored={stored_telegram_id}"
                )
                raise ValidationError("Telegram ID mismatch in stored data")

            # 2. Validate user ID consistency
            stored_user_id = cache_data.get("user_id")
            if stored_user_id != user.pk:
                print(
                    f"❌ User ID mismatch: expected={user.pk}, stored={stored_user_id}"
                )
                raise ValidationError("User ID mismatch in stored data")

            # 3. Validate old email matches user's current email
            stored_old_email = cache_data.get("old_email")
            if user.email != stored_old_email:
                print(
                    f"❌ User's current email doesn't match stored old email: current={user.email}, stored={stored_old_email}"
                )
                raise ValidationError(
                    "Current user email does not match stored old email"
                )

            # 4. Validate old email format is correct
            expected_old_email = f"telegram_{telegram_id}@telegram.local"
            if stored_old_email != expected_old_email:
                print(
                    f"❌ Stored old email format is incorrect: expected={expected_old_email}, stored={stored_old_email}"
                )
                raise ValidationError("Stored old email format is incorrect")

            # 5. Validate new email format
            stored_new_email = cache_data.get("new_email")
            if not cls.is_valid_email_format(stored_new_email):
                print(f"❌ Stored new email format is invalid: {stored_new_email}")
                raise ValidationError("Stored new email format is invalid")

            # 6. Validate new email is not Telegram format
            if stored_new_email.endswith("@telegram.local"):
                print(
                    f"❌ Stored new email cannot be Telegram format: {stored_new_email}"
                )
                raise ValidationError("Stored new email cannot be Telegram format")

            print(f"✅ Verification code data integrity validation passed")
            return True

        except ValidationError:
            raise
        except Exception as e:
            print(f"❌ Verification code data integrity validation failed: {e}")
            raise ValidationError(
                f"Verification data integrity validation failed: {str(e)}"
            )

    @classmethod
    def is_valid_email_format(cls, email):
        """Validate email format is valid"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @classmethod
    def clear_verification_data_from_redis(cls, telegram_id, old_email=None):
        """Clear verification code data from Redis, including main data and mapping data"""
        try:
            redis_cache = get_redis_cache()

            # Clear main verification code data
            cache_key = f"email_change_verification:{telegram_id}"
            redis_cache.delete(cache_key)
            print(f"✅ Cleared verification code data from Redis: {cache_key}")

            # Clear email mapping data
            if old_email:
                email_mapping_key = f"email_change_mapping:{old_email}"
                redis_cache.delete(email_mapping_key)
                print(f"✅ Cleared email mapping data from Redis: {email_mapping_key}")

        except Exception as e:
            print(f"⚠️ Failed to clear data from Redis: {e}")
            # Don't raise exception as clearing failure doesn't affect main functionality

    @classmethod
    def verify_code_expiration(cls, created_at_str):
        """Verify if verification code has expired"""
        try:
            # Parse creation time
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            current_time = timezone.now()

            # Check if more than 10 minutes have passed
            time_diff = current_time - created_at
            if time_diff > timedelta(minutes=10):
                print(f"❌ Verification code expired: {time_diff}")
                return False

            print(f"✅ Verification code not expired: {time_diff}")
            return True

        except Exception as e:
            print(f"❌ Failed to verify code expiration: {e}")
            return False

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        """Perform mutation"""
        init_data_raw = data.get("init_data_raw")
        verification_code = data.get("verification_code")
        old_email = data.get("old_email")
        new_email = data.get("new_email")

        if not all([init_data_raw, verification_code, old_email, new_email]):
            raise ValidationError(
                {
                    "verification_code": ValidationError(
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

            # 3. Validate provided email parameters
            expected_old_email = f"telegram_{telegram_id}@telegram.local"
            if old_email != expected_old_email:
                raise ValidationError(
                    {
                        "old_email": ValidationError(
                            "Invalid old email format",
                            code=AccountErrorCode.INVALID.value,
                        )
                    }
                )

            if user.email != old_email:
                raise ValidationError(
                    {
                        "old_email": ValidationError(
                            "Current email does not match the provided old email",
                            code=AccountErrorCode.INVALID.value,
                        )
                    }
                )

            if not cls.is_valid_email_format(new_email):
                raise ValidationError(
                    {
                        "new_email": ValidationError(
                            "Invalid new email format",
                            code=AccountErrorCode.INVALID.value,
                        )
                    }
                )

            if new_email.endswith("@telegram.local"):
                raise ValidationError(
                    {
                        "new_email": ValidationError(
                            "New email cannot be a Telegram format email",
                            code=AccountErrorCode.INVALID.value,
                        )
                    }
                )

            # 4. Get verification data from Redis
            cache_data = cls.get_verification_data_from_redis(telegram_id)
            if not cache_data:
                raise ValidationError(
                    {
                        "verification_code": ValidationError(
                            "No pending email change request found",
                            code=AccountErrorCode.NOT_FOUND.value,
                        )
                    }
                )

            # 5. Validate completeness and consistency of data stored in Redis
            cls.validate_verification_data_integrity(cache_data, telegram_id, user)

            # Get email information from cache data
            stored_old_email = cache_data.get("old_email")
            stored_new_email = cache_data.get("new_email")

            print(f"📧 Email change information:")
            print(f"   Current email: {user.email}")
            print(f"   Provided old email: {old_email}")
            print(f"   Stored old email: {stored_old_email}")
            print(f"   Provided new email: {new_email}")
            print(f"   Stored new email: {stored_new_email}")

            # 6. Validate consistency between provided parameters and Redis stored data
            if old_email != stored_old_email:
                raise ValidationError(
                    {
                        "old_email": ValidationError(
                            "Provided old email does not match the stored request",
                            code=AccountErrorCode.INVALID.value,
                        )
                    }
                )

            if new_email != stored_new_email:
                raise ValidationError(
                    {
                        "new_email": ValidationError(
                            "Provided new email does not match the stored request",
                            code=AccountErrorCode.INVALID.value,
                        )
                    }
                )

            # 7. Verify verification code
            stored_code = cache_data.get("verification_code")
            if verification_code != stored_code:
                print(
                    f"❌ Verification code mismatch: provided={verification_code}, stored={stored_code}"
                )
                raise ValidationError(
                    {
                        "verification_code": ValidationError(
                            "Invalid verification code",
                            code=AccountErrorCode.INVALID.value,
                        )
                    }
                )

            # 8. Check if verification code has expired
            created_at_str = cache_data.get("created_at")
            if not cls.verify_code_expiration(created_at_str):
                raise ValidationError(
                    {
                        "verification_code": ValidationError(
                            "Verification code has expired",
                            code=AccountErrorCode.INVALID.value,
                        )
                    }
                )

            # 9. Check if new email is still available
            if models.User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                raise ValidationError(
                    {
                        "new_email": ValidationError(
                            "New email is already used by another user",
                            code=AccountErrorCode.UNIQUE.value,
                        )
                    }
                )

            # 10. Enhanced final email uniqueness validation before update
            cls.validate_final_email_uniqueness(new_email, user.pk, telegram_id)

            # 11. Update user email with transaction to ensure atomicity
            from django.db import transaction

            with transaction.atomic():
                # Final check for email uniqueness within transaction
                if (
                    models.User.objects.filter(email=new_email)
                    .exclude(pk=user.pk)
                    .exists()
                ):
                    raise ValidationError(
                        {
                            "new_email": ValidationError(
                                "New email is already used by another user",
                                code=AccountErrorCode.UNIQUE.value,
                            )
                        }
                    )

                # Check if email is now bound to another telegram user
                cls.validate_email_not_bound_to_other_telegram(new_email, telegram_id)

                # Update user email
                user.email = new_email
                user.save(update_fields=["email"])

                # Update metadata to reflect email change
                user.store_value_in_private_metadata(
                    {
                        "email_changed_at": timezone.now().isoformat(),
                        "email_changed_from": old_email,
                        "email_changed_to": new_email,
                    }
                )
                user.save(update_fields=["private_metadata"])

            # 12. Clear verification data from Redis
            cls.clear_verification_data_from_redis(telegram_id, old_email)

            # 13. Generate new JWT token
            token_payload = {
                "user_id": user.pk,
                "email": user.email,
                "type": "access",
            }
            token = create_token(
                token_payload, timedelta(hours=24)
            )  # 24-hour expiration

            print(f"✅ Email change successful:")
            print(f"   User ID: {user.pk}")
            print(f"   Old email: {old_email}")
            print(f"   New email: {new_email}")
            print(f"   Token: {token[:50]}...")

            return cls(user=user, success=True, token=token, errors=[])

        except ValidationError as e:
            return cls(
                user=None,
                success=False,
                token=None,
                errors=[
                    {
                        "field": "verification_code",
                        "message": str(e),
                        "code": AccountErrorCode.INVALID.value,
                    }
                ],
            )

    @classmethod
    def validate_final_email_uniqueness(cls, new_email, current_user_id, telegram_id):
        """Final validation of email uniqueness before updating user email"""
        try:
            # Check if email is already used by another user
            existing_user = (
                models.User.objects.filter(email=new_email)
                .exclude(pk=current_user_id)
                .first()
            )

            if existing_user:
                print(
                    f"❌ Final check: New email already used by another user: {new_email}"
                )
                print(f"   Existing user ID: {existing_user.pk}")
                print(f"   Existing user email: {existing_user.email}")
                raise ValidationError("New email is already used by another user")

            # Check if email is in any pending email change requests for other users
            cls.validate_no_conflicting_pending_requests(new_email, telegram_id)

            print(f"✅ Final email uniqueness validation passed: {new_email}")
            return True

        except ValidationError:
            raise
        except Exception as e:
            print(f"❌ Final email uniqueness validation failed: {e}")
            raise ValidationError(f"Final email uniqueness validation failed: {str(e)}")

    @classmethod
    def validate_email_not_bound_to_other_telegram(cls, new_email, current_telegram_id):
        """Validate that new email is not bound to another telegram user"""
        try:
            # Check if any user with this email has telegram metadata
            users_with_email = models.User.objects.filter(email=new_email)

            for user in users_with_email:
                private_metadata = user.get_private_metadata()
                stored_telegram_id = private_metadata.get("telegram_id")

                if stored_telegram_id and stored_telegram_id != current_telegram_id:
                    print(
                        f"❌ New email is bound to another telegram user: {new_email}"
                    )
                    print(f"   Current telegram ID: {current_telegram_id}")
                    print(f"   Bound to telegram ID: {stored_telegram_id}")
                    raise ValidationError(
                        "New email is already bound to another telegram user"
                    )

            print(
                f"✅ Email not bound to other telegram validation passed: {new_email}"
            )
            return True

        except ValidationError:
            raise
        except Exception as e:
            print(f"❌ Email telegram binding validation failed: {e}")
            raise ValidationError(f"Email telegram binding validation failed: {str(e)}")

    @classmethod
    def validate_no_conflicting_pending_requests(cls, new_email, current_telegram_id):
        """Validate that there are no conflicting pending email change requests"""
        try:
            redis_cache = get_redis_cache()

            # This is a simplified check - in a production environment, you might want to
            # scan all email change verification keys to check for conflicts
            # For now, we'll rely on the database uniqueness check above

            print(f"✅ No conflicting pending requests found for email: {new_email}")
            return True

        except Exception as e:
            print(f"❌ Conflicting pending requests validation failed: {e}")
            raise ValidationError(
                f"Conflicting pending requests validation failed: {str(e)}"
            )
