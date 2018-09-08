from django.contrib.auth.models import AnonymousUser
from django.shortcuts import reverse
from graphql_jwt.middleware import JSONWebTokenMiddleware


def jwt_middleware(get_response):
    """Authenticate user using JSONWebTokenMiddleware
    ignoring the session-based authentication.

    This middleware resets authentication made by any previous middlewares
    and authenticates the user
    with graphql_jwt.middleware.JSONWebTokenMiddleware.
    """
    jwt_middleware = JSONWebTokenMiddleware(get_response=get_response)

    def middleware(request):
        if request.path == reverse('api'):
            # clear user authenticated by AuthenticationMiddleware
            request._cached_user = AnonymousUser()
            request.user = AnonymousUser()

            # authenticate using JWT middleware
            jwt_middleware.process_request(request)
        return get_response(request)

    return middleware
