from decimal import Decimal
from itertools import chain, zip_longest
from typing import List, Optional
from unittest.mock import Mock, patch

import pytest

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...order import FulfillmentLineData
from ...order.actions import create_refund_fulfillment
from ...order.fetch import OrderLineInfo
from ...order.models import Order
from ...plugins.manager import get_plugins_manager
from ..gateways.np_atobarai.utils import (
    calculate_manual_refund_amount,
    calculate_refunded_shipping,
    create_refunded_lines,
)
from ..interface import PaymentLineData, PaymentLinesData
from ..utils import (
    create_payment_lines_information,
    get_channel_slug_from_payment,
    try_void_or_refund_inactive_payment,
)


@pytest.fixture
def create_refund_fulfillment_helper(payment_dummy):
    def factory(
        order: Order,
        order_lines: List[OrderLineInfo] = None,
        fulfillment_lines: List[FulfillmentLineData] = None,
        manual_refund_amount: Optional[Decimal] = None,
        refund_shipping_costs: bool = False,
    ):
        if manual_refund_amount:
            payment_dummy.captured_amount = manual_refund_amount
            payment_dummy.save(update_fields=["captured_amount"])
        with patch("saleor.order.actions.gateway.refund"):
            return create_refund_fulfillment(
                user=None,
                app=None,
                order=order,
                payment=payment_dummy,
                order_lines_to_refund=order_lines or [],
                fulfillment_lines_to_refund=fulfillment_lines or [],
                manager=get_plugins_manager(),
                amount=manual_refund_amount,
                refund_shipping_costs=refund_shipping_costs,
            )

    return factory


def test_create_refund_lines_order_lines(order_with_lines):
    # given
    order_lines = order_with_lines.lines.all()
    order_refund_lines = [
        OrderLineInfo(line=(line := order_lines[0]), quantity=2, variant=line.variant),
        OrderLineInfo(line=(line := order_lines[1]), quantity=1, variant=line.variant),
    ]
    fulfillment_refund_lines = []

    # when
    lines = create_refunded_lines(
        order_with_lines,
        order_refund_lines,
        fulfillment_refund_lines,
    )

    # then
    assert lines == {line.line.variant_id: line.quantity for line in order_refund_lines}


def test_create_refund_lines_fulfillment_lines(fulfilled_order):
    # given
    fulfillment_lines = fulfilled_order.fulfillments.first().lines.all()
    order_refund_lines = []
    fulfillment_refund_lines = [
        FulfillmentLineData(
            line=fulfillment_lines[0],
            quantity=2,
        ),
        FulfillmentLineData(
            line=fulfillment_lines[1],
            quantity=1,
        ),
    ]

    # when
    lines = create_refunded_lines(
        fulfilled_order,
        order_refund_lines,
        fulfillment_refund_lines,
    )

    # then
    assert lines == {
        line.line.order_line.variant_id: line.quantity
        for line in fulfillment_refund_lines
    }


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize("previous_refund_shipping_costs", [True, False])
def test_create_refund_data_previously_refunded_order_lines(
    _mocked_refund,
    order_with_lines,
    create_refund_fulfillment_helper,
    previous_refund_shipping_costs,
):
    # given
    order_lines = order_with_lines.lines.all()
    previous_order_refund_lines = [
        OrderLineInfo(line=(line := order_lines[0]), quantity=1, variant=line.variant)
    ]
    create_refund_fulfillment_helper(
        order_with_lines,
        order_lines=previous_order_refund_lines,
        refund_shipping_costs=previous_refund_shipping_costs,
    )
    current_order_refund_lines = [
        OrderLineInfo(line=(line := order_lines[0]), quantity=1, variant=line.variant),
        OrderLineInfo(line=(line := order_lines[1]), quantity=1, variant=line.variant),
    ]
    fulfillment_refund_lines = []

    # when
    lines = create_refunded_lines(
        order_with_lines,
        current_order_refund_lines,
        fulfillment_refund_lines,
    )

    # then
    order_refund_lines = [
        OrderLineInfo(line=cl.line, quantity=pl.quantity + cl.quantity)
        for pl, cl in zip_longest(
            previous_order_refund_lines,
            current_order_refund_lines,
            fillvalue=Mock(spec=OrderLineInfo, quantity=0),
        )
    ]
    assert lines == {line.line.variant_id: line.quantity for line in order_refund_lines}


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize("previous_refund_shipping_costs", [True, False])
def test_create_refund_data_previously_refunded_fulfillment_lines(
    _mocked_refund,
    fulfilled_order,
    create_refund_fulfillment_helper,
    previous_refund_shipping_costs,
):
    # given
    fulfillment_lines = list(
        chain.from_iterable(f.lines.all() for f in fulfilled_order.fulfillments.all())
    )
    previous_fulfillment_refund_lines = [
        FulfillmentLineData(line=fulfillment_lines[0], quantity=1)
    ]
    create_refund_fulfillment_helper(
        fulfilled_order,
        fulfillment_lines=previous_fulfillment_refund_lines,
        refund_shipping_costs=previous_refund_shipping_costs,
    )
    order_refund_lines = []
    current_fulfillment_refund_lines = [
        FulfillmentLineData(
            line=fulfillment_lines[0],
            quantity=1,
        ),
        FulfillmentLineData(
            line=fulfillment_lines[1],
            quantity=1,
        ),
    ]

    # when
    lines = create_refunded_lines(
        fulfilled_order,
        order_refund_lines,
        current_fulfillment_refund_lines,
    )

    # then
    fulfillment_refund_lines = [
        FulfillmentLineData(line=cl.line, quantity=pl.quantity + cl.quantity)
        for pl, cl in zip_longest(
            previous_fulfillment_refund_lines,
            current_fulfillment_refund_lines,
            fillvalue=Mock(spec=FulfillmentLineData, quantity=0),
        )
    ]
    assert lines == {
        line.line.order_line.variant_id: line.quantity
        for line in fulfillment_refund_lines
    }


@pytest.mark.parametrize(
    "current_manual_refund_amount, expected_manual_amount",
    [
        (None, Decimal("0.00")),
        (Decimal("0.00"), Decimal("0.00")),
        (Decimal("12.34"), Decimal("12.34")),
    ],
)
def test_create_refund_manual_amount(
    order,
    current_manual_refund_amount,
    expected_manual_amount,
):
    assert (
        calculate_manual_refund_amount(order, current_manual_refund_amount)
        == expected_manual_amount
    )


@pytest.mark.parametrize(
    "previous_manual_refund_amount", [None, Decimal("0.00"), Decimal("12.34")]
)
@pytest.mark.parametrize(
    "current_manual_refund_amount", [None, Decimal("0.00"), Decimal("23.45")]
)
def test_create_refund_manual_amount_previously_refunded(
    order,
    create_refund_fulfillment_helper,
    previous_manual_refund_amount,
    current_manual_refund_amount,
):
    # given
    create_refund_fulfillment_helper(
        order, manual_refund_amount=previous_manual_refund_amount
    )

    # when
    manual_amount = calculate_manual_refund_amount(order, current_manual_refund_amount)

    # then
    expected_manual_amount = (previous_manual_refund_amount or Decimal("0.00")) + (
        current_manual_refund_amount or Decimal("0.00")
    )
    assert manual_amount == expected_manual_amount


@pytest.mark.parametrize("refund_shipping", [True, False])
def test_create_refund_shipping(order, refund_shipping):
    assert calculate_refunded_shipping(order, refund_shipping) is refund_shipping


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize(
    [
        "previous_refund_shipping_costs",
        "current_refund_shipping_costs",
        "refund_shipping_costs",
    ],
    [
        (True, True, True),
        (True, False, True),
        (False, True, True),
        (False, False, False),
    ],
)
def test_create_refund_shipping_previously_refunded(
    _mocked_refund,
    order,
    create_refund_fulfillment_helper,
    previous_refund_shipping_costs,
    current_refund_shipping_costs,
    refund_shipping_costs,
):
    # given
    create_refund_fulfillment_helper(
        order, refund_shipping_costs=previous_refund_shipping_costs
    )

    # when
    refund = calculate_refunded_shipping(
        order,
        current_refund_shipping_costs,
    )

    # then
    assert refund is refund_shipping_costs


def test_create_payment_lines_information_order(payment_dummy):
    # given
    manager = get_plugins_manager()

    # when
    payment_lines_data = create_payment_lines_information(payment_dummy, manager)

    # then
    order = payment_dummy.order
    assert payment_lines_data.lines == [
        PaymentLineData(
            amount=line.unit_price_gross_amount,
            variant_id=line.variant_id,
            product_name=f"{line.product_name}, {line.variant_name}",
            product_sku=line.product_sku,
            quantity=line.quantity,
        )
        for line in order.lines.all()
    ]
    assert payment_lines_data.shipping_amount == order.shipping_price_gross_amount
    assert payment_lines_data.voucher_amount == Decimal("0.00")


def test_create_payment_lines_information_order_with_voucher(payment_dummy):
    # given
    voucher_amount = Decimal("12.30")
    order = payment_dummy.order
    order.undiscounted_total_gross_amount += voucher_amount
    manager = get_plugins_manager()

    # when
    payment_lines_data = create_payment_lines_information(payment_dummy, manager)

    # then
    assert payment_lines_data.lines == [
        PaymentLineData(
            amount=line.unit_price_gross_amount,
            variant_id=line.variant_id,
            product_name=f"{line.product_name}, {line.variant_name}",
            product_sku=line.product_sku,
            quantity=line.quantity,
        )
        for line in order.lines.all()
    ]
    assert payment_lines_data.shipping_amount == order.shipping_price_gross_amount
    assert payment_lines_data.voucher_amount == -voucher_amount


def get_expected_checkout_payment_lines(
    manager, checkout_info, lines, address, discounts
):
    expected_payment_lines = []

    for line_info in lines:
        unit_gross = manager.calculate_checkout_line_unit_price(
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
        ).undiscounted_price.gross.amount
        quantity = line_info.line.quantity
        variant_id = line_info.variant.id
        product_name = f"{line_info.variant.product.name}, {line_info.variant.name}"
        product_sku = line_info.variant.sku
        expected_payment_lines.append(
            PaymentLineData(
                amount=unit_gross,
                variant_id=variant_id,
                product_name=product_name,
                product_sku=product_sku,
                quantity=quantity,
            )
        )

    shipping_gross = manager.calculate_checkout_shipping(
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=discounts,
    ).gross.amount

    return PaymentLinesData(
        lines=expected_payment_lines,
        shipping_amount=shipping_gross,
        voucher_amount=Decimal("0.00"),
    )


def test_create_payment_lines_information_checkout(payment_dummy, checkout_with_items):
    # given
    manager = get_plugins_manager()
    payment_dummy.order = None
    payment_dummy.checkout = checkout_with_items

    # when
    payment_lines = create_payment_lines_information(payment_dummy, manager)

    # then
    lines, _ = fetch_checkout_lines(checkout_with_items)
    discounts = []
    checkout_info = fetch_checkout_info(checkout_with_items, lines, discounts, manager)
    address = checkout_with_items.shipping_address
    expected_payment_lines = get_expected_checkout_payment_lines(
        manager, checkout_info, lines, address, discounts
    )

    assert payment_lines == expected_payment_lines


def test_create_payment_lines_information_checkout_with_voucher(
    payment_dummy, checkout_with_items
):
    # given
    manager = get_plugins_manager()
    voucher_amount = Decimal("12.30")
    payment_dummy.order = None
    checkout_with_items.discount_amount = voucher_amount
    payment_dummy.checkout = checkout_with_items

    # when
    payment_lines = create_payment_lines_information(payment_dummy, manager)

    # then
    lines, _ = fetch_checkout_lines(checkout_with_items)
    discounts = []
    checkout_info = fetch_checkout_info(checkout_with_items, lines, discounts, manager)
    address = checkout_with_items.shipping_address
    expected_payment_lines_data = get_expected_checkout_payment_lines(
        manager, checkout_info, lines, address, discounts
    )

    expected_payment_lines_data.voucher_amount = -voucher_amount

    assert payment_lines == expected_payment_lines_data


def test_create_payment_lines_information_invalid_payment(payment_dummy):
    # given
    manager = get_plugins_manager()
    payment_dummy.order = None

    # when
    payment_lines_data = create_payment_lines_information(payment_dummy, manager)

    # then
    assert not payment_lines_data.lines
    assert not payment_lines_data.shipping_amount
    assert not payment_lines_data.voucher_amount


def test_get_channel_slug_from_payment_with_order(payment_dummy):
    expected = payment_dummy.order.channel.slug
    assert get_channel_slug_from_payment(payment_dummy) == expected


def test_get_channel_slug_from_payment_with_checkout(checkout_with_payments):
    payment = checkout_with_payments.payments.first()
    expected = checkout_with_payments.channel.slug
    assert get_channel_slug_from_payment(payment) == expected


def test_get_channel_slug_from_payment_without_checkout_and_order(
    checkout_with_payments,
):
    payment = checkout_with_payments.payments.first()
    payment.checkout.delete()
    payment.refresh_from_db()
    assert not get_channel_slug_from_payment(payment)


@patch("saleor.payment.utils.update_payment_charge_status")
@patch("saleor.payment.utils.get_channel_slug_from_payment")
@patch("saleor.payment.gateway.payment_refund_or_void")
def test_try_void_or_refund_inactive_payment_failed_transaction(
    refund_or_void_mock,
    get_channel_slug_from_payment_mock,
    update_payment_charge_status_mock,
    payment_txn_capture_failed,
):
    transaction = payment_txn_capture_failed.transactions.first()

    assert not try_void_or_refund_inactive_payment(
        payment_txn_capture_failed, transaction, None
    )
    assert not update_payment_charge_status_mock.called
    assert not get_channel_slug_from_payment_mock.called
    assert not refund_or_void_mock.called


@patch("saleor.payment.utils.update_payment_charge_status")
@patch("saleor.payment.utils.get_channel_slug_from_payment")
@patch("saleor.payment.gateway.payment_refund_or_void")
def test_try_void_or_refund_inactive_payment_transaction_success(
    refund_or_void_mock,
    get_channel_slug_from_payment_mock,
    update_payment_charge_status_mock,
    payment_txn_captured,
):
    transaction = payment_txn_captured.transactions.first()

    assert not try_void_or_refund_inactive_payment(
        payment_txn_captured, transaction, None
    )
    assert update_payment_charge_status_mock.called
    assert get_channel_slug_from_payment_mock.called
    assert refund_or_void_mock.called
