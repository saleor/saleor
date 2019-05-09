# -*- coding: utf-8 -*-
import six

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.messages.api import MessageFailure
from django.shortcuts import redirect
from django.utils.http import urlquote

from social_core.exceptions import SocialAuthBaseException
from social_core.utils import social_logger
from .compat import MiddlewareMixin


class SocialAuthExceptionMiddleware(MiddlewareMixin):
    """Middleware that handles Social Auth AuthExceptions by providing the user
    with a message, logging an error, and redirecting to some next location.

    By default, the exception message itself is sent to the user and they are
    redirected to the location specified in the SOCIAL_AUTH_LOGIN_ERROR_URL
    setting.

    This middleware can be extended by overriding the get_message or
    get_redirect_uri methods, which each accept request and exception.
    """
    def process_exception(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        if strategy is None or self.raise_exception(request, exception):
            return

        if isinstance(exception, SocialAuthBaseException):
            backend = getattr(request, 'backend', None)
            backend_name = getattr(backend, 'name', 'unknown-backend')

            message = self.get_message(request, exception)
            url = self.get_redirect_uri(request, exception)

            if apps.is_installed('django.contrib.messages'):
                social_logger.info(message)
                try:
                    messages.error(request, message,
                                   extra_tags='social-auth ' + backend_name)
                except MessageFailure:
                    if url:
                        url += ('?' in url and '&' or '?') + \
                               'message={0}&backend={1}'.format(urlquote(message),
                                                                backend_name)
            else:
                social_logger.error(message)

            if url:
                return redirect(url)

    def raise_exception(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        if strategy is not None:
            return strategy.setting('RAISE_EXCEPTIONS') or settings.DEBUG

    def get_message(self, request, exception):
        return six.text_type(exception)

    def get_redirect_uri(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        return strategy.setting('LOGIN_ERROR_URL')
