from typing import Optional

import graphene
from django.core.exceptions import ValidationError

from ....order.actions import order_voided
from ....order.error_codes import OrderErrorCode
from ....payment import PaymentError, TransactionKind, gateway
from ....payment import models as payment_models
from ....payment.gateway import request_void_action
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order
from .utils import clean_payment, try_payment_action


def clean_void_payment(
    payment: Optional[payment_models.Payment],
) -> payment_models.Payment:
    """Check for payment errors."""
    payment = clean_payment(payment)
    if not payment.is_active:
        raise ValidationError(
            {
                "payment": ValidationError(
                    "Only pre-authorized payments can be voided",
                    code=OrderErrorCode.VOID_INACTIVE_PAYMENT.value,
                )
            }
        )
    return payment


class OrderVoid(BaseMutation):
    order = graphene.Field(Order, description="A voided order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to void.")

    class Meta:
        description = "Void an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        order = cls.get_node_or_error(info, id, only_type=Order)
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        if payment_transactions := list(order.payment_transactions.all()):
            # We use the last transaction as we don't have a possibility to
            # provide way of handling multiple transaction here
            try:
                request_void_action(
                    payment_transactions[-1],
                    manager,
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
            payment = clean_void_payment(payment)
            transaction = try_payment_action(
                order,
                info.context.user,
                app,
                payment,
                gateway.void,
                payment,
                manager,
                channel_slug=order.channel.slug,
            )
            # Confirm that we changed the status to void. Some payment can receive
            # asynchronous webhook with update status
            if transaction.kind == TransactionKind.VOID:
                order_voided(
                    order,
                    info.context.user,
                    app,
                    payment,
                    manager,
                )
        return OrderVoid(order=order)
