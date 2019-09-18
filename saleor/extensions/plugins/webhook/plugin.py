from typing import TYPE_CHECKING, Any

from ....webhook import WebhookEventType
from ...base_plugin import BasePlugin
from .payloads import generate_customer_payload, generate_order_payload
from .tasks import trigger_webhooks_for_event

if TYPE_CHECKING:
    from ....order.models import Order
    from ....account.models import User


class WebhookPlugin(BasePlugin):
    PLUGIN_NAME = "Webhooks"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = True

    def postprocess_order_creation(self, order: "Order", previous_value: Any) -> Any:
        self._initialize_plugin_configuration()
        if not self.active:
            return previous_value
        order.lines.prefetch_related("lines")
        order_data = generate_order_payload(order)
        trigger_webhooks_for_event.delay(WebhookEventType.ORDER_CREATED, order_data)

    def customer_created(self, customer: "User", previous_value: Any) -> Any:
        self._initialize_plugin_configuration()
        if not self.active:
            return previous_value

        customer_data = generate_customer_payload(customer)
        trigger_webhooks_for_event.delay(
            WebhookEventType.CUSTOMER_CREATED, customer_data
        )

    def order_fully_paid(self, order: "Order", previous_value: Any) -> Any:
        self._initialize_plugin_configuration()
        if not self.active:
            return previous_value
        order.lines.prefetch_related("lines")
        order_data = generate_order_payload(order)
        trigger_webhooks_for_event.delay(WebhookEventType.ORDER_FULLYPAID, order_data)

    @classmethod
    def _get_default_configuration(cls):
        defaults = {
            "name": cls.PLUGIN_NAME,
            "description": "",
            "active": True,
            "configuration": None,
        }
        return defaults
