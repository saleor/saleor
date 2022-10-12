import copy

import graphene

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.calculations import fetch_order_prices_if_expired
from ...app.dataloaders import load_app
from ...core.types import OrderError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Order
from .order_discount_common import OrderDiscountCommon, OrderDiscountCommonInput


class OrderDiscountUpdate(OrderDiscountCommon):
    order = graphene.Field(Order, description="Order which has been discounted.")

    class Arguments:
        discount_id = graphene.ID(
            description="ID of a discount to update.", required=True
        )
        input = OrderDiscountCommonInput(
            required=True,
            description="Fields required to update a discount for the order.",
        )

    class Meta:
        description = "Update discount for the order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def validate(cls, info, order, order_discount, input):
        cls.validate_order(info, order)
        input["value"] = input.get("value") or order_discount.value
        input["value_type"] = input.get("value_type") or order_discount.value_type

        cls.validate_order_discount_input(info, order.undiscounted_total.gross, input)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        manager = load_plugin_manager(info.context)
        order_discount = cls.get_node_or_error(
            info, data.get("discount_id"), only_type="OrderDiscount"
        )
        order = order_discount.order
        input = data.get("input")
        cls.validate(info, order, order_discount, input)

        reason = input.get("reason", order_discount.reason)
        value_type = input.get("value_type", order_discount.value_type)
        value = input.get("value", order_discount.value)

        order_discount_before_update = copy.deepcopy(order_discount)
        with traced_atomic_transaction():
            order_discount.reason = reason
            order_discount.value = value
            order_discount.value_type = value_type
            order_discount.save()
            if (
                order_discount_before_update.value_type != value_type
                or order_discount_before_update.value != value
            ):
                # call update event only when we changed the type or value of the
                # discount.
                # Calling refreshing prices because it's set proper discount amount
                # on OrderDiscount.
                fetch_order_prices_if_expired(order, manager, force_update=True)
                order_discount.refresh_from_db()
                app = load_app(info.context)
                events.order_discount_updated_event(
                    order=order,
                    user=info.context.user,
                    app=app,
                    order_discount=order_discount,
                    old_order_discount=order_discount_before_update,
                )
        return OrderDiscountUpdate(order=order)
