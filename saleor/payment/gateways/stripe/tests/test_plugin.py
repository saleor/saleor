from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from stripe.error import AuthenticationError
from stripe.stripe_object import StripeObject

from .....plugins.models import PluginConfiguration


@patch("saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint.list")
def test_validate_plugin_configuration_correct_configuration(
    mocked_stripe, stripe_plugin
):
    plugin = stripe_plugin(
        public_api_key="public",
        secret_api_key="ABC",
        active=True,
    )
    configuration = PluginConfiguration.objects.get()
    plugin.validate_plugin_configuration(configuration)

    assert mocked_stripe.called


@patch("saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint.list")
def test_validate_plugin_configuration_incorrect_configuration(
    mocked_stripe, stripe_plugin
):
    mocked_stripe.side_effect = AuthenticationError()
    plugin = stripe_plugin(
        public_api_key="public",
        secret_api_key="wrong",
        active=True,
    )
    configuration = PluginConfiguration.objects.get()
    with pytest.raises(ValidationError):
        plugin.validate_plugin_configuration(configuration)

    assert mocked_stripe.called


@patch("saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint.list")
def test_validate_plugin_configuration_missing_required_fields(
    mocked_stripe, stripe_plugin
):
    plugin = stripe_plugin(
        secret_api_key="wrong",
        active=True,
    )
    configuration = PluginConfiguration.objects.get()

    for config_field in configuration.configuration:
        if config_field["name"] == "public_api_key":
            config_field["value"] = None
            break
    with pytest.raises(ValidationError):
        plugin.validate_plugin_configuration(configuration)

    assert not mocked_stripe.called


@patch("saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint.list")
def test_validate_plugin_configuration_validate_only_when_active(
    mocked_stripe, stripe_plugin
):
    plugin = stripe_plugin(
        secret_api_key="wrong",
        active=False,
    )
    configuration = PluginConfiguration.objects.get()

    for config_field in configuration.configuration:
        if config_field["name"] == "public_api_key":
            config_field["value"] = None
            break

    plugin.validate_plugin_configuration(configuration)

    assert not mocked_stripe.called


@patch("saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint.delete")
def test_pre_save_plugin_configuration_removes_webhook_when_disabled(
    mocked_stripe, stripe_plugin
):
    plugin = stripe_plugin(
        active=False, webhook_secret_key="secret", webhook_endpoint_id="endpoint"
    )
    configuration = PluginConfiguration.objects.get()
    plugin.pre_save_plugin_configuration(configuration)

    assert all(
        [
            c_field["name"] != "webhook_endpoint_id"
            for c_field in configuration.configuration
        ]
    )
    assert all(
        [
            c_field["name"] != "webhook_secret_key"
            for c_field in configuration.configuration
        ]
    )
    assert mocked_stripe.called


def get_field_from_plugin_configuration(
    plugin_configuration: PluginConfiguration, field_name: str
):
    configuration = plugin_configuration.configuration
    for config_field in configuration:
        if config_field["name"] == field_name:
            return config_field
    return None


@patch("saleor.payment.gateways.stripe.stripe_api.stripe.WebhookEndpoint.create")
def test_pre_save_plugin_configuration(mocked_stripe, stripe_plugin):
    webhook_object = StripeObject(id="stripe_webhook_id", last_response={})
    webhook_object.secret = "stripe_webhook_secret"
    mocked_stripe.return_value = webhook_object

    plugin = stripe_plugin(active=True)
    configuration = PluginConfiguration.objects.get()
    plugin.pre_save_plugin_configuration(configuration)

    webhook_id = get_field_from_plugin_configuration(
        configuration, "webhook_endpoint_id"
    )
    webhook_secret = get_field_from_plugin_configuration(
        configuration, "webhook_secret_key"
    )

    assert webhook_id["value"] == "stripe_webhook_id"
    assert webhook_secret["value"] == "stripe_webhook_secret"

    assert mocked_stripe.called
