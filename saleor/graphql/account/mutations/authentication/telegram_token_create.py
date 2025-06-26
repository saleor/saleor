import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
import json
import asyncio
from urllib.parse import parse_qs, unquote

from telegram import Bot
from telegram.error import TelegramError

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....core.jwt import create_access_token, create_refresh_token
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_AUTH
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ...types import User
from .utils import _get_new_csrf_token, update_user_last_login_if_required


async def validate_telegram_data_async(init_data_raw, bot_token):
    """
    Validate Telegram initDataRaw data using python-telegram-bot asynchronously
    """
    try:
        # Create Bot instance
        bot = Bot(token=bot_token)

        # Validate bot token
        try:
            bot_info = await bot.get_me()
            print(
                f"Bot validation successful: {bot_info.first_name} (@{bot_info.username})"
            )
        except TelegramError as e:
            raise ValidationError(f"Invalid bot token: {str(e)}")

        print("=" * 50)
        print("Original init_data_raw:")
        print(init_data_raw)
        print("=" * 50)

        # URL decode first to handle double encoding
        decoded_data = unquote(init_data_raw)
        print("After URL decode:")
        print(decoded_data)
        print("=" * 50)

        # 更健壮的解析方式：user= 之后的所有内容都作为 user 字段
        user_start = decoded_data.find("user=")
        if user_start != -1:
            before_user = decoded_data[:user_start].strip("&")
            user_value = decoded_data[user_start + 5 :]  # 5 = len('user=')
            # 解析前面的参数
            params = dict(x.split("=", 1) for x in before_user.split("&") if "=" in x)
            params["user"] = user_value
        else:
            params = dict(x.split("=", 1) for x in decoded_data.split("&") if "=" in x)
        print(f"Parsed data: {params}")

        # Extract user data
        user_data = params.get("user", None)
        if not user_data:
            raise ValidationError("Missing user data in Telegram init data")

        # Parse user data
        try:
            user_info = json.loads(user_data)
        except json.JSONDecodeError:
            raise ValidationError("Invalid user data JSON")

        # Validate basic structure of user data
        required_fields = ["id", "first_name"]
        for field in required_fields:
            if field not in user_info:
                raise ValidationError(f"Missing required field: {field}")

        # Validate user ID is numeric
        try:
            user_id = int(user_info["id"])
            if user_id <= 0:
                raise ValidationError("Invalid user ID")
        except (ValueError, TypeError):
            raise ValidationError("User ID must be a positive integer")

        # Validate other required parameters
        required_params = [
            "auth_date",
            "hash",
        ]
        for param in required_params:
            if param not in params:
                raise ValidationError(f"Missing required parameter: {param}")

        # Optional parameters (some WebApp implementations may not provide these)
        optional_params = [
            "chat_instance",
            "chat_type",
            "signature",
        ]

        # Check if optional parameters exist but are empty
        for param in optional_params:
            if param in params and not params.get(param, None):
                print(f"Warning: {param} parameter is empty")

        return {
            "user": user_info,
            "auth_date": params.get("auth_date", None),
            "hash": params.get("hash", None),
            "chat_instance": params.get("chat_instance", None),
            "chat_type": params.get("chat_type", None),
            "signature": params.get("signature", None),
            "bot_info": {
                "id": bot_info.id,
                "first_name": bot_info.first_name,
                "username": bot_info.username,
            },
        }

    except ValidationError:
        # Re-raise ValidationError
        raise
    except Exception as e:
        raise ValidationError(f"Telegram validation error: {str(e)}")


def validate_telegram_data(init_data_raw):
    """
    Synchronous wrapper for async validation function
    """
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not bot_token:
        raise ValidationError("Telegram bot token not configured")

    # Run async validation
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            validate_telegram_data_async(init_data_raw, bot_token)
        )
        return result
    finally:
        loop.close()


class TelegramTokenCreate(BaseMutation):
    """Mutation that authenticates a user via Telegram and returns token and user data."""

    class Arguments:
        init_data_raw = graphene.String(
            required=True, description="Telegram WebApp initDataRaw string"
        )

    token = graphene.String(description="JWT access token")
    refresh_token = graphene.String(description="JWT refresh token")
    csrf_token = graphene.String(description="CSRF token")
    user = graphene.Field(User, description="Authenticated user")

    class Meta:
        description = "Authenticate user via Telegram WebApp"
        doc_category = DOC_CATEGORY_AUTH
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def find_user_by_telegram_id(cls, telegram_id):
        """Find user by telegram_id"""
        try:
            # Use external_reference field to store telegram_id
            user = models.User.objects.get(external_reference=f"telegram_{telegram_id}")
            return user
        except models.User.DoesNotExist:
            return None

    @classmethod
    def create_user_without_email_password(cls, telegram_data):
        """Create user without email and password"""
        user_info = telegram_data["user"]
        telegram_id = user_info["id"]

        # Generate unique email (though not verified)
        email = f"telegram_{telegram_id}@telegram.local"

        # Generate random password (though user won't use it)
        from django.contrib.auth.hashers import make_password
        import secrets

        random_password = secrets.token_urlsafe(32)

        # Create user
        user = models.User.objects.create(
            email=email,
            first_name=user_info.get("first_name", ""),
            last_name=user_info.get("last_name", ""),
            is_active=True,
            is_confirmed=True,
            external_reference=f"telegram_{telegram_id}",
            password=make_password(random_password),  # Set random password
        )

        # Prepare metadata, filtering out None values
        metadata_items = {
            "telegram_id": telegram_id,
            "created_via_telegram": True,
        }

        # Add optional fields only if they have values
        if user_info.get("username"):
            metadata_items["telegram_username"] = user_info.get("username")
        if user_info.get("language_code"):
            metadata_items["telegram_language_code"] = user_info.get("language_code")
        if user_info.get("photo_url"):
            metadata_items["telegram_photo_url"] = user_info.get("photo_url")
        if telegram_data.get("bot_info"):
            metadata_items["bot_info"] = telegram_data.get("bot_info")
        if telegram_data.get("chat_instance"):
            metadata_items["chat_instance"] = telegram_data.get("chat_instance")
        if telegram_data.get("chat_type"):
            metadata_items["chat_type"] = telegram_data.get("chat_type")
        if telegram_data.get("auth_date"):
            metadata_items["auth_date"] = telegram_data.get("auth_date")

        # Update metadata
        user.store_value_in_private_metadata(metadata_items)
        user.save(update_fields=["private_metadata"])

        return user

    @classmethod
    def generate_token_for_user(cls, user):
        """Generate token and refresh token for user"""
        # Generate token
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        csrf_token = _get_new_csrf_token()

        return {
            "token": access_token,
            "refresh_token": refresh_token,
            "csrf_token": csrf_token,
        }

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        """Perform mutation"""
        init_data_raw = data.get("init_data_raw")

        if not init_data_raw:
            raise ValidationError(
                {
                    "init_data_raw": ValidationError(
                        "initDataRaw is required", code=AccountErrorCode.INVALID.value
                    )
                }
            )

        try:
            # 1. Validate Telegram data
            telegram_data = validate_telegram_data(init_data_raw)
            user_info = telegram_data["user"]
            telegram_id = user_info["id"]

            # 2. Check if user with associated telegram_id exists
            user = cls.find_user_by_telegram_id(telegram_id)

            if not user:
                # 3. If no user exists, create new user
                user = cls.create_user_without_email_password(telegram_data)
            else:
                # If user exists, update user information
                user.first_name = user_info.get("first_name", "")
                user.last_name = user_info.get("last_name", "")
                user.save(update_fields=["first_name", "last_name"])

                # Prepare metadata for update, filtering out None values
                metadata_items = {}

                # Add optional fields only if they have values
                if user_info.get("username"):
                    metadata_items["telegram_username"] = user_info.get("username")
                if user_info.get("language_code"):
                    metadata_items["telegram_language_code"] = user_info.get(
                        "language_code"
                    )
                if user_info.get("photo_url"):
                    metadata_items["telegram_photo_url"] = user_info.get("photo_url")
                if telegram_data.get("bot_info"):
                    metadata_items["bot_info"] = telegram_data.get("bot_info")
                if telegram_data.get("chat_instance"):
                    metadata_items["chat_instance"] = telegram_data.get("chat_instance")
                if telegram_data.get("chat_type"):
                    metadata_items["chat_type"] = telegram_data.get("chat_type")
                if telegram_data.get("auth_date"):
                    metadata_items["auth_date"] = telegram_data.get("auth_date")

                # Update metadata only if there are items to update
                if metadata_items:
                    user.store_value_in_private_metadata(metadata_items)
                    user.save(update_fields=["private_metadata"])

            # 4. Update last login time
            update_user_last_login_if_required(user)

            # 5. Generate token
            tokens = cls.generate_token_for_user(user)

            return cls(
                token=tokens["token"],
                refresh_token=tokens["refresh_token"],
                csrf_token=tokens["csrf_token"],
                user=user,
                errors=[],
            )

        except ValidationError as e:
            return cls(
                token=None,
                refresh_token=None,
                csrf_token=None,
                user=None,
                errors=[
                    {
                        "field": "init_data_raw",
                        "message": str(e),
                        "code": AccountErrorCode.INVALID.value,
                    }
                ],
            )
