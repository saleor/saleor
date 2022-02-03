from typing import List, Mapping

from django.core.exceptions import ValidationError

from ...graphql.core.enums import PluginErrorCode
from ...graphql.views import GraphQLView
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..models import PluginConfiguration
from .graphql.schema import schema
from .utils import filter_truthy, map_many, normalize_config


class OAuth2Plugin(BasePlugin):
    name = "social-login"  # tackle saleor/saleor#8873
    PLUGIN_ID = "social-login"
    PLUGIN_NAME = "OAuth2 support"
    DEFAULT_ACTIVE = False
    PLUGIN_DESCRIPTION = "A plugin that adds support for OAuth2 and currently supports Google and Facebook"  # noqa: E501
    CONFIGURATION_PER_CHANNEL = False

    DEFAULT_CONFIGURATION = [
        {"name": "providers", "value": ""},
        {
            "name": "google_client_id",
            "value": None,
        },
        {
            "name": "google_client_secret",
            "value": None,
        },
        {"name": "facebook_client_id", "value": None},
        {"name": "facebook_client_secret", "value": None},
        {"name": "apple_client_id", "value": None},
        {"name": "apple_client_secret", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "providers": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provider names comma separated",
            "label": "Enabled services",
        },
        "google_client_id": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Your Google Client ID",
            "label": "Google Client ID",
        },
        "google_client_secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Google Your Client secret",
            "label": "Google Client Secret",
        },
        "facebook_client_id": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Your Facebook Client ID",
            "label": "Facebook Client ID",
        },
        "facebook_client_secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Google Your Client secret",
            "label": "Facebook Client Secret",
        },
        "apple_client_id": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Your Apple Client ID",
            "label": "Apple Client ID",
        },
        "apple_client_secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Apple Your Client secret",
            "label": "Apple Client Secret",
        },
    }

    def get_normalized_config(self):
        return normalize_config(self.configuration)

    def get_oauth2_info(self, provider):
        config = self.get_normalized_config()
        result = {}

        for key, val in config.items():
            if key.startswith(provider):
                prefix_length = len(f"{provider}_")
                new_key = key[prefix_length:]
                result.update(
                    {
                        new_key: val,
                    }
                )

        return result

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        configuration = normalize_config(plugin_configuration.configuration)
        providers = list(
            map_many(
                str.strip,
                str.lower,
                filter_truthy,
                iter=configuration["providers"].split(","),
            )
        )

        errors: Mapping[str, List] = {provider: [] for provider in providers}

        for provider in providers:
            provider = provider

            client_id = configuration.get(f"{provider}_client_id", None)
            client_secret = configuration.get(f"{provider}_client_secret", None)

            if client_id is None:
                errors[provider].append("client_id")

            if client_secret is None:
                errors[provider].append("client_secret")

        if plugin_configuration.active and all(errors.values()):
            error_msg = (
                "To enable {} plugin, you need to provide values for the "
                "following fields: "
            )

            raise ValidationError(
                {
                    f"{provider}_{error}": ValidationError(
                        error_msg.format(provider) + ", ".join(value),
                        code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
                    )
                    for provider, value in errors.items()
                    for error in value
                },
            )

    def webhook(self, request, path, previous_value):
        request.app = self
        view = GraphQLView.as_view(schema=schema)
        return view(request)
