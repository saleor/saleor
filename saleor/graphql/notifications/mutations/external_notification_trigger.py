import graphene

from ....core.exceptions import PermissionDenied
from ....core.notification.mutation_handler import (
    get_external_notification_payload,
    send_notification,
)
from ....core.notification.validation import (
    validate_and_get_channel,
    validate_and_get_external_event_type,
    validate_and_get_payload_params,
    validate_ids_and_get_model_type_and_pks,
)
from ...core.descriptions import ADDED_IN_31
from ...core.fields import JSONString
from ...core.mutations import BaseMutation
from ...core.types import ExternalNotificationError, NonNullList
from ...notifications.error_codes import ExternalNotificationErrorCodes


class ExternalNotificationTriggerInput(graphene.InputObjectType):
    ids = NonNullList(
        graphene.ID,
        required=True,
        description=(
            "The list of customers or orders node IDs that will be serialized and "
            "included in the notification payload."
        ),
    )
    extra_payload = JSONString(
        description=(
            "Additional payload that will be merged with "
            "the one based on the bussines object ID."
        )
    )
    external_event_type = graphene.String(
        required=True,
        description=(
            "External event type. This field is passed to a plugin as an event type."
        ),
    )


class ExternalNotificationTrigger(BaseMutation):
    class Arguments:
        input = ExternalNotificationTriggerInput(
            required=True, description="Input for External Notification Trigger."
        )
        plugin_id = graphene.String(description="The ID of notification plugin.")
        channel = graphene.String(
            required=True,
            description=(
                "Channel slug. "
                "Saleor will send a notification within a provided channel. "
                "Please, make sure that necessary plugins are active."
            ),
        )

    class Meta:
        description = (
            "Trigger sending a notification with the notify plugin method. "
            "Serializes nodes provided as ids parameter and includes this data in "
            "the notification payload." + ADDED_IN_31
        )
        error_type_class = ExternalNotificationError

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        manager = info.context.plugins
        plugin_id = data.get("plugin_id")
        channel_slug = validate_and_get_channel(data, ExternalNotificationErrorCodes)
        if data_input := data.get("input"):
            model_type, pks = validate_ids_and_get_model_type_and_pks(data_input)
            extra_payload = data_input.get("extra_payload")
            external_event_type = validate_and_get_external_event_type(data_input)
            model, payload_function, permission_type = validate_and_get_payload_params(
                model_type
            )
            if cls._requestor_has_permission(info.context, permission_type):
                objects = model.objects.filter(pk__in=pks)
                payload = get_external_notification_payload(
                    objects, extra_payload, payload_function
                )
                send_notification(
                    manager,
                    external_event_type,
                    payload,
                    channel_slug=channel_slug,
                    plugin_id=plugin_id,
                )
        return cls()

    @classmethod
    def _requestor_has_permission(cls, context, permission_type):
        if cls.check_permissions(context, (permission_type,)):
            return True
        raise PermissionDenied(permissions=[permission_type])
