from django.core.exceptions import ValidationError

from ...account.models import User
from ...core.permissions import AccountPermissions, OrderPermissions
from ...graphql.core.enums import ExternalNotificationTriggerErrorCode
from ...graphql.utils import resolve_global_ids_to_primary_keys
from ...order.models import Order
from ...webhook.payloads import generate_customer_payload, generate_order_payload

PAYLOAD_MAPPING = {
    "User": (
        User,
        generate_customer_payload,
        AccountPermissions.MANAGE_USERS,
    ),
    "Order": (
        Order,
        generate_order_payload,
        OrderPermissions.MANAGE_ORDERS,
    ),
}


def validate_ids_and_get_model_type_and_pks(data_input):
    if ids := data_input.get("ids"):
        model_type, pks = resolve_global_ids_to_primary_keys(ids)
        return model_type, pks
    raise ValidationError(
        "The obligatory param 'ids' is missing or is empty.",
        code=ExternalNotificationTriggerErrorCode.REQUIRED,
    )


def validate_and_get_external_event_type(data_input):
    if external_event_type := data_input.get("external_event_type"):
        return external_event_type
    raise ValidationError(
        "The obligatory param 'external_event_type' is missing or is empty.",
        code=ExternalNotificationTriggerErrorCode.REQUIRED,
    )


def validate_and_get_payload_params(model_type):
    if payload_params := PAYLOAD_MAPPING.get(model_type):
        return payload_params
    raise ValidationError(
        f"Wrong type of model."
        f" ExternalNotificationTrigger is "
        f"suitable for {','.join(PAYLOAD_MAPPING.keys())} models.",
        code=ExternalNotificationTriggerErrorCode.INVALID_MODEL_TYPE,
    )
