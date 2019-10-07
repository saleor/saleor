import graphene
import graphene_django_optimizer as gql_optimizer

from ...webhook import models
from ...webhook.payloads import generate_sample_payload
from ..core.connection import CountableDjangoObjectType


class WebhookEvent(graphene.ObjectType):
    event_type = graphene.String(description="Name of the event type.")
    sample_payload = graphene.JSONString(
        description="Sample payload that webhook sends."
    )

    class Meta:
        description = "Webhook event."

    @staticmethod
    def resolve_sample_payload(root: models.WebhookEvent, *_args, **_kwargs):
        return generate_sample_payload(root.event_type)


class Webhook(CountableDjangoObjectType):
    events = gql_optimizer.field(
        graphene.List(WebhookEvent, description="List of webhook events"),
        model_field="events",
    )

    class Meta:
        description = "Webhook"
        model = models.Webhook
        interfaces = [graphene.relay.Node]
        only_fields = ["service_account", "target_url", "is_active", "secret_key"]

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related=("events",))
    def resolve_events(root: models.Webhook, *_args, **_kwargs):
        return root.events.all()
