from typing import Optional

import graphene
from django.core.exceptions import ValidationError

from ....order.actions import order_captured
from ....order.error_codes import OrderErrorCode
from ....order.fetch import fetch_order_info
from ....payment import PaymentError, TransactionKind, gateway
from ....payment import models as payment_models
from ....payment.gateway import request_charge_action
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...site.dataloaders import get_site_promise
from ..types import Order
from .utils import clean_payment, try_payment_action


def clean_order_capture(
    payment: Optional[payment_models.Payment],
) -> payment_models.Payment:
    payment = clean_payment(payment)
    if not payment.is_active:
        raise ValidationError(
            {
                "payment": ValidationError(
                    "Only pre-authorized payments can be captured",
                    code=OrderErrorCode.CAPTURE_INACTIVE_PAYMENT.value,
                )
            }
        )
    return payment


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

        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        if payment_transactions := list(order.payment_transactions.all()):
            try:
                # We use the last transaction as we don't have a possibility to
                # provide way of handling multiple transaction here
                payment_transaction = payment_transactions[-1]
                request_charge_action(
                    transaction=payment_transaction,
                    manager=manager,
                    charge_value=amount,
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
            order_info = fetch_order_info(order)
            payment = order_info.payment
            payment = clean_order_capture(payment)
            transaction = try_payment_action(
                order,
                info.context.user,
                app,
                payment,
                gateway.capture,
                payment,
                manager,
                amount=amount,
                channel_slug=order.channel.slug,
            )
            payment.refresh_from_db()
            # Confirm that we changed the status to capture. Some payment can receive
            # asynchronous webhook with update status
            if transaction.kind == TransactionKind.CAPTURE:
                site = get_site_promise(info.context).get()
                order_captured(
                    order_info,
                    info.context.user,
                    app,
                    amount,
                    payment,
                    manager,
                    site.settings,
                )
        return OrderCapture(order=order)
