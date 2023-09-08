import graphene
from django.core.exceptions import ValidationError

from .....payment.interface import PaymentMethodProcessTokenizationRequestData
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventSyncType
from ....channel.utils import validate_channel
from ....core.descriptions import ADDED_IN_316, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.enums import PaymentMethodProcessTokenizationErrorCode
from ....core.mutations import BaseMutation
from ....core.scalars import JSON
from ....core.types.common import PaymentMethodProcessTokenizationError
from ....core.utils import WebhookEventInfo
from ...enums import PaymentMethodTokenizationResultEnum
from .utils import handle_payment_method_action


class PaymentMethodProcessTokenization(BaseMutation):
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
                "The identifier of the payment gateway app to process payment "
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
                type=(WebhookEventSyncType.PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION),
                description="The customer continues payment method tokenization.",
            ),
        ]
        error_type_class = PaymentMethodProcessTokenizationError
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)

    @classmethod
    def _perform_mutation(cls, root, info, id, channel, data=None):
        user = info.context.user
        channel = validate_channel(channel, PaymentMethodProcessTokenizationErrorCode)

        response, errors = handle_payment_method_action(
            info,
            "payment_method_process_tokenization",
            PaymentMethodProcessTokenizationRequestData(
                id=id, user=user, channel=channel, data=data
            ),
            PaymentMethodProcessTokenizationErrorCode,
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
