from typing import TYPE_CHECKING

from django.utils.translation import pgettext_lazy

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

from . import GatewayConfig, authorize, capture, process_payment, refund, void

GATEWAY_NAME = "Paypal"

if TYPE_CHECKING:
    # flake8: noqa
    from . import GatewayResponse, PaymentData


def require_active_plugin(fn):
    def wrapped(self, *args, **kwargs):
        previous = kwargs.get("previous_value", None)
        if not self.active:
            return previous
        return fn(self, *args, **kwargs)

    return wrapped


class PaypalGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    PLUGIN_ID = "mirumee.payments.paypal"
    DEFAULT_CONFIGURATION = [
        {"name": "Sandbox mode", "value": True},
        {"name": "Client ID", "value": ""},
        {"name": "Secret API key", "value": ""},
    ]
    CONFIG_STRUCTURE = {
        "Client ID": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text", "Provide Paypal Client Id (public API key)"
            ),
            "label": pgettext_lazy("Plugin label", "Client ID"),
        },
        "Secret API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": pgettext_lazy(
                "Plugin help text", "Provide Paypal secret API key"
            ),
            "label": pgettext_lazy("Plugin label", "Secret API key"),
        },
        "Sandbox mode": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": pgettext_lazy(
                "Plugin help text", "Check if Paypal in in test mode.",
            ),
            "label": pgettext_lazy("Plugin label", "Sandbox mode"),
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            # auto_capture=configuration["Automatic payment capture"],
            auto_capture=False,
            connection_params={
                "client_id": configuration["Client ID"],
                "private_key": configuration["Secret API key"],
                "sandbox_mode": configuration["Sandbox mode"],
            },
        )

    def _get_gateway_config(self):
        return self.config

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
    def get_payment_config(self, previous_value):
        config = self._get_gateway_config()
        return [
            {"field": "client_id", "value": config.connection_params["client_id"]},
        ]
