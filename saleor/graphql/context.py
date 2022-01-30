from typing import Optional

from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.db.models import Exists, OuterRef
from django.utils.functional import SimpleLazyObject

from ..app.models import App, AppToken
from ..core.auth import get_token_from_request
from .api import API_PATH


def get_context_value(request):
    set_app_on_context(request)
    set_auth_on_context(request)
    return request


def get_app(auth_token) -> Optional[App]:
    tokens = AppToken.objects.filter(auth_token=auth_token).values("pk")
    return App.objects.filter(
        Exists(tokens.filter(app_id=OuterRef("pk"))), is_active=True
    ).first()


def set_app_on_context(request):
    if request.path == API_PATH and not hasattr(request, "app"):
        request.app = None
        auth_token = get_token_from_request(request)
        if auth_token and len(auth_token) == 30:
            request.app = SimpleLazyObject(lambda: get_app(auth_token))


def get_user(request):
    if not hasattr(request, "_cached_user"):
        request._cached_user = authenticate(request=request)
    return request._cached_user


def set_auth_on_context(request):
    if hasattr(request, "app") and request.app:
        request.user = AnonymousUser()
        return request

    def user():
        return get_user(request) or AnonymousUser()

    request.user = SimpleLazyObject(lambda: user())
