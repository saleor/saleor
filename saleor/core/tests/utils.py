from django.conf import settings

from ..notification.utils import LOGO_URL


def get_site_context_payload(site):
    domain = site.domain
    return {
        "site_name": site.name,
        "domain": domain,
        "logo_url": f"http://{domain}{settings.STATIC_URL}{LOGO_URL}",
    }
