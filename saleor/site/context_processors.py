from __future__ import unicode_literals

from .utils import get_site_settings_from_request


def settings(request):
    # type: (django.http.request.HttpRequest) -> dict
    """Returns site settings which can be accessed with 'settings' key."""
    return {'settings': get_site_settings_from_request(request)}
