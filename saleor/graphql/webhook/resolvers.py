import graphene
from graphql_jwt.exceptions import PermissionDenied

from ...core.permissions import WebhookPermissions
from ...webhook import models, payloads
from ...webhook.event_types import WebhookEventType
from .types import Webhook, WebhookEvent


def resolve_webhooks(info, **_kwargs):
    app = info.context.app
    if app:
        qs = models.Webhook.objects.filter(app=app)
    else:
        user = info.context.user
        if not user.has_perm(WebhookPermissions.MANAGE_WEBHOOKS):
            raise PermissionDenied()
        qs = models.Webhook.objects.all()
    return qs


def resolve_webhook(info, webhook_id):
    app = info.context.app
    if app:
        _, webhook_id = graphene.Node.from_global_id(webhook_id)
        return app.webhooks.filter(id=webhook_id).first()
    user = info.context.user
    if user.has_perm(WebhookPermissions.MANAGE_WEBHOOKS):
        return graphene.Node.get_node_from_global_id(info, webhook_id, Webhook)
    raise PermissionDenied()


def resolve_webhook_events():
    return [
        WebhookEvent(event_type=event_type[0])
        for event_type in WebhookEventType.CHOICES
    ]


def resolve_sample_payload(info, event_name):
    app = info.context.app
    required_permission = WebhookEventType.PERMISSIONS.get(event_name)
    if required_permission:
        if app and app.has_perm(required_permission):
            return payloads.generate_sample_payload(event_name)
        if info.context.user.has_perm(required_permission):
            return payloads.generate_sample_payload(event_name)
    raise PermissionDenied()
