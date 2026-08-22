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


def _first_or_raise(queryset, lookup):
    """Return the first row, raising ``Site.DoesNotExist`` when there is none.

    ``django.contrib.sites`` reaches for a single row with ``self.get(...)``,
    so every caller — including the port-stripping fallback below and Django's
    own ``loaddata`` deserializer — handles ``Site.DoesNotExist``. Indexing an
    empty queryset instead raises ``IndexError``, which none of them catch, so
    the lookups here have to normalize it back. ``.first()`` is used rather
    than ``.get()`` because ``.get()`` discards the ``prefetch_related`` these
    callers rely on; ``Site`` is ordered by ``domain``, so it selects the same
    row ``[0]`` did.
    """
    site = queryset.first()
    if site is None:
        raise Site.DoesNotExist(f"Site matching query does not exist: {lookup}.")
    return site


def new_get_current(self, request=None):
    from django.conf import settings

    from ..graphql.core.context import get_database_connection_name

    if getattr(settings, "SITE_ID", ""):
        site_id = settings.SITE_ID
        if site_id not in THREADED_SITE_CACHE:
            with lock:
                site = _first_or_raise(
                    self.prefetch_related("settings")
                    .using(settings.DATABASE_CONNECTION_REPLICA_NAME)
                    .filter(pk=site_id),
                    f"SITE_ID={site_id!r}",
                )
                THREADED_SITE_CACHE[site_id] = site
        return THREADED_SITE_CACHE[site_id]
    if request:
        host = request.get_host()
        try:
            # First attempt to look up the site by host with or without port.
            if host not in THREADED_SITE_CACHE:
                with lock:
                    database_connection_name = get_database_connection_name(request)
                    site = _first_or_raise(
                        self.prefetch_related("settings")
                        .using(database_connection_name)
                        .filter(domain__iexact=host),
                        f"host={host!r}",
                    )
                    THREADED_SITE_CACHE[host] = site
            return THREADED_SITE_CACHE[host]
        except Site.DoesNotExist:
            # Fallback to looking up site after stripping port from the host.
            domain, dummy_port = split_domain_port(host)
            if domain not in THREADED_SITE_CACHE:
                with lock:
                    site = _first_or_raise(
                        self.prefetch_related("settings")
                        .using(settings.DATABASE_CONNECTION_REPLICA_NAME)
                        .filter(domain__iexact=domain),
                        f"domain={domain!r}",
                    )
                    THREADED_SITE_CACHE[domain] = site
        return THREADED_SITE_CACHE[domain]

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
    return _first_or_raise(
        self.prefetch_related("settings").filter(domain__iexact=domain),
        f"domain={domain!r}",
    )


def patch_contrib_sites():
    SiteManager.get_current = new_get_current  # type: ignore[method-assign] # hack
    SiteManager.clear_cache = new_clear_cache  # type: ignore[method-assign] # hack
    SiteManager.get_by_natural_key = new_get_by_natural_key  # type: ignore[method-assign] # hack # noqa: E501
