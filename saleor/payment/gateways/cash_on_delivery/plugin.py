from typing import TYPE_CHECKING

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

from ..utils import get_supported_currencies
from . import (
    GatewayConfig,
    authorize,
    capture,
    confirm,
    get_client_token,
    process_payment,
    refund,
    void,
)

GATEWAY_NAME = "Cash on Delivery"

if TYPE_CHECKING:
    from ...interface import GatewayResponse, PaymentData, TokenConfig


class CashOnDeliveryGatewayPlugin(BasePlugin):
    """Cash on Delivery payment gateway plugin.

    This plugin allows customers to pay for their orders when they receive them.
    The payment is authorized at checkout and captured when the order is delivered.
    """

    PLUGIN_ID = "app.saleor.cash-on-delivery"
    PLUGIN_NAME = GATEWAY_NAME
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = (
        "Cash on Delivery payment gateway. Customers pay when order is delivered."
    )
    DEFAULT_CONFIGURATION = [
        {"name": "Automatic payment capture", "value": False},
        {"name": "Supported currencies", "value": "USD, EUR, AED"},
    ]
    CONFIG_STRUCTURE = {
        "Automatic payment capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "For COD, this should typically be False. "
                "Payment is captured when order is delivered."
            ),
            "label": "Automatic payment capture",
        },
        "Supported currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Currencies supported by Cash on Delivery. "
                "Enter currency codes separated by a comma."
            ),
            "label": "Supported currencies",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=configuration.get("Automatic payment capture", False),
            supported_currencies=configuration.get("Supported currencies", "USD, EUR, AED"),
            connection_params={},
            store_customer=False,
        )

    def _get_gateway_config(self):
        return self.config

    def authorize_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return authorize(payment_information, self._get_gateway_config())

    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return capture(payment_information, self._get_gateway_config())

    def confirm_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return confirm(payment_information, self._get_gateway_config())

    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return refund(payment_information, self._get_gateway_config())

    def void_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return void(payment_information, self._get_gateway_config())

    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return process_payment(payment_information, self._get_gateway_config())

    def get_client_token(self, token_config: "TokenConfig", previous_value):
        if not self.active:
            return previous_value
        return get_client_token()

    def get_supported_currencies(self, previous_value):
        if not self.active:
            return previous_value
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)

    def get_payment_config(self, previous_value):
        if not self.active:
            return previous_value
        return [{"field": "store_customer_card", "value": False}]

    def token_is_required_as_payment_input(self, previous_value):
        """Token is not required for Cash on Delivery."""
        if not self.active:
            return previous_value
        return False
