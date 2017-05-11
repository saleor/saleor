from graphene_django.views import GraphQLView
from jwt_auth.utils import get_authorization_header

__author__ = 'tkolter'


from jwt_auth.mixins import JSONWebTokenAuthMixin


class OptionalJWTMixin(JSONWebTokenAuthMixin):
    def dispatch(self, request, *args, **kwargs):
        auth = get_authorization_header(request)
        if auth:
            return super(OptionalJWTMixin, self).dispatch(request, *args, **kwargs)
        else:
            return super(JSONWebTokenAuthMixin, self).dispatch(request, *args, **kwargs)


class AuthGraphQLView(OptionalJWTMixin, GraphQLView):
    pass
