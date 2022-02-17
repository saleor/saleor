from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.middleware.csrf import _get_new_csrf_token

from ...account import events as account_events
from ...account import search
from ...core.jwt import create_access_token, create_refresh_token
from ..base_plugin import BasePlugin
from .consts import providers_config_map
from .graphql import enums
from .providers import Provider

User = get_user_model()


def get_scope(provider_name):
    return providers_config_map[provider_name].scope


def normalize_config(config):
    return {item["name"]: item["value"] for item in config}


def get_oauth2_info(provider, config):
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


def get_user_tokens(user):
    access_token = create_access_token(user)
    csrf_token = _get_new_csrf_token()
    refresh_token = create_refresh_token(user, {"csrfToken": csrf_token})

    return {
        "token": access_token,
        "csrf_token": csrf_token,
        "refresh_token": refresh_token,
    }


def parse_providers_str(providers):
    result = []

    providers = providers.split(",")
    providers = list(filter_truthy(providers))

    for provider in providers:
        result.append(provider.strip().lower())

    return result


def filter_truthy(iter):
    return filter(bool, iter)


def get_or_create_user(provider: Provider, request, auth_response):
    email = provider.get_email(auth_response=auth_response)

    try:
        user = User.objects.get(email=email)
        created = False
    except User.DoesNotExist:
        password = User.objects.make_random_password()
        user = User(email=email, is_active=True)
        user.set_password(password)
        user.search_document = search.prepare_user_search_document_value(
            user, attach_addresses_data=False
        )
        user.save()
        account_events.customer_account_created_event(user=user)
        request.plugins.customer_created(customer=user)
        # TODO: send welcome email
        created = True

    return created, user


class PluginOAuthProvider:
    @classmethod
    def from_plugin(cls, name, plugin: BasePlugin):
        return cls.from_config(name, plugin.configuration)

    @classmethod
    def from_config(cls, name, config):
        provider_cls = providers_config_map[name]
        config = normalize_config(config)
        config = get_oauth2_info(name, config)
        provider: Provider = provider_cls(**config)

        try:
            provider.validate()
        except TypeError as e:
            raise ValidationError(e, code=enums.OAuth2ErrorCode.OAUTH2_ERROR.value)

        return provider
