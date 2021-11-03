from unittest.mock import DEFAULT, Mock, patch, sentinel

from saleor.payment.gateways.np_atobarai import api_helpers


def assert_invalid_np_response(np_response, error_keywords):
    assert not np_response.result
    for msg in error_keywords:
        assert msg in np_response.error_codes[0]


def test_register_no_billing_address(config, np_payment_data):
    # given
    np_payment_data.billing = None

    # when
    np_response = api_helpers.register(config, np_payment_data)

    # then
    assert_invalid_np_response(np_response, ["Billing address", "required"])


def test_register_no_shipping_address(config, np_payment_data):
    # given
    np_payment_data.shipping = None

    # when
    np_response = api_helpers.register(config, np_payment_data)

    # then
    assert_invalid_np_response(np_response, ["Shipping address", "required"])


INVALID = sentinel.INVALID


def format_address_side_effect(config, address):
    return None if address is INVALID else DEFAULT


@patch(
    "saleor.payment.gateways.np_atobarai.api_helpers.format_address",
    new=Mock(side_effect=format_address_side_effect),
)
@patch("saleor.payment.gateways.np_atobarai.api_helpers._request", new=Mock())
def test_register_invalid_billing_address(config, np_payment_data):
    # given
    np_payment_data.billing = INVALID

    # when
    np_response = api_helpers.register(config, np_payment_data)

    # then
    assert_invalid_np_response(np_response, ["Billing address", "valid"])


@patch(
    "saleor.payment.gateways.np_atobarai.api_helpers.format_address",
    new=Mock(side_effect=format_address_side_effect),
)
@patch("saleor.payment.gateways.np_atobarai.api_helpers._request", new=Mock())
def test_register_invalid_shipping_address(config, np_payment_data):
    # given
    np_payment_data.shipping = INVALID

    # when
    np_response = api_helpers.register(config, np_payment_data)

    # then
    assert_invalid_np_response(np_response, ["Shipping address", "valid"])
