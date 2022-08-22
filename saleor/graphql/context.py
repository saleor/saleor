from typing import Optional, Protocol, Union, cast

from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject
from promise import Promise

from ..account.models import User
from ..app.models import App
from ..core.auth import get_token_from_request
from ..core.jwt import jwt_decode_with_exception_handler
from .api import API_PATH
from .app.dataloaders import load_app


def get_context_value(request):
    set_app_on_context(request)
    set_auth_on_context(request)
    set_decoded_auth_token(request)
    return request


UserType = Union[User, AnonymousUser]


class RequestWithUser(Protocol):
    _cached_user: UserType
    app: Optional[App]
    user: Union[UserType, SimpleLazyObject, Promise]


def set_decoded_auth_token(request):
    auth_token = get_token_from_request(request)
    decoded_auth_token = jwt_decode_with_exception_handler(auth_token)
    request.decoded_auth_token = decoded_auth_token


def set_app_on_context(request):
    if request.path == API_PATH and not hasattr(request, "app"):
        request.app = load_app(request)


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
