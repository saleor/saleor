from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import graphene
import jwt
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest

from ..account.models import User
from ..app.models import App
from .permissions import get_permission_names, get_permissions_from_names

JWT_ALGORITHM = "HS256"
JWT_AUTH_HEADER = "HTTP_AUTHORIZATION"
JWT_AUTH_HEADER_PREFIX = "JWT"
JWT_ACCESS_TYPE = "access"
JWT_REFRESH_TYPE = "refresh"
JWT_THIRDPARTY_ACCESS_TYPE = "thirdparty"
JWT_REFRESH_TOKEN_COOKIE_NAME = "refreshToken"

PERMISSIONS_FIELD = "permissions"


def jwt_base_payload(exp_delta: Optional[timedelta] = None) -> Dict[str, Any]:
    utc_now = datetime.utcnow()
    payload = {
        "iat": utc_now,
    }
    if exp_delta:
        payload["exp"] = utc_now + exp_delta
    return payload


def jwt_user_payload(
    user: User,
    token_type: str,
    exp_delta: timedelta,
    additional_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not settings.JWT_EXPIRE:
        exp_delta = None  # type: ignore

    payload = jwt_base_payload(exp_delta)
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


def jwt_encode(payload: Dict[str, Any]) -> str:
    return jwt.encode(
        payload, settings.SECRET_KEY, JWT_ALGORITHM,  # type: ignore
    ).decode("utf-8")


def jwt_decode(token: str) -> Dict[str, Any]:
    return jwt.decode(
        token, settings.SECRET_KEY, algorithms=JWT_ALGORITHM  # type: ignore
    )


def create_token(payload: Dict[str, Any], exp_delta: timedelta) -> str:
    payload.update(jwt_base_payload(exp_delta))
    return jwt_encode(payload)


def create_access_token(
    user: User, additional_payload: Optional[Dict[str, Any]] = None
) -> str:
    payload = jwt_user_payload(
        user, JWT_ACCESS_TYPE, settings.JWT_TTL_ACCESS, additional_payload
    )
    return jwt_encode(payload)


def create_refresh_token(
    user: User, additional_payload: Optional[Dict[str, Any]] = None
) -> str:
    payload = jwt_user_payload(
        user, JWT_REFRESH_TYPE, settings.JWT_TTL_REFRESH, additional_payload,
    )
    return jwt_encode(payload)


def get_token_from_request(request: WSGIRequest) -> Optional[str]:
    auth = request.META.get(JWT_AUTH_HEADER, "").split(maxsplit=1)
    prefix = JWT_AUTH_HEADER_PREFIX

    if len(auth) != 2 or auth[0].upper() != prefix:
        return None
    return auth[1]


def get_user_from_payload(payload: Dict[str, Any]) -> Optional[User]:
    user = User.objects.filter(email=payload["email"], is_active=True).first()
    if user and user.jwt_token_key == payload["token"]:
        return user
    return None


def get_user_from_access_token(token: str) -> Optional[User]:
    payload = jwt_decode(token)
    if payload["type"] not in [JWT_ACCESS_TYPE, JWT_THIRDPARTY_ACCESS_TYPE]:
        return None
    permissions = payload.get(PERMISSIONS_FIELD, None)
    user = get_user_from_payload(payload)
    if user and permissions is not None:
        user.effective_permissions = get_permissions_from_names(permissions)
    return user


def create_access_token_for_app(app: "App", user: "User"):
    """Create access token for app.

    App can use user jwt token to proceed given operation on the Saleor side.
    The token which can be used by App has additional field defining the permissions
    assigned to it. The permissions set is the intersection of user permissions and
    app permissions.
    """
    app_permissions = app.permissions.all()
    app_permission_enums = get_permission_names(app_permissions)

    permissions = user.effective_permissions
    user_permission_enums = get_permission_names(permissions)
    app_id = graphene.Node.to_global_id("App", app.id)
    additional_payload = {
        "app": app_id,
        PERMISSIONS_FIELD: list(app_permission_enums & user_permission_enums),
    }
    payload = jwt_user_payload(
        user,
        JWT_THIRDPARTY_ACCESS_TYPE,
        exp_delta=settings.JWT_TTL_APP_ACCESS,
        additional_payload=additional_payload,
    )
    return jwt_encode(payload)
