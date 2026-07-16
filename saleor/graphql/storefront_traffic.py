import jwt
from django.contrib.sites.models import Site

STOREFRONT_TRAFFIC_ERROR_CODE = "STOREFRONT_TRAFFIC_NOT_ALLOWED"
STOREFRONT_TRAFFIC_ERROR_MESSAGE = "Storefront traffic is not allowed."


def is_storefront_traffic_blocked(request) -> bool:
    """Return True when a request must be rejected as disallowed storefront traffic.

    App-authenticated and staff-user requests may always call the API directly
    and never read the shop setting. Other requests follow the process-cached
    shop setting. Invalid or expired user tokens are treated as non-staff for
    this guard.
    """
    if getattr(request, "app", None):
        return False

    try:
        user = getattr(request, "user", None)
        if user and user.is_staff:
            return False
    except jwt.InvalidTokenError:
        pass

    return not Site.objects.get_current().settings.allow_storefront_traffic
