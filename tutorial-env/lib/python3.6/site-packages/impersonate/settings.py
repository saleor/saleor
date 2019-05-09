# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings
from django.contrib.auth import get_user_model
from django.conf import settings as django_settings


User = get_user_model()
username_field = getattr(User, 'USERNAME_FIELD', 'username')

_settings = {
    'MAX_FILTER_SIZE': 100,
    'REDIRECT_FIELD_NAME': None,
    'PAGINATE_COUNT': 20,
    'REQUIRE_SUPERUSER': False,
    'CUSTOM_USER_QUERYSET': None,
    'ALLOW_SUPERUSER': False,
    'CUSTOM_ALLOW': None,
    'URI_EXCLUSIONS': (r'^admin/',),
    'DISABLE_LOGGING': False,
    'USE_HTTP_REFERER': False,
    'LOOKUP_TYPE': 'icontains',
    'SEARCH_FIELDS': [username_field, 'first_name', 'last_name', 'email'],
    'REDIRECT_URL': getattr(django_settings, 'LOGIN_REDIRECT_URL', u'/'),
}


def deprecate_settings(name):
    # Silly reset of specific fields, needed for tests
    _settings['REDIRECT_URL'] = \
                getattr(django_settings, 'LOGIN_REDIRECT_URL', u'/')

    old_settings_name = 'IMPERSONATE_{0}'.format(name)
    if hasattr(django_settings, old_settings_name):
        warnings.warn(
            ('The IMPERSONATE_* settings are now deprecated and will be '
             'removed in an upcoming release. Please use the IMPERSONATE '
             'dictionary setting.')
        )
        return getattr(django_settings, old_settings_name)
    return _settings.get(name)


class Settings(object):
    def __getattribute__(self, name):
        sdict = getattr(django_settings, 'IMPERSONATE', {})
        return sdict.get(name, deprecate_settings(name))


settings = Settings()
