from django.contrib.auth import get_user_model
from django.middleware.csrf import _get_new_csrf_token

from ...core.jwt import create_access_token, create_refresh_token
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


def get_user_tokens(user):
    access_token = create_access_token(user)
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(user, {"csrfToken": csrf_token})

    return {
        "token": access_token,
        "csrf_token": csrf_token,
        "refresh_token": refresh_token,
    }
