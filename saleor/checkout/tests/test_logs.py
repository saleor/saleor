from decimal import Decimal
from unittest import mock

import graphene
import pytest
from prices import TaxedMoney

from ...core.taxes import zero_money
from ...discount import DiscountValueType
from ...order.fetch import OrderLineInfo
from ...plugins.manager import get_plugins_manager
from ..complete_checkout import (
    _create_order,
    _create_order_from_checkout,
    _prepare_order_data,
    logger,
)
from ..fetch import fetch_checkout_info, fetch_checkout_lines
from ..logs import log_order_with_zero_total, log_suspicious_order


@pytest.fixture
def order_with_item_total_0(
    order_generator, order_lines_generator, product_list, shipping_zone
):
    order = order_generator()
    variant = product_list[0].variants.first()

    order_lines_generator(
        order,
        [variant],
        [0],
        [2],
    )

    order.shipping_address = order.billing_address.get_copy()
    shipping_method = shipping_zone.shipping_methods.first()
    order.shipping_method_name = shipping_method.name
    order.shipping_method = shipping_method
    order.shipping_tax_class = shipping_method.tax_class
    order.shipping_tax_class_name = shipping_method.tax_class.name
    order.shipping_tax_class_metadata = shipping_method.tax_class.metadata
    order.shipping_tax_class_private_metadata = (
        shipping_method.tax_class.private_metadata
    )  # noqa: E501

    zero = zero_money(order.currency)
    order.shipping_price = TaxedMoney(net=zero, gross=zero)
    order.base_shipping_price = zero
    order.undiscounted_base_shipping_price = zero
    order.shipping_tax_rate = Decimal("0")
    order.total_gross_amount = Decimal("0")
    order.total_net_amount = Decimal("0")
    order.save()

    return order


def test_log_order_with_zero_total_valid_scenario(
    order_with_item_total_0, checkout, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].checkoutId == graphene.Node.to_global_id(
        "Checkout", checkout.pk
    )
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."


def test_log_order_with_zero_total_shipping_above_0_no_gift_cards(
    order_with_item_total_0, checkout, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    order.shipping_price_gross_amount = Decimal("10")
    order.shipping_price_net_amount = Decimal("10")
    order.save(
        update_fields=["shipping_price_gross_amount", "shipping_price_net_amount"]
    )

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for order: {order_id}. Shipping price is greater than 0."
    )


def test_log_order_with_zero_total_shipping_above_0_gift_cards(
    order_with_item_total_0, gift_card, checkout, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    gift_card.initial_balance_amount = 100
    gift_card.current_balance_amount = 100
    gift_card.save(update_fields=["current_balance_amount", "initial_balance_amount"])

    order.gift_cards.add(gift_card)

    order.shipping_price_gross_amount = Decimal("10")
    order.shipping_price_net_amount = Decimal("10")
    order.save(
        update_fields=["shipping_price_gross_amount", "shipping_price_net_amount"]
    )

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."


def test_log_order_with_zero_total_shipping_zero_no_reason(
    order_with_item_total_0, checkout, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    order.shipping_price_gross_amount = Decimal("0")
    order.shipping_price_net_amount = Decimal("0")
    order.undiscounted_base_shipping_price_amount = Decimal("5")
    order.save(
        update_fields=[
            "shipping_price_gross_amount",
            "shipping_price_net_amount",
            "undiscounted_base_shipping_price_amount",
        ]
    )

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for order: {order_id}. Shipping price is 0 for no reason."
    )


def test_log_order_with_zero_total_valid_shipping_zero(
    order_with_item_total_0, checkout, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    order.shipping_price_gross_amount = Decimal("0")
    order.shipping_price_net_amount = Decimal("0")
    order.save(
        update_fields=["shipping_price_gross_amount", "shipping_price_net_amount"]
    )

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."


def test_log_order_with_zero_total_valid_shipping_zero_voucher(
    order_with_item_total_0, checkout, caplog, voucher_free_shipping
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    code = voucher_free_shipping.codes.first()
    order.voucher_code = code.code
    order.shipping_price_gross_amount = Decimal("0")
    order.shipping_price_net_amount = Decimal("0")
    order.undiscounted_base_shipping_price_amount = Decimal("5")
    order.save(
        update_fields=[
            "shipping_price_gross_amount",
            "shipping_price_net_amount",
            "undiscounted_base_shipping_price_amount",
            "voucher_code",
        ]
    )

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    checkout_info.voucher = voucher_free_shipping
    checkout_info.voucher_code = code

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."


def test_log_order_with_zero_total_line_above_0_no_gift_cards(
    order_with_item_total_0, checkout, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    line.total_price_gross_amount = Decimal("10")
    line.total_price_net_amount = Decimal("10")
    line.save(update_fields=["total_price_gross_amount", "total_price_net_amount"])

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for order: {order_id}. Lines with total price above 0."
    )
    assert caplog.records[1].line_ids


def test_log_order_with_zero_total_line_above_0_gift_cards(
    order_with_item_total_0, checkout, gift_card, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    line.total_price_gross_amount = Decimal("10")
    line.total_price_net_amount = Decimal("10")
    line.save(update_fields=["total_price_gross_amount", "total_price_net_amount"])

    gift_card.initial_balance_amount = 100
    gift_card.current_balance_amount = 100
    gift_card.save(update_fields=["current_balance_amount", "initial_balance_amount"])

    order.gift_cards.add(gift_card)

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."


def test_log_order_with_zero_total_not_valid_line_total_zero(
    order_with_item_total_0, checkout, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    line.undiscounted_total_price_net_amount = Decimal("10")
    line.save(update_fields=["undiscounted_total_price_net_amount"])

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for order: {order_id}. Lines with total price 0 for no reason."
    )
    assert caplog.records[1].line_ids


def test_log_order_with_zero_total_valid_line_total_zero_voucher(
    order_with_item_total_0, checkout, caplog, voucher_percentage
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    line.undiscounted_total_price_net_amount = Decimal("10")
    line.save(update_fields=["undiscounted_total_price_net_amount"])

    code = voucher_percentage.codes.first()
    order.voucher_code = code.code
    order.save(update_fields=["voucher_code"])

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    checkout_info.voucher = voucher_percentage
    checkout_info.voucher_code = code

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."


def test_log_order_with_zero_total_valid_line_total_zero_price_overriden(
    order_with_item_total_0, checkout, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    line.is_price_overridden = True
    line.undiscounted_total_price_net_amount = Decimal("10")
    line.save(update_fields=["undiscounted_total_price_net_amount"])

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."


def test_log_order_with_zero_total_gift_cards_not_cover_whole_total(
    order_with_item_total_0, checkout, gift_card, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    line.total_price_gross_amount = Decimal("10")
    line.total_price_net_amount = Decimal("10")
    line.save(update_fields=["total_price_gross_amount", "total_price_net_amount"])

    gift_card.initial_balance_amount = Decimal("5")
    gift_card.current_balance_amount = Decimal("5")
    gift_card.save(update_fields=["current_balance_amount", "initial_balance_amount"])

    order.gift_cards.add(gift_card)

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for order: {order_id}. Existing gift cards not covers whole order."
    )


def test_log_order_with_zero_total_discounts_not_cover_full_total(
    order_with_item_total_0, checkout, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    order.undiscounted_total_net_amount = Decimal("10")
    order.undiscounted_total_gross_amount = Decimal("10")
    order.save(
        update_fields=[
            "undiscounted_total_net_amount",
            "undiscounted_total_gross_amount",
        ]
    )

    order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=Decimal("2"),
        amount_value=Decimal("2"),
    )
    line.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=Decimal("3"),
        amount_value=Decimal("3"),
    )

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for order: {order_id}. Discounts do not cover total price."
    )


def test_log_order_with_zero_total_discounts_cover_full_total(
    order_with_item_total_0, checkout, caplog
):
    # given
    order = order_with_item_total_0
    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    order.undiscounted_total_net_amount = Decimal("10")
    order.undiscounted_total_gross_amount = Decimal("10")
    order.save(
        update_fields=[
            "undiscounted_total_net_amount",
            "undiscounted_total_gross_amount",
        ]
    )

    order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=Decimal("7"),
        amount_value=Decimal("7"),
    )
    line_discount = line.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=Decimal("3"),
        amount_value=Decimal("3"),
    )
    lines_info.line_discounts = [line_discount]

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    # when
    log_order_with_zero_total(logger, order, [lines_info], checkout_info)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].checkoutId == checkout_id
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].message == f"Order with zero total created: {order_id}."


@mock.patch("saleor.checkout.complete_checkout.log_suspicious_order")
def test_failing_logging_in_create_order_from_checkout(
    mocked_logging, checkout, caplog
):
    # given
    err_msg = "Test error"
    mocked_logging.side_effect = ValueError(err_msg)
    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(
        checkout,
    )
    checkout_info = fetch_checkout_info(
        checkout,
        lines_info,
        manager,
    )

    # when
    order = _create_order_from_checkout(checkout_info, lines_info, manager, None, None)

    # then
    assert order
    assert f"Error logging suspicious order: {err_msg}" in [
        record.message for record in caplog.records
    ]


@mock.patch("saleor.checkout.complete_checkout.log_suspicious_order")
def test_failing_logging_in_create_order(
    mocked_logging, checkout, customer_user, caplog
):
    # given
    err_msg = "Test error"
    mocked_logging.side_effect = ValueError(err_msg)
    manager = get_plugins_manager(allow_replica=False)
    lines_info, _ = fetch_checkout_lines(
        checkout,
    )
    checkout_info = fetch_checkout_info(
        checkout,
        lines_info,
        manager,
    )

    # when
    order = _create_order(
        checkout_info=checkout_info,
        checkout_lines=lines_info,
        order_data=_prepare_order_data(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines_info,
            prices_entered_with_tax=True,
        ),
        user=customer_user,
        app=None,
        manager=manager,
    )

    # then
    assert order
    assert f"Error logging suspicious order: {err_msg}" in [
        record.message for record in caplog.records
    ]


def test_log_order_with_0_line_price(
    order_with_item_total_0, voucher_percentage, checkout, caplog
):
    # given
    order = order_with_item_total_0

    code = voucher_percentage.codes.first()
    order.voucher_code = code.code
    order.total_gross_amount = Decimal("10")
    order.total_net_amount = Decimal("10")
    order.save(update_fields=["voucher_code", "total_gross_amount", "total_net_amount"])

    order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=Decimal("100"),
        amount_value=Decimal("100"),
        voucher=voucher_percentage,
    )

    line = order.lines.first()
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    manager = get_plugins_manager(allow_replica=False)
    checkout_lines_info, _ = fetch_checkout_lines(
        checkout,
    )
    checkout_info = fetch_checkout_info(
        checkout,
        checkout_lines_info,
        manager,
    )

    # when
    log_suspicious_order(order, [lines_info], checkout_info, logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].order_id == order_id
    assert caplog.records[0].order
    assert caplog.records[0].discounts
    assert caplog.records[0].lines
    error_message = caplog.records[0].message
    assert "Order with 0 line total price" in error_message
    assert f"Suspicious order: {order_id}. Issues detected:" in error_message


def test_log_order_with_discount_higher_than_50_percent(
    order_with_item_total_0, checkout, caplog
):
    # given
    order = order_with_item_total_0

    order.total_gross_amount = Decimal("10")
    order.total_net_amount = Decimal("10")
    order.save(update_fields=["total_gross_amount", "total_net_amount"])

    line = order.lines.first()
    line.total_price_net_amount = Decimal("2")
    line.total_price_gross_amount = Decimal("2")
    line.undiscounted_total_price_net_amount = Decimal("10")
    line.undiscounted_total_price_gross_amount = Decimal("10")
    line.save(
        update_fields=[
            "undiscounted_unit_price_net_amount",
            "undiscounted_unit_price_gross_amount",
            "total_price_net_amount",
            "total_price_gross_amount",
        ]
    )
    lines_info = OrderLineInfo(
        line=line,
        quantity=line.quantity,
        variant=line.variant,
        warehouse_pk=line.allocations.first().stock.warehouse.pk,
    )

    manager = get_plugins_manager(allow_replica=False)
    checkout_lines_info, _ = fetch_checkout_lines(
        checkout,
    )
    checkout_info = fetch_checkout_info(
        checkout,
        checkout_lines_info,
        manager,
    )

    # when
    log_suspicious_order(order, [lines_info], checkout_info, logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].order_id == order_id
    assert caplog.records[0].order
    assert caplog.records[0].lines
    error_message = caplog.records[0].message
    assert "Line discounted by more than half" in error_message
    assert f"Suspicious order: {order_id}. Issues detected:" in error_message


def test_log_order_with_line_tax_issue(order_with_lines, checkout_info, caplog):
    # given
    order = order_with_lines

    line = order.lines.first()
    line.undiscounted_total_price_gross_amount += Decimal("1")
    line.save(update_fields=["undiscounted_total_price_gross_amount"])

    lines_info = [
        OrderLineInfo(
            line=line,
            quantity=line.quantity,
            variant=line.variant,
            warehouse_pk=line.allocations.first().stock.warehouse.pk,
        )
        for line in order.lines.all()
    ]

    # when
    log_suspicious_order(order, lines_info, checkout_info, logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].order_id == order_id
    assert caplog.records[0].order
    assert caplog.records[0].lines
    error_message = caplog.records[0].message
    assert "Line tax issue" in error_message
    assert f"Suspicious order: {order_id}. Issues detected:" in error_message


def test_log_order_with_tax_issue(order_with_lines, checkout_info, caplog):
    # given
    order = order_with_lines
    order.shipping_price_gross_amount += Decimal("1")
    order.save(update_fields=["shipping_price_gross_amount"])

    lines_info = [
        OrderLineInfo(
            line=line,
            quantity=line.quantity,
            variant=line.variant,
            warehouse_pk=line.allocations.first().stock.warehouse.pk,
        )
        for line in order.lines.all()
    ]

    # when
    log_suspicious_order(order, lines_info, checkout_info, logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].order_id == order_id
    assert caplog.records[0].order
    assert caplog.records[0].lines
    error_message = caplog.records[0].message
    assert "Order tax issue" in error_message
    assert f"Suspicious order: {order_id}. Issues detected:" in error_message


def test_log_order_with_incorrect_total(order_with_lines, checkout_info, caplog):
    # given
    order = order_with_lines
    line = order.lines.first()
    line.total_price_net_amount += Decimal("1")
    line.save(update_fields=["total_price_net_amount"])

    lines_info = [
        OrderLineInfo(
            line=line,
            quantity=line.quantity,
            variant=line.variant,
            warehouse_pk=line.allocations.first().stock.warehouse.pk,
        )
        for line in order.lines.all()
    ]

    # when
    log_suspicious_order(order, lines_info, checkout_info, logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert caplog.records[0].order_id == order_id
    assert caplog.records[0].order
    assert caplog.records[0].lines
    error_message = caplog.records[0].message
    assert "Order total does not match lines total and shipping" in error_message
    assert f"Suspicious order: {order_id}. Issues detected:" in error_message


def test_no_logs_for_correct_order(order_with_lines, checkout_info, caplog):
    # given
    order = order_with_lines
    lines_info = [
        OrderLineInfo(
            line=line,
            quantity=line.quantity,
            variant=line.variant,
            warehouse_pk=line.allocations.first().stock.warehouse.pk,
        )
        for line in order.lines.all()
    ]

    # when
    log_suspicious_order(order, lines_info, checkout_info, logger)

    # then
    assert not caplog.records
