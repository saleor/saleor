import graphene

from ..core.fields import PrefetchingConnectionField
from ..decorators import permission_required
from .mutations import WebhookCreate, WebhookDelete, WebhookUpdate
from .resolvers import resolve_webhooks
from .types import Webhook


class WebhookQueries(graphene.ObjectType):
    webhook = graphene.Field(
        Webhook,
        id=graphene.Argument(graphene.ID, required=True),
        description="Lookup a webhook by ID.",
    )
    webhooks = PrefetchingConnectionField(Webhook, description="List of webhooks")

    @permission_required("webhook.manage_webhooks")
    def resolve_webhooks(self, _info, **_kwargs):
        return resolve_webhooks()

    @permission_required("webhook.manage_webhooks")
    def resolve_webhook(self, info, **data):
        return graphene.Node.get_node_from_global_id(info, data["id"], Webhook)


class WebhookMutations(graphene.ObjectType):
    webhook_create = WebhookCreate.Field()
    webhook_delete = WebhookDelete.Field()
    webhook_update = WebhookUpdate.Field()
