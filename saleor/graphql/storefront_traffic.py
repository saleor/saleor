import warnings

from django.conf import settings
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
    return f"allow_storefront_traffic:{settings.SITE_ID}"


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
            .get(site_id=settings.SITE_ID)
        )
        set_allow_storefront_traffic_cache(allow_storefront_traffic)
    return allow_storefront_traffic


def _is_privileged(request: SaleorContext) -> bool:
    if request.app:
        return True

    if not get_token_from_request(request):
        # Anonymous request (no credentials): it can never be privileged, so we
        # avoid resolving `request.user`, which would run the (expensive)
        # authentication stack — a per-request cost on the storefront hot path.
        return False

    try:
        user = request.user
    # Needed because Saleor implicitly authenticates the user when
    # access the property `.user` (magic)
    except InvalidTokenError:
        return False

    if not user:
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

    ``_is_privileged`` is checked first: the view already resolves and caches the
    app/user via ``get_context_value`` before this guard runs, so the check is
    cheap and lets privileged requests skip the storefront-setting cache/DB
    lookup entirely.
    """
    if _is_privileged(request):
        return False
    return not get_allow_storefront_traffic()
