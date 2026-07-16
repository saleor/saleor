from django.contrib.sites.models import Site

STOREFRONT_TRAFFIC_ERROR_CODE = "STOREFRONT_TRAFFIC_NOT_ALLOWED"
STOREFRONT_TRAFFIC_ERROR_MESSAGE = "Storefront traffic is not allowed."


def is_storefront_traffic_blocked(request) -> bool:
    """Return True when a request must be rejected as disallowed storefront traffic.

    Only App-authenticated and staff-user requests may call the API directly.
    They short-circuit and never read the shop setting. Anonymous requests and
    authenticated non-staff customers (invalid/expired credentials resolve to
    neither app nor user, so they land here too) are rejected when the shop
    disables storefront traffic — read via the process-cached
    ``Site.objects.get_current()``, so privileged traffic pays no extra cost.
    """
    if getattr(request, "app", None):
        return False
    user = getattr(request, "user", None)
    if user and user.is_staff:
        return False
    return not Site.objects.get_current().settings.allow_storefront_traffic
