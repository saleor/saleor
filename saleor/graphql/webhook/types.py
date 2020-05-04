import graphene

from ...webhook import models
from ...webhook.event_types import WebhookEventType
from ..account.deprecated.types import ServiceAccount
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
    service_account = graphene.Field(
        ServiceAccount,
        required=True,
        deprecation_reason=(
            "Use the `app` field instead. This field will be removed after 2020-07-31."
        ),
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
    def resolve_service_account(root: models.Webhook, *_args, **_kwargs):
        return root.app

    @staticmethod
    def resolve_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.all()
