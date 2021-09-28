import graphene

from ...webhook import models
from ...webhook.event_types import WebhookEventType
from ..core.connection import CountableDjangoObjectType
from .enums import WebhookEventTypeEnum


class WebhookEvent(CountableDjangoObjectType):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = WebhookEventTypeEnum(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Webhook event."
        only_fields = ["event_type"]

    @staticmethod
    def resolve_name(root: models.WebhookEvent, *_args, **_kwargs):
        return WebhookEventType.DISPLAY_LABELS.get(root.event_type) or root.event_type


class Webhook(CountableDjangoObjectType):
    name = graphene.String(required=True)
    events = graphene.List(
        graphene.NonNull(WebhookEvent),
        description="List of webhook events.",
        required=True,
    )
    app = graphene.Field("saleor.graphql.app.types.App", required=True)

    class Meta:
        description = "Webhook."
        model = models.Webhook
        interfaces = [graphene.relay.Node]
        only_fields = [
            "target_url",
            "is_active",
            "secret_key",
            "name",
        ]

    @staticmethod
    def resolve_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.all()
