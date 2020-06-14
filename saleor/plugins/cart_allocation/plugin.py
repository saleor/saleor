from typing import TYPE_CHECKING, Any

from django.utils import timezone
from django.core.exceptions import ValidationError

from ...graphql.core.utils.error_codes import PluginErrorCode
from ...warehouse.management import allocate_stock
from ..base_plugin import BasePlugin, ConfigurationTypeField
from . import (
    CartAllocationConfiguration,
)

if TYPE_CHECKING:
    # flake8: noqa
    from ...checkout.models import Checkout, CheckoutLine
    from ..models import PluginConfiguration


class CartAllocation(BasePlugin):
    PLUGIN_ID = "rogerpublishing.cart.cart_allocation"
    PLUGIN_NAME = "CartAllocation"
    DEFAULT_CONFIGURATION = [
        {"name": "Validity time", "value": "20"},
        {"name": "Action extend validity", "value": False}
    ]
    CONFIG_STRUCTURE = {
        "Validity time": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Time in minutes, checkout expiration time is extended by provided amount.",
            "label": "Validity time",
        },
        "Action extend validity": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Defines if adding new variant to checkout or changing quantity extends checkout expiration time.",
            "label": "Action extend validity",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = CartAllocationConfiguration(validity_time=configuration["Validity time"],
                                                  action_extend_validity=configuration["Action extend validity"])

    def _skip_plugin(self, previous_value: Any) -> bool:
        if not self.active or not self.config.validity_time:
            return True

        return False

    def variant_added_to_checkout(self, checkout: "Checkout", checkout_line: "CheckoutLine",
                                  previous_value: Any) -> Any:
        if not self.active:
            return previous_value

        validity_time = int(self.config.validity_time)
        action_extend_validity = self.config.action_extend_validity

        if not checkout.user:
            return previous_value

        if checkout.expires is None:
            checkout.expires = timezone.now() + timezone.timedelta(minutes=validity_time)
            checkout.save(update_fields=["expires"])

        if checkout.expired():
            checkout.delete()
            return previous_value

        if checkout_line and checkout_line.quantity != 0:
            variant = checkout_line.variant
            if variant and variant.track_inventory:
                allocate_stock(checkout_line, checkout.get_country(), checkout_line.quantity)

                if action_extend_validity:
                    checkout.expires = timezone.now() + timezone.timedelta(minutes=validity_time)
                    checkout.save(update_fields=["expires"])

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}

        validity_time = configuration.get("Validity time")

        try:
            int(validity_time)
        except ValueError:
            raise ValidationError(
                {
                    "Validity time": ValidationError(
                        "Validity time must be integer",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )

        if plugin_configuration.active and int(validity_time) <= 0:
            raise ValidationError(
                {
                    "Validity time": ValidationError(
                        "Cannot be enabled with Validity time equal or smaller 0",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )
