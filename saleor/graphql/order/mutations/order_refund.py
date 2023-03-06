from typing import Optional

import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....giftcard.utils import order_has_gift_card_lines
from ....order import FulfillmentStatus, models
from ....order.actions import order_refunded
from ....order.error_codes import OrderErrorCode
from ....payment import PaymentError, TransactionKind, gateway
from ....payment import models as payment_models
from ....payment.gateway import request_refund_action
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order
from .utils import clean_payment, try_payment_action


def clean_refund_payment(
    payment: Optional[payment_models.Payment],
) -> payment_models.Payment:
    payment = clean_payment(payment)
    if not payment.can_refund():
        raise ValidationError(
            {
                "payment": ValidationError(
                    "Payment cannot be refunded.",
                    code=OrderErrorCode.CANNOT_REFUND.value,
                )
            }
        )
    return payment


def clean_order_refund(order: models.Order) -> models.Order:
    if order_has_gift_card_lines(order):
        raise ValidationError(
            {
                "id": ValidationError(
                    "Cannot refund order with gift card lines.",
                    code=OrderErrorCode.CANNOT_REFUND.value,
                )
            }
        )
    return order


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
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, amount, id: str
    ):
        if amount <= 0:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        "Amount should be a positive number.",
                        code=OrderErrorCode.ZERO_QUANTITY.value,
                    )
                }
            )

        order = cls.get_node_or_error(info, id, only_type=Order)
        order = clean_order_refund(order)
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        if payment_transactions := list(order.payment_transactions.all()):
            # We use the last transaction as we don't have a possibility to
            # provide way of handling multiple transaction here
            try:
                request_refund_action(
                    payment_transactions[-1],
                    manager,
                    refund_value=amount,
                    channel_slug=order.channel.slug,
                    user=info.context.user,
                    app=app,
                )
            except PaymentError as e:
                raise ValidationError(
                    str(e),
                    code=OrderErrorCode.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.value,
                )
        else:
            payment = order.get_last_payment()
            payment = clean_payment(payment)
            payment = clean_refund_payment(payment)
            transaction = try_payment_action(
                order,
                info.context.user,
                app,
                payment,
                gateway.refund,
                payment,
                manager,
                amount=amount,
                channel_slug=order.channel.slug,
            )
            # Confirm that we changed the status to refund. Some payment can receive
            # asynchronous webhook with update status
            if transaction.kind == TransactionKind.REFUND:
                order_refunded(
                    order,
                    info.context.user,
                    app,
                    amount,
                    payment,
                    manager,
                )

        order.fulfillments.create(
            status=FulfillmentStatus.REFUNDED, total_refund_amount=amount
        )
        return OrderRefund(order=order)
