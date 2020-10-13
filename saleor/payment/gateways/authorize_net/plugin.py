from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

from . import GatewayConfig


GATEWAY_NAME = "Authorize.Net"


class AuthorizeNetGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    PLUGIN_ID = "mirumee.payments.authorize_net"

    DEFAULT_CONFIGURATION = [
        {"name": "API Login ID", "value": None},
        {"name": "Transaction Key", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "API Login ID": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": ("Provide Authorize.Net Login ID."),
            "label": "API Login ID",
        },
        "Transaction Key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": ("Provide Authorize.Net Transaction Key."),
            "label": "Transaction Key",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            # auto_capture=configuration["Automatic payment capture"],
            # supported_currencies=configuration["Supported currencies"],
            # connection_params={
            #     "public_key": configuration["Public API key"],
            #     "private_key": configuration["Secret API key"],
            # },
            # store_customer=configuration["Store customers card"],
        )

    def _get_gateway_config(self) -> GatewayConfig:
        return self.config
