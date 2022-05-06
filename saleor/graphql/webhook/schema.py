import graphene

from ...core.permissions import AppPermission, AuthorizationFilters
from ..core.descriptions import DEPRECATED_IN_3X_FIELD
from ..core.fields import JSONString, PermissionsField
from ..core.types import NonNullList
from .enums import WebhookSampleEventTypeEnum
from .mutations import EventDeliveryRetry, WebhookCreate, WebhookDelete, WebhookUpdate
from .resolvers import resolve_sample_payload, resolve_webhook, resolve_webhook_events
from .types import Webhook, WebhookEvent


class WebhookQueries(graphene.ObjectType):
    webhook = graphene.Field(
        Webhook,
        id=graphene.Argument(
            graphene.ID, required=True, description="ID of the webhook."
        ),
        description=(
            "Look up a webhook by ID. Requires one of the following permissions: "
            f"{AppPermission.MANAGE_APPS.name}, {AuthorizationFilters.OWNER.name}."
        ),
    )
    webhook_events = PermissionsField(
        NonNullList(WebhookEvent),
        description="List of all available webhook events.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `WebhookEventTypeAsyncEnum` and "
            "`WebhookEventTypeSyncEnum` to get available event types."
        ),
        permissions=[AppPermission.MANAGE_APPS],
    )
    webhook_sample_payload = graphene.Field(
        JSONString,
        event_type=graphene.Argument(
            WebhookSampleEventTypeEnum,
            required=True,
            description="Name of the requested event type.",
        ),
        description=(
            "Retrieve a sample payload for a given webhook event based on real data. It"
            " can be useful for some integrations where sample payload is required."
        ),
    )

    @staticmethod
    def resolve_webhook_sample_payload(_root, info, **data):
        return resolve_sample_payload(info, data["event_type"])

    @staticmethod
    def resolve_webhook(_root, info, **data):
        return resolve_webhook(info, data["id"])

    @staticmethod
    def resolve_webhook_events(_root, _info):
        return resolve_webhook_events()


class WebhookMutations(graphene.ObjectType):
    webhook_create = WebhookCreate.Field()
    webhook_delete = WebhookDelete.Field()
    webhook_update = WebhookUpdate.Field()
    event_delivery_retry = EventDeliveryRetry.Field()
