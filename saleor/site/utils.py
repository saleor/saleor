from django.conf import settings

from .models import SiteSettings, AuthorizationKey


def get_site_settings_from_request(request):
    # type: (django.http.request.HttpRequest) -> SiteSettings
    """
    Returns site settings. If not found in request, gets one from database.
    Also saves it in request.
    """
    if not hasattr(request, 'site_settings'):
        site_settings_id = getattr(settings, 'SITE_SETTINGS_ID', None)
        request.site_settings = get_site_settings_uncached(site_settings_id)
    return request.site_settings


def get_site_settings():
    # type: () -> SiteSettings
    """
    Returns default site settings.
    """
    site_settings_id = getattr(settings, 'SITE_SETTINGS_ID', None)
    return get_site_settings_uncached(site_settings_id)


def get_domain():
    # type: () -> str
    """
    Returns domain name from default settings
    """
    return get_site_settings().domain


def get_site_settings_uncached(settings_id=None):
    # type: (str) -> SiteSettings
    """Query database for settings object."""
    return SiteSettings.objects.get_or_create(pk=settings_id)[0]


def get_authorization_key_for_backend(backend_name):
    # type: (str) -> AuthorizationKey
    site_settings_id = getattr(settings, 'SITE_SETTINGS_ID', None)
    authorization_key = AuthorizationKey.objects.filter(
        name=backend_name, site_settings__id=site_settings_id)
    return authorization_key.first()
