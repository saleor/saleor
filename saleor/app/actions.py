import logging

from django.utils import timezone

from ..core.telemetry import get_task_context
from ..core.utils.events import call_event
from ..plugins.manager import PluginsManager
from ..webhook.event_types import WebhookEventAsyncType
from ..webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
    send_webhook_request_async,
)
from ..webhook.utils import get_webhooks_for_app_lifecycle_event
from .models import App

logger = logging.getLogger(__name__)


def delete_app(app: App, manager: PluginsManager, *, force_sync: bool = False) -> None:
    """Soft-delete an app and dispatch APP_DELETED.

    Sets `removed_at` and `is_active=False`, then fires the lifecycle
    webhook. The row is removed by the `remove_apps_task` Celery job once
    `DELETE_APP_TTL` elapses.

    When `force_sync` is True, deliveries are persisted and the webhook
    task is executed in-process via Celery's eager `.apply()` instead of
    being queued.
    """
    app.removed_at = timezone.now()
    app.is_active = False
    app.save(update_fields=["removed_at", "is_active"])

    if force_sync:
        _dispatch_app_deleted_sync(app)
    else:
        call_event(manager.app_deleted, app)


def _dispatch_app_deleted_sync(app: App) -> None:
    event_type = WebhookEventAsyncType.APP_DELETED
    # Legacy (non-subscription) webhooks are intentionally not supported here.
    # They are deprecated and slated for removal; this path will not emit to
    # them. Only webhooks with a subscription query receive the event.
    # Apps are validated to always provide subscription query as required
    webhooks = [
        webhook
        for webhook in get_webhooks_for_app_lifecycle_event(event_type, app)
        if webhook.subscription_query
    ]
    if not webhooks:
        return

    deliveries = create_deliveries_for_subscriptions(
        event_type=event_type,
        subscribable_object=app,
        webhooks=webhooks,
    )

    telemetry_context = get_task_context().to_dict()
    for delivery in deliveries:
        try:
            send_webhook_request_async.apply(
                kwargs={
                    "event_delivery_id": delivery.pk,
                    "telemetry_context": telemetry_context,
                },
            )
        except Exception:
            logger.warning(
                "Sync APP_DELETED dispatch failed for app pk=%s delivery pk=%s",
                app.pk,
                delivery.pk,
                exc_info=True,
            )
