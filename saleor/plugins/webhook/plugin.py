from typing import TYPE_CHECKING, Any, Optional

from ...webhook.event_types import WebhookEventType
from ...webhook.payloads import (
    generate_checkout_payload,
    generate_customer_payload,
    generate_fulfillment_payload,
    generate_invoice_payload,
    generate_order_payload,
    generate_product_payload,
)
from ..base_plugin import BasePlugin
from .tasks import trigger_webhooks_for_event

if TYPE_CHECKING:
    from ...account.models import User
    from ...checkout.models import Checkout
    from ...invoice.models import Invoice
    from ...order.models import Fulfillment, Order
    from ...product.models import Product


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

    def order_confirmed(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_for_event.delay(WebhookEventType.ORDER_CONFIRMED, order_data)

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

    def invoice_request(
        self,
        order: "Order",
        invoice: "Invoice",
        number: Optional[str],
        previous_value: Any,
    ) -> Any:
        if not self.active:
            return previous_value
        invoice_data = generate_invoice_payload(invoice)
        trigger_webhooks_for_event.delay(
            WebhookEventType.INVOICE_REQUESTED, invoice_data
        )

    def invoice_delete(self, invoice: "Invoice", previous_value: Any):
        if not self.active:
            return previous_value
        invoice_data = generate_invoice_payload(invoice)
        trigger_webhooks_for_event.delay(WebhookEventType.INVOICE_DELETED, invoice_data)

    def invoice_sent(self, invoice: "Invoice", email: str, previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        invoice_data = generate_invoice_payload(invoice)
        trigger_webhooks_for_event.delay(WebhookEventType.INVOICE_SENT, invoice_data)

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

    def product_updated(self, product: "Product", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        product_data = generate_product_payload(product)
        trigger_webhooks_for_event.delay(WebhookEventType.PRODUCT_UPDATED, product_data)

    # Deprecated. This method will be removed in Saleor 3.0
    def checkout_quantity_changed(
        self, checkout: "Checkout", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        checkout_data = generate_checkout_payload(checkout)
        trigger_webhooks_for_event.delay(
            WebhookEventType.CHECKOUT_QUANTITY_CHANGED, checkout_data
        )

    def checkout_created(self, checkout: "Checkout", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        checkout_data = generate_checkout_payload(checkout)
        trigger_webhooks_for_event.delay(
            WebhookEventType.CHECKOUT_CREATED, checkout_data
        )

    def checkout_updated(self, checkout: "Checkout", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        checkout_data = generate_checkout_payload(checkout)
        trigger_webhooks_for_event.delay(
            WebhookEventType.CHECKOUT_UPADTED, checkout_data
        )
