from django.contrib.sites.shortcuts import get_current_site


def site(request):
    # type: (django.http.request.HttpRequest) -> dict
    """Add site settings to the context under the 'site' key."""
    return {'site': get_current_site(request)}
