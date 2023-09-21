import graphene
from celery.exceptions import Retry
from graphene.utils.str_converters import to_camel_case

from ....core import EventDeliveryStatus
from ....permission.auth_filters import AuthorizationFilters
from ....webhook.error_codes import WebhookTriggerErrorCode
from ....webhook.event_types import WebhookEventAsyncType
from ...core.descriptions import ADDED_IN_311, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_WEBHOOKS
from ...core.mutations import BaseMutation
from ...core.types.common import WebhookTriggerError
from ...core.utils import raise_validation_error
from ..subscription_query import SubscriptionQuery
from ..subscription_types import WEBHOOK_TYPES_MAP
from ..types import EventDelivery


class WebhookTrigger(BaseMutation):
    delivery = graphene.Field(EventDelivery)

    class Arguments:
        webhook_id = graphene.ID(description="The ID of the webhook.", required=True)
        object_id = graphene.ID(
            description="The ID of an object to serialize.", required=True
        )

    class Meta:
        description = (
            "Trigger a webhook event. Supports a single event (the first, if multiple "
            "provided in the `webhook.subscription_query`). Requires permission "
            "relevant to processed event. Successfully delivered webhook returns "
            "`delivery` with status='PENDING' and empty payload."
            + ADDED_IN_311
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_WEBHOOKS
        permissions = (AuthorizationFilters.AUTHENTICATED_STAFF_USER,)
        error_type_class = WebhookTriggerError

    @classmethod
    def validate_subscription_query(cls, webhook):
        query = getattr(webhook, "subscription_query")
        if not query:
            raise_validation_error(
                field="webhookId",
                message="Missing subscription query for given webhook.",
                code=WebhookTriggerErrorCode.MISSING_QUERY,
            )

        subscription_query = SubscriptionQuery(query)
        if not subscription_query.is_valid:
            raise_validation_error(
                message=subscription_query.error_msg,
                code=subscription_query.error_code,
            )

        events = subscription_query.events
        return events[0] if events else None

    @classmethod
    def validate_event_type(cls, event_type, object_id):
        event = WEBHOOK_TYPES_MAP[event_type] if event_type else None
        model, _ = graphene.Node.from_global_id(object_id)
        model_name = event._meta.root_type  # type: ignore[union-attr]
        enable_dry_run = event._meta.enable_dry_run  # type: ignore[union-attr]

        if not (model_name or enable_dry_run) and event_type:
            event_name = event_type[0].upper() + to_camel_case(event_type)[1:]
            raise_validation_error(
                message=f"Event type: {event_name}, which was parsed from webhook's "
                f"subscription query, is not supported.",
                code=WebhookTriggerErrorCode.TYPE_NOT_SUPPORTED,
            )
        if model != model_name:
            raise_validation_error(
                field="objectId",
                message="ObjectId doesn't match event type.",
                code=WebhookTriggerErrorCode.INVALID_ID,
            )

    @classmethod
    def validate_permissions(cls, info, event_type):
        if (
            permission := WebhookEventAsyncType.PERMISSIONS.get(event_type)
            if event_type
            else None
        ):
            codename = permission.value.split(".")[1]
            user_permissions = [
                perm.codename for perm in info.context.user.effective_permissions.all()
            ]
            if codename not in user_permissions:
                raise_validation_error(
                    message=f"The user doesn't have required permission: {codename}.",
                    code=WebhookTriggerErrorCode.MISSING_PERMISSION,
                )

    @classmethod
    def validate_input(cls, info, **data):
        object_id = data.get("object_id")
        webhook_id = data.get("webhook_id")
        webhook = cls.get_node_or_error(info, webhook_id, field="webhookId")

        event_type = cls.validate_subscription_query(webhook)
        cls.validate_event_type(event_type, object_id)
        cls.validate_permissions(info, event_type)

        object = cls.get_node_or_error(info, object_id, field="objectId")

        return event_type, object, webhook

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        from ....webhook.transport.asynchronous.transport import (
            create_deliveries_for_subscriptions,
            send_webhook_request_async,
        )

        event_type, object, webhook = cls.validate_input(info, **data)
        delivery = None

        if all([event_type, object, webhook]):
            deliveries = create_deliveries_for_subscriptions(
                event_type, object, [webhook]
            )
            if deliveries:
                delivery = deliveries[0]
                try:
                    send_webhook_request_async(delivery.id)
                    return WebhookTrigger(delivery=delivery)
                except Retry:
                    delivery.status = EventDeliveryStatus.FAILED
                    delivery.save(update_fields=["status"])

        return WebhookTrigger(delivery=delivery)
