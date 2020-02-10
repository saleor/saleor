from django.conf import settings
from django.utils.module_loading import import_module  # type: ignore


def pick_backend():
    """Return the currently configured storefront search function.

    Returns a callable that accepts the search phrase.
    """
    return import_module(settings.SEARCH_BACKEND).search_storefront
