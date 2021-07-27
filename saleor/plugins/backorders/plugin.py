from typing import Any
from ..base_plugin import BasePlugin
from ...warehouse.models import Backorder


class BackordersPlugin(BasePlugin):
    PLUGIN_ID = "firstech.backorders"
    PLUGIN_NAME = "Backorders"
    DEFAULT_ACTIVE = False
    CONFIGURATION_PER_CHANNEL = True

    def is_backorder_allowed(self, previous_value):
        return self.active

    def order_cancelled(self, order: "Order", previous_value: Any) -> Any:
        """Trigger when order is cancelled.
        """
        Backorder.objects.filter(
            order_line__order=order, quantity__gt=0
        ).delete()
