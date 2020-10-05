import json
import logging
from typing import List, Optional

import requests
from authlib.jose import jwt
from authlib.jose.errors import DecodeError, JoseError
from authlib.oidc.core import CodeIDToken
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.middleware.csrf import _compare_masked_tokens  # type: ignore
from django.middleware.csrf import _get_new_csrf_token
from jwt import PyJWTError

from ...account.models import User
from ...core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_REFRESH_TYPE,
    PERMISSIONS_FIELD,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)
from ...core.permissions import get_permission_names, get_permissions_from_codenames
from ...core.utils.url import validate_storefront_url
from ..error_codes import PluginErrorCode
from ..models import PluginConfiguration
from .exceptions import AuthenticationError

JWKS_KEY = "oauth_jwks"
JWKS_CACHE_TIME = 60 * 60  # 1 hour


OAUTH_TOKEN_REFRESH_FIELD = "oauth_refresh_token"
CSRF_FIELD = "csrf_token"

JWT_OWNER_FIELD = "owner"

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


def create_jwt_token(
    id_payload: CodeIDToken,
    user: User,
    access_token: str,
    permissions: Optional[List[str]],
    owner: str,
) -> str:
    additional_payload = {
        "exp": id_payload["exp"],
        "oauth_access_key": access_token,
        JWT_OWNER_FIELD: owner,
    }
    if permissions is not None:
        additional_payload[PERMISSIONS_FIELD] = permissions
    if permissions:
        user.is_staff = True
    jwt_payload = jwt_user_payload(
        user,
        JWT_ACCESS_TYPE,
        exp_delta=None,  # we pass exp from auth service, in additional_payload
        additional_payload=additional_payload,
    )
    return jwt_encode(jwt_payload)


def create_jwt_refresh_token(user: User, refresh_token: str, csrf: str, owner: str):
    additional_payload = {
        OAUTH_TOKEN_REFRESH_FIELD: refresh_token,
        CSRF_FIELD: csrf,
        JWT_OWNER_FIELD: owner,
    }
    jwt_payload = jwt_user_payload(
        user,
        JWT_REFRESH_TYPE,
        # oauth_refresh_token has own expiration time. No need to duplicate it here
        exp_delta=None,
        additional_payload=additional_payload,
    )
    return jwt_encode(jwt_payload)


def get_parsed_id_token(token_data, jwks_url) -> CodeIDToken:
    id_token = token_data.get("id_token")
    if not id_token:
        raise AuthenticationError("Missing ID Token.")
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
    user_email = claims.get("email")
    if not user_email:
        raise AuthenticationError("Missing user's email.")
    user, _ = User.objects.get_or_create(
        email=user_email,
        defaults={
            "is_active": True,
            "email": user_email,
            "first_name": claims.get("given_name", ""),
            "last_name": claims.get("family_name", ""),
        },
    )
    if not user.is_active:  # it is true only if we fetch disabled user.
        raise AuthenticationError("Unable to log in.")
    return user


def get_user_from_token(claims: CodeIDToken) -> User:
    user_email = claims.get("email")
    if not user_email:
        raise AuthenticationError("Missing user's email.")
    user = User.objects.filter(email=user_email, is_active=True).first()
    if not user:
        raise AuthenticationError("User does not exist.")
    return user


def is_owner_of_token_valid(token: str, owner: str) -> bool:
    try:
        payload = jwt_decode(token, verify_expiration=False)
        return payload.get(JWT_OWNER_FIELD, "") == owner
    except Exception:
        return False


def create_tokens_from_oauth_payload(
    token_data: dict,
    user: User,
    claims: CodeIDToken,
    permissions: Optional[List[str]],
    owner: str,
):
    refresh_token = token_data.get("refresh_token")
    access_token = token_data.get("access_token", "")

    tokens = {
        "token": create_jwt_token(claims, user, access_token, permissions, owner),
    }
    if refresh_token:
        csrf_token = _get_new_csrf_token()
        tokens["refreshToken"] = create_jwt_refresh_token(
            user, refresh_token, csrf_token, owner
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
        refresh_payload = jwt_decode(refresh_token, verify_expiration=True)
    except PyJWTError:
        raise ValidationError(
            {
                "refreshToken": ValidationError(
                    "Unable to decode the refresh token.",
                    code=PluginErrorCode.INVALID.value,
                )
            }
        )

    if not data.get("refreshToken"):
        if not refresh_payload.get(CSRF_FIELD):
            raise ValidationError(
                {
                    CSRF_FIELD: ValidationError(
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
        is_valid = _compare_masked_tokens(csrf_token, refresh_payload[CSRF_FIELD])
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


def get_incorrect_fields(plugin_configuration: "PluginConfiguration"):
    """Return missing or incorrect configuration fields for OpenIDConnectPlugin."""
    configuration = plugin_configuration.configuration
    configuration = {item["name"]: item["value"] for item in configuration}
    if plugin_configuration.active:
        urls_to_validate = {
            "json_web_key_set_url": configuration["json_web_key_set_url"],
            "oauth_authorization_url": configuration["oauth_authorization_url"],
            "oauth_token_url": configuration["oauth_token_url"],
        }
        incorrect_fields = get_incorrect_or_missing_urls(urls_to_validate)
        if not configuration["client_id"]:
            incorrect_fields.append("client_id")
        if not configuration["client_secret"]:
            incorrect_fields.append("client_secret")
        return incorrect_fields


def get_saleor_permissions_from_scope(scope: str) -> List[str]:
    if not scope:
        return []
    scope_list = scope.lower().strip().split()
    saleor_permissions_str = [s for s in scope_list if s.startswith("saleor:")]
    permission_codenames = list(
        map(lambda perm: perm.replace("saleor:", ""), saleor_permissions_str)
    )
    permissions = get_permissions_from_codenames(permission_codenames)
    permission_names = get_permission_names(permissions)
    return list(permission_names)
