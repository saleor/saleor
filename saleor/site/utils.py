from django.conf import settings

from .models import AuthorizationKey


def get_authorization_key_for_backend(backend_name):
    # type: (str) -> AuthorizationKey
    site_id = getattr(settings, 'SITE_ID', None)
    authorization_key = AuthorizationKey.objects.filter(
        name=backend_name, site_settings__site__id=site_id)
    return authorization_key.first()
