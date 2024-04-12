from django.core.exceptions import ValidationError

from .....channel.models import Channel
from .....payment.interface import (
    PaymentMethodTokenizationBaseRequestData,
    PaymentMethodTokenizationResponseData,
)
from ....core import ResolveInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import PaymentMethodTokenizationResultEnum


def handle_payment_method_action(
    info: ResolveInfo,
    manager_func_name: str,
    request_data: PaymentMethodTokenizationBaseRequestData,
    error_type_class,
    channel: "Channel",
) -> tuple[PaymentMethodTokenizationResponseData, list[dict]]:
    manager = get_plugin_manager_promise(info.context).get()
    is_active = manager.is_event_active_for_any_plugin(
        manager_func_name, channel_slug=channel.slug
    )

    if not is_active:
        raise ValidationError(
            "No active payment app to handle requested action.",
            code=error_type_class.NOT_FOUND.value,
        )

    response = getattr(manager, manager_func_name)(request_data=request_data)

    errors = []
    result_enum = PaymentMethodTokenizationResultEnum
    result_without_error = [
        result_enum.SUCCESSFULLY_TOKENIZED,
        result_enum.ADDITIONAL_ACTION_REQUIRED,
        result_enum.PENDING,
    ]
    if response.result not in result_without_error:
        error_code = error_type_class.GATEWAY_ERROR.value
        errors.append(
            {
                "message": response.error,
                "code": error_code,
            }
        )
    return response, errors
