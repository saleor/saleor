from urllib.parse import urlsplit

from django.contrib.sites.models import Site


def get_email_context():
    site: Site = Site.objects.get_current()
    send_email_kwargs = {"from_email": site.settings.default_from_email}
    email_template_context = {
        "domain": site.domain,
        "site_name": site.name,
    }
    return send_email_kwargs, email_template_context


def prepare_url(params: str, redirect_url: str) -> str:
    """Add params to redirect url."""
    split_url = urlsplit(redirect_url)
    split_url = split_url._replace(query=params)
    return split_url.geturl()
