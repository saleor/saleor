import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....order.actions import order_captured
from ....order.error_codes import OrderErrorCode
from ....order.fetch import fetch_order_info
from ....payment import PaymentError, TransactionKind, gateway
from ....payment.gateway import request_charge_action
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types import OrderError
from ..types import Order
from .utils import clean_payment, try_payment_action


def clean_order_capture(payment):
    clean_payment(payment)
    if not payment.is_active:
        raise ValidationError(
            {
                "payment": ValidationError(
                    "Only pre-authorized payments can be captured",
                    code=OrderErrorCode.CAPTURE_INACTIVE_PAYMENT,
                )
            }
        )


class OrderCapture(BaseMutation):
    order = graphene.Field(Order, description="Captured order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to capture.")
        amount = PositiveDecimal(
            required=True, description="Amount of money to capture."
        )

    class Meta:
        description = "Capture an order."
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

        if payment_transactions := list(order.payment_transactions.all()):
            try:
                # We use the last transaction as we don't have a possibility to
                # provide way of handling multiple transaction here
                payment_transaction = payment_transactions[-1]
                request_charge_action(
                    transaction=payment_transaction,
                    manager=info.context.plugins,
                    charge_value=amount,
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
            order_info = fetch_order_info(order)
            payment = order_info.payment
            clean_order_capture(payment)
            transaction = try_payment_action(
                order,
                info.context.user,
                info.context.app,
                payment,
                gateway.capture,
                payment,
                info.context.plugins,
                amount=amount,
                channel_slug=order.channel.slug,
            )
            order_info.payment.refresh_from_db()
            # Confirm that we changed the status to capture. Some payment can receive
            # asynchronous webhook with update status
            if transaction.kind == TransactionKind.CAPTURE:
                order_captured(
                    order_info,
                    info.context.user,
                    info.context.app,
                    amount,
                    payment,
                    info.context.plugins,
                    info.context.site.settings,
                )
        return OrderCapture(order=order)
