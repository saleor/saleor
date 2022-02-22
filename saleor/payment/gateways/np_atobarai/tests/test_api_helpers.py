from dataclasses import fields
from decimal import Decimal
from unittest.mock import DEFAULT, Mock, patch, sentinel

import pytest
from posuto import Posuto

from ....interface import AddressData, RefundData
from ....utils import price_to_minor_unit
from .. import api_helpers, errors
from ..api_helpers import get_goods, get_goods_with_refunds


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


@pytest.mark.parametrize("sku_as_name", [True, False])
def test_get_goods(
    config,
    np_payment_data,
    sku_as_name,
):
    # given
    config.sku_as_name = sku_as_name

    # when
    goods = get_goods(config, np_payment_data)

    # then
    assert goods == [
        {
            "goods_name": line.product_sku if sku_as_name else line.product_name,
            "goods_price": int(
                price_to_minor_unit(line.amount, np_payment_data.currency)
            ),
            "quantity": line.quantity,
        }
        for line in np_payment_data.lines_data.lines
    ] + [
        {
            "goods_name": "Voucher",
            "goods_price": int(
                price_to_minor_unit(
                    np_payment_data.lines_data.voucher_amount, np_payment_data.currency
                )
            ),
            "quantity": 1,
        },
        {
            "goods_name": "Shipping",
            "goods_price": int(
                price_to_minor_unit(
                    np_payment_data.lines_data.shipping_amount, np_payment_data.currency
                )
            ),
            "quantity": 1,
        },
    ]


@pytest.mark.parametrize(
    "refund_amount, discount_goods",
    [
        (None, []),
        (
            Decimal("5.00"),
            [{"goods_name": "Discount", "goods_price": -500, "quantity": 1}],
        ),
    ],
)
@pytest.mark.parametrize("sku_as_name", [True, False])
def test_get_goods_with_refunds(
    config,
    payment_dummy,
    np_payment_data,
    sku_as_name,
    refund_amount,
    discount_goods,
):
    # given
    config.sku_as_name = sku_as_name
    np_payment_data.amount = refund_amount
    np_payment_data.refund_data = RefundData(
        refund_amount_is_automatically_calculated=False
    )

    # when
    goods, billed_amount = get_goods_with_refunds(
        config, payment_dummy, np_payment_data
    )

    # then
    assert (
        goods
        == [
            {
                "goods_name": line.product_sku if sku_as_name else line.product_name,
                "goods_price": int(
                    price_to_minor_unit(line.amount, np_payment_data.currency)
                ),
                "quantity": line.quantity,
            }
            for line in np_payment_data.lines_data.lines
        ]
        + [
            {
                "goods_name": "Voucher",
                "goods_price": int(
                    price_to_minor_unit(
                        np_payment_data.lines_data.voucher_amount,
                        np_payment_data.currency,
                    )
                ),
                "quantity": 1,
            },
            {
                "goods_name": "Shipping",
                "goods_price": int(
                    price_to_minor_unit(
                        np_payment_data.lines_data.shipping_amount,
                        np_payment_data.currency,
                    )
                ),
                "quantity": 1,
            },
        ]
        + discount_goods
    )
    manual_refund_amount = refund_amount or Decimal("0.00")
    assert (
        billed_amount
        == sum(line.amount * line.quantity for line in np_payment_data.lines_data.lines)
        + np_payment_data.lines_data.voucher_amount
        + np_payment_data.lines_data.shipping_amount
        - manual_refund_amount
    )
