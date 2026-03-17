from typing import cast

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
    _clear_dataloaders_fields_cache(context)
    context.dataloaders.clear()
    del context.user


def _clear_dataloaders_fields_cache(context: SaleorContext):
    """Clear Django model fields_cache on all cached dataloader values.

    Django's OneToOneField descriptors create bidirectional caches in
    _state.fields_cache (e.g. Site ↔ SiteSettings), forming reference cycles
    that survive after dataloaders are cleared. Breaking these caches here
    prevents the cycles from leaking into garbage collection.

    How it works:
    - `_promise_cache` is an internal dict on the `promise` library's DataLoader
      (BaseLoader). It maps loader keys to Promise objects — this is where the
      dataloader stores its cached results.
    - Each value in `_promise_cache` is a Promise, not the actual model instance.
      `.get()` extracts the resolved value. By the time `clear_context` runs (in
      the `finally` block after GraphQL execution), all promises are already
      resolved — no additional DB queries are triggered here.
    - Rejected promises (failed DB queries) raise on `.get()`, so we skip them
      via try/except since there is no model instance to clean up.
    """
    for loader in context.dataloaders.values():
        for promise in getattr(loader, "_promise_cache", {}).values():
            try:
                value = promise.get()
            except Exception:
                continue
            if hasattr(value, "_state"):
                value._state.fields_cache.clear()


class RequestWithUser(HttpRequest):
    _cached_user: User | None
    app: App | None


def set_decoded_auth_token(request: SaleorContext):
    auth_token = get_token_from_request(request)
    if auth_token:
        request.decoded_auth_token = jwt_decode_with_exception_handler(auth_token)
    else:
        request.decoded_auth_token = None


def set_app_on_context(request: SaleorContext):
    if request.path == API_PATH and not hasattr(request, "app"):
        request.app = get_app_promise(request).get()


def get_user(request: SaleorContext) -> User | None:
    if not hasattr(request, "_cached_user"):
        request._cached_user = cast(User | None, authenticate(request=request))
    return request._cached_user


def set_auth_on_context(request: SaleorContext):
    if hasattr(request, "app") and request.app:
        request.user = SimpleLazyObject(lambda: None)  # type: ignore[assignment]
        return

    def user():
        return get_user(request) or None

    request.user = SimpleLazyObject(user)  # type: ignore[assignment]
