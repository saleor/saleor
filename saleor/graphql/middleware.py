from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject
from graphene_django.settings import graphene_settings
from graphql_jwt.middleware import JSONWebTokenMiddleware

from ..account.models import ServiceAccount
from .views import API_PATH, GraphQLView


def jwt_middleware(get_response):
    """Authenticate a user using JWT and ignore the session-based authentication.

    This middleware resets authentication made by any previous middlewares
    and authenticates the user
    with graphql_jwt.middleware.JSONWebTokenMiddleware.
    """
    # Disable warnings for django-graphene-jwt
    graphene_settings.MIDDLEWARE.append(JSONWebTokenMiddleware)
    jwt_middleware_inst = JSONWebTokenMiddleware(get_response=get_response)
    graphene_settings.MIDDLEWARE.remove(JSONWebTokenMiddleware)

    def middleware(request):
        if request.path == API_PATH:
            # clear user authenticated by AuthenticationMiddleware
            request._cached_user = AnonymousUser()
            request.user = AnonymousUser()

            # authenticate using JWT middleware
            jwt_middleware_inst.process_request(request)
        return get_response(request)

    return middleware


def get_service_account(auth_token) -> Optional[ServiceAccount]:
    qs = ServiceAccount.objects.filter(tokens__auth_token=auth_token, is_active=True)
    return qs.first()


def service_account_middleware(get_response):

    service_account_auth_header = "HTTP_AUTHORIZATION"
    prefix = "bearer"

    def middleware(request):
        if request.path == API_PATH:
            request.service_account = None
            auth = request.META.get(service_account_auth_header, "").split()
            if len(auth) == 2:
                auth_prefix, auth_token = auth
                if auth_prefix.lower() == prefix:
                    request.service_account = SimpleLazyObject(
                        lambda: get_service_account(auth_token)
                    )
        return get_response(request)

    return middleware


def process_view(self, request, view_func, *args):
    if hasattr(view_func, "view_class") and issubclass(
        view_func.view_class, GraphQLView
    ):
        request._graphql_view = True


if settings.ENABLE_DEBUG_TOOLBAR:
    import warnings

    try:
        from graphiql_debug_toolbar.middleware import DebugToolbarMiddleware
    except ImportError:
        warnings.warn("The graphiql debug toolbar was not installed.")
    else:
        DebugToolbarMiddleware.process_view = process_view
