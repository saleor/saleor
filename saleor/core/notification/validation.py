from django.core.exceptions import ValidationError

from ...account.models import User
from ...account.notifications import get_user_custom_payload
from ...channel.models import Channel
from ...core.permissions import AccountPermissions, OrderPermissions
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
                "The obligatory param 'ids' is missing or is empty.",
                code=ExternalNotificationTriggerErrorCode.REQUIRED,
            )
        }
    )


def validate_and_get_external_event_type(data_input):
    if external_event_type := data_input.get("external_event_type"):
        return external_event_type
    raise ValidationError(
        {
            "external_event_type": ValidationError(
                "The obligatory param 'external_event_type' is missing or is empty.",
                code=ExternalNotificationTriggerErrorCode.REQUIRED,
            )
        }
    )


def validate_and_get_channel(data_input):
    if channel_slug := data_input.get("channel"):
        if Channel.objects.filter(slug=channel_slug).exists():
            if Channel.objects.get(slug=channel_slug).is_active:
                return channel_slug
            raise ValidationError(
                {
                    "channel": ValidationError(
                        "Cannot complete checkout with inactive channel.",
                        code=ExternalNotificationTriggerErrorCode.CHANNEL_INACTIVE,
                    )
                }
            )
        raise ValidationError(
            {
                "channel": ValidationError(
                    "The channel with given not exists.",
                    code=ExternalNotificationTriggerErrorCode.REQUIRED,
                )
            }
        )

    raise ValidationError(
        {
            "channel": ValidationError(
                "The obligatory param 'channel' is missing or is empty.",
                code=ExternalNotificationTriggerErrorCode.REQUIRED,
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
