from functools import wraps
from typing import Callable

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from graphene_django.settings import graphene_settings
from graphql_jwt.middleware import JSONWebTokenMiddleware


def api_only_request_handler(get_response: Callable, handler: Callable):
    @wraps(handler)
    def handle_request(request):
        api_path = reverse("api")
        if request.path != api_path:
            return get_response(request)
        return handler(request)

    return handle_request


def api_only_middleware(middleware):
    @wraps(middleware)
    def wrapped(get_response):
        handler = middleware(get_response)
        return api_only_request_handler(get_response, handler)

    return wrapped


@api_only_middleware
def jwt_middleware(get_response):
    """Authenticate user using JSONWebTokenMiddleware
    ignoring the session-based authentication.

    This middleware resets authentication made by any previous middlewares
    and authenticates the user
    with graphql_jwt.middleware.JSONWebTokenMiddleware.
    """
    # Disable warnings for django-graphene-jwt
    graphene_settings.MIDDLEWARE.append(JSONWebTokenMiddleware)
    jwt_middleware_inst = JSONWebTokenMiddleware(get_response=get_response)
    graphene_settings.MIDDLEWARE.remove(JSONWebTokenMiddleware)

    def middleware(request):
        # clear user authenticated by AuthenticationMiddleware
        request._cached_user = AnonymousUser()
        request.user = AnonymousUser()

        # authenticate using JWT middleware
        jwt_middleware_inst.process_request(request)
        return get_response(request)

    return middleware
