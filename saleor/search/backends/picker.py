from __future__ import unicode_literals

import importlib
from django.conf import settings


def pick_backend():
    '''Get storefront search function of configured backend

    :rtype: callable with one argument of type str

    '''
    backend = importlib.import_module(
        settings.SEARCH_BACKENDS[settings.SEARCH_BACKEND]['storefront'])
    return backend.search


def pick_dashboard_backend():
    '''Get dashboard search function of configured backend

    :rtype: callable with one argument of type str

    '''
    backend = importlib.import_module(
        settings.SEARCH_BACKENDS[settings.SEARCH_BACKEND]['dashboard'])
    return backend.search
