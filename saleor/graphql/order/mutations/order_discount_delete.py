import graphene

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.search import update_order_search_vector
from ....order.utils import invalidate_order_prices, remove_order_discount_from_order
from ...app.dataloaders import load_app
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
    def perform_mutation(cls, _root, info, **data):
        order_discount = cls.get_node_or_error(
            info, data.get("discount_id"), only_type="OrderDiscount"
        )
        order = order_discount.order
        app = load_app(info.context)

        cls.validate_order(info, order)
        with traced_atomic_transaction():
            remove_order_discount_from_order(order, order_discount)
            events.order_discount_deleted_event(
                order=order,
                user=info.context.user,
                app=app,
                order_discount=order_discount,
            )

            order.refresh_from_db()

            update_order_search_vector(order, save=False)
            invalidate_order_prices(order)
            order.save(
                update_fields=["should_refresh_prices", "search_vector", "updated_at"]
            )
        return OrderDiscountDelete(order=order)
