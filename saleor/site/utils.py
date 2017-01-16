from django.conf import settings

from .models import SiteSetting


def get_site_settings(request):
    if not hasattr(request, 'site_settings'):
        site_settings_id = getattr(settings, 'SITE_SETTINGS_ID', None)
        request.site_settings = get_site_settings_uncached(site_settings_id)
    return request.site_settings


def get_site_settings_uncached(site_id=None):
    return SiteSetting.objects.get(pk=site_id)
