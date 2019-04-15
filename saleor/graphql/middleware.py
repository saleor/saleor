from django.contrib.auth.models import AnonymousUser
from django.shortcuts import reverse
from graphene_django.settings import graphene_settings
from graphql_jwt.middleware import JSONWebTokenMiddleware


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
        if request.path == reverse('api'):
            # clear user authenticated by AuthenticationMiddleware
            request._cached_user = AnonymousUser()
            request.user = AnonymousUser()

            # authenticate using JWT middleware
            jwt_middleware_inst.process_request(request)
        return get_response(request)

    return middleware
