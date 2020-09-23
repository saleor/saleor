import json
import logging
from typing import Optional
from urllib.parse import urlencode

import requests
from authlib.jose import jwt
from authlib.oidc.core import CodeIDToken
from django.core.cache import cache
from django.core.exceptions import ValidationError

from ...account.models import User
from ...core.jwt import JWT_ACCESS_TYPE, jwt_encode, jwt_user_payload
from ...core.utils import build_absolute_uri
from ...core.utils.url import prepare_url
from ..error_codes import PluginErrorCode
from .exceptions import AuthenticationError

JWKS_KEY = "auth0_jwks"
JWKS_CACHE_TIME = 60 * 60 * 24  # 1 day
JWKS_PATH = "/.well-known/jwks.json"

logger = logging.getLogger(__name__)


def prepare_redirect_url(
    plugin_id, storefront_redirect_url: Optional[str] = None
) -> str:
    """Prepare redirect url used by auth0 to return to Saleor.

    /plugins/mirumee.authentication.auth0/callback?redirectUrl=https://localhost:3000/
    """
    params = {}
    if storefront_redirect_url:
        params["redirectUrl"] = storefront_redirect_url
    redirect_url = build_absolute_uri(f"/plugins/{plugin_id}/callback")

    return prepare_url(urlencode(params), redirect_url)  # type: ignore


def get_auth_service_url(domain: str, service):
    return f"https://{domain}{service}"


def fetch_jwks(jwks_url) -> Optional[dict]:
    response = None
    try:
        response = requests.get(jwks_url)
        jwks = response.json()
    except requests.exceptions.RequestException:
        logger.error("Unable to fetch jwks from %s", jwks_url)
        raise AuthenticationError("Unable to finalize the authentication process.")
    except json.JSONDecodeError:
        content = response.content if response else "Unable to find the response"
        logger.exception(
            "Unable to decode the response from Auth0 with jwks. Response: %s", content
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


def create_jwt_token(id_payload: CodeIDToken, user: User, access_token: str) -> str:
    additional_payload = {
        "exp": id_payload["exp"],
        "auth0_access_key": access_token,
    }
    jwt_payload = jwt_user_payload(
        user,
        JWT_ACCESS_TYPE,
        exp_delta=None,  # we pass exp from auth0 in additional_payload
        additional_payload=additional_payload,
    )
    return jwt_encode(jwt_payload)


def get_valid_auth_tokens_from_auth0_payload(
    token_data: dict, domain: str, get_or_create=True
):
    id_token = token_data["id_token"]
    keys = get_jwks_keys_from_cache_or_fetch(get_auth_service_url(domain, JWKS_PATH))

    claims = jwt.decode(id_token, keys, claims_cls=CodeIDToken)
    claims.validate()
    # raises JoseError

    refresh_token = token_data.get("refresh_token")

    if get_or_create:
        user, created = User.objects.get_or_create(
            email=claims["email"],
            defaults={"is_active": True, "email": claims["email"]},
        )
    else:
        user = User.objects.filter(email=claims["email"], is_active=True).first()
        if not user:
            raise ValidationError(
                "User does not exist.", code=PluginErrorCode.INVALID.value,
            )

    tokens = {
        "token": create_jwt_token(claims, user, token_data["access_token"]),
    }
    if refresh_token:
        tokens["refreshToken"] = refresh_token
    return tokens
