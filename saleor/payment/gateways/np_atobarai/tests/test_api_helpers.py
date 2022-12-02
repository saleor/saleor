from dataclasses import fields
from decimal import Decimal
from unittest.mock import DEFAULT, Mock, patch, sentinel

import pytest
from posuto import Posuto

from .....order.fetch import OrderLineInfo
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
        (Decimal("0.00"), []),
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


@pytest.fixture
def order_lines(order_with_lines):
    return list(order_with_lines.lines.all())


def test_get_goods_with_refunds_manual_product_refund_product_refund(
    create_refund, order_with_lines, config, np_payment_data, payment_dummy, order_lines
):
    # given
    line_to_refund = order_lines[0]

    create_refund(
        order_with_lines,
        order_lines=[
            OrderLineInfo(
                line=line_to_refund, quantity=1, variant=line_to_refund.variant
            )
        ],
        manual_refund_amount=Decimal("3.00"),
    )

    # when
    np_payment_data.refund_data = RefundData(
        order_lines_to_refund=[
            OrderLineInfo(
                line=line_to_refund, quantity=1, variant=line_to_refund.variant
            ),
        ]
    )
    np_payment_data.amount = line_to_refund.unit_price_gross_amount
    goods, billed_amount = get_goods_with_refunds(
        config, payment_dummy, np_payment_data
    )

    # then
    expected_billed_amount = order_with_lines.total_gross_amount - (
        Decimal("3.00") + line_to_refund.unit_price_gross_amount
    )
    assert billed_amount == expected_billed_amount
    assert goods[0]["quantity"] == line_to_refund.quantity - 1
    for goods_line, order_line in zip(goods[1:], order_lines[1:]):
        assert goods_line["quantity"] == order_line.quantity


def test_get_goods_with_refunds_product_refund_shipping_refund(
    create_refund, order_with_lines, config, np_payment_data, payment_dummy, order_lines
):
    # given
    line_to_refund = order_lines[0]

    create_refund(
        order_with_lines,
        order_lines=[
            OrderLineInfo(
                line=line_to_refund, quantity=1, variant=line_to_refund.variant
            )
        ],
    )

    # when
    np_payment_data.refund_data = RefundData(refund_shipping_costs=True)
    np_payment_data.amount = order_with_lines.shipping_price_gross_amount
    goods, billed_amount = get_goods_with_refunds(
        config, payment_dummy, np_payment_data
    )

    # then
    expected_billed_amount = order_with_lines.total_gross_amount - (
        line_to_refund.unit_price_gross_amount
        + order_with_lines.shipping_price_gross_amount
    )
    assert billed_amount == expected_billed_amount
    assert goods[0]["quantity"] == line_to_refund.quantity - 1
    for goods_line, order_line in zip(goods[1:], order_lines[1:]):
        assert goods_line["quantity"] == order_line.quantity


def test_get_goods_with_refunds_manual_shipping_misc_refund(
    create_refund, order_with_lines, config, np_payment_data, payment_dummy, order_lines
):
    # given
    create_refund(
        order_with_lines,
        refund_shipping_costs=True,
        manual_refund_amount=Decimal("5.30"),
    )

    # when
    np_payment_data.refund_data = RefundData(refund_shipping_costs=True)
    np_payment_data.amount = Decimal("4.30")
    goods, billed_amount = get_goods_with_refunds(
        config, payment_dummy, np_payment_data
    )

    # then
    expected_billed_amount = order_with_lines.total_gross_amount - (
        Decimal("5.30") + Decimal("4.30")
    )
    assert billed_amount == expected_billed_amount
    for goods_line, order_line in zip(goods, order_lines):
        assert goods_line["quantity"] == order_line.quantity


def test_get_goods_with_refunds_shipping_refund_manual_product_refund(
    create_refund, order_with_lines, config, np_payment_data, payment_dummy, order_lines
):
    # given
    create_refund(
        order_with_lines,
        refund_shipping_costs=True,
    )

    # when
    line_to_refund = order_lines[0]
    np_payment_data.refund_data = RefundData(
        order_lines_to_refund=[
            OrderLineInfo(
                line=line_to_refund,
                quantity=1,
                variant=line_to_refund.variant,
            )
        ],
        refund_amount_is_automatically_calculated=False,
    )
    np_payment_data.amount = Decimal("8.20")
    goods, billed_amount = get_goods_with_refunds(
        config, payment_dummy, np_payment_data
    )

    # then
    expected_billed_amount = order_with_lines.total_gross_amount - (
        order_with_lines.shipping_price_gross_amount + Decimal("8.20")
    )
    assert billed_amount == expected_billed_amount
    for goods_line, order_line in zip(goods, order_lines):
        assert goods_line["quantity"] == order_line.quantity
