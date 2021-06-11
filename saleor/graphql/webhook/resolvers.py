from ...core.exceptions import PermissionDenied
from ...core.permissions import AppPermission
from ...core.tracing import traced_resolver
from ...webhook import models, payloads
from ...webhook.event_types import WebhookEventType
from ..core.utils import from_global_id_or_error
from .types import WebhookEvent


@traced_resolver
def resolve_webhooks(info, **_kwargs):
    app = info.context.app
    if app:
        qs = models.Webhook.objects.filter(app=app)
    else:
        user = info.context.user
        if not user.has_perm(AppPermission.MANAGE_APPS):
            raise PermissionDenied()
        qs = models.Webhook.objects.all()
    return qs


@traced_resolver
def resolve_webhook(info, webhook_id):
    app = info.context.app
    _, webhook_id = from_global_id_or_error(webhook_id)
    if app:
        return app.webhooks.filter(id=webhook_id).first()
    user = info.context.user
    if user.has_perm(AppPermission.MANAGE_APPS):
        return models.Webhook.objects.filter(pk=webhook_id).first()
    raise PermissionDenied()


def resolve_webhook_events():
    return [
        WebhookEvent(event_type=event_type[0])
        for event_type in WebhookEventType.CHOICES
    ]


@traced_resolver
def resolve_sample_payload(info, event_name):
    app = info.context.app
    required_permission = WebhookEventType.PERMISSIONS.get(event_name)
    if required_permission:
        if app and app.has_perm(required_permission):
            return payloads.generate_sample_payload(event_name)
        if info.context.user.has_perm(required_permission):
            return payloads.generate_sample_payload(event_name)
    raise PermissionDenied()
