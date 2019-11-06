from typing import TYPE_CHECKING, List

from django.utils.translation import pgettext_lazy

from saleor.extensions import ConfigurationTypeField
from saleor.extensions.base_plugin import BasePlugin

from . import (
    GatewayConfig,
    authorize,
    capture,
    process_payment,
)

GATEWAY_NAME = "PayU"

if TYPE_CHECKING:
    from . import GatewayResponse, PaymentData


def require_active_plugin(fn):
    def wrapped(self, *args, **kwargs):
        previous = kwargs.get("previous_value", None)
        self._initialize_plugin_configuration()
        if not self.active:
            return previous
        return fn(self, *args, **kwargs)

    return wrapped


class PayuGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    CONFIG_STRUCTURE = {
        "Client ID": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text", "Provide PayU client ID"
            ),
            "label": pgettext_lazy("Plugin label", "Client ID"),
        },
        "Client secret key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text", "Provide PayU client secret key"
            ),
            "label": pgettext_lazy("Plugin label", "Client secret key"),
        },
        "Merchant POS ID": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text", "Provide PayU merchant POS ID"
            ),
            "label": pgettext_lazy("Plugin label", "Merchant POS ID"),
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "Determines if Saleor should use PayU sandbox API.",
            ),
            "label": pgettext_lazy("Plugin label", "Use sandbox"),
        },
        "Validity time": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "Validity time of PayU payment (in seconds)",
            ),
            "label": pgettext_lazy("Plugin label", "Validity time"),
        },
        "Continue URL": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "URL to redirect after PayU payment",
            ),
            "label": pgettext_lazy("Plugin label", "Continue URL"),
        },
        "PayU notification URL": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "URL for PayU payment to send payment status",
            ),
            "label": pgettext_lazy("Plugin label", "PayU notification URL"),
        },
        "Store customers card": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "Determines if Saleor should store cards on payments"
                " in PayU customer.",
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
                    "client_id": configuration["Client ID"],
                    "client_secret_key": configuration["Client secret key"],
                    "merchant_pos_id": configuration["Merchant POS ID"],
                    "sandbox_mode": configuration["Use sandbox"],
                    "validity_time": configuration["Validity time"],
                    "continue_url": configuration["Continue URL"],
                    "payu_notification_url": configuration["PayU notification URL"],
                },
                template_path="",
                store_customer=configuration["Store customers card"],
            )

    @classmethod
    def _hide_secret_configuration_fields(cls, configuration):
        secret_fields = ["Client ID", "Client secret key", "Merchant POS ID"]
        for field in configuration:
            # We don't want to share our secret data
            if field.get("name") in secret_fields and field.get("value"):
                field["value"] = cls.REDACTED_FORM

    @classmethod
    def _get_default_configuration(cls):
        defaults = {
            "name": cls.PLUGIN_NAME,
            "description": "",
            "active": False,
            "configuration": [
                {"name": "Client ID", "value": ""},
                {"name": "Client secret key", "value": ""},
                {"name": "Merchant POS ID", "value": ""},
                {"name": "Validity time", "value": ""},
                {"name": "Continue URL", "value": ""},
                {"name": "PayU notification URL", "value": ""},
                {"name": "Store customers card", "value": False},
                {"name": "Automatic payment capture", "value": True},
                {"name": "Use sandbox", "value": True},
            ],
        }
        return defaults

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

    # @require_active_plugin
    # def refund_payment(
    #     self, payment_information: "PaymentData", previous_value
    # ) -> "GatewayResponse":
    #     return refund(payment_information, self._get_gateway_config())

    # @require_active_plugin
    # def void_payment(
    #     self, payment_information: "PaymentData", previous_value
    # ) -> "GatewayResponse":
    #     return void(payment_information, self._get_gateway_config())

    @require_active_plugin
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return process_payment(payment_information, self._get_gateway_config())

    # @require_active_plugin
    # def list_payment_sources(
    #     self, customer_id: str, previous_value
    # ) -> List["CustomerSource"]:
    #     sources = list_client_sources(self._get_gateway_config(), customer_id)
    #     previous_value.extend(sources)
    #     return previous_value

    @require_active_plugin
    def get_payment_config(self, previous_value):
        config = self._get_gateway_config()
        return [
            {"field": "client_id", "value": config.connection_params["client_id"]},
            {"field": "store_customer_card", "value": config.store_customer},
        ]
