from django.core.exceptions import ValidationError

from ...account.models import User
from ...account.notifications import get_user_custom_payload
from ...core.permissions import AccountPermissions, OrderPermissions
from ...graphql.channel.utils import validate_channel
from ...graphql.core.enums import ExternalNotificationTriggerErrorCode
from ...graphql.utils import resolve_global_ids_to_primary_keys
from ...order.models import Order
from ...order.notifications import get_custom_order_payload

PAYLOAD_MAPPING_FOR_CUSTOM_NOTIFICATION = {
    "User": (
        User,
        get_user_custom_payload,
        AccountPermissions.MANAGE_USERS,
    ),
    "Order": (
        Order,
        get_custom_order_payload,
        OrderPermissions.MANAGE_ORDERS,
    ),
}


def validate_ids_and_get_model_type_and_pks(data_input):
    if ids := data_input.get("ids"):
        model_type, pks = resolve_global_ids_to_primary_keys(ids)
        return model_type, pks
    raise ValidationError(
        {
            "ids": ValidationError(
                "The obligatory param 'ids' is empty.",
                code=ExternalNotificationTriggerErrorCode.REQUIRED,
            )
        }
    )


def validate_and_get_external_event_type(data_input):
    if external_event_type := data_input.get("external_event_type"):
        return external_event_type
    raise ValidationError(
        {
            "externalEventType": ValidationError(
                "The obligatory param 'externalEventType' is empty.",
                code=ExternalNotificationTriggerErrorCode.REQUIRED,
            )
        }
    )


def validate_and_get_channel(data_input, error_class):
    if channel_slug := data_input.get("channel"):
        return validate_channel(channel_slug, error_class).slug
    raise ValidationError(
        {
            "channel": ValidationError(
                "The obligatory param 'channel' is empty.",
                code=ExternalNotificationTriggerErrorCode.REQUIRED.value,
            )
        }
    )


def validate_and_get_payload_params(model_type):
    if payload_params := PAYLOAD_MAPPING_FOR_CUSTOM_NOTIFICATION.get(model_type):
        return payload_params
    available_object_types = ",".join(PAYLOAD_MAPPING_FOR_CUSTOM_NOTIFICATION.keys())
    raise ValidationError(
        {
            "external_notification_trigger": ValidationError(
                f"Wrong type of object."
                f"ExternalNotificationTrigger is suitable for "
                f"{available_object_types} object types.",
                code=ExternalNotificationTriggerErrorCode.INVALID_MODEL_TYPE,
            )
        }
    )
