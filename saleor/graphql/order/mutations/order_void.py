import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....order.actions import order_voided
from ....order.error_codes import OrderErrorCode
from ....payment import TransactionKind, gateway
from ...app.dataloaders import load_app
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Order
from .utils import clean_payment, try_payment_action


def clean_void_payment(payment):
    """Check for payment errors."""
    clean_payment(payment)
    if not payment.is_active:
        raise ValidationError(
            {
                "payment": ValidationError(
                    "Only pre-authorized payments can be voided",
                    code=OrderErrorCode.VOID_INACTIVE_PAYMENT,
                )
            }
        )


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
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        app = load_app(info.context)
        manager = load_plugin_manager(info.context)
        payment = order.get_last_payment()
        clean_void_payment(payment)
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
