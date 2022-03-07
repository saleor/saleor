import graphene

from ....permission.enums import OrderPermissions
from ...core.types import OrderError
from ..types import Order
from .order_discount_common import OrderDiscountCommon, DiscountCommonInput


class OrderShippingDiscountUpdate(OrderDiscountCommon):
    order = graphene.Field(Order, description="Order which has discounted shipping.")

    class Arguments:
        discount_id = graphene.ID(
            description="ID of a discount to update.", required=True
        )
        input = DiscountCommonInput(
            required=True,
            description="Fields required to update price for the shipping.",
        )

    class Meta:
        description = "Updates discounts for the shipping."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
