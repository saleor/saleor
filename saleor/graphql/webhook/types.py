import graphene

from ...core import models as core_models
from ...webhook import models
from ...webhook.event_types import WebhookEventType
from ..core.connection import CountableDjangoObjectType
from ..core.fields import FilterInputConnectionField
from ..webhook.enums import EventDeliveryStatusEnum, WebhookEventTypeEnum
from ..webhook.filters import EventDeliveryFilterInput
from ..webhook.sorters import (
    EventDeliveryAttemptSortingInput,
    EventDeliverySortingInput,
)


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


class EventDelivery(CountableDjangoObjectType):
    status = EventDeliveryStatusEnum(
        description="Event delivery status.", required=True
    )
    attempts = FilterInputConnectionField(
        EventDeliveryAttempt,
        sort_by=EventDeliveryAttemptSortingInput(description="Event delivery sorter"),
        description="Event delivery attempts.",
    )
    event_type = WebhookEventTypeEnum(description="Webhook event type.", required=True)

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
    def resolve_attempts(root: core_models.EventDelivery, *_args, **_kwargs):
        return core_models.EventDeliveryAttempt.objects.filter(delivery=root)


class Webhook(CountableDjangoObjectType):
    name = graphene.String(required=True)
    events = graphene.List(
        graphene.NonNull(WebhookEvent),
        description="List of webhook events.",
        required=True,
    )
    app = graphene.Field("saleor.graphql.app.types.App", required=True)
    deliveries = FilterInputConnectionField(
        EventDelivery,
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
    def resolve_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.all()
