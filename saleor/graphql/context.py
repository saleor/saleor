from typing import Optional, cast

from django.contrib.auth import authenticate
from django.http import HttpRequest
from django.utils import timezone
from django.utils.functional import SimpleLazyObject

from ..account.models import User
from ..app.models import App
from ..core.auth import get_token_from_request
from ..core.jwt import jwt_decode_with_exception_handler
from .api import API_PATH
from .app.dataloaders import get_app_promise
from .core import SaleorContext


def get_context_value(request: HttpRequest) -> SaleorContext:
    request = cast(SaleorContext, request)
    if not hasattr(request, "dataloaders"):
        request.dataloaders = {}
    request.allow_replica = getattr(request, "allow_replica", True)
    request.request_time = getattr(request, "request_time", timezone.now())
    set_app_on_context(request)
    set_auth_on_context(request)
    set_decoded_auth_token(request)
    return request


def clear_context(context: SaleorContext):
    context.dataloaders.clear()


class RequestWithUser(HttpRequest):
    _cached_user: Optional[User]
    app: Optional[App]


def set_decoded_auth_token(request: SaleorContext):
    auth_token = get_token_from_request(request)
    if auth_token:
        request.decoded_auth_token = jwt_decode_with_exception_handler(auth_token)
    else:
        request.decoded_auth_token = None


def set_app_on_context(request: SaleorContext):
    if request.path == API_PATH and not hasattr(request, "app"):
        request.app = get_app_promise(request).get()


def get_user(request: SaleorContext) -> Optional[User]:
    if not hasattr(request, "_cached_user"):
        request._cached_user = cast(Optional[User], authenticate(request=request))
    return request._cached_user


def set_auth_on_context(request: SaleorContext):
    if hasattr(request, "app") and request.app:
        request.user = SimpleLazyObject(lambda: None)  # type: ignore
        return request

    def user():
        return get_user(request) or None

    request.user = SimpleLazyObject(user)  # type: ignore
