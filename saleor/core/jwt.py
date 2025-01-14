import datetime
from collections.abc import Iterable
from typing import Any

import graphene
import jwt
from django.conf import settings

from ..account.models import User
from ..app.models import App, AppExtension
from ..permission.enums import (
    get_permission_names,
    get_permissions_from_codenames,
    get_permissions_from_names,
)
from ..permission.models import Permission
from .jwt_manager import get_jwt_manager

JWT_ACCESS_TYPE = "access"
JWT_REFRESH_TYPE = "refresh"
JWT_THIRDPARTY_ACCESS_TYPE = "thirdparty"
JWT_REFRESH_TOKEN_COOKIE_NAME = "refreshToken"

APP_KEY_FIELD = "app"
PERMISSIONS_FIELD = "permissions"
USER_PERMISSION_FIELD = "user_permissions"
JWT_SALEOR_OWNER_NAME = "saleor"
JWT_OWNER_FIELD = "owner"


def jwt_base_payload(
    exp_delta: datetime.timedelta | None, token_owner: str
) -> dict[str, Any]:
    utc_now = datetime.datetime.now(tz=datetime.UTC)

    payload = {
        "iat": utc_now,
        JWT_OWNER_FIELD: token_owner,
        "iss": get_jwt_manager().get_issuer(),
    }
    if exp_delta:
        payload["exp"] = utc_now + exp_delta
    return payload


def jwt_user_payload(
    user: User,
    token_type: str,
    exp_delta: datetime.timedelta | None,
    additional_payload: dict[str, Any] | None = None,
    token_owner: str = JWT_SALEOR_OWNER_NAME,
) -> dict[str, Any]:
    payload = jwt_base_payload(exp_delta, token_owner)
    payload.update(
        {
            "token": user.jwt_token_key,
            "email": user.email,
            "type": token_type,
            "user_id": graphene.Node.to_global_id("User", user.id),
            "is_staff": user.is_staff,
        }
    )
    if additional_payload:
        payload.update(additional_payload)
    return payload


def jwt_encode(payload: dict[str, Any]) -> str:
    jwt_manager = get_jwt_manager()
    return jwt_manager.encode(payload)


def jwt_decode_with_exception_handler(
    token: str, verify_expiration=settings.JWT_EXPIRE
) -> dict[str, Any] | None:
    try:
        return jwt_decode(token, verify_expiration=verify_expiration)
    except jwt.PyJWTError:
        return None


def jwt_decode(
    token: str, verify_expiration=settings.JWT_EXPIRE, verify_aud: bool = False
) -> dict[str, Any]:
    jwt_manager = get_jwt_manager()
    return jwt_manager.decode(token, verify_expiration, verify_aud=verify_aud)


def create_token(payload: dict[str, Any], exp_delta: datetime.timedelta) -> str:
    payload.update(jwt_base_payload(exp_delta, token_owner=JWT_SALEOR_OWNER_NAME))
    return jwt_encode(payload)


def create_access_token(
    user: User, additional_payload: dict[str, Any] | None = None
) -> str:
    payload = jwt_user_payload(
        user, JWT_ACCESS_TYPE, settings.JWT_TTL_ACCESS, additional_payload
    )
    return jwt_encode(payload)


def create_refresh_token(
    user: User, additional_payload: dict[str, Any] | None = None
) -> str:
    payload = jwt_user_payload(
        user,
        JWT_REFRESH_TYPE,
        settings.JWT_TTL_REFRESH,
        additional_payload,
    )
    return jwt_encode(payload)


def get_user_from_payload(payload: dict[str, Any], request=None) -> User | None:
    # TODO: dataloader
    user = User.objects.filter(email=payload["email"], is_active=True).first()
    user_jwt_token = payload.get("token")
    if not user_jwt_token or not user:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    if user.jwt_token_key != user_jwt_token:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    return user


def is_saleor_token(token: str) -> bool:
    """Confirm that token was generated by Saleor not by plugin."""
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError:
        return False
    owner = payload.get(JWT_OWNER_FIELD)
    if not owner or owner != JWT_SALEOR_OWNER_NAME:
        return False
    return True


def get_user_from_access_payload(payload: dict, request=None) -> User | None:
    jwt_type = payload.get("type")
    if jwt_type not in [JWT_ACCESS_TYPE, JWT_THIRDPARTY_ACCESS_TYPE]:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    permissions = payload.get(PERMISSIONS_FIELD, None)
    user = get_user_from_payload(payload, request)
    if user:
        if permissions is not None:
            token_permissions = get_permissions_from_names(permissions)
            token_codenames = [perm.codename for perm in token_permissions]
            user.effective_permissions = get_permissions_from_codenames(token_codenames)
            user.is_staff = True if user.effective_permissions else False

        if payload.get("is_staff"):
            user.is_staff = True
    return user


def _create_access_token_for_third_party_actions(
    permissions: Iterable["Permission"],
    user: "User",
    app: "App",
    extra: dict[str, Any] | None = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    app_permission_enums = get_permission_names(permissions)

    permissions = user.effective_permissions.using(database_connection_name)
    user_permission_enums = get_permission_names(permissions)
    additional_payload = {
        APP_KEY_FIELD: graphene.Node.to_global_id("App", app.id),
        PERMISSIONS_FIELD: list(app_permission_enums & user_permission_enums),
        USER_PERMISSION_FIELD: list(user_permission_enums),
    }
    if app.audience:
        additional_payload["aud"] = app.audience
    if extra:
        additional_payload.update(extra)

    payload = jwt_user_payload(
        user,
        JWT_THIRDPARTY_ACCESS_TYPE,
        exp_delta=settings.JWT_TTL_APP_ACCESS,
        additional_payload=additional_payload,
    )
    return jwt_encode(payload)


def create_access_token_for_app(
    app: "App",
    user: "User",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Create access token for app.

    App can use user's JWT token to proceed given operation in Saleor.
    The token which can be used by App has additional field defining the permissions
    assigned to it. The permissions set is the intersection of user permissions and
    app permissions.
    """
    app_permissions = app.permissions.all()
    return _create_access_token_for_third_party_actions(
        permissions=app_permissions,
        user=user,
        app=app,
        database_connection_name=database_connection_name,
    )


def create_access_token_for_app_extension(
    app_extension: "AppExtension",
    permissions: Iterable["Permission"],
    user: "User",
    app: "App",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    app_extension_id = graphene.Node.to_global_id("AppExtension", app_extension.id)
    return _create_access_token_for_third_party_actions(
        permissions=permissions,
        user=user,
        app=app,
        extra={"app_extension": app_extension_id},
        database_connection_name=database_connection_name,
    )
