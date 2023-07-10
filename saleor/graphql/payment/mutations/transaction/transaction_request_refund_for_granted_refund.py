from typing import TYPE_CHECKING, cast

import graphene
from django.core.exceptions import ValidationError

from .....order import models as order_models
from .....payment import PaymentError, TransactionEventType
from .....payment import models as payment_models
from .....payment.error_codes import TransactionRequestActionErrorCode
from .....payment.gateway import request_refund_action
from .....permission.enums import PaymentPermissions
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.enums import TransactionRequestRefundForGrantedRefundErrorCode
from ....core.mutations import BaseMutation
from ....core.types import common as common_types
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import TransactionItem
from .utils import get_transaction_item

if TYPE_CHECKING:
    pass


class TransactionRequestRefundForGrantedRefund(BaseMutation):
    transaction = graphene.Field(TransactionItem)

    class Arguments:
        id = graphene.ID(
            description="The ID of the transaction.",
            required=True,
        )
        granted_refund_id = graphene.ID(
            required=True,
            description="The ID of the granted refund.",
        )

    class Meta:
        description = (
            "Request a refund for payment transaction based on granted refund."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.TransactionRequestRefundForGrantedRefundError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)

    @classmethod
    def clean_input(
        cls, info, transaction_id: str, granted_refund_id: str
    ) -> tuple[payment_models.TransactionItem, order_models.OrderGrantedRefund]:
        transaction_item = get_transaction_item(transaction_id)
        granted_refund = cls.get_node_or_error(
            info,
            granted_refund_id,
            field="granted_refund_id",
            only_type="OrderGrantedRefund",
            qs=order_models.OrderGrantedRefund.objects.select_related(
                "order__channel"
            ).all(),
        )
        granted_refund = cast(order_models.OrderGrantedRefund, granted_refund)
        if transaction_item.order_id != granted_refund.order_id:
            error_code = TransactionRequestRefundForGrantedRefundErrorCode.INVALID.value
            raise ValidationError(
                {
                    "granted_refund_id": ValidationError(
                        "The granted refund belongs to different order than "
                        "transaction.",
                        code=error_code,
                    ),
                    "id": ValidationError(
                        "The transaction belongs to different order than "
                        "granted refund.",
                        code=error_code,
                    ),
                }
            )
        return transaction_item, granted_refund

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, id, granted_refund_id
    ):
        transaction_item, granted_refund = cls.clean_input(info, id, granted_refund_id)
        order = granted_refund.order

        channel = order.channel
        cls.check_channel_permissions(info, [channel.id])
        channel_slug = channel.slug

        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        action_value = granted_refund.amount_value or transaction_item.charged_value
        action_value = min(action_value, transaction_item.charged_value)
        request_event = transaction_item.events.create(
            amount_value=action_value,
            currency=transaction_item.currency,
            type=TransactionEventType.REFUND_REQUEST,
        )

        try:
            request_refund_action(
                transaction=transaction_item,
                manager=manager,
                refund_value=action_value,
                request_event=request_event,
                channel_slug=channel_slug,
                user=info.context.user,
                app=app,
                granted_refund=granted_refund,
            )
        except PaymentError as e:
            error_enum = TransactionRequestActionErrorCode
            code = error_enum.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.value
            raise ValidationError(str(e), code=code)
        return cls(transaction=transaction_item)
