import graphene
import graphene_django_optimizer as gql_optimizer

from ...webhook import WebhookEventType, models
from ..core.connection import CountableDjangoObjectType
from .enums import WebhookEventTypeEnum


class WebhookEvent(CountableDjangoObjectType):
    name = graphene.String(description="Display name of the event.")
    event_type = WebhookEventTypeEnum(description="Internal name of the event type.")

    class Meta:
        model = models.WebhookEvent
        description = "Webhook event."
        only_fields = ["event_type", "name"]

    @staticmethod
    def resolve_name(root: models.WebhookEvent, *_args, **_kwargs):
        return WebhookEventType.DISPLAY_LABELS.get(root.event_type) or root.event_type


class Webhook(CountableDjangoObjectType):
    events = gql_optimizer.field(
        graphene.List(WebhookEvent, description="List of webhook events."),
        model_field="events",
    )

    class Meta:
        description = "Webhook."
        model = models.Webhook
        interfaces = [graphene.relay.Node]
        only_fields = [
            "service_account",
            "target_url",
            "is_active",
            "secret_key",
            "name",
        ]

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related=("events",))
    def resolve_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.all()
