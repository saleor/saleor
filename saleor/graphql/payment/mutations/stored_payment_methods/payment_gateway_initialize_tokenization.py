import graphene
from django.core.exceptions import ValidationError

from .....payment.interface import PaymentGatewayInitializeTokenizationRequestData
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventSyncType
from ....channel.utils import validate_channel
from ....core.descriptions import ADDED_IN_316, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.enums import PaymentGatewayInitializeTokenizationErrorCode
from ....core.mutations import BaseMutation
from ....core.scalars import JSON
from ....core.types.common import PaymentGatewayInitializeTokenizationError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import PaymentGatewayInitializeTokenizationResultEnum


class PaymentGatewayInitializeTokenization(BaseMutation):
    result = PaymentGatewayInitializeTokenizationResultEnum(
        description="A status of the payment gateway initialization.", required=True
    )
    data = JSON(
        description="A data returned by payment app.",
    )

    class Arguments:
        id = graphene.String(
            required=True,
            description=(
                "The identifier of the payment gateway app to initialize tokenization."
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
        description = (
            "Initializes payment gateway for tokenizing payment method session."
            + ADDED_IN_316
            + PREVIEW_FEATURE
        )
        webhook_events_info = [
            WebhookEventInfo(
                type=(
                    WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION_SESSION
                ),
                description=(
                    "The customer requested to initialize payment gateway for "
                    "tokenization."
                ),
            ),
        ]
        error_type_class = PaymentGatewayInitializeTokenizationError
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)

    @classmethod
    def _perform_mutation(cls, root, info, id, channel, data=None):
        user = info.context.user
        channel = validate_channel(
            channel, PaymentGatewayInitializeTokenizationErrorCode
        )

        manager = get_plugin_manager_promise(info.context).get()
        is_active = manager.is_event_active_for_any_plugin(
            "payment_gateway_initialize_tokenization", channel_slug=channel.slug
        )

        if not is_active:
            raise ValidationError(
                (
                    "No active payment app that could initialize payment gateway for "
                    "tokenization."
                ),
                code=PaymentGatewayInitializeTokenizationErrorCode.NOT_FOUND.value,
            )

        response = manager.payment_gateway_initialize_tokenization(
            request_data=PaymentGatewayInitializeTokenizationRequestData(
                app_identifier=id, user=user, channel=channel, data=data
            )
        )
        errors = []
        result_enum = PaymentGatewayInitializeTokenizationResultEnum
        if response.result != result_enum.SUCCESSFULLY_INITIALIZED.value:
            error_code = (
                PaymentGatewayInitializeTokenizationErrorCode.GATEWAY_ERROR.value
            )
            errors.append(
                {
                    "message": response.error,
                    "code": error_code,
                }
            )

        return cls(result=response.result, data=response.data, errors=errors)

    @classmethod
    def perform_mutation(cls, root, info, id, channel, data=None):
        try:
            return cls._perform_mutation(root, info, id, channel, data)
        except ValidationError as error:
            error_response = cls.handle_errors(error)
            error_response.result = (
                PaymentGatewayInitializeTokenizationResultEnum.FAILED_TO_DELIVER.value
            )
            return error_response
