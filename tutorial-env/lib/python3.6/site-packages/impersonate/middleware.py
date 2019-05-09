# -*- coding: utf-8 -*-
from .helpers import (
    User, check_allow_for_user, check_allow_for_uri, is_authenticated,
)

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object  # fallback for Django < 1.10


class ImpersonateMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.user.is_impersonate = False
        request.impersonator = None

        if is_authenticated(request.user) and \
           '_impersonate' in request.session:
            new_user_id = request.session['_impersonate']
            if isinstance(new_user_id, User):
                # Edge case for issue 15
                new_user_id = new_user_id.pk

            try:
                new_user = User.objects.get(pk=new_user_id)
            except User.DoesNotExist:
                return

            if check_allow_for_user(request, new_user) and \
               check_allow_for_uri(request.path):
                request.impersonator = request.user
                request.user = new_user
                request.user.is_impersonate = True

        request.real_user = request.impersonator or request.user
