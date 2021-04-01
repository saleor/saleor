from django.contrib.sites.models import Site


def get_site_context():
    site: Site = Site.objects.get_current()
    site_context = {
        "domain": site.domain,
        "site_name": site.name,
    }
    return site_context
