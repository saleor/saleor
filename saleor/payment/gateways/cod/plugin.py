import uuid
from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

from ..utils import get_supported_currencies, require_active_plugin
from . import GatewayConfig, authorize, capture, confirm, process_payment, refund, void

if TYPE_CHECKING:
    from ...interface import GatewayResponse, PaymentData

GATEWAY_NAME = str(_("Cash"))


class CashGatewayPlugin(BasePlugin):
    DEFAULT_ACTIVE = True
    PLUGIN_ID = "payments.cash"
    PLUGIN_NAME = GATEWAY_NAME

    DEFAULT_CONFIGURATION = [
        {"name": "Supported Currencies", "value": "SAR,"},
        {"name": "Automatic payment capture", "value": True},
    ]
    CONFIG_STRUCTURE = {
        "Automatic payment capture": {
            "label": "Automatic payment capture",
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should automatically capture payments.",
        },
        "Supported Currencies": {
            "label": "Supported Currencies",
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines countries that support COD payments.",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            connection_params={},
            gateway_name=GATEWAY_NAME,
            auto_capture=configuration["Automatic payment capture"],
            supported_currencies=configuration["Supported Currencies"],
        )

    def _get_gateway_config(self):
        return self.config

    @require_active_plugin
    def get_supported_currencies(self, previous_value):
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)

    @require_active_plugin
    def authorize_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return authorize(payment_information, self._get_gateway_config())

    @require_active_plugin
    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return capture(payment_information, self._get_gateway_config())

    @require_active_plugin
    def confirm_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return confirm(payment_information, self._get_gateway_config())

    @require_active_plugin
    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return refund(payment_information, self._get_gateway_config())

    @require_active_plugin
    def void_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return void(payment_information, self._get_gateway_config())

    @require_active_plugin
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return process_payment(payment_information, self._get_gateway_config())

    @require_active_plugin
    def get_client_token(self):
        return str(uuid.uuid4())

    @require_active_plugin
    def get_payment_config(self, previous_value):
        return [{"field": "client_token", "value": self.get_client_token()}]

    @require_active_plugin
    def token_is_required_as_payment_input(self, previous_value):
        return False
