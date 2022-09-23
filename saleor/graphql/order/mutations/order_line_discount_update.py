import copy

import graphene

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.utils import invalidate_order_prices, update_discount_for_order_line
from ...app.dataloaders import load_app
from ...core.types import OrderError
from ...plugins.dataloaders import load_plugin_manager
from ...site.dataloaders import load_site
from ..types import Order, OrderLine
from .order_discount_common import OrderDiscountCommon, OrderDiscountCommonInput


class OrderLineDiscountUpdate(OrderDiscountCommon):
    order_line = graphene.Field(
        OrderLine, description="Order line which has been discounted."
    )
    order = graphene.Field(
        Order, description="Order which is related to the discounted line."
    )

    class Arguments:
        order_line_id = graphene.ID(
            description="ID of a order line to update price", required=True
        )
        input = OrderDiscountCommonInput(
            required=True,
            description="Fields required to update price for the order line.",
        )

    class Meta:
        description = "Update discount for the order line."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def validate(cls, info, order, order_line, input):
        cls.validate_order(info, order)
        input["value"] = input.get("value") or order_line.unit_discount_value
        input["value_type"] = input.get("value_type") or order_line.unit_discount_type

        cls.validate_order_discount_input(
            info, order_line.undiscounted_unit_price.gross, input
        )

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):

        order_line = cls.get_node_or_error(
            info, data.get("order_line_id"), only_type=OrderLine
        )
        input = data.get("input")
        order = order_line.order
        cls.validate(info, order, order_line, input)
        reason = input.get("reason")
        value_type = input.get("value_type")
        value = input.get("value")
        manager = load_plugin_manager(info.context)
        site = load_site(info.context)
        order_line_before_update = copy.deepcopy(order_line)
        tax_included = site.settings.include_taxes_in_prices

        update_discount_for_order_line(
            order_line,
            order=order,
            reason=reason,
            value_type=value_type,
            value=value,
            manager=manager,
            tax_included=tax_included,
        )
        if (
            order_line_before_update.unit_discount_value != value
            or order_line_before_update.unit_discount_type != value_type
        ):
            # Create event only when we change type or value of the discount
            app = load_app(info.context)
            events.order_line_discount_updated_event(
                order=order,
                user=info.context.user,
                app=app,
                line=order_line,
                line_before_update=order_line_before_update,
            )
            invalidate_order_prices(order, save=True)
        return OrderLineDiscountUpdate(order_line=order_line, order=order)
