import copy

import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import events, models
from ....order.calculations import fetch_order_prices_if_expired
from ....order.error_codes import OrderErrorCode
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.types import OrderError
from ...discount.types import OrderDiscount
from ...plugins.dataloaders import get_plugin_manager_promise
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
    def validate(cls, info: ResolveInfo, order: models.Order, order_discount, input):
        cls.validate_order(info, order)
        input["value"] = input.get("value") or order_discount.value
        input["value_type"] = input.get("value_type") or order_discount.value_type

        cls.validate_order_discount_input(info, order.undiscounted_total.gross, input)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, discount_id: str, input
    ):
        manager = get_plugin_manager_promise(info.context).get()
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
                app = get_app_promise(info.context).get()
                events.order_discount_updated_event(
                    order=order,
                    user=info.context.user,
                    app=app,
                    order_discount=order_discount,
                    old_order_discount=order_discount_before_update,
                )
        return OrderDiscountUpdate(order=order)
