from django.conf import settings

from .models import SiteSettings


def get_site_settings(request):
    # type: (django.http.request.HttpRequest) -> SiteSettings
    """
    Returns site settings. If not found in request, gets one from database.
    """
    if not hasattr(request, 'site_settings'):
        site_settings_id = getattr(settings, 'SITE_SETTINGS_ID', None)
        request.site_settings = get_site_settings_uncached(site_settings_id)
    return request.site_settings


def get_site_settings_uncached(settings_id=None):
    # type: (str) -> SiteSettings
    """Query database for settings object."""
    return SiteSettings.objects.get_or_create(pk=settings_id)[0]
