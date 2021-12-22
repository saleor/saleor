from typing import List, Mapping

from django.core.exceptions import ValidationError

from ...graphql.core.enums import PluginErrorCode
from ...graphql.views import GraphQLView
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..models import PluginConfiguration
from .graphql.schema import schema
from .utils import normalize_config


class OAuth2Plugin(BasePlugin):
    PLUGIN_ID = "social-login"
    PLUGIN_NAME = "OAuth2 support"
    DEFAULT_ACTIVE = True
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
        {"name": "google_redirect_uri", "value": None},
        {"name": "facebook_client_id", "value": None},
        {"name": "facebook_client_secret", "value": None},
        {"name": "facebook_redirect_uri", "value": None},
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
        "google_redirect_uri": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The URL to redirect to after the user accepts the consent in Google OAuth2",  # noqa: E501
            "label": "Google Redirect URL",
        },
        "facebook_client_id": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Your Google Client ID",
            "label": "Facebook Client ID",
        },
        "facebook_client_secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Google Your Client secret",
            "label": "Facebook Client Secret",
        },
        "facebook_redirect_uri": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The URL to redirect to after the user accepts the consent in Google OAuth2",  # noqa: E501
            "label": "Facebook Redirect URL",
        },
    }

    def get_normalized_config(self):
        return normalize_config(self.configuration)

    def get_oauth2_info(self, provider):
        config = self.get_normalized_config()
        items = config.items()
        result = {}

        for key, val in items:
            if key.startswith(provider):
                new_key = key.replace(provider, "", 1)
                result.update(
                    {
                        new_key: val,
                    }
                )

        return result

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        configuration = normalize_config(plugin_configuration.configuration)
        providers = list(filter(bool, configuration["providers"].split(",")))
        errors: Mapping[str, List] = {provider: [] for provider in providers}

        for provider in providers:
            provider = provider.lower()

            client_id = configuration.get(f"{provider}_client_id", None)
            client_secret = configuration.get(f"{provider}_client_secret", None)
            redirect_uri = configuration.get(f"{provider}_redirect_uri", None)

            if client_id is None:
                errors[provider].append("client_id")

            if client_secret is None:
                errors[provider].append("client_secret")

            if redirect_uri is None:
                errors[provider].append("redirect_uri")

        if plugin_configuration.active and errors:
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
        view = GraphQLView.as_view(schema=schema)
        request.app = self
        return view(request)
