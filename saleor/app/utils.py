from ..webhook.event_types import WebhookEventSyncType
from ..webhook.utils import get_webhooks_for_event
from .models import DEPRECATION_REASON_MAX_LENGTH


def get_active_tax_apps(identifiers: list[str] | None = None):
    checkout_webhooks = get_webhooks_for_event(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        apps_identifier=identifiers,
    )
    order_webhooks = get_webhooks_for_event(
        event_type=WebhookEventSyncType.ORDER_CALCULATE_TAXES,
        apps_identifier=identifiers,
    )

    checkout_apps = {webhook.app for webhook in checkout_webhooks}
    order_apps = {webhook.app for webhook in order_webhooks}

    return checkout_apps.union(order_apps)


def normalize_deprecation_reason(value: str | None) -> str | None:
    """Normalize an app's deprecation reason to what the column accepts.

    Blank and whitespace-only values mean "not deprecated" and are stored as
    NULL. Over-long values are truncated rather than rejected: the reason is
    purely informational, so it must never be able to fail an app install or a
    mutation.
    """
    reason = (value or "").strip()
    if not reason:
        return None
    if len(reason) > DEPRECATION_REASON_MAX_LENGTH:
        return reason[: DEPRECATION_REASON_MAX_LENGTH - 3] + "..."
    return reason
