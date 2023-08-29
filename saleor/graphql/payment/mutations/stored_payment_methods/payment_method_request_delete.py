import graphene
from django.core.exceptions import ValidationError

from .....payment.interface import StoredPaymentMethodRequestDeleteData
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventSyncType
from ....channel.utils import validate_channel
from ....core.descriptions import ADDED_IN_316, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.enums import StoredPaymentMethodRequestDeleteErrorCode
from ....core.mutations import BaseMutation
from ....core.types.common import PaymentMethodRequestDeleteError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise


class StoredPaymentMethodRequestDelete(BaseMutation):
    success = graphene.Boolean(
        description="True, if the delete request was processed successfully.",
    )
    message = graphene.String(
        description="A message returned by payment app.",
    )

    class Arguments:
        id = graphene.ID(
            description="The ID of the payment method.",
            required=True,
        )
        channel = graphene.String(
            description="Slug of a channel related to delete request.", required=True
        )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        description = (
            "Request to delete a stored payment method on payment provider side."
            + ADDED_IN_316
            + PREVIEW_FEATURE
        )

        error_type_class = PaymentMethodRequestDeleteError
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventSyncType.STORED_PAYMENT_METHOD_DELETE_REQUESTED,
                description="The customer requested to delete a payment method.",
            ),
        ]

    @classmethod
    def perform_mutation(cls, root, info, id, channel):
        user = info.context.user
        if not user:
            raise ValidationError(
                "You need to be authenticated user to delete a payment method.",
                code=StoredPaymentMethodRequestDeleteErrorCode.INVALID.value,
            )
        channel = validate_channel(channel, StoredPaymentMethodRequestDeleteErrorCode)

        manager = get_plugin_manager_promise(info.context).get()
        is_active = manager.is_event_active_for_any_plugin(
            "stored_payment_method_request_delete"
        )
        if not is_active:
            raise ValidationError(
                "No active payment app that could process the delete request.",
                code=StoredPaymentMethodRequestDeleteErrorCode.NOT_FOUND.value,
            )

        response = manager.stored_payment_method_request_delete(
            request_delete_data=StoredPaymentMethodRequestDeleteData(
                payment_method_id=id,
                user=user,
                channel=channel,
            )
        )
        return cls(success=response.success, message=response.message)
