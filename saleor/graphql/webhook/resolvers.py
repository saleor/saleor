import graphene
from graphql_jwt.exceptions import PermissionDenied

from ...webhook import WebhookEventType, models, payloads
from .types import Webhook, WebhookEvent


def resolve_webhooks(info):
    service_account = info.context.service_account
    if service_account:
        return models.Webhook.objects.filter(service_account=service_account)
    user = info.context.user
    if not user.has_perm("webhook.manage_webhooks"):
        raise PermissionDenied()
    return models.Webhook.objects.all()


def resolve_webhook(info, webhook_id):
    service_account = info.context.service_account
    if service_account:
        _, webhook_id = graphene.Node.from_global_id(webhook_id)
        return service_account.webhooks.filter(id=webhook_id).first()
    user = info.context.user
    if user.has_perm("webhook.manage_webhooks"):
        return graphene.Node.get_node_from_global_id(info, webhook_id, Webhook)
    raise PermissionDenied()


def resolve_webhook_events():
    return [
        WebhookEvent(event_type=event_type[0])
        for event_type in WebhookEventType.CHOICES
    ]


def resolve_sample_payload(info, event_name):
    service_account = info.context.service_account
    required_permission = WebhookEventType.PERMISSIONS.get(event_name)
    if service_account and service_account.has_perm(required_permission):
        return payloads.generate_sample_payload(event_name)
    if info.context.user.has_perm(required_permission):
        return payloads.generate_sample_payload(event_name)
    raise PermissionDenied()
