import graphene

from ..core.fields import PrefetchingConnectionField
from .mutations import WebhookCreate, WebhookDelete, WebhookUpdate
from .resolvers import resolve_webhook, resolve_webhooks
from .types import Webhook


class WebhookQueries(graphene.ObjectType):
    webhook = graphene.Field(
        Webhook,
        id=graphene.Argument(
            graphene.ID, required=True, description="ID of the webhook."
        ),
        description="Look up a webhook by ID.",
    )
    webhooks = PrefetchingConnectionField(Webhook, description="List of webhooks.")

    def resolve_webhooks(self, info, **_kwargs):
        return resolve_webhooks(info)

    def resolve_webhook(self, info, **data):
        return resolve_webhook(info, data["id"])


class WebhookMutations(graphene.ObjectType):
    webhook_create = WebhookCreate.Field()
    webhook_delete = WebhookDelete.Field()
    webhook_update = WebhookUpdate.Field()
