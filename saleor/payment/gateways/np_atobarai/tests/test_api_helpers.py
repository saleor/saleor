from dataclasses import fields
from unittest.mock import DEFAULT, Mock, patch, sentinel

from posuto import Posuto

from saleor.payment.interface import AddressData

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


def test_format_name(np_address_data):
    # given
    double_byte_space = "\u3000"

    # when
    formatted_name = api_helpers.format_name(np_address_data)

    # then
    assert formatted_name == (
        f"{np_address_data.last_name}"
        f"{double_byte_space}"
        f"{np_address_data.first_name}"
    )


def test_format_address_do_not_fill(config, np_address_data):
    # given
    config.fill_missing_address = False

    # when
    formatted_address = api_helpers.format_address(config, np_address_data)

    # then
    assert formatted_address == (
        f"{np_address_data.country_area}"
        f"{np_address_data.street_address_1}"
        f"{np_address_data.street_address_2}"
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
        f"{np_address_data.street_address_1}"
        f"{np_address_data.street_address_2}"
    )


def test_format_address_fill_invalid_postal_code(config, np_address_data):
    # given
    np_address_data.postal_code = ""

    # when
    formatted_address = api_helpers.format_address(config, np_address_data)

    # then
    assert formatted_address is None


def test_format_address_proper_formatting(config):
    # given
    config.fill_missing_address = False
    address_data = AddressData(**{f.name: f.name for f in fields(AddressData)})

    # when
    formatted_address = api_helpers.format_address(config, address_data)

    # then
    assert formatted_address == (
        f"{address_data.country_area}"
        f"{address_data.street_address_1}"
        f"{address_data.street_address_2}"
    )
