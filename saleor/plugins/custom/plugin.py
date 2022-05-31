import logging
from typing import Any, Optional
from ..base_plugin import BasePlugin


class CustomPlugin(BasePlugin):
    PLUGIN_ID = "custom.write"
    PLUGIN_NAME = "CustomWrite"

    def write_to_db(
            self,
            custom: "Custom",
            previous_value: Any,
    ) -> Any:
        # logging.getLogger().info(custom.name)
        logging.getLogger().info("da vao")
        return []
