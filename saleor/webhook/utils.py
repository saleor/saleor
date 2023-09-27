from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef

from ..app.models import App
from .event_types import WebhookEventAsyncType, WebhookEventSyncType
from .models import Webhook, WebhookEvent

if TYPE_CHECKING:
    from django.db.models import QuerySet


def get_webhooks_for_event(
    event_type: str,
    webhooks: Optional["QuerySet[Webhook]"] = None,
    apps_ids: Optional["list[int]"] = None,
    apps_identifier: Optional[list[str]] = None,
) -> "QuerySet[Webhook]":
    """Get active webhooks from the database for an event."""
    permissions = {}
    required_permission = WebhookEventAsyncType.PERMISSIONS.get(
        event_type, WebhookEventSyncType.PERMISSIONS.get(event_type)
    )
    if required_permission:
        app_label, codename = required_permission.value.split(".")
        permissions["permissions__content_type__app_label"] = app_label
        permissions["permissions__codename"] = codename

    # In this function we use the replica database for all queryset reads, as there is
    # no risk that any mutation would change the result of these querysets.

    if webhooks is None:
        webhooks = Webhook.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).all()

    app_kwargs: dict = {"is_active": True, **permissions}
    if apps_ids:
        app_kwargs["id__in"] = apps_ids
    if apps_identifier:
        app_kwargs["identifier__in"] = apps_identifier

    apps = App.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME).filter(
        **app_kwargs
    )
    event_types = [event_type]
    if event_type in WebhookEventAsyncType.ALL:
        event_types.append(WebhookEventAsyncType.ANY)

    webhook_events = WebhookEvent.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(event_type__in=event_types)
    return (
        webhooks.filter(
            Q(is_active=True, app__in=apps)
            & Q(Exists(webhook_events.filter(webhook_id=OuterRef("id"))))
        )
        .select_related("app")
        .prefetch_related("app__permissions__content_type")
    )
