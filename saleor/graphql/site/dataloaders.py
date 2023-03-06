from functools import partial, reduce
from typing import Callable, TypeVar

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.http.request import split_domain_port
from promise import Promise

from ..core.dataloaders import DataLoader


class SiteByIdLoader(DataLoader[int, Site]):
    context_key = "site_by_id"

    def batch_load(self, keys):
        sites_mapped = Site.objects.using(self.database_connection_name).in_bulk(keys)
        return [sites_mapped.get(site_id) for site_id in keys]


class SiteByHostLoader(DataLoader):
    context_key = "site_by_host"

    def batch_load(self, keys):
        # simulate non existing `domain__iexact__in`
        q_list = map(lambda k: Q(domain__iexact=k), keys)
        q_list = reduce(lambda a, b: a | b, q_list)
        sites = Site.objects.using(self.database_connection_name).filter(q_list)
        sites_mapped = {s.domain.lower(): s for s in sites}
        return [sites_mapped.get(host.lower()) for host in keys]


def get_site_promise(request) -> Promise[Site]:
    if getattr(settings, "SITE_ID", ""):
        site_id = settings.SITE_ID
        return SiteByIdLoader(request).load(site_id)

    host = request.get_host()
    return (
        SiteByHostLoader(request)
        .load(host)
        .then(partial(ensure_that_site_is_not_none, request, host))
    )


def execute_callback_if_site_not_none(site):
    if site is None:
        raise ImproperlyConfigured(
            'You\'re using the Django "sites framework" without having '
            "set the SITE_ID setting. Create a site in your database and "
            "set the SITE_ID setting."
        )

    return site


def ensure_that_site_is_not_none(request, host, site):
    if site is None:
        domain = split_domain_port(host)[0]
        return (
            SiteByHostLoader(request)
            .load(domain)
            .then(partial(execute_callback_if_site_not_none))
        )

    return execute_callback_if_site_not_none(site)


T = TypeVar("T")


def load_site_callback(func: Callable[..., T]) -> Callable[..., Promise[T]]:
    def _wrapper(root, info, *args, **kwargs):
        return get_site_promise(info.context).then(
            partial(func, root, info, *args, **kwargs)
        )

    return _wrapper
