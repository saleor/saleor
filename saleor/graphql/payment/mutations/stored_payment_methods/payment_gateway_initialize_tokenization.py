import graphene
from django.core.exceptions import ValidationError

from .....payment.interface import PaymentGatewayInitializeTokenizationRequestData
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventSyncType
from ....channel.utils import validate_channel
from ....core.descriptions import ADDED_IN_316, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.enums import (
    PaymentGatewayInitializeTokenizationErrorCode,
    StoredPaymentMethodRequestDeleteErrorCode,
)
from ....core.mutations import BaseMutation
from ....core.scalars import JSON
from ....core.types.common import PaymentGatewayInitializeTokenizationError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise


class PaymentGatewayInitializeTokenization(BaseMutation):
    success = graphene.Boolean(
        description="True, if the request was processed successfully.",
    )
    message = graphene.String(
        description="A message returned by payment app.",
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
            description="Slug of a channel related to delete request.", required=True
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
    def perform_mutation(cls, root, info, id, channel, data=None):
        user = info.context.user
        if not user:
            raise ValidationError(
                "You need to be authenticated user to initialize payment gateway for "
                "tokenization.",
                code=StoredPaymentMethodRequestDeleteErrorCode.INVALID.value,
            )
        channel = validate_channel(
            channel, PaymentGatewayInitializeTokenizationErrorCode
        )

        manager = get_plugin_manager_promise(info.context).get()
        is_active = manager.is_event_active_for_any_plugin(
            "payment_gateway_initialize_tokenization"
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
        return cls(
            success=response.success, message=response.message, data=response.data
        )
