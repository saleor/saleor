import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....giftcard.utils import deactivate_order_gift_cards
from ....order.actions import cancel_order
from ....order.error_codes import OrderErrorCode
from ...app.dataloaders import load_app
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ..types import Order


def clean_order_cancel(order):
    if order and not order.can_cancel():
        raise ValidationError(
            {
                "order": ValidationError(
                    "This order can't be canceled.",
                    code=OrderErrorCode.CANNOT_CANCEL_ORDER,
                )
            }
        )


class OrderCancel(BaseMutation):
    order = graphene.Field(Order, description="Canceled order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to cancel.")

    class Meta:
        description = "Cancel an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        clean_order_cancel(order)
        user = info.context.user
        app = load_app(info.context)
        cancel_order(
            order=order,
            user=user,
            app=app,
            manager=info.context.plugins,
        )
        deactivate_order_gift_cards(order.id, user, app)
        return OrderCancel(order=order)
