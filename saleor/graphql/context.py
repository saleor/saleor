from typing import Optional, cast

from django.http import HttpRequest

from ..account.models import User
from ..app.models import App
from ..core.auth import get_token_from_request
from ..core.jwt import jwt_decode_with_exception_handler
from .core import SaleorContext


def get_context_value(request: HttpRequest) -> SaleorContext:
    request = cast(SaleorContext, request)
    request.dataloaders = {}
    request.is_mutation = False
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


def set_auth_on_context(request: SaleorContext):
    return
