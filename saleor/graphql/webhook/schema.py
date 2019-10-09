import graphene

from ..core.fields import PrefetchingConnectionField
from .enums import WebhookEventTypeEnum
from .mutations import WebhookCreate, WebhookDelete, WebhookUpdate
from .resolvers import resolve_sample_payload, resolve_webhook, resolve_webhooks
from .types import Webhook


class WebhookQueries(graphene.ObjectType):
    webhook = graphene.Field(
        Webhook,
        id=graphene.Argument(
            graphene.ID, required=True, description="ID of the webhook"
        ),
        description="Lookup a webhook by ID.",
    )
    webhooks = PrefetchingConnectionField(Webhook, description="List of webhooks")
    webhook_sample_payload = graphene.Field(
        graphene.JSONString,
        event_type=graphene.Argument(
            WebhookEventTypeEnum,
            required=True,
            description="Name of the reguested event type.",
        ),
    )

    def resolve_webhook_sample_payload(self, info, **data):
        return resolve_sample_payload(info, data["event_type"])

    def resolve_webhooks(self, info, **_kwargs):
        return resolve_webhooks(info)

    def resolve_webhook(self, info, **data):
        return resolve_webhook(info, data["id"])


class WebhookMutations(graphene.ObjectType):
    webhook_create = WebhookCreate.Field()
    webhook_delete = WebhookDelete.Field()
    webhook_update = WebhookUpdate.Field()
