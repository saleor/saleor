import json
import logging
from typing import Optional
from urllib.parse import urlencode

import requests
from django.core.cache import cache

from ...core.utils import build_absolute_uri
from ...core.utils.url import prepare_url
from .exceptions import AuthenticationError

JWKS_KEY = "auth0_jwks"
JWKS_CACHE_TIME = 60 * 60 * 24  # 1 day


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


def fetch_jwks(jwks_url) -> Optional[dict]:
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
