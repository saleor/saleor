from functools import reduce

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.requests import RequestSite
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.http.request import split_domain_port

from ..core.dataloaders import DataLoader


class SiteByIdLoader(DataLoader):
    context_key = "site_by_id"

    def batch_load(self, keys):
        sites_mapped = Site.objects.using(self.database_connection_name).in_bulk(keys)
        return [sites_mapped.get(site_id) for site_id in keys]


class SiteByHostLoader(DataLoader):
    context_key = "site_by_host"

    def batch_load(self, keys):
        sites_mapped = Site.objects.using(self.database_connection_name).in_bulk(keys)
        # simulate nonexisting `domain__iexact__in`
        q_list = map(lambda k: Q(domain__iexact=k), keys)
        q_list = reduce(lambda a, b: a | b, q_list)
        sites = Site.objects.using(self.database_connection_name).filter(q_list)
        sites_mapped = {s.domain.lower(): s for s in sites}
        return [sites_mapped.get(host.lower()) for host in keys]


def load_current_site(request):
    if getattr(settings, "SITE_ID", ""):
        site_id = settings.SITE_ID
        return SiteByIdLoader(request).load(site_id).get()

    host = request.get_host()
    site = SiteByHostLoader(request).load(host).get()

    if site is None:
        domain, port = split_domain_port(host)
        site = SiteByHostLoader(request).load(domain).get()

    if site is None:
        raise ImproperlyConfigured(
            'You\'re using the Django "sites framework" without having '
            "set the SITE_ID setting. Create a site in your database and "
            "set the SITE_ID setting."
        )

    # Populate the other loader for free
    SiteByIdLoader(request).prime(site.id, site)
    return site


def load_site(request, site_id=None):
    if site_id is None:
        return load_current_site(request)
    return SiteByIdLoader(request).load(site_id).get() or RequestSite(request)
