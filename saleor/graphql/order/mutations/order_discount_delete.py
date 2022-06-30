import graphene

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.search import update_order_search_vector
from ....order.utils import remove_order_discount_from_order
from ...core.types import OrderError
from ..types import Order
from .order_discount_common import OrderDiscountCommon


class OrderDiscountDelete(OrderDiscountCommon):
    order = graphene.Field(Order, description="Order which has removed discount.")

    class Arguments:
        discount_id = graphene.ID(
            description="ID of a discount to remove.", required=True
        )

    class Meta:
        description = "Remove discount from the order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        order_discount = cls.get_node_or_error(
            info, data.get("discount_id"), only_type="OrderDiscount"
        )
        order = order_discount.order
        cls.validate_order(info, order)

        remove_order_discount_from_order(order, order_discount)
        events.order_discount_deleted_event(
            order=order,
            user=info.context.user,
            app=info.context.app,
            order_discount=order_discount,
        )

        order.refresh_from_db()

        cls.recalculate_order(order)
        update_order_search_vector(order)

        return OrderDiscountDelete(order=order)
