import graphene

from ....permission.enums import OrderPermissions
from ...core.types import OrderError
from ..types import Order, OrderLine
from .order_discount_common import OrderDiscountCommon, DiscountCommonInput


class OrderLineDiscountAdd(OrderDiscountCommon):
    order_line = graphene.Field(
        OrderLine, description="Order line which has added discount."
    )
    order = graphene.Field(
        Order, description="Order which is related to line which has added discount."
    )

    class Arguments:
        order_line_id = graphene.ID(
            description="ID of a order line to update price", required=True
        )
        input = DiscountCommonInput(
            required=True,
            description="Fields required to update price for the order line.",
        )

    class Meta:
        description = "Add discounts for the order line."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
