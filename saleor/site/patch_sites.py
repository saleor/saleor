"""A hack to allow safe clearing of the cache in django.contrib.sites.

Since django.contrib.sites may not be thread-safe when there are
multiple instances of the application server, we're patching it with
a thread-safe structure and methods that use it underneath.
"""

import threading

from django.contrib.sites.models import Site, SiteManager
from django.core.exceptions import ImproperlyConfigured
from django.http.request import split_domain_port

lock = threading.Lock()
with lock:
    THREADED_SITE_CACHE: dict[str | int, Site] = {}


def _fetch_site(manager, database_connection_name: str, **lookup) -> Site:
    return (
        manager.prefetch_related("settings")
        .using(database_connection_name)
        .filter(**lookup)[0]
    )


def _store_site(cache: dict[str | int, Site], key: str | int, site: Site) -> None:
    """Store a fetched site in the cache it was looked up in.

    The site is fetched without holding the lock, so the cache may have been
    cleared in the meantime. In that case `cache` is no longer the current
    cache and the site, which may predate the clear, is not stored.
    """
    with lock:
        if cache is THREADED_SITE_CACHE:
            cache[key] = site


def new_get_current(self, request=None):
    from django.conf import settings

    from ..graphql.core.context import get_database_connection_name

    if getattr(settings, "SITE_ID", ""):
        site_id = settings.SITE_ID
        cache = THREADED_SITE_CACHE
        site = cache.get(site_id)
        if site is None:
            site = _fetch_site(
                self, settings.DATABASE_CONNECTION_REPLICA_NAME, pk=site_id
            )
            _store_site(cache, site_id, site)
        return site
    if request:
        host = request.get_host()
        try:
            # First attempt to look up the site by host with or without port.
            cache = THREADED_SITE_CACHE
            site = cache.get(host)
            if site is None:
                database_connection_name = get_database_connection_name(request)
                site = _fetch_site(self, database_connection_name, domain__iexact=host)
                _store_site(cache, host, site)
            return site
        except Site.DoesNotExist:
            # Fallback to looking up site after stripping port from the host.
            domain, dummy_port = split_domain_port(host)
            cache = THREADED_SITE_CACHE
            site = cache.get(domain)
            if site is None:
                site = _fetch_site(
                    self,
                    settings.DATABASE_CONNECTION_REPLICA_NAME,
                    domain__iexact=domain,
                )
                _store_site(cache, domain, site)
        return site

    raise ImproperlyConfigured(
        "You're using the Django sites framework without having"
        " set the SITE_ID setting. Create a site in your database and"
        " set the SITE_ID setting or pass a request to"
        " Site.objects.get_current() to fix this error."
    )


def new_clear_cache(self):
    global THREADED_SITE_CACHE
    with lock:
        THREADED_SITE_CACHE = {}


def new_get_by_natural_key(self, domain):
    return self.prefetch_related("settings").filter(domain__iexact=domain)[0]


def patch_contrib_sites():
    SiteManager.get_current = new_get_current  # type: ignore[method-assign] # hack
    SiteManager.clear_cache = new_clear_cache  # type: ignore[method-assign] # hack
    SiteManager.get_by_natural_key = new_get_by_natural_key  # type: ignore[method-assign] # hack # noqa: E501
