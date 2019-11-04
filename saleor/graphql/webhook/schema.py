import graphene

from ..core.fields import FilterInputConnectionField
from ..decorators import permission_required
from .enums import WebhookEventTypeEnum
from .filters import WebhookFilterInput
from .mutations import WebhookCreate, WebhookDelete, WebhookUpdate
from .resolvers import (
    resolve_sample_payload,
    resolve_webhook,
    resolve_webhook_events,
    resolve_webhooks,
)
from .types import Webhook, WebhookEvent


class WebhookQueries(graphene.ObjectType):
    webhook = graphene.Field(
        Webhook,
        id=graphene.Argument(
            graphene.ID, required=True, description="ID of the webhook."
        ),
        description="Look up a webhook by ID.",
    )
    webhooks = FilterInputConnectionField(
        Webhook,
        description="List of webhooks.",
        filter=WebhookFilterInput(description="Filtering options for webhooks."),
    )
    webhook_events = graphene.List(
        WebhookEvent, description="List of all available webhook events."
    )

    webhook_sample_payload = graphene.Field(
        graphene.JSONString,
        event_type=graphene.Argument(
            WebhookEventTypeEnum,
            required=True,
            description="Name of the requested event type.",
        ),
        description=(
            "Retrieve a sample payload for a given webhook event based on real data. It"
            " can be useful for some integrations where sample payload is required."
        ),
    )

    @staticmethod
    def resolve_webhook_sample_payload(_, info, **data):
        return resolve_sample_payload(info, data["event_type"])

    @staticmethod
    def resolve_webhooks(_, info, **_kwargs):
        return resolve_webhooks(info)

    @staticmethod
    def resolve_webhook(_, info, **data):
        return resolve_webhook(info, data["id"])

    @staticmethod
    @permission_required("webhook.manage_webhooks")
    def resolve_webhook_events(_, *_args, **_data):
        return resolve_webhook_events()


class WebhookMutations(graphene.ObjectType):
    webhook_create = WebhookCreate.Field()
    webhook_delete = WebhookDelete.Field()
    webhook_update = WebhookUpdate.Field()
