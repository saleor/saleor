import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....giftcard.utils import order_has_gift_card_lines
from ....order import FulfillmentStatus
from ....order.actions import order_refunded
from ....order.error_codes import OrderErrorCode
from ....payment import PaymentError, TransactionKind, gateway
from ....payment.gateway import request_refund_action
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types import OrderError
from ..types import Order
from .utils import clean_payment, try_payment_action


def clean_refund_payment(payment):
    clean_payment(payment)
    if not payment.can_refund():
        raise ValidationError(
            {
                "payment": ValidationError(
                    "Payment cannot be refunded.",
                    code=OrderErrorCode.CANNOT_REFUND,
                )
            }
        )


def clean_order_refund(order):
    if order_has_gift_card_lines(order):
        raise ValidationError(
            {
                "id": ValidationError(
                    "Cannot refund order with gift card lines.",
                    code=OrderErrorCode.CANNOT_REFUND.value,
                )
            }
        )


class OrderRefund(BaseMutation):
    order = graphene.Field(Order, description="A refunded order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to refund.")
        amount = PositiveDecimal(
            required=True, description="Amount of money to refund."
        )

    class Meta:
        description = "Refund an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, amount, **data):
        if amount <= 0:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        "Amount should be a positive number.",
                        code=OrderErrorCode.ZERO_QUANTITY,
                    )
                }
            )

        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        clean_order_refund(order)

        if payment_transactions := list(order.payment_transactions.all()):
            # We use the last transaction as we don't have a possibility to
            # provide way of handling multiple transaction here
            try:
                request_refund_action(
                    payment_transactions[-1],
                    info.context.plugins,
                    refund_value=amount,
                    channel_slug=order.channel.slug,
                    user=info.context.user,
                    app=info.context.app,
                )
            except PaymentError as e:
                raise ValidationError(
                    str(e),
                    code=OrderErrorCode.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK,
                )
        else:
            payment = order.get_last_payment()
            clean_payment(payment)
            clean_refund_payment(payment)
            transaction = try_payment_action(
                order,
                info.context.user,
                info.context.app,
                payment,
                gateway.refund,
                payment,
                info.context.plugins,
                amount=amount,
                channel_slug=order.channel.slug,
            )
            # Confirm that we changed the status to refund. Some payment can receive
            # asynchronous webhook with update status
            if transaction.kind == TransactionKind.REFUND:
                order_refunded(
                    order,
                    info.context.user,
                    info.context.app,
                    amount,
                    payment,
                    info.context.plugins,
                )

        order.fulfillments.create(
            status=FulfillmentStatus.REFUNDED, total_refund_amount=amount
        )
        return OrderRefund(order=order)
