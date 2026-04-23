import json

import graphene
from django.utils import timezone

from ..core.utils.events import call_event
from ..core.utils.json_serializer import CustomJsonEncoder
from ..plugins.manager import PluginsManager
from ..webhook.event_types import WebhookEventAsyncType
from ..webhook.payloads import generate_meta, generate_requestor
from ..webhook.transport.synchronous.transport import trigger_webhook_sync_promise
from ..webhook.utils import get_webhooks_for_app_lifecycle_event
from .models import App


def delete_app(app: App, manager: PluginsManager, *, force_sync: bool = False) -> None:
    """Soft-delete an app and dispatch APP_DELETED.

    Sets `removed_at` and `is_active=False`, then fires the lifecycle
    webhook. The row is removed by the `remove_apps_task` Celery job once
    `DELETE_APP_TTL` elapses.

    When `force_sync` is True, the webhook is sent synchronously in-process
    instead of being queued on Celery.
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
    webhooks = get_webhooks_for_app_lifecycle_event(event_type, app)
    if not webhooks:
        return
    payload = json.dumps(
        {
            "id": graphene.Node.to_global_id("App", app.id),
            "is_active": app.is_active,
            "name": app.name,
            "meta": generate_meta(requestor_data=generate_requestor(None)),
        },
        cls=CustomJsonEncoder,
    )
    for webhook in webhooks:
        trigger_webhook_sync_promise(
            event_type=event_type,
            static_payload=payload,
            webhook=webhook,
            allow_replica=False,
            subscribable_object=app,
        ).get()
