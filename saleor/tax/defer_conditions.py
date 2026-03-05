from ..checkout.models import Checkout
from ..order.models import Order

ADDRESS_MISSING = "ADDRESS_MISSING"

TAX_EVENTS = {
    "checkout_calculate_taxes",
    "order_calculate_taxes",
    "calculate_taxes",
}


def validate_defer_if_for_tax_events(subscription_events: list[str]) -> bool:
    """Return True if any of the subscription events are tax-related."""
    return any(e in TAX_EVENTS for e in subscription_events)


def should_defer_webhook(
    defer_if_conditions: list[str],
    subscribable_object,
) -> bool:
    """Return True if any defer condition is met (webhook should be skipped)."""
    for condition in defer_if_conditions:
        if condition == ADDRESS_MISSING and _is_address_missing(subscribable_object):
            return True
    return False


def _is_address_missing(obj) -> bool:
    if isinstance(obj, Checkout):
        if obj.is_shipping_required():
            return obj.shipping_address_id is None
        return obj.billing_address_id is None
    if isinstance(obj, Order):
        if obj.is_shipping_required():
            return obj.shipping_address_id is None
        return obj.billing_address_id is None
    return False
