from ....plugins.base_plugin import BasePlugin, ConfigurationTypeField

from ...interface import (
    CustomerSource,
    GatewayConfig,
    GatewayResponse,
    PaymentData,
    PaymentMethodInfo,
)

from .consts import (
    PLUGIN_ID,
    PLUGIN_NAME,
)


class PayfastGatewayPlugin(BasePlugin):
    PLUGIN_NAME = PLUGIN_NAME
    PLUGIN_ID = PLUGIN_ID

    DEFAULT_CONFIGURATION = [
        {"name": "public_api_key", "value": None},
        {"name": "secret_api_key", "value": None},
        {"name": "automatic_payment_capture", "value": True},
        {"name": "supported_currencies", "value": ""},
        {"name": "merchant_passphrase", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "public_api_key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide Payfast public API key.",
            "label": "Public API key",
        },
        "secret_api_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Payfast secret API key.",
            "label": "Secret API key",
        },
        "automatic_payment_capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should automatically capture payments.",
            "label": "Automatic payment capture",
        },
        "supported_currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines currencies supported by gateway."
            " Please enter currency codes separated by a comma.",
            "label": "Supported currencies",
        },
        "merchant_passphrase": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Credentials passphrase.",
            "label": "Merchant passphrase",
        },
    }

    def __init__(self, *, configuration, **kwargs):

        super().__init__(configuration=configuration, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=PLUGIN_NAME,
            auto_capture=configuration["automatic_payment_capture"],
            supported_currencies=configuration["supported_currencies"],
            connection_params={
                "public_api_key": configuration["public_api_key"],
                "secret_api_key": configuration["secret_api_key"],
                "merchant_passphrase": configuration["merchant_passphrase"],
            },
            store_customer=True,
        )


