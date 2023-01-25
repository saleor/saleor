import graphene
from graphene.utils.str_converters import to_camel_case

from ....permission.auth_filters import AuthorizationFilters
from ....webhook.error_codes import WebhookDryRunErrorCode
from ....webhook.event_types import WebhookEventAsyncType
from ...core.descriptions import ADDED_IN_311, PREVIEW_FEATURE
from ...core.fields import JSONString
from ...core.mutations import BaseMutation
from ...core.types import WebhookDryRunError
from ...core.utils import raise_validation_error
from ..subscription_payload import (
    generate_payload_from_subscription,
    initialize_request,
)
from ..subscription_query import SubscriptionQuery
from ..subscription_types import WEBHOOK_TYPES_MAP


class WebhookDryRun(BaseMutation):
    payload = JSONString(
        description="JSON payload, that would be sent out to webhook's target URL."
    )

    class Arguments:
        query = graphene.String(
            description="The subscription query that defines the webhook event and its "
            "payload.",
            required=True,
        )
        object_id = graphene.ID(
            description="The ID of an object to serialize.", required=True
        )

    class Meta:
        description = (
            "Performs a dry run of a webhook event. "
            "Supports a single event (the first, if multiple provided in the `query`). "
            "Requires permission relevant to processed event."
            + ADDED_IN_311
            + PREVIEW_FEATURE
        )
        permissions = (AuthorizationFilters.AUTHENTICATED_STAFF_USER,)
        error_type_class = WebhookDryRunError

    @classmethod
    def validate_query(cls, query):
        subscription_query = SubscriptionQuery(query)
        if not subscription_query.is_valid:
            raise_validation_error(
                field="query",
                message=subscription_query.error_msg,
                code=subscription_query.error_code,
            )

        events = subscription_query.events
        return events[0] if events else None

    @classmethod
    def validate_event_type(cls, event_type, object_id):
        event = WEBHOOK_TYPES_MAP[event_type]
        model, _ = graphene.Node.from_global_id(object_id)
        model_name = event._meta.root_type  # type: ignore[attr-defined]
        enable_dry_run = event._meta.enable_dry_run  # type: ignore[attr-defined]

        if not (model_name or enable_dry_run) and event_type:
            event_name = event_type[0].upper() + to_camel_case(event_type)[1:]
            raise_validation_error(
                field="query",
                message=f"Event type: {event_name} not supported.",
                code=WebhookDryRunErrorCode.TYPE_NOT_SUPPORTED,
            )
        if model != model_name:
            raise_validation_error(
                field="objectId",
                message="ObjectId doesn't match event type.",
                code=WebhookDryRunErrorCode.INVALID_ID,
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
                    code=WebhookDryRunErrorCode.MISSING_PERMISSION,
                )

    @classmethod
    def validate_input(cls, info, **data):
        query = data.get("query")
        object_id = data.get("object_id")

        event_type = cls.validate_query(query)
        cls.validate_event_type(event_type, object_id)
        cls.validate_permissions(info, event_type)

        object = cls.get_node_or_error(info, object_id, field="objectId")

        return event_type, object, query

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        event_type, object, query = cls.validate_input(info, **data)
        payload = None
        if all([event_type, object, query]):
            request = initialize_request()
            payload = generate_payload_from_subscription(
                event_type, object, query, request
            )
        return WebhookDryRun(payload=payload)
