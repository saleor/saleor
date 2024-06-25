import graphene

from ...core import models as core_models
from ...webhook import models
from ...webhook.deprecated_event_types import WebhookEventType
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ..core import ResolveInfo
from ..core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ..core.context import get_database_connection_name
from ..core.descriptions import ADDED_IN_312, DEPRECATED_IN_3X_FIELD, PREVIEW_FEATURE
from ..core.fields import FilterConnectionField, JSONString
from ..core.scalars import DateTime
from ..core.types import ModelObjectType, NonNullList
from ..webhook.enums import EventDeliveryStatusEnum, WebhookEventTypeEnum
from ..webhook.filters import EventDeliveryFilterInput
from ..webhook.sorters import (
    EventDeliveryAttemptSortingInput,
    EventDeliverySortingInput,
)
from . import enums
from .dataloaders import PayloadByIdLoader, WebhookEventsByWebhookIdLoader


class WebhookEvent(ModelObjectType[models.WebhookEvent]):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = enums.WebhookEventTypeEnum(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Webhook event."

    @staticmethod
    def resolve_name(root: models.WebhookEvent, _info):
        return WebhookEventType.DISPLAY_LABELS.get(root.event_type) or root.event_type


class WebhookEventAsync(ModelObjectType[models.WebhookEvent]):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = enums.WebhookEventTypeAsyncEnum(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Asynchronous webhook event."

    @staticmethod
    def resolve_name(root: models.WebhookEvent, _info):
        if root.event_type in WebhookEventAsyncType.EVENT_MAP:
            return WebhookEventAsyncType.EVENT_MAP[root.event_type]["name"]
        return root.event_type


class WebhookEventSync(ModelObjectType[models.WebhookEvent]):
    name = graphene.String(description="Display name of the event.", required=True)
    event_type = enums.WebhookEventTypeSyncEnum(
        description="Internal name of the event type.", required=True
    )

    class Meta:
        model = models.WebhookEvent
        description = "Synchronous webhook event."

    @staticmethod
    def resolve_name(root: models.WebhookEvent, _info):
        if root.event_type in WebhookEventSyncType.EVENT_MAP:
            return WebhookEventSyncType.EVENT_MAP[root.event_type]["name"]
        return root.event_type


class EventDeliveryAttempt(ModelObjectType[core_models.EventDeliveryAttempt]):
    id = graphene.GlobalID(
        required=True, description="The ID of Event Delivery Attempt."
    )
    created_at = DateTime(
        description="Event delivery creation date and time.", required=True
    )
    task_id = graphene.String(description="Task id for delivery attempt.")
    duration = graphene.Float(description="Delivery attempt duration.")
    response = graphene.String(description="Delivery attempt response content.")
    response_headers = graphene.String(
        description="Response headers for delivery attempt."
    )
    response_status_code = graphene.Int(
        description="Delivery attempt response status code."
    )
    request_headers = graphene.String(
        description="Request headers for delivery attempt."
    )
    status = EventDeliveryStatusEnum(
        description="Event delivery status.", required=True
    )

    class Meta:
        description = "Event delivery attempts."
        model = core_models.EventDeliveryAttempt
        interfaces = [graphene.relay.Node]


class EventDeliveryAttemptCountableConnection(CountableConnection):
    class Meta:
        node = EventDeliveryAttempt


class EventDelivery(ModelObjectType[core_models.EventDelivery]):
    id = graphene.GlobalID(required=True, description="The ID of an event delivery.")
    created_at = DateTime(
        required=True, description="Creation time of an event delivery."
    )
    status = EventDeliveryStatusEnum(
        description="Event delivery status.", required=True
    )
    event_type = WebhookEventTypeEnum(description="Webhook event type.", required=True)
    attempts = FilterConnectionField(
        EventDeliveryAttemptCountableConnection,
        sort_by=EventDeliveryAttemptSortingInput(description="Event delivery sorter"),
        description="Event delivery attempts.",
    )
    payload = graphene.String(description="Event payload.")

    class Meta:
        description = "Event delivery."
        model = core_models.EventDelivery
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_attempts(root: core_models.EventDelivery, info: ResolveInfo, **kwargs):
        qs = core_models.EventDeliveryAttempt.objects.using(
            get_database_connection_name(info.context)
        ).filter(delivery=root)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(
            qs, info, kwargs, EventDeliveryAttemptCountableConnection
        )

    @staticmethod
    def resolve_payload(root: core_models.EventDelivery, info: ResolveInfo):
        if not root.payload_id:
            return None
        return PayloadByIdLoader(info.context).load(root.payload_id)


class EventDeliveryCountableConnection(CountableConnection):
    class Meta:
        node = EventDelivery


class Webhook(ModelObjectType[models.Webhook]):
    id = graphene.GlobalID(required=True, description="The ID of webhook.")
    name = graphene.String(required=False, description="The name of webhook.")
    events = NonNullList(
        WebhookEvent,
        description="List of webhook events.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `asyncEvents` or `syncEvents` instead."
        ),
        required=True,
    )
    sync_events = NonNullList(
        WebhookEventSync,
        description="List of synchronous webhook events.",
        required=True,
    )
    async_events = NonNullList(
        WebhookEventAsync,
        description="List of asynchronous webhook events.",
        required=True,
    )
    app = graphene.Field(
        "saleor.graphql.app.types.App",
        required=True,
        description="The app associated with Webhook.",
    )
    event_deliveries = FilterConnectionField(
        EventDeliveryCountableConnection,
        sort_by=EventDeliverySortingInput(description="Event delivery sorter."),
        filter=EventDeliveryFilterInput(description="Event delivery filter options."),
        description="Event deliveries.",
    )
    target_url = graphene.String(required=True, description="Target URL for webhook.")
    is_active = graphene.Boolean(
        required=True, description="Informs if webhook is activated."
    )
    secret_key = graphene.String(
        description="Used to create a hash signature for each payload.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} As of Saleor 3.5, webhook payloads default to "
            "signing using a verifiable JWS."
        ),
    )
    subscription_query = graphene.String(
        description="Used to define payloads for specific events."
    )
    custom_headers = JSONString(
        description="Custom headers, which will be added to HTTP request."
        + ADDED_IN_312
        + PREVIEW_FEATURE
    )

    class Meta:
        description = "Webhook."
        model = models.Webhook
        interfaces = [graphene.relay.Node]

    @staticmethod
    def resolve_async_events(root: models.Webhook, info: ResolveInfo):
        def _filter_by_async_type(webhook_events: list[WebhookEvent]):
            return filter(
                lambda webhook_event: webhook_event.event_type
                in WebhookEventAsyncType.ALL,
                webhook_events,
            )

        return (
            WebhookEventsByWebhookIdLoader(info.context)
            .load(root.id)
            .then(_filter_by_async_type)
        )

    @staticmethod
    def resolve_sync_events(root: models.Webhook, info: ResolveInfo):
        def _filter_by_sync_type(webhook_events: list[WebhookEvent]):
            return filter(
                lambda webhook_event: webhook_event.event_type
                in WebhookEventSyncType.ALL,
                webhook_events,
            )

        return (
            WebhookEventsByWebhookIdLoader(info.context)
            .load(root.id)
            .then(_filter_by_sync_type)
        )

    @staticmethod
    def resolve_events(root: models.Webhook, info: ResolveInfo):
        return WebhookEventsByWebhookIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_event_deliveries(root: models.Webhook, info: ResolveInfo, **kwargs):
        qs = core_models.EventDelivery.objects.using(
            get_database_connection_name(info.context)
        ).filter(webhook_id=root.pk)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(
            qs, info, kwargs, EventDeliveryCountableConnection
        )
