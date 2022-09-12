import graphene

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.utils import invalidate_order_prices, remove_discount_from_order_line
from ...app.dataloaders import load_app
from ...core.types import OrderError
from ...site.dataloaders import load_site
from ..types import Order, OrderLine
from .order_discount_common import OrderDiscountCommon


class OrderLineDiscountRemove(OrderDiscountCommon):
    order_line = graphene.Field(
        OrderLine, description="Order line which has removed discount."
    )
    order = graphene.Field(
        Order, description="Order which is related to line which has removed discount."
    )

    class Arguments:
        order_line_id = graphene.ID(
            description="ID of a order line to remove its discount", required=True
        )

    class Meta:
        description = "Remove discount applied to the order line."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def validate(cls, info, order):
        cls.validate_order(info, order)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        site = load_site(info.context)
        tax_included = site.settings.include_taxes_in_prices
        order_line = cls.get_node_or_error(
            info, data.get("order_line_id"), only_type=OrderLine
        )
        order = order_line.order
        cls.validate(info, order)

        remove_discount_from_order_line(
            order_line, order, manager=info.context.plugins, tax_included=tax_included
        )
        app = load_app(info.context)
        events.order_line_discount_removed_event(
            order=order,
            user=info.context.user,
            app=app,
            line=order_line,
        )

        invalidate_order_prices(order, save=True)
        return OrderLineDiscountRemove(order_line=order_line, order=order)
