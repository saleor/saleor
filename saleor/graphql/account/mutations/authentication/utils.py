import jwt
from django.core.exceptions import ValidationError
from django.middleware.csrf import (  # type: ignore
    _get_new_csrf_string,
    _mask_cipher_secret,
    _unmask_cipher_token,
)
from django.utils.crypto import constant_time_compare

from .....account.error_codes import AccountErrorCode
from .....core.jwt import PERMISSIONS_FIELD, get_user_from_payload, jwt_decode
from .....permission.enums import get_permissions_from_names


def get_user(payload):
    try:
        user = get_user_from_payload(payload)
    except Exception:
        user = None
    if not user:
        raise ValidationError(
            "Invalid token", code=AccountErrorCode.JWT_INVALID_TOKEN.value
        )
    permissions = payload.get(PERMISSIONS_FIELD)
    if permissions is not None:
        user.effective_permissions = get_permissions_from_names(permissions)
    return user


def get_payload(token):
    try:
        payload = jwt_decode(token)
    except jwt.ExpiredSignatureError:
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


def _get_new_csrf_token() -> str:
    return _mask_cipher_secret(_get_new_csrf_string())


def _does_token_match(token: str, csrf_token: str) -> bool:
    return constant_time_compare(
        _unmask_cipher_token(token),
        _unmask_cipher_token(csrf_token),
    )
