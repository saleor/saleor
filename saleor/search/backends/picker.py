from django.conf import settings
from django.utils.module_loading import import_module


def pick_backend():
    """Return the currently configured storefront search function.

    Returns a callable that accepts the search phrase.
    """
    return import_module(settings.SEARCH_BACKEND).search_storefront


def pick_dashboard_backend():
    """Return the currently configured dashboard search function.

    Returns a callable that accepts the search phrase.
    """
    return import_module(settings.SEARCH_BACKEND).search_dashboard
