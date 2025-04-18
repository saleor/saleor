import uuid
from contextlib import contextmanager

from django.db import DatabaseError, transaction
from django.utils import timezone

from ..webhook.event_types import WebhookEventSyncType
from ..webhook.utils import get_webhooks_for_event
from .models import AppWebhookMutex


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
    obj = None
    acquired = False
    try:
        with transaction.atomic():
            obj = AppWebhookMutex.objects.select_for_update(
                nowait=True, of=(["self"])
            ).get(app_id=app_id)

            acquired = True
            obj.acquired_at = timezone.now()
            obj.uuid = str(uuid.uuid4())
            obj.save()
            yield obj, acquired
    except AppWebhookMutex.DoesNotExist:
        "Safe fail, mutex object is expected to be created."
        obj, _created = AppWebhookMutex.objects.get_or_create(app_id=app_id)
        yield obj, acquired
    except DatabaseError:
        obj = AppWebhookMutex.objects.get(app_id=app_id)
        yield obj, acquired
