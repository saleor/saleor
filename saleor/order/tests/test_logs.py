import logging
from decimal import Decimal
from unittest import mock

import graphene
import pytest
from prices import TaxedMoney

from ...core.taxes import zero_money
from ...discount import DiscountValueType
from ...graphql.order.tests.mutations.test_draft_order_complete import (
    DRAFT_ORDER_COMPLETE_MUTATION,
)
from ...graphql.tests.utils import get_graphql_content
from .. import OrderStatus
from ..fetch import OrderLineInfo
from ..logs import (
    log_draft_order_complete_with_zero_total,
    log_suspicious_order_in_draft_order_flow,
)

logger = logging.getLogger(__name__)


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


def test_log_draft_order_complete_with_zero_total_valid_scenario(
    order_with_item_total_0, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )


def test_log_draft_order_complete_with_zero_total_shipping_above_0_no_gift_cards(
    order_with_item_total_0, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for draft order completion: {order_id}. Shipping price is greater than 0."
    )


def test_log_draft_order_complete_with_zero_total_shipping_above_0_gift_cards(
    order_with_item_total_0, gift_card, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )


def test_log_draft_order_complete_with_zero_total_shipping_zero_no_reason(
    order_with_item_total_0, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for draft order completion: {order_id}. Shipping price is 0 for no reason."
    )


def test_log_draft_order_complete_with_zero_total_valid_shipping_zero(
    order_with_item_total_0, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )


def test_log_draft_order_complete_with_zero_total_valid_shipping_zero_voucher(
    order_with_item_total_0, caplog, voucher_free_shipping
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )


def test_log_draft_order_complete_with_zero_total_line_above_0_no_gift_cards(
    order_with_item_total_0, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for draft order completion: {order_id}. Lines with total price above 0."
    )
    assert caplog.records[1].line_ids


def test_log_draft_order_complete_with_zero_total_line_above_0_gift_cards(
    order_with_item_total_0, gift_card, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )


def test_log_draft_order_complete_with_zero_total_not_valid_line_total_zero(
    order_with_item_total_0, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for draft order completion: {order_id}. Lines with total price 0 for no reason."
    )
    assert caplog.records[1].line_ids


def test_log_draft_order_complete_with_zero_total_valid_line_total_zero_voucher(
    order_with_item_total_0, caplog, voucher_percentage
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )


def test_log_draft_order_complete_with_zero_total_valid_line_total_zero_price_overriden(
    order_with_item_total_0, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )


def test_log_draft_order_complete_with_zero_total_gift_cards_not_cover_whole_total(
    order_with_item_total_0, gift_card, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for draft order completion: {order_id}. Existing gift cards not covers whole order."
    )


def test_log_draft_order_complete_with_zero_total_discounts_not_cover_full_total(
    order_with_item_total_0, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )

    assert (
        caplog.records[1].message
        == f"Not valid 0 total amount for draft order completion: {order_id}. Discounts do not cover total price."
    )


def test_log_draft_order_complete_with_zero_total_discounts_cover_full_total(
    order_with_item_total_0, caplog
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

    # when
    log_draft_order_complete_with_zero_total(order, [lines_info], logger)

    # then
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].orderId == order_id
    assert (
        caplog.records[0].message
        == f"Draft Order with zero total completed: {order_id}."
    )


@mock.patch(
    "saleor.graphql.order.mutations.draft_order_complete.log_suspicious_order_in_draft_order_flow"
)
def test_failing_logs_in_draft_order_complete(
    mocked_logging,
    staff_api_client,
    permission_group_manage_orders,
    order_with_item_total_0,
    caplog,
):
    # given
    order = order_with_item_total_0
    order.status = OrderStatus.DRAFT
    order.save(update_fields=["status"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    err_msg = "Test error"
    mocked_logging.side_effect = ValueError(err_msg)

    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_COMPLETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["draftOrderComplete"]
    assert data["order"]
    assert f"Error logging suspicious order: {err_msg}" in [
        record.message for record in caplog.records
    ]


def test_log_order_with_0_line_price(
    order_with_item_total_0, voucher_percentage, caplog
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

    # when
    log_suspicious_order_in_draft_order_flow(order, [lines_info], logger)

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
    order_with_item_total_0, caplog
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

    # when
    log_suspicious_order_in_draft_order_flow(order, [lines_info], logger)

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


def test_log_order_with_line_tax_issue(order_with_lines, caplog):
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
    log_suspicious_order_in_draft_order_flow(order, lines_info, logger)

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


def test_log_order_with_tax_issue(order_with_lines, caplog):
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
    log_suspicious_order_in_draft_order_flow(order, lines_info, logger)

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


def test_log_order_with_incorrect_total(order_with_lines, caplog):
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
    log_suspicious_order_in_draft_order_flow(order, lines_info, logger)

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
    log_suspicious_order_in_draft_order_flow(order, lines_info, logger)

    # then
    assert not caplog.records
