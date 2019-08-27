from django.contrib.auth.models import AnonymousUser
from django.shortcuts import reverse
from django.utils.functional import SimpleLazyObject
from graphene_django.settings import graphene_settings
from graphql_jwt.middleware import JSONWebTokenMiddleware

from saleor.account.models import Bot


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
        if request.path == reverse("api"):
            # clear user authenticated by AuthenticationMiddleware
            request._cached_user = AnonymousUser()
            request.user = AnonymousUser()

            # authenticate using JWT middleware
            jwt_middleware_inst.process_request(request)
        return get_response(request)

    return middleware


def get_bot(auth_token):
    qs = Bot.objects.filter(auth_token=auth_token, is_active=True)
    return qs.first()


def bot_middleware(get_response):

    bot_auth_header = "HTTP_AUTHORIZATION"
    prefix = "Bearer"

    def middleware(request):
        if request.path == reverse("api"):
            auth = request.META.get(bot_auth_header, "").split()
            if len(auth) == 2:
                auth_prefix, auth_token = auth
                if auth_prefix == prefix:
                    request.bot = SimpleLazyObject(lambda: get_bot(auth_token))
        return get_response(request)

    return middleware
