from __future__ import unicode_literals

from django.contrib.sites.shortcuts import get_current_site


def site(request):
    # type: (django.http.request.HttpRequest) -> dict
    """Returns site settings which can be accessed with 'site' key."""
    return {'site': get_current_site(request)}
