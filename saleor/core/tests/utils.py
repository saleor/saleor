from django.conf import settings

from ..notification.utils import LOGO_URL


def get_site_context_payload(site):
    return {
        "site_name": site.name,
        "domain": "example.com",
        "logo_url": f"https://example.com{settings.STATIC_URL}{LOGO_URL}",
    }
