from typing import TYPE_CHECKING

from django.utils.translation import pgettext_lazy

from saleor.extensions import ConfigurationTypeField
from saleor.extensions.base_plugin import BasePlugin

from . import GatewayConfig, capture, create_form, process_payment, refund

GATEWAY_NAME = "Razorpay"

if TYPE_CHECKING:
    from . import GatewayResponse, PaymentData
    from django import forms


def require_active_plugin(fn):
    def wrapped(self, *args, **kwargs):
        previous = kwargs.get("previous_value", None)
        self._initialize_plugin_configuration()
        if not self.active:
            return previous
        return fn(self, *args, **kwargs)

    return wrapped


class RazorpayGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    CONFIG_STRUCTURE = {
        "Template path": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text", "Location of django payment template for gateway."
            ),
            "label": pgettext_lazy("Plugin label", "Template path"),
        },
        "Public API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": pgettext_lazy("Plugin help text", "Provide  public API key"),
            "label": pgettext_lazy("Plugin label", "Public API key"),
        },
        "Secret API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": pgettext_lazy(
                "Plugin help text", "Provide Stripe secret API key"
            ),
            "label": pgettext_lazy("Plugin label", "Secret API key"),
        },
        "Store customers card": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "Determines if Saleor should store cards on payments"
                "in Stripe customer.",
            ),
            "label": pgettext_lazy("Plugin label", "Store customers card"),
        },
        "Automatic payment capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "Determines if Saleor should automaticaly capture payments.",
            ),
            "label": pgettext_lazy("Plugin label", "Automatic payment capture"),
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = None

    def _initialize_plugin_configuration(self):
        super()._initialize_plugin_configuration()

        if self._cached_config and self._cached_config.configuration:
            configuration = self._cached_config.configuration

            configuration = {item["name"]: item["value"] for item in configuration}
            self.config = GatewayConfig(
                gateway_name=GATEWAY_NAME,
                auto_capture=configuration["Automatic payment capture"],
                connection_params={
                    "public_key": configuration["Public API key"],
                    "private_key": configuration["Secret API key"],
                    "prefill": True,
                    "store_name": None,
                    "store_image": None,
                },
                template_path=configuration["Template path"],
                store_customer=configuration["Store customers card"],
            )

    @classmethod
    def _get_default_configuration(cls):
        defaults = {
            "name": cls.PLUGIN_NAME,
            "description": "",
            "active": False,
            "configuration": [
                {"name": "Template path", "value": "order/payment/razorpay.html"},
                {"name": "Public API key", "value": None},
                {"name": "Secret API key", "value": None},
                {"name": "Store customers card", "value": False},
                {"name": "Automatic payment capture", "value": True},
            ],
        }
        return defaults

    def _get_gateway_config(self):
        return self.config

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
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return process_payment(payment_information, self._get_gateway_config())

    @require_active_plugin
    def get_payment_template(self, previous_value) -> str:
        return self._get_gateway_config().template_path

    @require_active_plugin
    def create_form(
        self, data, payment_information: "PaymentData", previous_value
    ) -> "forms.Form":
        return create_form(
            data,
            payment_information,
            connection_params=self._get_gateway_config().connection_params,
        )

    @require_active_plugin
    def get_payment_config(self, previous_value):
        config = self._get_gateway_config()
        return [{"field": "api_key", "value": config.connection_params["public_key"]}]
