from typing import Optional, Protocol, Union, cast

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AnonymousUser
from django.db.models import Exists, OuterRef
from django.utils.functional import SimpleLazyObject

from ..account.models import User
from ..app.models import App, AppToken
from ..core.auth import get_token_from_request
from ..core.jwt import jwt_decode_with_exception_handler
from .api import API_PATH


def get_context_value(request):
    set_app_on_context(request)
    set_auth_on_context(request)
    set_decoded_auth_token(request)
    return request


UserType = Union[User, AnonymousUser]


class RequestWithUser(Protocol):
    _cached_user: UserType
    app: Optional[App]
    user: Union[UserType, SimpleLazyObject]


def get_app(raw_auth_token) -> Optional[App]:
    tokens = AppToken.objects.filter(token_last_4=raw_auth_token[-4:]).values_list(
        "id", "auth_token"
    )
    token_ids = [
        id for id, auth_token in tokens if check_password(raw_auth_token, auth_token)
    ]
    return App.objects.filter(
        Exists(tokens.filter(id__in=token_ids, app_id=OuterRef("pk"))), is_active=True
    ).first()


def set_decoded_auth_token(request):
    token = get_token_from_request(request)
    decoded_auth_token = jwt_decode_with_exception_handler(token)
    request.decoded_auth_token = decoded_auth_token


def set_app_on_context(request):
    if request.path == API_PATH and not hasattr(request, "app"):
        request.app = None
        auth_token = get_token_from_request(request)
        if auth_token and len(auth_token) == 30:
            request.app = SimpleLazyObject(lambda: get_app(auth_token))


def get_user(request: RequestWithUser) -> Optional[UserType]:
    if not hasattr(request, "_cached_user"):
        request._cached_user = cast(UserType, authenticate(request=request))
    return request._cached_user


def set_auth_on_context(request: RequestWithUser):
    if hasattr(request, "app") and request.app:
        request.user = AnonymousUser()
        return request

    def user():
        return get_user(request) or AnonymousUser()

    request.user = SimpleLazyObject(user)
