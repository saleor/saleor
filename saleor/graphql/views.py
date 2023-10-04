from graphene_django.views import GraphQLView

# from jwt_auth.utils import get_authorization_header
# from jwt_auth.mixins import JSONWebTokenAuthMixin

__author__ = 'tkolter'


# class OptionalJWTMixin(JSONWebTokenAuthMixin):
#     def dispatch(self, request, *args, **kwargs):
#         auth = get_authorization_header(request)
#         if auth:
#             return super(OptionalJWTMixin, self).dispatch(request, *args, **kwargs)
#         else:
#             return super(JSONWebTokenAuthMixin, self).dispatch(request, *args, **kwargs)


# class AuthGraphQLView(OptionalJWTMixin, GraphQLView):
#     pass

from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

class JWTAuthMixin(AccessMixin):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(JWTAuthMixin, self).dispatch(request, *args, **kwargs)
        # auth = request.headers[api_settings.AUTH_HEADER_NAME]
        # if auth:
        #   else:
        #     return super(JSONWebTokenAuthMixin, self).dispatch(request, *args, **kwargs)


        # try:
        #     request.user, request.token = self.authenticate(request)
        # except exceptions.AuthenticationFailed as e:
        #     response = HttpResponse(
        #         json.dumps({'errors': [str(e)]}),
        #         status=401,
        #         content_type='application/json'
        #     )

        #     response['WWW-Authenticate'] = self.authenticate_header(request)

        #     return response

        # return super(JWTAuthMixin, self).dispatch(
        #     request, *args, **kwargs)

class PrivateGraphQLView(JWTAuthMixin, GraphQLView):
    pass
