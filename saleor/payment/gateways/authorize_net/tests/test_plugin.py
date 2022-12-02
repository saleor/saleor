from unittest import mock

import pytest
from django.core.exceptions import ValidationError

from .... import PaymentError
from ..plugin import AuthorizeNetGatewayPlugin


def test_get_payment_gateway_for_checkout(
    authorize_net_plugin, checkout_with_single_item, address
):
    checkout_with_single_item.billing_address = address
    checkout_with_single_item.save()
    response = authorize_net_plugin.get_payment_gateways(
        currency=None, checkout=checkout_with_single_item, previous_value=None
    )[0]
    assert response.id == authorize_net_plugin.PLUGIN_ID
    assert response.name == authorize_net_plugin.PLUGIN_NAME
    config = response.config
    assert len(config) == 4
    assert config[0] == {
        "field": "api_login_id",
        "value": authorize_net_plugin.config.connection_params["api_login_id"],
    }
    assert config[1] == {
        "field": "client_key",
        "value": authorize_net_plugin.config.connection_params["client_key"],
    }
    assert config[2] == {
        "field": "use_sandbox",
        "value": authorize_net_plugin.config.connection_params["use_sandbox"],
    }
    assert config[3] == {
        "field": "store_customer_card",
        "value": authorize_net_plugin.config.store_customer,
    }


def test_get_payment_gateway_for_checkout_inactive(
    authorize_net_plugin, checkout_with_single_item
):
    authorize_net_plugin.active = False
    currency = checkout_with_single_item.currency
    response = authorize_net_plugin.get_payment_gateways(
        currency=currency, checkout=checkout_with_single_item, previous_value=None
    )
    assert not response


@mock.patch("saleor.payment.gateways.authorize_net.plugin.authenticate_test")
def test_payment_gateway_validate(mocked_authenticate_test, authorize_net_plugin):
    mocked_authenticate_test.return_value = (True, "")
    response = AuthorizeNetGatewayPlugin.validate_plugin_configuration(
        authorize_net_plugin
    )
    assert not response


@pytest.mark.integration
@pytest.mark.vcr()
def test_payment_gateway_validate_production(authorize_net_plugin):
    for config in authorize_net_plugin.configuration:
        if config["name"] == "use_sandbox":
            config["value"] = False
    with pytest.raises(ValidationError):
        AuthorizeNetGatewayPlugin.validate_plugin_configuration(authorize_net_plugin)


@pytest.mark.integration
@pytest.mark.vcr()
def test_payment_gateway_process_payment_production_failure(
    authorize_net_plugin, dummy_payment_data
):
    authorize_net_plugin.config.connection_params["use_sandbox"] = False
    dummy_payment_data.token = "a"
    response = authorize_net_plugin.process_payment(dummy_payment_data, None)
    assert not response.is_success


@mock.patch("saleor.payment.gateways.authorize_net.plugin.authenticate_test")
def test_payment_gateway_validate_failure(
    mocked_authenticate_test, authorize_net_plugin
):
    mocked_authenticate_test.return_value = (False, "")
    with pytest.raises(ValidationError):
        AuthorizeNetGatewayPlugin.validate_plugin_configuration(authorize_net_plugin)


@mock.patch("saleor.payment.gateways.authorize_net.plugin.refund")
def test_payment_gateway_refund_payment(
    mocked_refund, authorize_net_plugin, dummy_payment_data
):
    mocked_refund.return_value(None)
    authorize_net_plugin.refund_payment(dummy_payment_data, None)
    mocked_refund.assert_called_with(
        dummy_payment_data, "1111", authorize_net_plugin._get_gateway_config()
    )


@pytest.mark.parametrize("payment_id", [-1, None])
def test_payment_gateway_refund_payment_no_payment(
    payment_id, authorize_net_plugin, dummy_payment_data
):
    dummy_payment_data.payment_id = payment_id
    with pytest.raises(PaymentError):
        authorize_net_plugin.refund_payment(dummy_payment_data, None)


@mock.patch("saleor.payment.gateways.authorize_net.plugin.authorize")
def test_payment_gateway_authorize_payment(
    mocked_authorize, authorize_net_plugin, dummy_payment_data
):
    mocked_authorize.return_value(None)
    authorize_net_plugin.authorize_payment(dummy_payment_data, None)
    mocked_authorize.assert_called_with(
        dummy_payment_data, authorize_net_plugin._get_gateway_config()
    )


@mock.patch("saleor.payment.gateways.authorize_net.plugin.capture")
def test_payment_gateway_capture_payment(
    mocked_capture, authorize_net_plugin, dummy_payment_data
):
    mocked_capture.return_value(None)
    authorize_net_plugin.capture_payment(dummy_payment_data, None)
    mocked_capture.assert_called_with(
        dummy_payment_data, authorize_net_plugin._get_gateway_config()
    )


@mock.patch("saleor.payment.gateways.authorize_net.plugin.process_payment")
def test_payment_gateway_process_payment(
    mocked_process_payment, authorize_net_plugin, dummy_payment_data
):
    mocked_process_payment.return_value = None
    authorize_net_plugin.process_payment(dummy_payment_data, None)
    mocked_process_payment.assert_called_with(
        dummy_payment_data, authorize_net_plugin.config, None
    )


@mock.patch("saleor.payment.gateways.authorize_net.plugin.list_client_sources")
def test_payment_gateway_list_payment_sources(
    mocked_list_client_sources, authorize_net_plugin
):
    mocked_list_client_sources.return_value = []
    sources = authorize_net_plugin.list_payment_sources("1", [])
    assert sources == []
