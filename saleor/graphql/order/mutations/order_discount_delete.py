import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.error_codes import OrderErrorCode
from ....order.search import update_order_search_vector
from ....order.utils import invalidate_order_prices, remove_order_discount_from_order
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.types import OrderError
from ...discount.types import OrderDiscount
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
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, discount_id: str
    ):
        order_discount = cls.get_node_or_error(
            info, discount_id, only_type=OrderDiscount
        )
        order = order_discount.order
        if not order:
            # FIXME: the order field in OrderDiscount is nullable
            raise ValidationError(
                {
                    "discountId": ValidationError(
                        "Discount doesn't belong to any order.",
                        code=OrderErrorCode.NOT_FOUND.value,
                    )
                }
            )
        app = get_app_promise(info.context).get()

        order = cls.validate_order(info, order)
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
