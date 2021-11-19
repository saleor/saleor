from unittest.mock import DEFAULT, Mock, patch, sentinel

from posuto import Posuto

from .. import api_helpers, errors


def test_register_no_billing_address(config, np_payment_data):
    # given
    np_payment_data.billing = None

    # when
    np_response = api_helpers.register(config, np_payment_data)

    # then
    assert not np_response.result
    assert np_response.error_codes == [f"{errors.NO_BILLING_ADDRESS}"]


def test_register_no_shipping_address(config, np_payment_data):
    # given
    np_payment_data.shipping = None

    # when
    np_response = api_helpers.register(config, np_payment_data)

    # then
    assert not np_response.result
    assert np_response.error_codes == [f"{errors.NO_SHIPPING_ADDRESS}"]


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
    assert not np_response.result
    assert np_response.error_codes == [f"{errors.BILLING_ADDRESS_INVALID}"]


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
    assert not np_response.result
    assert np_response.error_codes == [f"{errors.SHIPPING_ADDRESS_INVALID}"]


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
