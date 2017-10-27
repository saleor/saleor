from __future__ import unicode_literals

from django.contrib.sites.shortcuts import get_current_site


def settings(request):
    # type: (django.http.request.HttpRequest) -> dict
    """Returns site settings which can be accessed with 'settings' key."""
    return {'settings': get_current_site(request)}
