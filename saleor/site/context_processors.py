import os
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import prefetch_related_objects


def site(request):
    # type: (django.http.request.HttpRequest) -> dict
    """Add site settings to the context under the 'site' key."""
    data = {}
    data["GA_CODE"] = os.environ.get('GOOGLE_ANALYTICS_TRACKING_ID')
    site = get_current_site(request)
    prefetch_related_objects([site], 'settings__translations')
    return {'site': site, 'data': data}
