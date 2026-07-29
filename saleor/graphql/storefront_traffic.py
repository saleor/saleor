import warnings

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from jwt import InvalidTokenError

from ..account.models import User
from ..core.auth import get_token_from_request
from ..site.models import SiteSettings
from .core import SaleorContext
from .site.dataloaders import get_site_promise

STOREFRONT_TRAFFIC_ERROR_CODE = "STOREFRONT_TRAFFIC_NOT_ALLOWED"
STOREFRONT_TRAFFIC_ERROR_MESSAGE = "Storefront traffic is not allowed."
STOREFRONT_TRAFFIC_CACHE_TIMEOUT = 5 * 60


def _get_allow_storefront_traffic_cache_key(request: SaleorContext | None) -> str:
    """Namespace the cache key per site without loading the ``Site``.

    Resolves the site the same way ``SiteManager.get_current`` does — by
    ``settings.SITE_ID`` when it is configured, otherwise by the request host, which
    is how multi-tenant deployments serve several sites from one process. Both are
    read straight off the settings/request, so the hot path stays free of queries.

    Calling ``Site.objects.get_current()`` instead would populate the patched,
    process-global ``THREADED_SITE_CACHE``. That cache is not invalidated by
    ``Site``/``SiteSettings`` saves (Django's ``clear_site_cache`` signal targets the
    unused original ``SITE_CACHE``), so it would leak stale site data across requests
    and tests.
    """
    if site_id := getattr(settings, "SITE_ID", None):
        return f"allow_storefront_traffic:{site_id}"
    if request is None:
        raise ImproperlyConfigured(
            "Without settings.SITE_ID the site can only be identified by the request "
            "host, so a request is required to namespace the storefront traffic cache."
        )
    return f"allow_storefront_traffic:{request.get_host()}"


def set_allow_storefront_traffic_cache(
    allow_storefront_traffic: bool, request: SaleorContext | None = None
) -> None:
    """Cache the flag for the request's site.

    ``request`` is only consulted when ``settings.SITE_ID`` is unset, so single-site
    deployments may omit it.
    """
    cache.set(
        _get_allow_storefront_traffic_cache_key(request),
        allow_storefront_traffic,
        STOREFRONT_TRAFFIC_CACHE_TIMEOUT,
    )


def clear_allow_storefront_traffic_cache(request: SaleorContext | None = None) -> None:
    cache.delete(_get_allow_storefront_traffic_cache_key(request))


def get_allow_storefront_traffic(request: SaleorContext) -> bool:
    cache_key = _get_allow_storefront_traffic_cache_key(request)
    allow_storefront_traffic = cache.get(cache_key)
    if allow_storefront_traffic is None:
        # Only on a cache miss. The dataloader resolves the site exactly like
        # `get_current` (SITE_ID, else host with a port-stripping fallback) but keeps
        # the result on the request instead of the process-global site cache.
        site = get_site_promise(request).get()
        allow_storefront_traffic = (
            SiteSettings.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
            .values_list("allow_storefront_traffic", flat=True)
            .get(site_id=site.pk)
        )
        set_allow_storefront_traffic_cache(allow_storefront_traffic, request)
    return allow_storefront_traffic


def _is_staff_user(request: SaleorContext) -> bool:
    """Resolve the request's user and report whether it is a staff member.

    ``get_context_value`` only binds ``request.user`` as a ``SimpleLazyObject``, so
    reading it here is what actually runs the authentication stack (a JWT decode plus
    a database read). Call this last, once the cheaper checks have failed to settle
    the decision on their own.
    """
    if not get_token_from_request(request):
        # No credentials at all, so there is no user to resolve.
        return False

    try:
        # Needed because Saleor implicitly authenticates the user when accessing the
        # property `.user` (magic). Binding the SimpleLazyObject does not
        # authenticate — the first attribute access does. Force it inside this try
        # (via `if not user`) so the implicit auth and any InvalidTokenError it
        # raises are caught here.
        user = request.user
        if not user:
            return False
    except InvalidTokenError:
        return False

    if isinstance(user, User) is False:
        warnings.warn(
            f"An invalid user object was found: {user}",
            stacklevel=3,
        )
        return False

    return user.is_staff


def is_storefront_traffic_blocked(request: SaleorContext) -> bool:
    """Return True when a request must be rejected as disallowed storefront traffic.

    App-authenticated and staff-user requests may always call the API directly.
    Other requests follow the cached shop setting.

    The checks run cheapest first. ``request.app`` is already resolved by
    ``get_context_value``, so reading it is free. The shop setting is a cached
    lookup. Only when traffic is actually disabled do we resolve ``request.user``
    and pay for authentication — on the common path, where traffic is allowed, that
    cost is never incurred.
    """
    if request.app:
        return False
    if get_allow_storefront_traffic(request):
        return False
    return not _is_staff_user(request)
