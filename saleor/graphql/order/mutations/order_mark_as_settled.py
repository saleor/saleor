import graphene

from ....core.permissions import OrderPermissions
from ....order.actions import mark_order_as_settled
from ...core.descriptions import ADDED_IN_34, PREVIEW_FEATURE
from ...core.mutations import BaseMutation
from ...core.types.common import OrderMarkAsSettledError
from ..types import Order


class OrderMarkAsSettled(BaseMutation):
    order = graphene.Field(Order, description="Order marked as settled.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to mark settled.")

    class Meta:
        description = "Mark order as settled." + ADDED_IN_34 + PREVIEW_FEATURE
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderMarkAsSettledError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data.get("id"), only_type=Order)
        mark_order_as_settled(
            order, info.context.user, info.context.app, info.context.plugins
        )
        return cls(order=order)
