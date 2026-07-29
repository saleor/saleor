import warnings

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from jwt import InvalidTokenError

from ..account.models import User
from ..core.auth import get_token_from_request
from ..site.models import SiteSettings
from .core import SaleorContext

STOREFRONT_TRAFFIC_ERROR_CODE = "STOREFRONT_TRAFFIC_NOT_ALLOWED"
STOREFRONT_TRAFFIC_ERROR_MESSAGE = "Storefront traffic is not allowed."
STOREFRONT_TRAFFIC_CACHE_TIMEOUT = 5 * 60


def _get_allow_storefront_traffic_cache_key() -> str:
    """Build the cache key from ``settings.SITE_ID`` directly.

    Using ``Site.objects.get_current()`` here would populate the patched,
    process-global ``THREADED_SITE_CACHE`` on every request. That cache is not
    invalidated by ``Site``/``SiteSettings`` saves (Django's ``clear_site_cache``
    signal targets the unused original ``SITE_CACHE``), so it would leak stale
    site data across requests and tests.
    """
    site = Site.objects.get_current()
    return f"allow_storefront_traffic:{site.pk}"


def set_allow_storefront_traffic_cache(allow_storefront_traffic: bool) -> None:
    cache.set(
        _get_allow_storefront_traffic_cache_key(),
        allow_storefront_traffic,
        STOREFRONT_TRAFFIC_CACHE_TIMEOUT,
    )


def clear_allow_storefront_traffic_cache() -> None:
    cache.delete(_get_allow_storefront_traffic_cache_key())


def get_allow_storefront_traffic() -> bool:
    cache_key = _get_allow_storefront_traffic_cache_key()
    allow_storefront_traffic = cache.get(cache_key)
    if allow_storefront_traffic is None:
        allow_storefront_traffic = (
            SiteSettings.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
            .values_list("allow_storefront_traffic", flat=True)
            .get(site=Site.objects.get_current())
        )
        set_allow_storefront_traffic_cache(allow_storefront_traffic)
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
    if get_allow_storefront_traffic():
        return False
    return not _is_staff_user(request)
