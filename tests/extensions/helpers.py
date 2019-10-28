from typing import TYPE_CHECKING, Union

from saleor.extensions import ConfigurationTypeField
from saleor.extensions.base_plugin import BasePlugin

if TYPE_CHECKING:
    from saleor.extensions import ConfigurationType


def get_config_value(
    field_name: str, configuration: "ConfigurationType"
) -> Union[str, bool]:
    for elem in configuration:
        if elem["name"] == field_name:
            return elem["value"]


class PluginSample(BasePlugin):
    PLUGIN_NAME = "PluginSample"
    CONFIG_STRUCTURE = {
        "Username": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Username input field",
            "label": "Username",
        },
        "Password": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Password input field",
            "label": "Password",
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Use sandbox",
            "label": "Use sandbox",
        },
    }

    @classmethod
    def _get_default_configuration(cls):
        return {
            "name": "PluginSample",
            "description": "Test plugin description",
            "active": True,
            "configuration": [
                {"name": "Username", "value": "admin"},
                {"name": "Password", "value": "123"},
                {"name": "Use sandbox", "value": False},
            ],
        }
