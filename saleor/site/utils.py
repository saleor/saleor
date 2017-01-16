from django.conf import settings

from .models import SiteSetting


def get_site_settings(request):
    if hasattr(request, 'site_settings'):
        site_settings = request.site_settings
    else:
        site_settings_id = getattr(settings, 'SITE_SETTINGS_ID', None)
        try:
            site_settings = get_site_settings_uncached(site_settings_id)
        except SiteSetting.DoesNotExist:
            site_settings = None
        request.site_settings = site_settings
    return site_settings


def get_site_settings_uncached(site_id=None):
    return SiteSetting.objects.get(pk=site_id)
