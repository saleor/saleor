from typing import TYPE_CHECKING, Dict

from django.core.exceptions import ValidationError
from django.utils.translation import pgettext_lazy

if TYPE_CHECKING:
    from ..account.models import ServiceAccount


class WebhookEventType:
    ORDER_CREATED = "order_created"

    CHOICES = [(ORDER_CREATED, pgettext_lazy("Order has been placed", "Order created"))]

    PERMISSIONS = {ORDER_CREATED: "order.manage_orders"}


def service_account_has_required_permissions_for_events(
    service_account: "ServiceAccount", events: Dict[str, str]
):
    """Confirm that service account has all permissions required by events."""
    errors = {}
    for event in events:
        required_permission = WebhookEventType.PERMISSIONS.get(event)
        if not service_account.has_perm(required_permission):
            errors[
                event
            ] = "serviceAccount doesn't have expected permissions required by the event"

    if errors:
        raise ValidationError(errors)
