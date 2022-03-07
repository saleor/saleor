import graphene

from ....permission.enums import OrderPermissions
from ...core.types import OrderError
from ..types import Order
from .order_discount_common import OrderDiscountCommon


class OrderShippingDiscountDelete(OrderDiscountCommon):
    order = graphene.Field(
        Order, description="Order which has removed discount for shipping."
    )

    class Arguments:
        discount_id = graphene.ID(
            description="ID of a discount to remove.", required=True
        )

    class Meta:
        description = "Remove discounts for the shipping."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError

