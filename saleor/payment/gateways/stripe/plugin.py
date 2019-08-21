from typing import TYPE_CHECKING, List

from django.conf import settings
from django.utils.translation import pgettext_lazy

from saleor.extensions import ConfigurationTypeField
from saleor.extensions.base_plugin import BasePlugin

from . import (
    GatewayConfig,
    authorize,
    capture,
    list_client_sources,
    process_payment,
    refund,
    void,
)

GATEWAY_NAME = "stripe"

if TYPE_CHECKING:
    from . import GatewayResponse, PaymentData, CustomerSource


class StripeGatewayPlugin(BasePlugin):
    PLUGIN_NAME = "Stripe Gateway"
    CONFIG_STRUCTURE = {
        "Public API key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text", "Provide Stripe public API key"
            ),
            "label": pgettext_lazy("Plugin label", "Public API key"),
        },
        "Secret API key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text", "Provide Stripe secret API key"
            ),
            "label": pgettext_lazy("Plugin label", "Secret API key"),
        },
        "Store customers card": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "Determines if Saleor should store cards on payments in Stripe customer.",
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

    @classmethod
    def _get_default_configuration(cls):
        defaults = None
        return defaults

    def _initialize_plugin_configuration(self):
        super()._initialize_plugin_configuration()

        if self._cached_config and self._cached_config.configuration:
            configuration = self._cached_config.configuration

            self.config = GatewayConfig(
                gateway_name=GATEWAY_NAME,
                auto_capture=configuration["Automatic payment capture"],
                connection_params={
                    "public_key": configuration["Public API key"],
                    "private_key": configuration["Secret API key"],
                },
                template_path="",
                store_customer=configuration["Store customers card"],
            )
        else:
            # This should be removed after we drop payment configs in settings
            gateway_config = settings.PAYMENT_GATEWAYS[GATEWAY_NAME]["config"]
            self.config = GatewayConfig(
                gateway_name=GATEWAY_NAME,
                auto_capture=gateway_config["auto_capture"],
                template_path=gateway_config["template_path"],
                connection_params=gateway_config["connection_params"],
                store_customer=gateway_config["store_card"],
            )
            self.active = GATEWAY_NAME in settings.CHECKOUT_PAYMENT_GATEWAYS

    @classmethod
    def _get_default_configuration(cls):
        defaults = {
            "name": cls.PLUGIN_NAME,
            "description": "",
            "active": False,
            "configuration": [
                {"name": "Public API key", "value": ""},
                {"name": "Secret API key", "value": ""},
                {"name": "Store customers card", "value": False},
                {"name": "Automatic payment capture", "value": True},
            ],
        }
        return defaults

    def _get_gateway_config(self):
        return self.config

    def authorize_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return authorize(payment_information, self._get_gateway_config())

    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return capture(payment_information, self._get_gateway_config())

    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return refund(payment_information, self._get_gateway_config())

    def void_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return void(payment_information, self._get_gateway_config())

    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return process_payment(payment_information, self._get_gateway_config())

    def list_payment_sources(
        self, customer_id: str, previous_value
    ) -> List["CustomerSource"]:
        sources = list_client_sources(self._get_gateway_config(), customer_id)
        previous_value.extend(sources)
        return previous_value
