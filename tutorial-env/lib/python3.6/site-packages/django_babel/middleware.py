# -*- coding: utf-8 -*-

from babel import Locale, UnknownLocaleError
from django.utils.translation import get_language
from threading import local

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    # Not required for Django <= 1.9, see:
    # https://docs.djangoproject.com/en/1.10/topics/http/middleware/#upgrading-pre-django-1-10-style-middleware
    MiddlewareMixin = object


__all__ = ['get_current_locale', 'LocaleMiddleware']

_thread_locals = local()


def get_current_locale():
    """Get current locale data outside views.

    See http://babel.pocoo.org/en/stable/api/core.html#babel.core.Locale
    for Locale objects documentation
    """
    return getattr(_thread_locals, 'locale', None)


class LocaleMiddleware(MiddlewareMixin):

    """Simple Django middleware that makes available a Babel `Locale` object
    via the `request.locale` attribute.
    """

    def process_request(self, request):
        try:
            code = getattr(request, 'LANGUAGE_CODE', get_language())
            locale = Locale.parse(code, sep='-')
        except (ValueError, UnknownLocaleError):
            pass
        else:
            _thread_locals.locale = request.locale = locale
