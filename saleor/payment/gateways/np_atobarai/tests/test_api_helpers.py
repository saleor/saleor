from unittest.mock import DEFAULT, Mock, patch, sentinel

from posuto import Posuto

from .. import api_helpers


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


def test_format_address_do_not_fill(config, np_address_data):
    # given
    config.fill_missing_address = False

    # when
    formatted_address = api_helpers.format_address(config, np_address_data)

    # then
    assert formatted_address == (
        f"{np_address_data.country_area}"
        f"{np_address_data.street_address_2}"
        f"{np_address_data.street_address_1}"
    )


def test_format_address_fill(config, np_address_data):
    # when
    formatted_address = api_helpers.format_address(config, np_address_data)

    # then
    pp = Posuto()
    japanese_address = pp.get(np_address_data.postal_code)
    assert formatted_address == (
        f"{np_address_data.country_area}"
        f"{japanese_address.city}"
        f"{japanese_address.neighborhood}"
        f"{np_address_data.street_address_2}"
        f"{np_address_data.street_address_1}"
    )


def test_format_address_fill_invalid_postal_code(config, np_address_data):
    # given
    np_address_data.postal_code = ""

    # when
    formatted_address = api_helpers.format_address(config, np_address_data)

    # then
    assert formatted_address is None
