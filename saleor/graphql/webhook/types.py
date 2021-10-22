import graphene

from ...webhook import models
from ...webhook.event_types import WebhookEventType
from ..core.connection import CountableDjangoObjectType
from ..core.descriptions import DEPRECATED_IN_3X_FIELD
from . import enums


class WebhookEvent(CountableDjangoObjectType):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = enums.WebhookEventTypeEnum(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Webhook event."
        only_fields = ["event_type"]

    @staticmethod
    def resolve_name(root: models.WebhookEvent, *_args, **_kwargs):
        return WebhookEventType.DISPLAY_LABELS.get(root.event_type) or root.event_type


class WebhookEventAsync(CountableDjangoObjectType):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = enums.WebhookEventTypeAsync(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Asynchronous webhook event."
        only_fields = ["event_type"]

    @staticmethod
    def resolve_name(root: models.WebhookEvent, *_args, **_kwargs):
        return WebhookEventType.DISPLAY_LABELS.get(root.event_type) or root.event_type


class WebhookEventSync(CountableDjangoObjectType):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = enums.WebhookEventTypeSync(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Synchronous webhook event."
        only_fields = ["event_type"]

    @staticmethod
    def resolve_name(root: models.WebhookEvent, *_args, **_kwargs):
        return WebhookEventType.DISPLAY_LABELS.get(root.event_type) or root.event_type


class Webhook(CountableDjangoObjectType):
    name = graphene.String(required=True)
    events = graphene.List(
        graphene.NonNull(WebhookEvent),
        description="List of webhook events.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `asyncEvents` or `syncEvents` instead."
        ),
        required=True,
    )
    sync_events = graphene.List(
        graphene.NonNull(WebhookEventSync),
        description="List of synchronous webhook events.",
        required=True,
    )
    async_events = graphene.List(
        graphene.NonNull(WebhookEventAsync),
        description="List of asynchronous webhook events.",
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
    def resolve_async_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.exclude(event_type__in=WebhookEventType.SYNC_EVENTS)

    @staticmethod
    def resolve_sync_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.filter(event_type__in=WebhookEventType.SYNC_EVENTS)

    @staticmethod
    def resolve_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.all()
