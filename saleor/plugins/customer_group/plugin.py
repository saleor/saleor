from django.core.exceptions import ValidationError

from saleor.plugins.models import PluginConfiguration

from ...graphql.views import GraphQLView
from ..base_plugin import BasePlugin, ConfigurationTypeField
from .graphql.schema import schema


class CustomerGroupPlugin(BasePlugin):
    PLUGIN_ID = "customer.group"
    PLUGIN_NAME = "Customer Group"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False

    DEFAULT_CONFIGURATION = [
        {"name": "name", "value": ""},
        {"name": "description", "value": ""},
        {"name": "Active", "value": True},
    ]

    CONFIG_STRUCTURE = {
        "name": {
            "type": ConfigurationTypeField.STRING,
            "help_text": " Please enter the name of customer group.",
            "label": "customer group name",
        },
        "description": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "description of customer group",
            "label": "description",
        },
    }

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""

        errors = []
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        if not configuration["name"]:
            errors.append("name")

        if plugin_configuration.active and errors:
            error_msg = (
                "To enable a plugin, you need to provide values for the "
                "following fields: "
            )
            raise ValidationError(
                {
                    errors[0]: ValidationError(
                        error_msg + ", ".join(errors), code="invalid"
                    )
                }
            )

    def webhook(self, request, path, previous_value):
        view = GraphQLView.as_view(schema=schema)
        request.app = self
        return view(request)
