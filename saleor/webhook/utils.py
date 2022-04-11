from typing import TYPE_CHECKING, Optional

from ..app.models import App
from .event_types import WebhookEventAsyncType, WebhookEventSyncType
from .models import Webhook

if TYPE_CHECKING:
    from django.db.models import QuerySet


def get_webhooks_for_event(
    event_type: str, webhooks: Optional["QuerySet[Webhook]"] = None
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

    if webhooks is None:
        webhooks = Webhook.objects.all()
    apps = App.objects.filter(is_active=True, **permissions)
    event_type_webhooks = Webhook.objects.filter(
        events__event_type__in=[event_type, WebhookEventAsyncType.ANY]
    )
    webhooks = (
        webhooks.filter(is_active=True, app__in=apps, id__in=event_type_webhooks)
        .select_related("app")
        .prefetch_related("app__permissions__content_type")
    )
    return webhooks
