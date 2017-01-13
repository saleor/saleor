from django.conf import settings

from .models import SiteSetting


def get_site_settings_and_add_to_request(request):
    settings_id = getattr(settings, 'SITE_SETTINGS_ID', None)
    try:
        site_settings = SiteSetting.objects.get(id=settings_id)
    except SiteSetting.DoesNotExist:
        site_settings = None
    request.site_settings = site_settings
    return site_settings