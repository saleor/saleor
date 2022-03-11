import graphene

from ....checkout.complete_checkout import create_order_from_checkout
from ....core import analytics
from ....core.permissions import CheckoutPermissions
from ...core.mutations import BaseMutation
from ...core.types.common import OrderFromCheckoutCreateError
from ...order.types import Order
from ..types import Checkout


class OrderFromCheckoutCreate(BaseMutation):
    order = graphene.Field(Order, description="Placed order.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of a checkout that will be converted to an order.",
        )
        clear_checkout = graphene.Boolean(
            description=(
                "Determines if checkout should be removed after creating an order."
                "Default true."
            ),
            default_value=True,
        )

    class Meta:
        description = "Create new order from existing checkout."
        object_type = Order

        # FIXME this should be a separate permission probably
        permissions = (CheckoutPermissions.MANAGE_CHECKOUTS,)
        error_type_class = OrderFromCheckoutCreateError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        checkout_id = data.get("id")
        checkout = cls.get_node_or_error(
            info, checkout_id, field="token", only_type=Checkout
        )
        tracking_code = analytics.get_client_id(info.context)
        # FIXME Do we want to limit this mutation only to App's token?
        return OrderFromCheckoutCreate(
            order=create_order_from_checkout(
                checkout=checkout,
                discounts=info.context.discounts,
                manager=info.context.plugins,
                user=info.context.user,
                app=info.context.app,
                tracking_code=tracking_code,
                delete_checkout=data["clear_checkout"],
            )
        )
