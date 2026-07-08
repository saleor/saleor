import logging
from contextlib import contextmanager

from django.db import OperationalError, transaction

from ..core.db.connection import allow_writer
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
            AppWebhookMutex.objects.select_for_update(nowait=True, of=("self",)).get(
                app_id=app_id
            )
            logger.info("Acquired webhook lock for App ID: %s", app_id)
            yield True

    except OperationalError:
        logger.warning("Couldn't acquire the webhook lock. App ID: %s", app_id)
        yield False

    except AppWebhookMutex.DoesNotExist:
        logger.warning("AppWebhookMutex entry does not exist. App ID: %s", app_id)
        AppWebhookMutex.objects.get_or_create(app_id=app_id)
        with acquire_webhook_lock(app_id) as acquired:
            yield acquired


def get_app_ids_with_mutex_acquired(app_ids: list[int]) -> set[int]:
    """Return IDs of apps whose webhook mutex row is currently locked."""

    with allow_writer(), transaction.atomic():
        existing_ids = set(
            AppWebhookMutex.objects.filter(app_id__in=app_ids).values_list(
                "app_id", flat=True
            )
        )
        free_ids = set(
            AppWebhookMutex.objects.select_for_update(skip_locked=True, of=("self",))
            .filter(app_id__in=app_ids)
            .values_list("app_id", flat=True)
        )
    return existing_ids - free_ids
