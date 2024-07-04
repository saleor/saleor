from datetime import timedelta
from typing import Optional

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .....account.error_codes import AccountErrorCode
from .....core.jwt import (
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    JWT_REFRESH_TYPE,
    create_access_token,
)
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_AUTH
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ...types import User
from .utils import _does_token_match, get_payload, get_user


class RefreshToken(BaseMutation):
    """Mutation that refresh user token and returns token and user data."""

    token = graphene.String(description="JWT token, required to authenticate.")
    user = graphene.Field(User, description="A user instance.")

    class Arguments:
        refresh_token = graphene.String(required=False, description="Refresh token.")
        csrf_token = graphene.String(
            required=False,
            description=(
                "CSRF token required to refresh token. This argument is "
                "required when `refreshToken` is provided as a cookie."
            ),
        )

    class Meta:
        description = (
            "Refresh JWT token. Mutation tries to take refreshToken from the input. "
            "If it fails it will try to take `refreshToken` from the http-only cookie "
            f"`{JWT_REFRESH_TOKEN_COOKIE_NAME}`. "
            "`csrfToken` is required when `refreshToken` is provided as a cookie."
        )
        doc_category = DOC_CATEGORY_AUTH
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def get_refresh_token_payload(cls, refresh_token):
        try:
            payload = get_payload(refresh_token)
        except ValidationError as e:
            raise ValidationError({"refreshToken": e})
        return payload

    @classmethod
    def get_refresh_token(
        cls, info: ResolveInfo, refresh_token: Optional[str] = None
    ) -> Optional[str]:
        request = info.context
        if refresh_token is None:
            refresh_token = request.COOKIES.get(JWT_REFRESH_TOKEN_COOKIE_NAME, None)
        return refresh_token

    @classmethod
    def clean_refresh_token(cls, refresh_token):
        if refresh_token is None:
            raise ValidationError(
                {
                    "refresh_token": ValidationError(
                        "Missing refreshToken",
                        code=AccountErrorCode.JWT_MISSING_TOKEN.value,
                    )
                }
            )
        payload = cls.get_refresh_token_payload(refresh_token)
        if payload["type"] != JWT_REFRESH_TYPE:
            raise ValidationError(
                {
                    "refresh_token": ValidationError(
                        "Incorrect refreshToken",
                        code=AccountErrorCode.JWT_INVALID_TOKEN.value,
                    )
                }
            )
        return payload

    @classmethod
    def clean_csrf_token(cls, csrf_token, payload):
        if not csrf_token:
            msg = "CSRF token is required when refreshToken is provided by the cookie"
            raise ValidationError(
                {
                    "csrf_token": ValidationError(
                        msg,
                        code=AccountErrorCode.REQUIRED.value,
                    )
                }
            )
        is_valid = _does_token_match(csrf_token, payload["csrfToken"])
        if not is_valid:
            raise ValidationError(
                {
                    "csrf_token": ValidationError(
                        "Invalid csrf token",
                        code=AccountErrorCode.JWT_INVALID_CSRF_TOKEN.value,
                    )
                }
            )

    @classmethod
    def get_user(cls, payload):
        try:
            user = get_user(payload)
        except ValidationError as e:
            raise ValidationError({"refresh_token": e})
        return user

    @classmethod
    def perform_mutation(
        cls, _root, info: ResolveInfo, /, *, csrf_token=None, refresh_token=None
    ):
        need_csrf = refresh_token is None
        refresh_token = cls.get_refresh_token(info, refresh_token)
        payload = cls.clean_refresh_token(refresh_token)

        # None when we got refresh_token from cookie.
        if need_csrf:
            cls.clean_csrf_token(csrf_token, payload)

        additional_payload = {}
        if audience := payload.get("aud"):
            additional_payload["aud"] = audience
        user = get_user(payload)
        token = create_access_token(user, additional_payload=additional_payload)
        if user and not user.is_anonymous:
            time_now = timezone.now()
            threshold_delta = timedelta(
                seconds=settings.TOKEN_UPDATE_LAST_LOGIN_THRESHOLD
            )
            if not user.last_login or user.last_login + threshold_delta < time_now:
                user.last_login = time_now
                user.save(update_fields=["last_login", "updated_at"])
        return cls(errors=[], user=user, token=token)
