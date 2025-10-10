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
def acquire_webhook_lock(app_id: int):
    try:
        with transaction.atomic():
            mutex = AppWebhookMutex.objects.select_for_update(
                nowait=True, of=(["self"])
            ).get(app_id=app_id)
            new_lock_uuid = uuid.uuid4()  # Generate a new lock UUID for next iteration
            yield True, new_lock_uuid
            mutex.lock_uuid = new_lock_uuid
            mutex.save()

    except DatabaseError:
        logger.warning("Couldn't acquire the webhook lock. App ID: %s", app_id)
        yield False, None
    except AppWebhookMutex.DoesNotExist:
        logger.warning("AppWebhookMutex entry does not exist. App ID: %s", app_id)
        AppWebhookMutex.objects.get_or_create(app_id=app_id)
        with acquire_webhook_lock(app_id) as (acquired, lock_uuid):
            yield acquired, lock_uuid
