from typing import TYPE_CHECKING, Any

from ...webhook.event_types import WebhookEventType
from ...webhook.payloads import (
    generate_checkout_payload,
    generate_customer_payload,
    generate_fulfillment_payload,
    generate_order_payload,
    generate_product_payload,
)
from ..base_plugin import BasePlugin
from .tasks import trigger_webhooks_for_event

if TYPE_CHECKING:
    from ...order.models import Fulfillment, Order
    from ...account.models import User
    from ...product.models import Product
    from ...checkout.models import Checkout


class WebhookPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.webhooks"
    PLUGIN_NAME = "Webhooks"
    DEFAULT_ACTIVE = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = True

    def order_created(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_for_event.delay(WebhookEventType.ORDER_CREATED, order_data)

    def order_fully_paid(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_for_event.delay(WebhookEventType.ORDER_FULLY_PAID, order_data)

    def order_updated(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_for_event.delay(WebhookEventType.ORDER_UPDATED, order_data)

    def order_cancelled(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_for_event.delay(WebhookEventType.ORDER_CANCELLED, order_data)

    def order_fulfilled(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_for_event.delay(WebhookEventType.ORDER_FULFILLED, order_data)

    def fulfillment_created(self, fulfillment: "Fulfillment", previous_value):
        if not self.active:
            return previous_value

        fulfillment_data = generate_fulfillment_payload(fulfillment)
        trigger_webhooks_for_event.delay(
            WebhookEventType.FULFILLMENT_CREATED, fulfillment_data
        )

    def customer_created(self, customer: "User", previous_value: Any) -> Any:
        if not self.active:
            return previous_value

        customer_data = generate_customer_payload(customer)
        trigger_webhooks_for_event.delay(
            WebhookEventType.CUSTOMER_CREATED, customer_data
        )

    def product_created(self, product: "Product", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        product_data = generate_product_payload(product)
        trigger_webhooks_for_event.delay(WebhookEventType.PRODUCT_CREATED, product_data)

    def checkout_quantity_changed(
        self, checkout: "Checkout", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        checkout_data = generate_checkout_payload(checkout)
        trigger_webhooks_for_event.delay(
            WebhookEventType.CHECKOUT_QUANTITY_CHANGED, checkout_data
        )
