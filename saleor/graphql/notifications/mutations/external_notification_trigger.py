import graphene
from django.core.exceptions import ValidationError

from ....core.exceptions import PermissionDenied
from ....core.notification.mutation_handler import (
    ExternalNotificationTriggerPayload,
    get_payload_params,
    send_notification,
)
from ....core.notification.validation import (
    validate_and_get_external_event_type,
    validate_ids_and_get_model_type_and_pks,
)
from ....graphql.core.types.common import ExternalNotificationError
from ...core.mutations import BaseMutation


class ExternalNotificationTriggerInput(graphene.InputObjectType):
    ids = graphene.List(
        graphene.ID,
        required=True,
        description="""
        The list of customers or orders node IDs that will be serialized
         and included in the notification payload.""",
    )
    extra_payload = graphene.JSONString(
        description="""
        Additional payload that will be merged with
         the one based on the bussines object ID."""
    )
    external_event_type = graphene.String(
        required=True,
        description="""
        External event type. In case of invalid type,
         Saleor will consider the content
          of that field like a ID of dynamic template.""",
    )


class ExternalNotificationTrigger(BaseMutation):
    class Arguments:
        input = ExternalNotificationTriggerInput(
            required=True, description="Input for External Notification Trigger."
        )
        plugin_id = graphene.String(description="The ID of notification plugin.")

    class Meta:
        description = """
        Trigger sending a notification with the notify plugin method.
         Serializes nodes provided as ids parameter and includes this data in
          the notification payload."""
        error_type_class = ExternalNotificationError

    @classmethod
    def perform_mutation(cls, root, info, **data):
        manager = info.context.plugins
        plugin_id = data.get("plugin_id")
        if data_input := data.get("input"):
            model_type, pks = validate_ids_and_get_model_type_and_pks(data_input)
            extra_payload = data_input.get("extra_payload")
            external_event_type = validate_and_get_external_event_type(data_input)
            model, payload_function, input_type, permission_type = get_payload_params(
                model_type
            )
            if cls._is_user_has_permission(info.context, permission_type):
                payload = ExternalNotificationTriggerPayload(
                    model, payload_function, input_type
                ).as_dict(pks, extra_payload)
                send_notification(
                    manager, external_event_type, payload, plugin_id=plugin_id
                )
            return cls()
        raise ValidationError(
            "The obligatory param 'input' is missing or is empty.",
            code=cls._meta.error_type_class.INPUT_MISSING,
        )

    @classmethod
    def _is_user_has_permission(cls, context, permission_type):
        if cls.check_permissions(context, (permission_type,)):
            return True
        raise PermissionDenied()
