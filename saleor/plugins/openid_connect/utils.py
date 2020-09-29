import json
import logging
from typing import List, Optional
from urllib.parse import urlencode

import requests
from authlib.jose import jwt
from authlib.jose.errors import DecodeError, JoseError
from authlib.oidc.core import CodeIDToken
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.middleware.csrf import _compare_masked_tokens  # type: ignore
from django.middleware.csrf import _get_new_csrf_token  # type: ignore
from jwt import PyJWTError

from ...account.models import User
from ...core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_REFRESH_TYPE,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)
from ...core.utils import build_absolute_uri
from ...core.utils.url import prepare_url, validate_storefront_url
from ..error_codes import PluginErrorCode
from .exceptions import AuthenticationError

JWKS_KEY = "oauth_jwks"
JWKS_CACHE_TIME = 60 * 60  # 1 hour

logger = logging.getLogger(__name__)


def validate_storefront_redirect_url(storefront_redirect_url: Optional[str]):
    if not storefront_redirect_url:
        raise ValidationError(
            {
                "redirectUrl": ValidationError(
                    "Missing redirect url.", code=PluginErrorCode.NOT_FOUND.value
                )
            }
        )
    try:
        validate_storefront_url(storefront_redirect_url)
    except ValidationError as error:
        raise ValidationError(
            {"redirectUrl": error}, code=PluginErrorCode.INVALID.value
        )


def prepare_redirect_url(
    plugin_id, storefront_redirect_url: Optional[str] = None
) -> str:
    """Prepare redirect url used by auth service to return to Saleor.

    /plugins/mirumee.authentication.openidconnect/callback?redirectUrl=https://localhost:3000/
    """
    params = {}
    if storefront_redirect_url:
        params["redirectUrl"] = storefront_redirect_url
    redirect_url = build_absolute_uri(f"/plugins/{plugin_id}/callback")

    return prepare_url(urlencode(params), redirect_url)  # type: ignore


def fetch_jwks(jwks_url) -> Optional[dict]:
    response = None
    try:
        response = requests.get(jwks_url)
        jwks = response.json()
    except requests.exceptions.RequestException:
        logger.exception("Unable to fetch jwks from %s", jwks_url)
        raise AuthenticationError("Unable to finalize the authentication process.")
    except json.JSONDecodeError:
        content = response.content if response else "Unable to find the response"
        logger.exception(
            "Unable to decode the response from auth service with jwks. "
            "Response: %s",
            content,
        )
        raise AuthenticationError("Unable to finalize the authentication process.")
    keys = jwks.get("keys", [])
    if not keys:
        logger.warning("List of JWKS keys is empty")
    return keys


def get_jwks_keys_from_cache_or_fetch(jwks_url: str) -> dict:
    jwks_keys = cache.get(JWKS_KEY)
    if jwks_keys is None:
        jwks_keys = fetch_jwks(jwks_url)
        cache.set(JWKS_KEY, jwks_keys, JWKS_CACHE_TIME)
    return jwks_keys


def create_jwt_token(id_payload: CodeIDToken, user: User, access_token: str,) -> str:
    additional_payload = {
        "exp": id_payload["exp"],
        "oauth_access_key": access_token,
    }
    jwt_payload = jwt_user_payload(
        user,
        JWT_ACCESS_TYPE,
        exp_delta=None,  # we pass exp from auth service, in additional_payload
        additional_payload=additional_payload,
    )
    return jwt_encode(jwt_payload)


def create_jwt_refresh_token(user: User, refresh_token: str, csrf: str):
    additional_payload = {"oauth_refresh_token": refresh_token, "csrf_token": csrf}
    jwt_payload = jwt_user_payload(
        user,
        JWT_REFRESH_TYPE,
        # oauth_refresh_token has own expiration time. No need to duplicate it here
        exp_delta=None,
        additional_payload=additional_payload,
    )
    return jwt_encode(jwt_payload)


def get_parsed_id_token(token_data, jwks_url) -> CodeIDToken:
    id_token = token_data["id_token"]
    keys = get_jwks_keys_from_cache_or_fetch(jwks_url)
    try:
        claims = jwt.decode(id_token, keys, claims_cls=CodeIDToken)
        claims.validate()
    except DecodeError:
        raise AuthenticationError("Unable to decode provided token")
    except JoseError:
        raise AuthenticationError("Token validation failed")
    return claims


def get_or_create_user_from_token(claims: CodeIDToken) -> User:
    user = User.objects.filter(email=claims["email"]).first()
    if not user:
        user = User.objects.create(
            is_active=True,
            email=claims["email"],
            first_name=claims.get("given_name", ""),
            last_name=claims.get("family_name", ""),
        )
    if not user.is_active:  # it is true only if we fetch disabled user.
        raise AuthenticationError("Unable to log in.",)
    return user


def get_user_from_token(claims: CodeIDToken) -> User:
    user = User.objects.filter(email=claims["email"], is_active=True).first()
    if not user:
        raise AuthenticationError("User does not exist.",)
    return user


def get_valid_auth_tokens_from_auth_payload(
    token_data: dict, user: User, claims: CodeIDToken
):
    refresh_token = token_data.get("refresh_token")

    tokens = {
        "token": create_jwt_token(claims, user, token_data["access_token"]),
    }
    if refresh_token:
        csrf_token = _get_new_csrf_token()
        tokens["refreshToken"] = create_jwt_refresh_token(
            user, refresh_token, csrf_token
        )
        tokens["csrfToken"] = csrf_token
    return tokens


def validate_refresh_token(refresh_token, data):
    csrf_token = data.get("csrfToken")
    if not refresh_token:
        raise ValidationError(
            {
                "refreshToken": ValidationError(
                    "Missing token.", code=PluginErrorCode.NOT_FOUND.value
                )
            }
        )
    try:
        refresh_payload = jwt_decode(refresh_token)
    except PyJWTError:
        raise ValidationError(
            {
                "refreshToken": ValidationError(
                    "Unable to decode provided token.",
                    code=PluginErrorCode.INVALID.value,
                )
            }
        )

    if not data.get("refreshToken"):
        if not refresh_payload.get("csrf_token"):
            raise ValidationError(
                {
                    "csrf_token": ValidationError(
                        "Missing CSRF token in refresh payload.",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )
        if not csrf_token:
            raise ValidationError(
                {
                    "csrfToken": ValidationError(
                        "CSRF token needs to be provided.",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )
        is_valid = _compare_masked_tokens(csrf_token, refresh_payload["csrf_token"])
        if not is_valid:
            raise ValidationError(
                {
                    "csrfToken": ValidationError(
                        "CSRF token doesn't match.", code=PluginErrorCode.INVALID.value,
                    )
                }
            )


def get_incorrect_or_missing_urls(urls: dict) -> List[str]:
    validator = URLValidator()
    incorrect_urls = []
    for field, url in urls.items():
        try:
            validator(url)
        except ValidationError:
            incorrect_urls.append(field)
    return incorrect_urls
