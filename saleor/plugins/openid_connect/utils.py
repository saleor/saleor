import json
import logging
from datetime import datetime
from typing import List, Optional

import requests
from authlib.jose import JWTClaims, jwt
from authlib.jose.errors import DecodeError, JoseError
from authlib.oidc.core import CodeIDToken
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import QuerySet
from django.utils.timezone import make_aware
from jwt import PyJWTError

from ...account.models import User
from ...core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_OWNER_FIELD,
    JWT_REFRESH_TYPE,
    PERMISSIONS_FIELD,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)
from ...core.permissions import get_permission_names, get_permissions_from_codenames
from ...graphql.account.mutations.authentication import (
    _does_token_match,
    _get_new_csrf_token,
)
from ..error_codes import PluginErrorCode
from ..models import PluginConfiguration
from . import PLUGIN_ID
from .const import SALEOR_STAFF_PERMISSION
from .exceptions import AuthenticationError

JWKS_KEY = "oauth_jwks"
JWKS_CACHE_TIME = 60 * 60  # 1 hour
USER_INFO_DEFAULT_CACHE_TIME = 60 * 60  # 1 hour

REQUEST_TIMEOUT = 5


OAUTH_TOKEN_REFRESH_FIELD = "oauth_refresh_token"
CSRF_FIELD = "csrf_token"


logger = logging.getLogger(__name__)


def fetch_jwks(jwks_url) -> Optional[dict]:
    """Fetch JSON Web Key Sets from a provider.

    Fetched keys will be stored in the cache to the reduced amount of possible
    requests.
    :raises AuthenticationError
    """
    response = None
    try:
        response = requests.get(jwks_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
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
    cache.set(JWKS_KEY, keys, JWKS_CACHE_TIME)
    return keys


def get_jwks_keys_from_cache_or_fetch(jwks_url: str) -> dict:
    jwks_keys = cache.get(JWKS_KEY)
    if jwks_keys is None:
        jwks_keys = fetch_jwks(jwks_url)
    return jwks_keys


def get_user_info_from_cache_or_fetch(
    user_info_url: str, access_token: str, exp_time: Optional[int]
) -> Optional[dict]:
    user_info_data = cache.get(f"{PLUGIN_ID}.{access_token}", None)

    if not user_info_data:
        user_info_data = get_user_info(user_info_url, access_token)
        cache_time = USER_INFO_DEFAULT_CACHE_TIME

        if exp_time:
            now_ts = int(datetime.now().timestamp())
            exp_delta = exp_time - now_ts
            cache_time = exp_delta if exp_delta > 0 else cache_time

        if user_info_data:
            cache.set(f"{PLUGIN_ID}.{access_token}", user_info_data, cache_time)

    # user_info_data is None when we were not able to use an access token to fetch
    # the user info data
    return user_info_data


def get_user_info(user_info_url, access_token) -> Optional[dict]:
    try:
        response = requests.get(
            user_info_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.warning(
            "Fetching OIDC user info failed. HTTP error occurred",
            extra={"user_info_url": user_info_url, "error": e},
        )
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(
            "Fetching OIDC user info failed",
            extra={"user_info_url": user_info_url, "error": e},
        )
        return None
    except json.JSONDecodeError as e:
        logger.warning(
            "Invalid OIDC user info response",
            extra={"user_info_url": user_info_url, "error": e},
        )
        return None


def decode_access_token(token, jwks_url):
    try:
        return get_decoded_token(token, jwks_url)
    except (JoseError, ValueError) as e:
        logger.info(
            "Invalid OIDC access token format", extra={"error": e, "jwks_url": jwks_url}
        )
        return None


def get_user_from_oauth_access_token_in_jwt_format(
    token_payload: JWTClaims,
    user_info_url: str,
    access_token: str,
    use_scope_permissions: bool,
    audience: str,
):
    try:
        token_payload.validate()
    except (JoseError, ValueError) as e:
        logger.info(
            "OIDC access token validation failed",
            extra={"error": e, "user_info_url": user_info_url},
        )
        return None

    user_info = get_user_info_from_cache_or_fetch(
        user_info_url,
        access_token,
        token_payload["exp"],
    )
    if not user_info:
        logger.info(
            "Failed to fetch user info for a valid OIDC access token",
            extra={"token_exp": token_payload["exp"], "user_info_url": user_info_url},
        )
        return None

    try:
        user = get_or_create_user_from_payload(
            user_info, user_info_url, last_login=token_payload.get("iat")
        )
    except AuthenticationError as e:
        logger.info("Unable to create a user object", extra={"error": e})
        return None

    scope = token_payload.get("scope")
    token_permissions = token_payload.get("permissions", [])

    # check if token contains expected aud
    aud = token_payload.get("aud")
    if not audience:
        audience_in_token = False
    elif isinstance(aud, list):
        audience_in_token = audience in aud
    else:
        audience_in_token = audience == aud

    is_staff_id = SALEOR_STAFF_PERMISSION

    if use_scope_permissions and audience_in_token:
        permissions = get_saleor_permissions_qs_from_scope(scope)
        if not permissions and token_permissions:
            permissions = get_saleor_permissions_from_list(token_permissions)
        user.effective_permissions = permissions
        is_staff_in_scope = is_staff_id in scope
        is_staff_in_token_permissions = is_staff_id in token_permissions
        if is_staff_in_scope or is_staff_in_token_permissions or permissions:
            if not user.is_staff:
                user.is_staff = True
                user.save(update_fields=["is_staff"])
        elif user.is_staff:
            user.is_staff = False
            user.save(update_fields=["is_staff"])
    else:
        user.is_staff = False

    return user


def get_user_from_oauth_access_token(
    access_token: str,
    jwks_url: str,
    user_info_url: str,
    use_scope_permissions: bool,
    audience: str,
):
    # we try to decode token to define if the structure is a jwt format.
    access_token_jwt_payload = decode_access_token(access_token, jwks_url)
    if access_token_jwt_payload:
        return get_user_from_oauth_access_token_in_jwt_format(
            access_token_jwt_payload,
            user_info_url=user_info_url,
            access_token=access_token,
            use_scope_permissions=use_scope_permissions,
            audience=audience,
        )

    user_info = get_user_info_from_cache_or_fetch(
        user_info_url, access_token, exp_time=None
    )
    if not user_info:
        logger.info(
            "Failed to fetch OIDC user info", extra={"user_info_url": user_info_url}
        )
        return None
    user = get_or_create_user_from_payload(user_info, oauth_url=user_info_url)
    if not use_scope_permissions:
        user.is_staff = False
    return user


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
    }
    if permissions is not None:
        additional_payload[PERMISSIONS_FIELD] = permissions

    jwt_payload = jwt_user_payload(
        user,
        JWT_ACCESS_TYPE,
        exp_delta=None,  # we pass exp from auth service, in additional_payload
        additional_payload=additional_payload,
        token_owner=owner,
    )
    return jwt_encode(jwt_payload)


def create_jwt_refresh_token(user: User, refresh_token: str, csrf: str, owner: str):
    additional_payload = {
        OAUTH_TOKEN_REFRESH_FIELD: refresh_token,
        CSRF_FIELD: csrf,
    }
    jwt_payload = jwt_user_payload(
        user,
        JWT_REFRESH_TYPE,
        # oauth_refresh_token has own expiration time. No need to duplicate it here
        exp_delta=None,
        additional_payload=additional_payload,
        token_owner=owner,
    )
    return jwt_encode(jwt_payload)


def get_decoded_token(token, jwks_url, claims_cls=None):
    keys = get_jwks_keys_from_cache_or_fetch(jwks_url)
    decoded_token = jwt.decode(token, keys, claims_cls=claims_cls)
    return decoded_token


def get_parsed_id_token(token_data, jwks_url) -> CodeIDToken:
    id_token = token_data.get("id_token")
    if not id_token:
        raise AuthenticationError("Missing ID Token.")
    try:
        decoded_token = get_decoded_token(id_token, jwks_url, CodeIDToken)
        decoded_token.validate()
        return decoded_token
    except DecodeError:
        logger.warning("Unable to decode provided token", exc_info=True)
        raise AuthenticationError("Unable to decode provided token")
    except (JoseError, ValueError):
        logger.warning("Token validation failed", exc_info=True)
        raise AuthenticationError("Token validation failed")


def get_or_create_user_from_payload(
    payload: dict, oauth_url: str, last_login: Optional[int] = None
) -> User:
    oidc_metadata_key = f"oidc-{oauth_url}"
    user_email = payload.get("email")
    if not user_email:
        raise AuthenticationError("Missing user's email.")

    sub = payload.get("sub")
    get_kwargs = {"private_metadata__contains": {oidc_metadata_key: sub}}
    if not sub:
        get_kwargs = {"email": user_email}
        logger.warning("Missing sub section in OIDC payload")

    defaults_create = {
        "is_active": True,
        "email": user_email,
        "first_name": payload.get("given_name", ""),
        "last_name": payload.get("family_name", ""),
        "private_metadata": {oidc_metadata_key: sub},
    }
    try:
        user = User.objects.get(**get_kwargs)
    except User.DoesNotExist:
        user, _ = User.objects.get_or_create(
            email=user_email,
            defaults=defaults_create,
        )
    except User.MultipleObjectsReturned:
        logger.warning("Multiple users returned for single OIDC sub ID")
        user, _ = User.objects.get_or_create(
            email=user_email,
            defaults=defaults_create,
        )

    if not user.is_active:  # it is true only if we fetch disabled user.
        raise AuthenticationError("Unable to log in.")

    _update_user_details(
        user=user,
        oidc_key=oidc_metadata_key,
        user_email=user_email,
        sub=sub,  # type: ignore
        last_login=last_login,
    )

    return user


def _update_user_details(
    user: User, oidc_key: str, user_email: str, sub: str, last_login: Optional[int]
):
    user_sub = user.get_value_from_private_metadata(oidc_key)
    fields_to_save = []
    if user_sub != sub:
        user.store_value_in_private_metadata({oidc_key: sub})
        fields_to_save.append("private_metadata")

    if user.email != user_email:
        if User.objects.filter(email=user_email).exists():
            logger.warning(
                "Unable to update user email as the new one already exists in DB",
                extra={"oidc_key": oidc_key},
            )
            return
        user.email = user_email
        fields_to_save.append("email")
    if last_login:
        if not user.last_login or user.last_login.timestamp() < last_login:
            login_time = make_aware(datetime.fromtimestamp(last_login))
            user.last_login = login_time
            fields_to_save.append("last_login")

    if fields_to_save:
        user.save(update_fields=fields_to_save)


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
        tokens["refresh_token"] = create_jwt_refresh_token(
            user, refresh_token, csrf_token, owner
        )
        tokens["csrf_token"] = csrf_token
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
        is_valid = _does_token_match(csrf_token, refresh_payload[CSRF_FIELD])
        if not is_valid:
            raise ValidationError(
                {
                    "csrfToken": ValidationError(
                        "CSRF token doesn't match.",
                        code=PluginErrorCode.INVALID.value,
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
    incorrect_fields = []
    if plugin_configuration.active:
        urls_to_validate = {}
        if any(
            [configuration["oauth_authorization_url"], configuration["oauth_token_url"]]
        ):
            urls_to_validate.update(
                {
                    "json_web_key_set_url": configuration["json_web_key_set_url"],
                    "oauth_authorization_url": configuration["oauth_authorization_url"],
                    "oauth_token_url": configuration["oauth_token_url"],
                }
            )

        elif configuration["user_info_url"]:
            urls_to_validate.update(
                {
                    "json_web_key_set_url": configuration["json_web_key_set_url"],
                    "user_info_url": configuration["user_info_url"],
                }
            )
        else:
            incorrect_fields.extend(
                [
                    "json_web_key_set_url",
                    "oauth_authorization_url",
                    "oauth_token_url",
                    "user_info_url",
                ]
            )

        incorrect_fields.extend(get_incorrect_or_missing_urls(urls_to_validate))
        if not configuration["client_id"]:
            incorrect_fields.append("client_id")
        if not configuration["client_secret"]:
            incorrect_fields.append("client_secret")
        return incorrect_fields


def get_saleor_permissions_qs_from_scope(scope: str) -> QuerySet[Permission]:
    scope_list = scope.lower().strip().split()
    return get_saleor_permissions_from_list(scope_list)


def get_saleor_permissions_from_list(permissions: list) -> QuerySet[Permission]:
    saleor_permissions_str = [s for s in permissions if s.startswith("saleor:")]
    if SALEOR_STAFF_PERMISSION in saleor_permissions_str:
        saleor_permissions_str.remove(SALEOR_STAFF_PERMISSION)
    if not saleor_permissions_str:
        return Permission.objects.none()

    permission_codenames = list(
        map(lambda perm: perm.replace("saleor:", ""), saleor_permissions_str)
    )
    permissions = get_permissions_from_codenames(permission_codenames)
    return permissions


def get_saleor_permission_names(permissions: QuerySet) -> List[str]:
    permission_names = get_permission_names(permissions)
    return list(permission_names)
