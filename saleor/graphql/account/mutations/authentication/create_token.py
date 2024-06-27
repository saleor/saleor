from datetime import timedelta
from math import ceil
from typing import Optional

import graphene
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address
from django.utils import timezone

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....account.utils import retrieve_user_by_email
from .....core.jwt import create_access_token, create_refresh_token
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_38
from ....core.doc_category import DOC_CATEGORY_AUTH
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....site.dataloaders import get_site_promise
from ...types import User
from .utils import _get_new_csrf_token

MIN_DELAY = 1
MAX_DELAY = 3600
ATTEMPT_COUNTER_EXPIRE_TIME = 300


class CreateToken(BaseMutation):
    """Mutation that authenticates a user and returns token and user data."""

    class Arguments:
        email = graphene.String(required=True, description="Email of a user.")
        password = graphene.String(required=True, description="Password of a user.")
        audience = graphene.String(
            required=False,
            description=(
                "The audience that will be included to JWT tokens with "
                "prefix `custom:`." + ADDED_IN_38
            ),
        )

    class Meta:
        description = "Create JWT token."
        doc_category = DOC_CATEGORY_AUTH
        error_type_class = AccountError
        error_type_field = "account_errors"

    token = graphene.String(description="JWT token, required to authenticate.")
    refresh_token = graphene.String(
        description="JWT refresh token, required to re-generate access token."
    )
    csrf_token = graphene.String(
        description="CSRF token required to re-generate access token."
    )
    user = graphene.Field(User, description="A user instance.")

    @staticmethod
    def is_ip_address_valid(ip):
        if not ip:
            return False
        try:
            validate_ipv46_address(ip)
            return True
        except ValidationError:
            return False

    @classmethod
    def get_ip_address(cls, info: ResolveInfo) -> str:
        proxy_address = info.context.META.get("HTTP_X_FORWARDED_FOR", "").strip()
        remote_address = info.context.META.get("REMOTE_ADDR", "").strip()
        ip = proxy_address or remote_address
        if ip and cls.is_ip_address_valid(ip):
            return ip
        # TODO zedzior
        return ""

    @classmethod
    def get_cache_key_failed_ip(cls, ip: str) -> str:
        return f"login:failed:ip:{ip}"

    @classmethod
    def get_cache_key_failed_ip_with_user(cls, ip: str, user_id) -> str:
        return f"login:failed:ip:{ip}:user:{user_id}"

    @classmethod
    def get_cache_key_blocked_ip(cls, ip: str) -> str:
        return f"login:blocked:ip:{ip}"

    @classmethod
    def clear_cache(cls, keys: list[str]):
        for key in keys:
            cache.delete(key)

    @classmethod
    def get_delay_time(cls, ip_attempts_count: int, ip_user_attempts_count: int) -> int:
        ip_delay = (
            2 ^ (ceil(ip_attempts_count / 10) - 1)
            if ip_attempts_count < 100
            else MAX_DELAY
        )
        ip_user_delay = (
            2 ^ (ip_attempts_count - 1) if ip_user_attempts_count < 10 else MAX_DELAY
        )
        return max(ip_delay, ip_user_delay)

    @classmethod
    def block_next_attempt(cls, block_key: str, time_delta: int):
        next_attempt_time = timezone.now() + timedelta(seconds=time_delta)
        cache.set(block_key, next_attempt_time, timeout=time_delta)

    @classmethod
    def increment_attempt(cls, key: str) -> int:
        # `cache.add` returns False and does nothing, when key already exists
        if not cache.add(key, 1, timeout=ATTEMPT_COUNTER_EXPIRE_TIME):
            return cache.incr(key, 1)
        return 1

    @classmethod
    def authenticate_with_throttling(
        cls, info: ResolveInfo, email, password
    ) -> Optional[models.User]:
        ip = cls.get_ip_address(info)
        if not ip:
            # TODO zedzior
            pass

        ip_key = cls.get_cache_key_failed_ip(ip)
        block_key = cls.get_cache_key_blocked_ip(ip)

        # check if next login attempt is blocked
        if next_attempt_time := cache.get(block_key):
            raise ValidationError(
                {
                    "email": ValidationError(
                        f"Due to too many failed authentication attempts, "
                        f"logining has been suspended till {next_attempt_time}.",
                        code=AccountErrorCode.LOGIN_ATTEMPT_DELAYED.value,
                    )
                }
            )

        # block the IP address before the next attempt to prevent concurrent requests
        cls.block_next_attempt(block_key, MIN_DELAY)

        ip_user_attempts_count = MIN_DELAY
        # retrieve user from credential
        if user := retrieve_user_by_email(email):
            ip_user_key = cls.get_cache_key_failed_ip_with_user(ip, user.pk)
            if user.check_password(password):
                # clear cache entries when login successful
                cls.clear_cache([ip_key, ip_user_key, block_key])
                return user

            else:
                # increment failed attempt for known user
                ip_user_attempts_count = cls.increment_attempt(ip_user_key)

        # increment failed attempt for whatever user
        ip_attempts_count = cls.increment_attempt(ip_key)

        # calculate next allowed login attempt time and block the IP till the time
        delay = cls.get_delay_time(ip_attempts_count, ip_user_attempts_count)
        cls.block_next_attempt(block_key, delay)

        return None

    @classmethod
    def _retrieve_user_from_credentials(cls, email, password) -> Optional[models.User]:
        user = retrieve_user_by_email(email)
        if user and user.check_password(password):
            return user
        return None

    @classmethod
    def get_user(cls, info: ResolveInfo, email, password):
        user = cls.authenticate_with_throttling(info, email, password)
        if not user:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "Please, enter valid credentials",
                        code=AccountErrorCode.INVALID_CREDENTIALS.value,
                    )
                }
            )

        site_settings = get_site_promise(info.context).get().settings
        if (
            not user.is_confirmed
            and not site_settings.allow_login_without_confirmation
            and site_settings.enable_account_confirmation_by_email
        ):
            raise ValidationError(
                {
                    "email": ValidationError(
                        "Account needs to be confirmed via email.",
                        code=AccountErrorCode.ACCOUNT_NOT_CONFIRMED.value,
                    )
                }
            )

        if not user.is_active:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "Account inactive.",
                        code=AccountErrorCode.INACTIVE.value,
                    )
                }
            )
        return user

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, audience=None, email, password
    ):
        additional_paylod = {}

        csrf_token = _get_new_csrf_token()
        refresh_additional_payload = {
            "csrfToken": csrf_token,
        }
        if audience:
            additional_paylod["aud"] = f"custom:{audience}"
            refresh_additional_payload["aud"] = f"custom:{audience}"

        user = cls.get_user(info, email, password)
        access_token = create_access_token(user, additional_payload=additional_paylod)
        refresh_token = create_refresh_token(
            user, additional_payload=refresh_additional_payload
        )
        setattr(info.context, "refresh_token", refresh_token)
        info.context.user = user
        info.context._cached_user = user
        time_now = timezone.now()
        threshold_delta = timedelta(seconds=settings.TOKEN_UPDATE_LAST_LOGIN_THRESHOLD)

        if not user.last_login or user.last_login + threshold_delta < time_now:
            user.last_login = time_now
            user.save(update_fields=["last_login", "updated_at"])
        return cls(
            errors=[],
            user=user,
            token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )
