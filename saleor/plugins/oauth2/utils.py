from django.contrib.auth import get_user_model

from .consts import providers_config_map
from .providers import Provider

User = get_user_model()


def get_oauth_provider(name, info) -> Provider:
    plugin = info.context.app
    config = plugin.get_oauth2_info(name)

    provider_cls = providers_config_map[name]
    return provider_cls(**config)


def get_scope(provider_name):
    return providers_config_map[provider_name].scope


def normalize_config(config):
    return {item["name"]: item["value"] for item in config}
