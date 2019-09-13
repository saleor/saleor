from typing import TYPE_CHECKING, Any

from django.core import serializers

from ....webhook import WebhookEventType
from ...base_plugin import BasePlugin
from .tasks import trigger_webhooks_for_event

if TYPE_CHECKING:
    from ....order.models import Order


class WebhookPlugin(BasePlugin):
    PLUGIN_NAME = "Webhooks"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = True

    def postprocess_order_creation(self, order: "Order", previous_value: Any) -> Any:
        self._initialize_plugin_configuration()

        if not self.active:
            return previous_value
        data = serializers.serialize("json", [order])
        trigger_webhooks_for_event.delay(WebhookEventType.ORDER_CREATED, data)

    @classmethod
    def _get_default_configuration(cls):
        defaults = {
            "name": cls.PLUGIN_NAME,
            "description": "",
            "active": True,
            "configuration": None,
        }
        return defaults
