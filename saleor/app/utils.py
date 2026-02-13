import logging
from contextlib import contextmanager

from django.db import transaction
from django.utils import timezone

from ..webhook.event_types import WebhookEventSyncType
from ..webhook.utils import get_webhooks_for_event
from .models import AppWebhookMutex

logger = logging.getLogger(__name__)


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


@contextmanager
def refresh_webhook_mutex(app_id: int):
    """Get mutex object and refresh acquisition date."""
    with transaction.atomic():
        mutex, _created = AppWebhookMutex.objects.select_for_update(
            of=(["self"])
        ).get_or_create(app_id=app_id)

        if not _created:
            mutex.acquired_at = timezone.now()
            mutex.save(update_fields=["acquired_at"])

        yield mutex
