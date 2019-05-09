# -*- coding: utf-8 -*-
import django
from django.conf import settings
from django.utils.http import urlquote
from django.utils.encoding import force_str
from django.shortcuts import redirect, resolve_url
from django.contrib.auth import REDIRECT_FIELD_NAME

from .helpers import get_redir_path, check_allow_impersonate, is_authenticated


def get_login_url():
    return force_str(resolve_url(settings.LOGIN_URL))


def allowed_user_required(view_func):
    def _checkuser(request, *args, **kwargs):
        if not is_authenticated(request.user):
            return redirect(u'{0}?{1}={2}'.format(
                get_login_url(),
                REDIRECT_FIELD_NAME,
                urlquote(request.get_full_path()),
            ))

        if getattr(request.user, 'is_impersonate', False):
            # Do not allow an impersonated session to use the
            # impersonate views.
            return redirect(get_redir_path())

        if check_allow_impersonate(request):
            # user is allowed to impersonate
            return view_func(request, *args, **kwargs)
        else:
            # user not allowed impersonate at all
            return redirect(get_redir_path())

    return _checkuser
