from typing import Optional, cast

from django.contrib.auth import authenticate
from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject

from ..account.models import User
from ..app.models import App
from ..core.auth import get_token_from_request
from ..core.jwt import jwt_decode_with_exception_handler
from .api import API_PATH
from .app.dataloaders import load_app
from .core import SaleorContext


def get_context_value(request: HttpRequest) -> SaleorContext:
    request = cast(SaleorContext, request)
    request.dataloaders = {}
    request.is_mutation = False
    set_app_on_context(request)
    set_auth_on_context(request)
    set_decoded_auth_token(request)
    return request


UserType = Optional[User]


class RequestWithUser(HttpRequest):
    _cached_user: UserType
    app: Optional[App]


def set_decoded_auth_token(request: SaleorContext):
    auth_token = get_token_from_request(request)
    if auth_token:
        request.decoded_auth_token = jwt_decode_with_exception_handler(auth_token)
    else:
        request.decoded_auth_token = None


def set_app_on_context(request: SaleorContext):
    if request.path == API_PATH and not hasattr(request, "app"):
        request.app = load_app(request)


def get_user(request: SaleorContext) -> UserType:
    if not hasattr(request, "_cached_user"):
        request._cached_user = cast(UserType, authenticate(request=request))
    return request._cached_user


def set_auth_on_context(request: SaleorContext):
    if hasattr(request, "app") and request.app:
        request.user = SimpleLazyObject(lambda: None)  # type: ignore
        return request

    def user():
        return get_user(request) or None

    request.user = SimpleLazyObject(user)  # type: ignore
