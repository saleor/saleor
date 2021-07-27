from ..base_plugin import BasePlugin


class BackordersPlugin(BasePlugin):
    PLUGIN_ID = "firstech.backorders"
    PLUGIN_NAME = "Backorders"
    DEFAULT_ACTIVE = False
    CONFIGURATION_PER_CHANNEL = True

    def is_backorder_allowed(self, previous_value):
        return self.active
