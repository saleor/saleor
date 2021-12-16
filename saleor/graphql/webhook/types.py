import graphene

from ...core import models as core_models
from ...webhook import models
from ...webhook.deprecated_event_types import WebhookEventType
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..core.connection import (
    CountableConnection,
    CountableDjangoObjectType,
    create_connection_slice,
    filter_connection_queryset,
)
from ..core.descriptions import DEPRECATED_IN_3X_FIELD
from ..core.fields import FilterConnectionField
from ..webhook.enums import EventDeliveryStatusEnum, WebhookEventTypeEnum
from ..webhook.filters import EventDeliveryFilterInput
from ..webhook.sorters import (
    EventDeliveryAttemptSortingInput,
    EventDeliverySortingInput,
)
from . import enums
from .dataloaders import PayloadByIdLoader


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
    event_type = enums.WebhookEventTypeAsyncEnum(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Asynchronous webhook event."
        only_fields = ["event_type"]

    @staticmethod
    def resolve_name(root: models.WebhookEvent, *_args, **_kwargs):
        return (
            WebhookEventAsyncType.DISPLAY_LABELS.get(root.event_type) or root.event_type
        )


class WebhookEventSync(CountableDjangoObjectType):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = enums.WebhookEventTypeSyncEnum(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Synchronous webhook event."
        only_fields = ["event_type"]

    @staticmethod
    def resolve_name(root: models.WebhookEvent, *_args, **_kwargs):
        return (
            WebhookEventAsyncType.DISPLAY_LABELS.get(root.event_type) or root.event_type
        )


class EventDeliveryAttempt(CountableDjangoObjectType):
    created_at = graphene.DateTime(
        description="Event delivery creation date and time.", required=True
    )
    status = EventDeliveryStatusEnum(
        description="Event delivery status.", required=True
    )

    class Meta:
        description = "Event delivery attempts."
        model = core_models.EventDeliveryAttempt
        interfaces = [graphene.relay.Node]
        only_fields = [
            "id",
            "created_at",
            "task_id",
            "duration",
            "status",
            "response",
            "response_headers",
            "request_headers",
        ]


class EventDeliveryAttemptCountableConnection(CountableConnection):
    class Meta:
        node = EventDeliveryAttempt


class EventDelivery(CountableDjangoObjectType):
    status = EventDeliveryStatusEnum(
        description="Event delivery status.", required=True
    )
    attempts = FilterConnectionField(
        EventDeliveryAttemptCountableConnection,
        sort_by=EventDeliveryAttemptSortingInput(description="Event delivery sorter"),
        description="Event delivery attempts.",
    )
    event_type = WebhookEventTypeEnum(description="Webhook event type.", required=True)
    payload = graphene.String(description="Event payload.")

    class Meta:
        description = "Event delivery."
        model = core_models.EventDelivery
        interfaces = [graphene.relay.Node]
        only_fields = [
            "id",
            "created_at",
            "status",
            "event_type",
        ]

    @staticmethod
    def resolve_attempts(root: core_models.EventDelivery, info, *_args, **kwargs):
        qs = core_models.EventDeliveryAttempt.objects.filter(delivery=root)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(
            qs, info, kwargs, EventDeliveryAttemptCountableConnection
        )

    @staticmethod
    def resolve_payload(root: core_models.EventDelivery, info):
        if not root.payload_id:
            return None
        return PayloadByIdLoader(info.context).load(root.payload_id)


class EventDeliveryCountableConnection(CountableConnection):
    class Meta:
        node = EventDelivery


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
    event_deliveries = FilterConnectionField(
        EventDeliveryCountableConnection,
        sort_by=EventDeliverySortingInput(description="Event delivery sorter."),
        filter=EventDeliveryFilterInput(description="Event delivery filter options."),
        description="Event deliveries.",
    )

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
        return root.events.filter(event_type__in=WebhookEventAsyncType.ALL)

    @staticmethod
    def resolve_sync_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.filter(event_type__in=WebhookEventSyncType.ALL)

    @staticmethod
    def resolve_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.all()

    @staticmethod
    def resolve_event_deliveries(root: models.Webhook, info, *_args, **kwargs):
        qs = core_models.EventDelivery.objects.filter(webhook_id=root.pk)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(
            qs, info, kwargs, EventDeliveryCountableConnection
        )
