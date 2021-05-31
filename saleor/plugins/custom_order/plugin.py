from typing import TYPE_CHECKING, Any

from ..base_plugin import BasePlugin

if TYPE_CHECKING:
    from ...order.models import Order


class CustomOrderPlugin(BasePlugin):
    PLUGIN_NAME = "Custom Order Create"
    PLUGIN_ID = "custom_order"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = (
        "set order is_order, requested_shipment_date if needed"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = True

    def order_created(self, order: "Order", previous_value: Any):
        checkout = Order.objects.get_by_checkout_token(
            order.checkout_token
        )
        if checkout.is_preorder:
            order.is_preorder = True
            order.requested_shipment_date = checkout.requested_shipment_date
            order.save()
        return previous_value
