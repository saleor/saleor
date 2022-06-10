from ...core.exceptions import PermissionDenied
from ...core.permissions import AppPermission
from ...core.tracing import traced_resolver
from ...webhook import models, payloads
from ...webhook.deprecated_event_types import WebhookEventType
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..core.utils import from_global_id_or_error
from .types import Webhook, WebhookEvent


def resolve_webhook(info, id):
    app = info.context.app
    _, id = from_global_id_or_error(id, Webhook)
    if app:
        return app.webhooks.filter(id=id).first()
    user = info.context.user
    if user.has_perm(AppPermission.MANAGE_APPS):
        return models.Webhook.objects.filter(pk=id).first()
    raise PermissionDenied(permissions=[AppPermission.MANAGE_APPS])


def resolve_webhook_events():
    return [
        WebhookEvent(event_type=event_type[0])
        for event_type in WebhookEventType.CHOICES
    ]


@traced_resolver
def resolve_sample_payload(info, event_name):
    app = info.context.app
    required_permission = WebhookEventAsyncType.PERMISSIONS.get(
        event_name, WebhookEventSyncType.PERMISSIONS.get(event_name)
    )
    if required_permission:
        if app and app.has_perm(required_permission):
            return payloads.generate_sample_payload(event_name)
        if info.context.user.has_perm(required_permission):
            return payloads.generate_sample_payload(event_name)
    raise PermissionDenied(permissions=[required_permission])
