import graphene
from django.core.exceptions import ValidationError

from .....payment.interface import PaymentMethodInitializeTokenizationRequestData
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventSyncType
from ....channel.utils import validate_channel
from ....core.descriptions import ADDED_IN_316, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.enums import PaymentMethodInitializeTokenizationErrorCode
from ....core.mutations import BaseMutation
from ....core.scalars import JSON
from ....core.types.common import PaymentMethodInitializeTokenizationError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import PaymentMethodTokenizationResultEnum


class PaymentMethodInitializeTokenization(BaseMutation):
    result = PaymentMethodTokenizationResultEnum(
        description="A status of the payment method tokenization.", required=True
    )
    id = graphene.String(description="The identifier of the payment method.")
    data = JSON(
        description="A data returned by the payment app.",
    )

    class Arguments:
        id = graphene.String(
            required=True,
            description=(
                "The identifier of the payment gateway app to initialize payment "
                "method tokenization."
            ),
        )
        channel = graphene.String(
            description="Slug of a channel related to tokenization request.",
            required=True,
        )

        data = graphene.Argument(
            JSON, description="The data that will be passed to the payment gateway."
        )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        description = "Tokenize payment method." + ADDED_IN_316 + PREVIEW_FEATURE
        webhook_events_info = [
            WebhookEventInfo(
                type=(
                    WebhookEventSyncType.PAYMENT_METHOD_INITIALIZE_TOKENIZATION_SESSION
                ),
                description=("The customer requested to tokenize payment method."),
            ),
        ]
        error_type_class = PaymentMethodInitializeTokenizationError
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)

    @classmethod
    def _perform_mutation(cls, root, info, id, channel, data=None):
        user = info.context.user
        channel = validate_channel(
            channel, PaymentMethodInitializeTokenizationErrorCode
        )

        manager = get_plugin_manager_promise(info.context).get()
        is_active = manager.is_event_active_for_any_plugin(
            "payment_method_initialize_tokenization"
        )

        if not is_active:
            raise ValidationError(
                ("No active payment app to handle requested action."),
                code=PaymentMethodInitializeTokenizationErrorCode.NOT_FOUND.value,
            )

        response = manager.payment_method_initialize_tokenization(
            request_data=PaymentMethodInitializeTokenizationRequestData(
                app_identifier=id, user=user, channel=channel, data=data
            )
        )
        errors = []
        result_enum = PaymentMethodTokenizationResultEnum
        result_without_error = [
            result_enum.SUCCESSFULLY_TOKENIZED,
            result_enum.ADDITIONAL_ACTION_REQUIRED,
        ]
        if response.result not in result_without_error:
            error_code = (
                PaymentMethodInitializeTokenizationErrorCode.GATEWAY_ERROR.value
            )
            errors.append(
                {
                    "message": response.error,
                    "code": error_code,
                }
            )

        return cls(
            result=response.result, data=response.data, errors=errors, id=response.id
        )

    @classmethod
    def perform_mutation(cls, root, info, id, channel, data=None):
        try:
            return cls._perform_mutation(root, info, id, channel, data)
        except ValidationError as error:
            error_response = cls.handle_errors(error)
            error_response.result = (
                PaymentMethodTokenizationResultEnum.FAILED_TO_DELIVER.value
            )
            return error_response
