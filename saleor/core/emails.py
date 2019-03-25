from django.contrib.sites.models import Site
from django.templatetags.static import static

from ..core.utils import build_absolute_uri


def get_email_base_context():
    site = Site.objects.get_current()
    logo_url = build_absolute_uri(static('images/logo-light.svg'))
    return {
        'domain': site.domain,
        'logo_url': logo_url,
        'site_name': site.name}
