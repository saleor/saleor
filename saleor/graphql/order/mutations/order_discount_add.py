import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.calculations import fetch_order_prices_if_expired
from ....order.error_codes import OrderErrorCode
from ....order.utils import create_order_discount_for_order, get_order_discounts
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order
from .order_discount_common import OrderDiscountCommon, OrderDiscountCommonInput


class OrderDiscountAdd(OrderDiscountCommon):
    order = graphene.Field(Order, description="Order which has been discounted.")

    class Arguments:
        order_id = graphene.ID(description="ID of an order to discount.", required=True)
        input = OrderDiscountCommonInput(
            required=True,
            description="Fields required to create a discount for the order.",
        )

    class Meta:
        description = "Adds discount to the order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def validate_order(cls, info: ResolveInfo, order):
        order = super().validate_order(info, order)
        # This condition can be removed when we introduce support for multi discounts.
        order_discounts = get_order_discounts(order)
        if len(order_discounts) >= 1:
            error_msg = "Order already has assigned discount."
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        error_msg, code=OrderErrorCode.CANNOT_DISCOUNT.value
                    )
                }
            )
        return order

    @classmethod
    def validate(cls, info: ResolveInfo, order, input):
        cls.validate_order(info, order)
        cls.validate_order_discount_input(info, order.undiscounted_total.gross, input)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, order_id: str
    ):
        manager = get_plugin_manager_promise(info.context).get()
        order = cls.get_node_or_error(info, order_id, only_type=Order)
        cls.validate(info, order, input)

        reason = input.get("reason")
        value_type = input.get("value_type")
        value = input.get("value")
        app = get_app_promise(info.context).get()
        with traced_atomic_transaction():
            order_discount = create_order_discount_for_order(
                order, reason, value_type, value
            )
            # Calling refreshing prices because it's set proper discount amount
            # on OrderDiscount.
            order, _ = fetch_order_prices_if_expired(order, manager, force_update=True)
            order_discount.refresh_from_db()

            events.order_discount_added_event(
                order=order,
                user=info.context.user,
                app=app,
                order_discount=order_discount,
            )
        return OrderDiscountAdd(order=order)
