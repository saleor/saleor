import logging
import uuid
from contextlib import contextmanager

from django.db import DatabaseError, transaction

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
def refresh_webhook_lock(app_id: int):
    """Generate a new lock UUID next batch of app webhooks."""
    with transaction.atomic():
        mutex, _created = AppWebhookMutex.objects.select_for_update(
            of=(["self"])
        ).get_or_create(app_id=app_id)

        if not _created:
            mutex.lock_uuid = uuid.uuid4()
            mutex.save(update_fields=["lock_uuid"])

        yield mutex.lock_uuid
