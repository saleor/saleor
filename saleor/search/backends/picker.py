from django.conf import settings
from django.utils.module_loading import import_module


def pick_backend():
    '''Get storefront search function of configured backend

    :rtype: callable with one argument of type str

    '''
    return import_module(settings.SEARCH_BACKEND).search_storefront


def pick_dashboard_backend():
    '''Get dashboard search function of configured backend

    :rtype: callable with one argument of type str

    '''
    return import_module(settings.SEARCH_BACKEND).search_dashboard
