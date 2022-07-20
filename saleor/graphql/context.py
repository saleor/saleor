from collections import defaultdict
from typing import Optional, Protocol, Union, cast

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject
from promise import Promise

from ..account.models import User
from ..app.models import App, AppToken
from ..core.auth import get_token_from_request
from ..core.jwt import jwt_decode_with_exception_handler
from .api import API_PATH
from .core.dataloaders import DataLoader


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


def get_app(raw_auth_token) -> Optional[App]:
    tokens = AppToken.objects.filter(token_last_4=raw_auth_token[-4:]).values_list(
        "app_id", "auth_token"
    )
    app_ids = [
        app_id
        for app_id, auth_token in tokens
        if check_password(raw_auth_token, auth_token)
    ]
    return App.objects.filter(id__in=app_ids, is_active=True).first()


class AppByTokenLoader(DataLoader):
    context_key = "app_by_token"

    def batch_load(self, keys):
        last_4s_map = defaultdict(list)
        for key in keys:
            last_4s_map[key[-4:]].append(key)

        tokens = (
            AppToken.objects.using(self.database_connection_name)
            .filter(token_last_4__in=last_4s_map.keys())
            .values_list("auth_token", "token_last_4", "app_id")
        )
        app_ids = set()
        for auth_token, token_last_4, app_id in tokens:
            for raw_token in last_4s_map[token_last_4]:
                if check_password(raw_token, auth_token):
                    app_ids.add(app_id)
        apps = App.objects.using(self.database_connection_name).filter(
            id__in=app_ids, is_active=True
        )

        return list(apps)


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
