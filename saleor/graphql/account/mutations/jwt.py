import graphene
import jwt
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.middleware.csrf import _compare_salted_tokens, _get_new_csrf_token
from django.utils import timezone
from graphene.types.generic import GenericScalar

from ....account import models
from ....account.error_codes import AccountErrorCode
from ....core.jwt import (
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    JWT_REFRESH_TYPE,
    create_access_token,
    create_refresh_token,
    jwt_decode,
)
from ...core.mutations import BaseMutation
from ...core.types.common import AccountError
from ..types import User


def get_payload(token):
    try:
        payload = jwt_decode(token)
    except jwt.ExpiredSignature:
        raise ValidationError(
            "Signature has expired", code=AccountErrorCode.JWT_SIGNATURE_EXPIRED.value
        )
    except jwt.DecodeError:
        raise ValidationError(
            "Error decoding signature", code=AccountErrorCode.JWT_DECODE_ERROR.value
        )
    except jwt.InvalidTokenError:
        raise ValidationError(
            "Invalid token", code=AccountErrorCode.JWT_INVALID_TOKEN.value
        )
    return payload


class CreateToken(BaseMutation):
    """Mutation that authenticates a user and returns token and user data."""

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    class Meta:
        description = "Create JWT token."
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

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = authenticate(
            request=info.context, username=data["email"], password=data["password"],
        )
        if not user:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "Please, enter valid credentials",
                        code=AccountErrorCode.INVALID_CREDENTIALS.value,
                    )
                }
            )
        access_token = create_access_token(user)
        csrf_token = _get_new_csrf_token()
        refresh_token = create_refresh_token(user, {"csrfToken": csrf_token})
        info.context.refresh_token = refresh_token
        info.context._cached_user = user
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return cls(
            errors=[],
            user=user,
            token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )


class RefreshToken(BaseMutation):
    """Mutation that refresh user token and returns token and user data."""

    token = graphene.String(description="JWT token, required to authenticate.")
    user = graphene.Field(User, description="A user instance.")

    class Arguments:
        refresh_token = graphene.String(required=False, description="Refresh token.")
        csrf_token = graphene.String(
            required=True, description="CSRF token required to refresh token."
        )

    class Meta:
        description = (
            "Refresh JWT token. Mutation tries to take refreshToken from "
            f"the http-only cookie {JWT_REFRESH_TOKEN_COOKIE_NAME}. If it "
            "fails it will try to take refreshToken provided as an argument."
        )
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
    def get_refresh_token(cls, info, data):
        request = info.context
        refresh_token = request.COOKIES.get(JWT_REFRESH_TOKEN_COOKIE_NAME, None)
        refresh_token = refresh_token or data.get("refresh_token")
        return refresh_token

    @classmethod
    def clean_refresh_token(cls, refresh_token):
        if not refresh_token:
            raise ValidationError(
                {
                    "refreshToken": ValidationError(
                        "Missing refreshToken",
                        code=AccountErrorCode.JWT_MISSING_TOKEN.value,
                    )
                }
            )
        payload = cls.get_refresh_token_payload(refresh_token)
        if payload["type"] != JWT_REFRESH_TYPE:
            raise ValidationError(
                {
                    "refreshToken": ValidationError(
                        "Incorrect refreshToken",
                        code=AccountErrorCode.JWT_INVALID_TOKEN.value,
                    )
                }
            )
        return payload

    @classmethod
    def clean_csrf_token(cls, csrf_token, payload):
        is_valid = _compare_salted_tokens(csrf_token, payload["csrfToken"])
        if not is_valid:
            raise ValidationError(
                {
                    "csrfToken": ValidationError(
                        "Invalid csrf token",
                        code=AccountErrorCode.JWT_INVALID_CSRF_TOKEN.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        refresh_token = cls.get_refresh_token(info, data)
        payload = cls.clean_refresh_token(refresh_token)

        csrf_token = data.get("csrf_token")
        cls.clean_csrf_token(csrf_token, payload)

        user = models.User.objects.filter(email=payload["email"]).first()
        token = create_access_token(user)
        return cls(errors=[], user=user, token=token)


class VerifyToken(BaseMutation):
    """Mutation that confirms if token is valid and also returns user data."""

    user = graphene.Field(User, description="User assigned to token.")
    is_valid = graphene.Boolean(
        default_value=False, description="Determine if token is valid or not."
    )
    payload = GenericScalar(description="JWT payload.")

    class Arguments:
        token = graphene.String(required=True, description="JWT token to validate.")

    class Meta:
        description = "Verify JWT token."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def get_payload(cls, token):
        try:
            payload = get_payload(token)
        except ValidationError as e:
            raise ValidationError({"token": e})
        return payload

    @classmethod
    def perform_mutation(cls, root, info, **data):
        token = data["token"]
        payload = cls.get_payload(token)
        user = models.User.objects.filter(email=payload["email"]).first()
        return cls(errors=[], user=user, is_valid=True, payload=payload)
