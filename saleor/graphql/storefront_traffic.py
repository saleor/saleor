import warnings

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from jwt import InvalidTokenError

from ..account.models import User
from ..site.models import SiteSettings
from .core import SaleorContext

STOREFRONT_TRAFFIC_ERROR_CODE = "STOREFRONT_TRAFFIC_NOT_ALLOWED"
STOREFRONT_TRAFFIC_ERROR_MESSAGE = "Storefront traffic is not allowed."
STOREFRONT_TRAFFIC_CACHE_TIMEOUT = 5 * 60


def _get_allow_storefront_traffic_cache_key() -> str:
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


def _is_privileged(request: SaleorContext) -> bool:
    if request.app:
        return True

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

    The cheap cached setting is checked first so the expensive ``_is_privileged``
    call (which implicitly authenticates the user) only runs when storefront
    traffic is disallowed.
    """
    if get_allow_storefront_traffic():
        return False
    return not _is_privileged(request)
