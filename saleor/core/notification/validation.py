from django.core.exceptions import ValidationError

from ...graphql.core.enums import ExternalNotificationTriggerErrorCode
from ...graphql.utils import resolve_global_ids_to_primary_keys


def validate_ids_and_get_model_type_and_pks(data_input):
    if ids := data_input.get("ids"):
        model_type, pks = resolve_global_ids_to_primary_keys(ids)
        return model_type, pks
    raise ValidationError(
        "The obligatory param 'ids' is missing or is empty.",
        code=ExternalNotificationTriggerErrorCode.IDS_MISSING,
    )


def validate_and_get_external_event_type(data_input):
    if external_event_type := data_input.get("external_event_type"):
        return external_event_type
    raise ValidationError(
        "The obligatory param 'external_event_type' is missing or is empty.",
        code=ExternalNotificationTriggerErrorCode.EXTERNAL_EVENT_TYPE_MISSING,
    )
