from decimal import Decimal
from unittest.mock import Mock

import graphene
import pytest

from ...core.prices import quantize_price
from ...core.taxes import TaxData, TaxLineData
from ...discount import DiscountType, DiscountValueType, VoucherType
from ...discount.models import OrderDiscount, OrderLineDiscount, PromotionRule
from ...plugins.avatax.tests.conftest import plugin_configuration  # noqa: F401
from .. import OrderStatus
from ..calculations import fetch_order_prices_if_expired


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.status = OrderStatus.UNCONFIRMED
    return order_with_lines


def test_fetch_order_prices_tax_app(order_with_lines, tax_configuration_tax_app):
    # given
    order = order_with_lines
    currency = order.currency
    line_1, line_2 = order.lines.all()

    app_tax_rate = Decimal(10)
    db_tax_rate = app_tax_rate / Decimal(100)
    tax_rate = Decimal(1) + db_tax_rate

    line_1_total_price_net = line_1.undiscounted_total_price_net_amount
    line_1_total_price_gross = line_1_total_price_net * tax_rate
    line_1_unit_price_net = quantize_price(
        line_1_total_price_net / line_1.quantity, currency
    )
    line_1_unit_price_gross = quantize_price(
        line_1_total_price_gross / line_1.quantity, currency
    )

    line_2_total_price_net = line_2.undiscounted_total_price_net_amount
    line_2_total_price_gross = line_2_total_price_net * tax_rate
    line_2_unit_price_net = quantize_price(
        line_2_total_price_net / line_2.quantity, currency
    )
    line_2_unit_price_gross = quantize_price(
        line_2_total_price_gross / line_2.quantity, currency
    )

    shipping_price_net = order.shipping_price_net_amount
    shipping_price_gross = shipping_price_net * tax_rate

    subtotal_net = line_1_total_price_net + line_2_total_price_net
    subtotal_gross = line_1_total_price_gross + line_2_total_price_gross
    total_net = subtotal_net + shipping_price_net
    total_gross = subtotal_gross + shipping_price_gross

    tax_data = TaxData(
        shipping_price_net_amount=shipping_price_net,
        shipping_price_gross_amount=shipping_price_gross,
        shipping_tax_rate=app_tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=line_1_total_price_net,
                total_gross_amount=line_1_total_price_gross,
                tax_rate=app_tax_rate,
            ),
            TaxLineData(
                total_net_amount=line_2_total_price_net,
                total_gross_amount=line_2_total_price_gross,
                tax_rate=app_tax_rate,
            ),
        ],
    )

    manager_methods = {"get_taxes_for_order": Mock(return_value=tax_data)}
    manager = Mock(**manager_methods)

    # when
    order, lines = fetch_order_prices_if_expired(order, manager, None, True)

    # then
    assert order.shipping_price_net_amount == shipping_price_net
    assert order.shipping_price_gross_amount == shipping_price_gross
    assert order.shipping_tax_rate == db_tax_rate
    assert order.subtotal_net_amount == subtotal_net
    assert order.subtotal_gross_amount == subtotal_gross
    assert order.total_net_amount == total_net
    assert order.total_gross_amount == total_gross

    line_1, line_2 = lines

    assert line_1.undiscounted_total_price_net_amount == line_1_total_price_net
    assert line_1.undiscounted_total_price_gross_amount == line_1_total_price_gross
    assert line_1.undiscounted_unit_price_net_amount == line_1_unit_price_net
    assert line_1.undiscounted_unit_price_gross_amount == line_1_unit_price_gross

    assert line_1.base_unit_price_amount == line_1_unit_price_net
    assert line_1.total_price_net_amount == line_1_total_price_net
    assert line_1.total_price_gross_amount == line_1_total_price_gross
    assert line_1.unit_price_net_amount == line_1_unit_price_net
    assert line_1.unit_price_gross_amount == line_1_unit_price_gross

    assert line_1.unit_discount_reason is None
    assert line_1.unit_discount_amount == Decimal(0)

    assert line_2.undiscounted_total_price_net_amount == line_2_total_price_net
    assert line_2.undiscounted_total_price_gross_amount == line_2_total_price_gross
    assert line_2.undiscounted_unit_price_net_amount == line_2_unit_price_net
    assert line_2.undiscounted_unit_price_gross_amount == line_2_unit_price_gross

    assert line_2.base_unit_price_amount == line_2_unit_price_net
    assert line_2.total_price_net_amount == line_2_total_price_net
    assert line_2.total_price_gross_amount == line_2_total_price_gross
    assert line_2.unit_price_net_amount == line_2_unit_price_net
    assert line_2.unit_price_gross_amount == line_2_unit_price_gross

    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_amount == Decimal(0)


def test_fetch_order_prices_catalogue_discount_tax_app(
    order_with_lines_and_catalogue_promotion,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines_and_catalogue_promotion
    currency = order.currency
    line_1, line_2 = order.lines.all()

    rule = PromotionRule.objects.get()
    assert rule.reward_value_type == DiscountValueType.FIXED
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    reward_value = rule.reward_value

    app_tax_rate = Decimal(10)
    db_tax_rate = app_tax_rate / Decimal(100)
    tax_rate = Decimal(1) + db_tax_rate

    line_1_undiscounted_total_price_net = line_1.undiscounted_total_price_net_amount
    line_1_undiscounted_total_price_gross = (
        line_1_undiscounted_total_price_net * tax_rate
    )
    line_1_undiscounted_unit_price_net = quantize_price(
        line_1_undiscounted_total_price_net / line_1.quantity, currency
    )
    line_1_undiscounted_unit_price_gross = quantize_price(
        line_1_undiscounted_total_price_gross / line_1.quantity, currency
    )

    line_1_unit_price_net = quantize_price(
        line_1_undiscounted_unit_price_net - reward_value, currency
    )
    line_1_unit_price_gross = line_1_unit_price_net * tax_rate
    line_1_total_price_net = line_1_unit_price_net * line_1.quantity
    line_1_total_price_gross = line_1_total_price_net * tax_rate

    line_2_total_price_net = line_2.undiscounted_total_price_net_amount
    line_2_total_price_gross = line_2_total_price_net * tax_rate
    line_2_unit_price_net = quantize_price(
        line_2_total_price_net / line_2.quantity, currency
    )
    line_2_unit_price_gross = quantize_price(
        line_2_total_price_gross / line_2.quantity, currency
    )

    shipping_price_net = order.shipping_price_net_amount
    shipping_price_gross = shipping_price_net * tax_rate

    subtotal_net = line_1_total_price_net + line_2_total_price_net
    subtotal_gross = line_1_total_price_gross + line_2_total_price_gross
    total_net = subtotal_net + shipping_price_net
    total_gross = subtotal_gross + shipping_price_gross

    tax_data = TaxData(
        shipping_price_net_amount=shipping_price_net,
        shipping_price_gross_amount=shipping_price_gross,
        shipping_tax_rate=app_tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=line_1_total_price_net,
                total_gross_amount=line_1_total_price_gross,
                tax_rate=app_tax_rate,
            ),
            TaxLineData(
                total_net_amount=line_2_total_price_net,
                total_gross_amount=line_2_total_price_gross,
                tax_rate=app_tax_rate,
            ),
        ],
    )

    manager_methods = {"get_taxes_for_order": Mock(return_value=tax_data)}
    manager = Mock(**manager_methods)

    # when
    order, lines = fetch_order_prices_if_expired(order, manager, None, True)

    # then
    discount = line_1.discounts.get()
    reward_amount = reward_value * line_1.quantity
    assert discount.amount_value == reward_amount
    assert discount.value == reward_value
    assert discount.type == DiscountType.PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"

    assert order.shipping_price_net_amount == shipping_price_net
    assert order.shipping_price_gross_amount == shipping_price_gross
    assert order.shipping_tax_rate == db_tax_rate
    assert order.subtotal_net_amount == subtotal_net
    assert order.subtotal_gross_amount == subtotal_gross
    assert order.total_net_amount == total_net
    assert order.total_gross_amount == total_gross

    line_1, line_2 = lines

    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1_undiscounted_total_price_net
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1_undiscounted_total_price_gross
    )
    assert (
        line_1.undiscounted_unit_price_net_amount == line_1_undiscounted_unit_price_net
    )
    assert (
        line_1.undiscounted_unit_price_gross_amount
        == line_1_undiscounted_unit_price_gross
    )

    assert line_1.base_unit_price_amount == line_1_unit_price_net
    assert line_1.total_price_net_amount == line_1_total_price_net
    assert line_1.total_price_gross_amount == line_1_total_price_gross
    assert line_1.unit_price_net_amount == line_1_unit_price_net
    assert line_1.unit_price_gross_amount == line_1_unit_price_gross

    assert line_1.unit_discount_reason == f"Promotion: {promotion_id}"
    assert line_1.unit_discount_amount == reward_value

    assert line_2.undiscounted_total_price_net_amount == line_2_total_price_net
    assert line_2.undiscounted_total_price_gross_amount == line_2_total_price_gross
    assert line_2.undiscounted_unit_price_net_amount == line_2_unit_price_net
    assert line_2.undiscounted_unit_price_gross_amount == line_2_unit_price_gross

    assert line_2.base_unit_price_amount == line_2_unit_price_net
    assert line_2.total_price_net_amount == line_2_total_price_net
    assert line_2.total_price_gross_amount == line_2_total_price_gross
    assert line_2.unit_price_net_amount == line_2_unit_price_net
    assert line_2.unit_price_gross_amount == line_2_unit_price_gross

    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_amount == Decimal(0)


def test_fetch_order_prices_order_discount_tax_app(
    order_with_lines_and_order_promotion,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines_and_order_promotion
    currency = order.currency
    line_1, line_2 = order.lines.all()

    rule = PromotionRule.objects.get()
    assert rule.reward_value_type == DiscountValueType.FIXED
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    reward_value = rule.reward_value

    line_1_base_total = line_1.quantity * line_1.base_unit_price_amount
    line_2_base_total = line_2.quantity * line_2.base_unit_price_amount
    base_total = line_1_base_total + line_2_base_total
    line_1_order_discount_portion = reward_value * line_1_base_total / base_total
    line_2_order_discount_portion = reward_value - line_1_order_discount_portion

    app_tax_rate = Decimal(10)
    db_tax_rate = app_tax_rate / Decimal(100)
    tax_rate = Decimal(1) + db_tax_rate

    line_1_undiscounted_total_price_net = line_1.undiscounted_total_price_net_amount
    line_1_undiscounted_total_price_gross = (
        line_1_undiscounted_total_price_net * tax_rate
    )
    line_1_undiscounted_unit_price_net = (
        line_1_undiscounted_total_price_net / line_1.quantity
    )
    line_1_undiscounted_unit_price_gross = line_1_undiscounted_unit_price_net * tax_rate

    line_1_total_price_net = (
        line_1_undiscounted_total_price_net - line_1_order_discount_portion
    )
    line_1_total_price_gross = line_1_total_price_net * tax_rate
    line_1_unit_price_net = line_1_total_price_net / line_1.quantity
    line_1_unit_price_gross = line_1_unit_price_net * tax_rate

    line_2_undiscounted_total_price_net = line_2.undiscounted_total_price_net_amount
    line_2_undiscounted_total_price_gross = (
        line_2_undiscounted_total_price_net * tax_rate
    )
    line_2_undiscounted_unit_price_net = quantize_price(
        line_2_undiscounted_total_price_net / line_2.quantity, currency
    )
    line_2_undiscounted_unit_price_gross = quantize_price(
        line_2_undiscounted_total_price_gross / line_2.quantity, currency
    )

    line_2_total_price_net = (
        line_2_undiscounted_total_price_net - line_2_order_discount_portion
    )
    line_2_total_price_gross = line_2_total_price_net * tax_rate
    line_2_unit_price_net = line_2_total_price_net / line_2.quantity
    line_2_unit_price_gross = line_2_unit_price_net * tax_rate

    shipping_price_net = order.shipping_price_net_amount
    shipping_price_gross = shipping_price_net * tax_rate

    undiscounted_subtotal_net = (
        line_1_undiscounted_total_price_net + line_2_undiscounted_total_price_net
    )
    subtotal_net = line_1_total_price_net + line_2_total_price_net
    subtotal_gross = line_1_total_price_gross + line_2_total_price_gross
    total_net = subtotal_net + shipping_price_net
    total_gross = subtotal_gross + shipping_price_gross

    tax_data = TaxData(
        shipping_price_net_amount=shipping_price_net,
        shipping_price_gross_amount=shipping_price_gross,
        shipping_tax_rate=app_tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=line_1_total_price_net,
                total_gross_amount=line_1_total_price_gross,
                tax_rate=app_tax_rate,
            ),
            TaxLineData(
                total_net_amount=line_2_total_price_net,
                total_gross_amount=line_2_total_price_gross,
                tax_rate=app_tax_rate,
            ),
        ],
    )

    manager_methods = {"get_taxes_for_order": Mock(return_value=tax_data)}
    manager = Mock(**manager_methods)

    # when
    order, lines = fetch_order_prices_if_expired(order, manager, None, True)

    # then
    discount = order.discounts.get()
    assert discount.amount_value == reward_value
    assert discount.value == reward_value
    assert discount.value_type == DiscountValueType.FIXED
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"

    assert order.shipping_price_net_amount == shipping_price_net
    assert order.shipping_price_gross_amount == shipping_price_gross
    assert order.shipping_tax_rate == db_tax_rate
    assert order.subtotal_net_amount == subtotal_net
    assert order.subtotal_gross_amount == subtotal_gross
    assert order.total_net_amount == total_net
    assert order.total_gross_amount == total_gross
    assert (
        order.total_net_amount
        == undiscounted_subtotal_net - reward_value + shipping_price_net
    )
    assert order.total_gross_amount == order.total_net_amount * tax_rate

    line_1, line_2 = lines

    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1_undiscounted_total_price_net
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1_undiscounted_total_price_gross
    )
    assert (
        line_1.undiscounted_unit_price_net_amount == line_1_undiscounted_unit_price_net
    )
    assert (
        line_1.undiscounted_unit_price_gross_amount
        == line_1_undiscounted_unit_price_gross
    )

    assert line_1.base_unit_price_amount == line_1_undiscounted_unit_price_net
    assert line_1.total_price_net_amount == line_1_total_price_net
    assert line_1.total_price_gross_amount == line_1_total_price_gross
    assert line_1.unit_price_net_amount == quantize_price(
        line_1_unit_price_net, currency
    )
    assert line_1.unit_price_gross_amount == quantize_price(
        line_1_unit_price_gross, currency
    )

    # TODO shopx-1531
    # assert line_1.unit_discount_reason == f"Promotion: {promotion_id}"
    # assert line_1.unit_discount_amount == quantize_price(
    #     line_1_undiscounted_unit_price_net - line_1_unit_price_net, currency
    # )

    assert (
        line_2.undiscounted_total_price_net_amount
        == line_2_undiscounted_total_price_net
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2_undiscounted_total_price_gross
    )
    assert (
        line_2.undiscounted_unit_price_net_amount == line_2_undiscounted_unit_price_net
    )
    assert (
        line_2.undiscounted_unit_price_gross_amount
        == line_2_undiscounted_unit_price_gross
    )

    assert line_2.base_unit_price_amount == line_2_undiscounted_unit_price_net
    assert line_2.total_price_net_amount == line_2_total_price_net
    assert line_2.total_price_gross_amount == line_2_total_price_gross
    assert line_2.unit_price_net_amount == quantize_price(
        line_2_unit_price_net, currency
    )
    assert line_2.unit_price_gross_amount == quantize_price(
        line_2_unit_price_gross, currency
    )

    # TODO shopx-1531
    # assert line_2.unit_discount_reason == f"Promotion: {promotion_id}"
    # assert line_2.unit_discount_amount == quantize_price(
    #     line_2_undiscounted_unit_price_net - line_2_unit_price_net, currency
    # )


def test_fetch_order_prices_order_discount_tax_app_prices_entered_with_taxes(
    order_with_lines_and_order_promotion,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines_and_order_promotion
    currency = order.currency
    line_1, line_2 = order.lines.all()

    tax_configuration_tax_app.prices_entered_with_tax = True
    tax_configuration_tax_app.save(update_fields=["prices_entered_with_tax"])

    rule = PromotionRule.objects.get()
    assert rule.reward_value_type == DiscountValueType.FIXED
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    reward_value = rule.reward_value

    line_1_base_total = line_1.quantity * line_1.base_unit_price_amount
    line_2_base_total = line_2.quantity * line_2.base_unit_price_amount
    base_total = line_1_base_total + line_2_base_total
    line_1_order_discount_portion = reward_value * line_1_base_total / base_total
    line_2_order_discount_portion = reward_value - line_1_order_discount_portion

    app_tax_rate = Decimal(10)
    db_tax_rate = app_tax_rate / Decimal(100)
    tax_rate = Decimal(1) + db_tax_rate

    line_1_undiscounted_total_price_gross = line_1_base_total
    line_1_undiscounted_total_price_net = (
        line_1_undiscounted_total_price_gross / tax_rate
    )
    line_1_undiscounted_unit_price_gross = (
        line_1_undiscounted_total_price_gross / line_1.quantity
    )
    line_1_undiscounted_unit_price_net = line_1_undiscounted_unit_price_gross / tax_rate

    line_1_total_price_gross = (
        line_1_undiscounted_total_price_gross - line_1_order_discount_portion
    )
    line_1_total_price_net = line_1_total_price_gross / tax_rate
    line_1_unit_price_gross = line_1_total_price_gross / line_1.quantity
    line_1_unit_price_net = line_1_unit_price_gross / tax_rate

    line_2_undiscounted_total_price_gross = line_2_base_total
    line_2_undiscounted_total_price_net = (
        line_2_undiscounted_total_price_gross / tax_rate
    )
    line_2_undiscounted_unit_price_gross = (
        line_2_undiscounted_total_price_gross / line_2.quantity
    )
    line_2_undiscounted_unit_price_net = line_2_undiscounted_unit_price_gross / tax_rate

    line_2_total_price_gross = (
        line_2_undiscounted_total_price_gross - line_2_order_discount_portion
    )
    line_2_total_price_net = line_2_total_price_gross / tax_rate
    line_2_unit_price_gross = line_2_total_price_gross / line_2.quantity
    line_2_unit_price_net = line_2_unit_price_gross / tax_rate

    shipping_price_gross = order.undiscounted_base_shipping_price_amount
    shipping_price_net = shipping_price_gross / tax_rate

    undiscounted_subtotal_gross = (
        line_1_undiscounted_total_price_gross + line_2_undiscounted_total_price_gross
    )
    subtotal_gross = line_1_total_price_gross + line_2_total_price_gross
    subtotal_net = line_1_total_price_net + line_2_total_price_net
    total_gross = subtotal_gross + shipping_price_gross
    total_net = subtotal_net + shipping_price_net

    tax_data = TaxData(
        shipping_price_net_amount=quantize_price(shipping_price_net, currency),
        shipping_price_gross_amount=quantize_price(shipping_price_gross, currency),
        shipping_tax_rate=app_tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=quantize_price(line_1_total_price_net, currency),
                total_gross_amount=quantize_price(line_1_total_price_gross, currency),
                tax_rate=app_tax_rate,
            ),
            TaxLineData(
                total_net_amount=quantize_price(line_2_total_price_net, currency),
                total_gross_amount=quantize_price(line_2_total_price_gross, currency),
                tax_rate=app_tax_rate,
            ),
        ],
    )

    manager_methods = {"get_taxes_for_order": Mock(return_value=tax_data)}
    manager = Mock(**manager_methods)

    # when
    order, lines = fetch_order_prices_if_expired(order, manager, None, True)

    # then
    discount = order.discounts.get()
    assert discount.amount_value == reward_value
    assert discount.value == reward_value
    assert discount.value_type == DiscountValueType.FIXED
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"

    assert order.shipping_price_net_amount == quantize_price(
        shipping_price_net, currency
    )
    assert order.shipping_price_gross_amount == shipping_price_gross
    assert order.shipping_tax_rate == db_tax_rate
    assert order.subtotal_net_amount == quantize_price(subtotal_net, currency)
    assert order.subtotal_gross_amount == subtotal_gross
    assert order.total_net_amount == quantize_price(total_net, currency)
    assert order.total_gross_amount == total_gross
    assert (
        order.total_gross_amount
        == undiscounted_subtotal_gross - reward_value + shipping_price_gross
    )
    assert order.total_net_amount == order.total_gross_amount / tax_rate

    line_1, line_2 = lines

    assert line_1.undiscounted_total_price_net_amount == quantize_price(
        line_1_undiscounted_total_price_net, currency
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1_undiscounted_total_price_gross
    )
    assert line_1.undiscounted_unit_price_net_amount == quantize_price(
        line_1_undiscounted_unit_price_net, currency
    )
    assert (
        line_1.undiscounted_unit_price_gross_amount
        == line_1_undiscounted_unit_price_gross
    )

    assert line_1.base_unit_price_amount == quantize_price(
        line_1_undiscounted_unit_price_gross, currency
    )
    assert line_1.total_price_net_amount == quantize_price(
        line_1_total_price_net, currency
    )
    assert line_1.total_price_gross_amount == quantize_price(
        line_1_total_price_gross, currency
    )
    assert line_1.unit_price_net_amount == quantize_price(
        line_1_unit_price_net, currency
    )
    assert line_1.unit_price_gross_amount == quantize_price(
        line_1_unit_price_gross, currency
    )

    # TODO shopx-1531
    # assert line_1.unit_discount_reason == f"Promotion: {promotion_id}"
    # assert line_1.unit_discount_amount == quantize_price(
    #     line_1_undiscounted_unit_price_gross - line_1_unit_price_gross, currency
    # )

    assert line_2.undiscounted_total_price_net_amount == quantize_price(
        line_2_undiscounted_total_price_net, currency
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2_undiscounted_total_price_gross
    )
    assert line_2.undiscounted_unit_price_net_amount == quantize_price(
        line_2_undiscounted_unit_price_net, currency
    )
    assert (
        line_2.undiscounted_unit_price_gross_amount
        == line_2_undiscounted_unit_price_gross
    )

    assert line_2.base_unit_price_amount == line_2_undiscounted_unit_price_gross
    assert line_2.total_price_net_amount == quantize_price(
        line_2_total_price_net, currency
    )
    assert line_2.total_price_gross_amount == quantize_price(
        line_2_total_price_gross, currency
    )
    assert line_2.unit_price_net_amount == quantize_price(
        line_2_unit_price_net, currency
    )
    assert line_2.unit_price_gross_amount == quantize_price(
        line_2_unit_price_gross, currency
    )

    # TODO shopx-1531
    # assert line_2.unit_discount_reason == f"Promotion: {promotion_id}"
    # assert line_2.unit_discount_amount == quantize_price(
    #     line_2_undiscounted_unit_price_gross - line_2_unit_price_gross, currency
    # )


def test_fetch_order_prices_gift_discount_tax_app(
    order_with_lines_and_gift_promotion,
    tax_configuration_tax_app,
    channel_USD,
):
    # given
    order = order_with_lines_and_gift_promotion
    currency = order.currency
    line_1, line_2, gift_line = order.lines.all()

    rule = PromotionRule.objects.get()
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    gift_variant = rule.gifts.get()
    gift_price = gift_variant.channel_listings.get(channel=channel_USD).price_amount

    app_tax_rate = Decimal(10)
    db_tax_rate = app_tax_rate / Decimal(100)
    tax_rate = Decimal(1) + db_tax_rate

    line_1_total_price_net = line_1.undiscounted_total_price_net_amount
    line_1_total_price_gross = line_1_total_price_net * tax_rate
    line_1_unit_price_net = quantize_price(
        line_1_total_price_net / line_1.quantity, currency
    )
    line_1_unit_price_gross = quantize_price(
        line_1_total_price_gross / line_1.quantity, currency
    )

    line_2_total_price_net = line_2.undiscounted_total_price_net_amount
    line_2_total_price_gross = line_2_total_price_net * tax_rate
    line_2_unit_price_net = quantize_price(
        line_2_total_price_net / line_2.quantity, currency
    )
    line_2_unit_price_gross = quantize_price(
        line_2_total_price_gross / line_2.quantity, currency
    )

    shipping_price_net = order.shipping_price_net_amount
    shipping_price_gross = shipping_price_net * tax_rate

    subtotal_net = line_1_total_price_net + line_2_total_price_net
    subtotal_gross = line_1_total_price_gross + line_2_total_price_gross
    total_net = subtotal_net + shipping_price_net
    total_gross = subtotal_gross + shipping_price_gross

    tax_data = TaxData(
        shipping_price_net_amount=shipping_price_net,
        shipping_price_gross_amount=shipping_price_gross,
        shipping_tax_rate=app_tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=line_1_total_price_net,
                total_gross_amount=line_1_total_price_gross,
                tax_rate=app_tax_rate,
            ),
            TaxLineData(
                total_net_amount=line_2_total_price_net,
                total_gross_amount=line_2_total_price_gross,
                tax_rate=app_tax_rate,
            ),
            TaxLineData(
                total_net_amount=Decimal(0),
                total_gross_amount=Decimal(0),
                tax_rate=app_tax_rate,
            ),
        ],
    )

    manager_methods = {"get_taxes_for_order": Mock(return_value=tax_data)}
    manager = Mock(**manager_methods)

    # when
    order, lines = fetch_order_prices_if_expired(order, manager, None, True)

    # then
    assert order.shipping_price_net_amount == shipping_price_net
    assert order.shipping_price_gross_amount == shipping_price_gross
    assert order.shipping_tax_rate == db_tax_rate
    assert order.subtotal_net_amount == subtotal_net
    assert order.subtotal_gross_amount == subtotal_gross
    assert order.total_net_amount == total_net
    assert order.total_gross_amount == total_gross

    line_1, line_2, gift_line = lines

    assert line_1.undiscounted_total_price_net_amount == line_1_total_price_net
    assert line_1.undiscounted_total_price_gross_amount == line_1_total_price_gross
    assert line_1.undiscounted_unit_price_net_amount == line_1_unit_price_net
    assert line_1.undiscounted_unit_price_gross_amount == line_1_unit_price_gross

    assert line_1.base_unit_price_amount == line_1_unit_price_net
    assert line_1.total_price_net_amount == line_1_total_price_net
    assert line_1.total_price_gross_amount == line_1_total_price_gross
    assert line_1.unit_price_net_amount == line_1_unit_price_net
    assert line_1.unit_price_gross_amount == line_1_unit_price_gross

    assert line_1.unit_discount_reason is None
    assert line_1.unit_discount_amount == Decimal(0)

    assert line_2.undiscounted_total_price_net_amount == line_2_total_price_net
    assert line_2.undiscounted_total_price_gross_amount == line_2_total_price_gross
    assert line_2.undiscounted_unit_price_net_amount == line_2_unit_price_net
    assert line_2.undiscounted_unit_price_gross_amount == line_2_unit_price_gross

    assert line_2.base_unit_price_amount == line_2_unit_price_net
    assert line_2.total_price_net_amount == line_2_total_price_net
    assert line_2.total_price_gross_amount == line_2_total_price_gross
    assert line_2.unit_price_net_amount == line_2_unit_price_net
    assert line_2.unit_price_gross_amount == line_2_unit_price_gross

    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_amount == Decimal(0)

    assert gift_line.undiscounted_total_price_net_amount == Decimal(0)
    assert gift_line.undiscounted_total_price_gross_amount == Decimal(0)
    assert gift_line.undiscounted_unit_price_net_amount == Decimal(0)
    assert gift_line.undiscounted_unit_price_gross_amount == Decimal(0)

    assert gift_line.base_unit_price_amount == Decimal(0)
    assert gift_line.total_price_net_amount == Decimal(0)
    assert gift_line.total_price_gross_amount == Decimal(0)
    assert gift_line.unit_price_net_amount == Decimal(0)
    assert gift_line.unit_price_gross_amount == Decimal(0)

    assert gift_line.unit_discount_reason == f"Promotion: {promotion_id}"
    assert gift_line.unit_discount_amount == gift_price

    gift_discount = gift_line.discounts.get()
    assert gift_discount.amount.amount == gift_price


def test_fetch_order_prices_catalogue_and_order_discounts_tax_app(
    draft_order_and_promotions,
    tax_configuration_tax_app,
):
    # given
    order, rule_catalogue, rule_total, _ = draft_order_and_promotions
    catalogue_promotion_id = graphene.Node.to_global_id(
        "Promotion", rule_catalogue.promotion_id
    )
    order_promotion_id = graphene.Node.to_global_id(
        "Promotion", rule_total.promotion_id
    )
    rule_catalogue_reward = rule_catalogue.reward_value
    rule_total_reward = rule_total.reward_value
    currency = order.currency
    line_1, line_2 = order.lines.all()

    app_tax_rate = Decimal(10)
    db_tax_rate = app_tax_rate / Decimal(100)
    tax_rate = Decimal(1) + db_tax_rate

    line_1_base_unit_price = line_1.undiscounted_unit_price_net_amount
    line_2_base_unit_price = (
        line_2.undiscounted_unit_price_net_amount - rule_catalogue_reward
    )
    line_1_base_total = line_1.quantity * line_1_base_unit_price
    line_2_base_total = line_2.quantity * line_2_base_unit_price
    base_total = line_1_base_total + line_2_base_total
    line_1_order_discount_portion = rule_total_reward * line_1_base_total / base_total
    line_2_order_discount_portion = rule_total_reward - line_1_order_discount_portion

    line_1_total_price_net = quantize_price(
        line_1_base_total - line_1_order_discount_portion, currency
    )
    line_1_total_price_gross = quantize_price(
        line_1_total_price_net * tax_rate, currency
    )
    line_2_total_price_net = quantize_price(
        line_2_base_total - line_2_order_discount_portion, currency
    )
    line_2_total_price_gross = quantize_price(
        line_2_total_price_net * tax_rate, currency
    )

    shipping_price_net = order.shipping_price_net_amount
    shipping_price_gross = shipping_price_net * tax_rate

    tax_data = TaxData(
        shipping_price_net_amount=shipping_price_net,
        shipping_price_gross_amount=shipping_price_gross,
        shipping_tax_rate=app_tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=line_1_total_price_net,
                total_gross_amount=line_1_total_price_gross,
                tax_rate=app_tax_rate,
            ),
            TaxLineData(
                total_net_amount=line_2_total_price_net,
                total_gross_amount=line_2_total_price_gross,
                tax_rate=app_tax_rate,
            ),
        ],
    )

    manager_methods = {"get_taxes_for_order": Mock(return_value=tax_data)}
    manager = Mock(**manager_methods)

    # when
    order, lines = fetch_order_prices_if_expired(order, manager, None, True)

    # then
    line_1, line_2 = lines
    catalogue_discount = OrderLineDiscount.objects.get()
    order_discount = OrderDiscount.objects.get()

    line_1_base_total = line_1.quantity * line_1.base_unit_price_amount
    line_2_base_total = line_2.quantity * line_2.base_unit_price_amount
    base_total = line_1_base_total + line_2_base_total
    line_1_order_discount_portion = rule_total_reward * line_1_base_total / base_total
    line_2_order_discount_portion = rule_total_reward - line_1_order_discount_portion

    assert order_discount.order == order
    assert order_discount.amount_value == rule_total_reward
    assert order_discount.value == rule_total_reward
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.type == DiscountType.ORDER_PROMOTION
    assert order_discount.reason == f"Promotion: {order_promotion_id}"

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    line_1_total_net_amount = quantize_price(
        line_1.undiscounted_total_price_net_amount - line_1_order_discount_portion,
        currency,
    )
    assert not line_1.discounts.exists()
    assert (
        line_1.undiscounted_total_price_net_amount
        == variant_1_undiscounted_unit_price * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_total_price_net_amount * tax_rate
    )
    assert (
        line_1.undiscounted_unit_price_net_amount == variant_1_undiscounted_unit_price
    )
    assert (
        line_1.undiscounted_unit_price_gross_amount
        == variant_1_undiscounted_unit_price * tax_rate
    )
    assert line_1.base_unit_price_amount == variant_1_undiscounted_unit_price
    assert line_1.total_price_net_amount == line_1_total_net_amount
    assert line_1.total_price_gross_amount == quantize_price(
        line_1_total_net_amount * tax_rate, currency
    )
    assert line_1.unit_price_net_amount == quantize_price(
        line_1_total_net_amount / line_1.quantity, currency
    )
    assert line_1.unit_price_gross_amount == quantize_price(
        line_1.unit_price_net_amount * tax_rate, currency
    )

    # TODO shopx-1531
    # assert line_1.unit_discount_reason == order_discount.reason
    # assert line_1.unit_discount_amount == quantize_price(
    #     line_1_order_discount_portion / line_1.quantity, currency
    # )
    # assert line_1.unit_discount_amount == quantize_price(
    #     line_1.undiscounted_unit_price_net_amount - line_1.unit_price_net_amount,
    #     currency,
    # )

    assert catalogue_discount.line == line_2
    assert catalogue_discount.amount_value == rule_catalogue_reward * line_2.quantity
    assert catalogue_discount.value == rule_catalogue_reward
    assert catalogue_discount.value_type == DiscountValueType.FIXED
    assert catalogue_discount.type == DiscountType.PROMOTION
    assert catalogue_discount.reason == f"Promotion: {catalogue_promotion_id}"

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=order.channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
    line_2_total_net_amount = quantize_price(
        line_2.undiscounted_total_price_net_amount
        - line_2_order_discount_portion
        - catalogue_discount.amount_value,
        currency,
    )
    assert (
        line_2.undiscounted_total_price_net_amount
        == variant_2_undiscounted_unit_price * line_2.quantity
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_total_price_net_amount * tax_rate
    )
    assert (
        line_2.undiscounted_unit_price_net_amount == variant_2_undiscounted_unit_price
    )
    assert (
        line_2.undiscounted_unit_price_gross_amount
        == variant_2_undiscounted_unit_price * tax_rate
    )
    assert (
        line_2.base_unit_price_amount
        == variant_2_undiscounted_unit_price - rule_catalogue_reward
    )
    assert line_2.total_price_net_amount == line_2_total_net_amount
    assert line_2.total_price_gross_amount == quantize_price(
        line_2_total_net_amount * tax_rate, currency
    )
    assert line_2.unit_price_net_amount == quantize_price(
        line_2_total_net_amount / line_2.quantity, currency
    )
    assert line_2.unit_price_gross_amount == quantize_price(
        line_2.unit_price_net_amount * tax_rate, currency
    )

    # TODO shopx-1531
    # assert line_2.unit_discount_reason == "; ".join(
    #     [catalogue_discount.reason, order_discount.reason]
    # )
    # assert line_2.unit_discount_amount == quantize_price(
    #     line_2.undiscounted_unit_price_net_amount - line_2.unit_price_net_amount,
    #     currency,
    # )

    shipping_price = order.shipping_price_net_amount
    total_net_amount = quantize_price(
        order.undiscounted_total_net_amount
        - order_discount.amount_value
        - catalogue_discount.amount_value,
        currency,
    )
    assert (
        order.undiscounted_total_net_amount
        == line_1.undiscounted_total_price_net_amount
        + line_2.undiscounted_total_price_net_amount
        + shipping_price
    )
    assert (
        order.undiscounted_total_gross_amount
        == order.undiscounted_total_net_amount * tax_rate
    )
    assert order.total_net_amount == total_net_amount
    assert order.total_gross_amount == quantize_price(
        total_net_amount * tax_rate, currency
    )
    assert (
        order.subtotal_net_amount == line_1_total_net_amount + line_2_total_net_amount
    )
    assert order.subtotal_gross_amount == quantize_price(
        order.subtotal_net_amount * tax_rate, currency
    )


def test_fetch_order_prices_manual_order_discount_and_line_level_voucher_tax_app(
    order_with_lines,
    voucher,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines
    currency = order.currency
    line_1, line_2 = order.lines.all()

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    voucher_reward = Decimal("4")
    voucher_listing.discount_value = voucher_reward
    voucher_listing.save(update_fields=["discount_value"])

    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type", "apply_once_per_order"])

    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    order.save(update_fields=["voucher", "voucher_code"])

    # create manual order discount
    manual_reward = Decimal("10")
    manual_discount_reason = "Manual discount reason"
    manual_discount = order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=manual_reward,
        name="Manual order discount",
        type=DiscountType.MANUAL,
        reason=manual_discount_reason,
    )

    app_tax_rate = Decimal(10)
    db_tax_rate = app_tax_rate / Decimal(100)
    tax_rate = Decimal(1) + db_tax_rate

    line_1_undiscounted_unit_price_net = line_1.undiscounted_unit_price_net_amount
    line_2_undiscounted_unit_price_net = line_2.undiscounted_unit_price_net_amount
    line_1_undiscounted_unit_price_gross = line_1_undiscounted_unit_price_net * tax_rate
    line_2_undiscounted_unit_price_gross = line_2_undiscounted_unit_price_net * tax_rate

    line_1_undiscounted_total_price_net = (
        line_1.undiscounted_unit_price_net_amount * line_1.quantity
    )
    line_2_undiscounted_total_price_net = (
        line_2.undiscounted_unit_price_net_amount * line_2.quantity
    )
    line_1_undiscounted_total_price_gross = (
        line_1_undiscounted_total_price_net * tax_rate
    )
    line_2_undiscounted_total_price_gross = (
        line_2_undiscounted_total_price_net * tax_rate
    )

    undiscounted_subtotal_net = (
        line_1_undiscounted_total_price_net + line_2_undiscounted_total_price_net
    )
    shipping_base_price = order.shipping_price_net_amount

    line_1_base_unit_price = (
        line_1.undiscounted_unit_price_net_amount - voucher_reward / line_1.quantity
    )
    line_2_base_unit_price = line_2.undiscounted_unit_price_net_amount
    line_1_base_total_price = line_1_base_unit_price * line_1.quantity
    line_2_base_total_price = line_2_base_unit_price * line_2.quantity
    base_subtotal = line_1_base_total_price + line_2_base_total_price
    base_total = base_subtotal + shipping_base_price

    subtotal_discount_portion = quantize_price(
        manual_reward * base_subtotal / base_total, currency
    )
    shipping_discount_portion = manual_reward - subtotal_discount_portion
    line_1_manual_discount_portion = quantize_price(
        subtotal_discount_portion * line_1_base_total_price / base_subtotal, currency
    )
    line_2_manual_discount_portion = quantize_price(
        subtotal_discount_portion - line_1_manual_discount_portion, currency
    )
    line_1_total_price_net = line_1_base_total_price - line_1_manual_discount_portion
    line_2_total_price_net = line_2_base_total_price - line_2_manual_discount_portion
    line_1_total_price_gross = line_1_total_price_net * tax_rate
    line_2_total_price_gross = line_2_total_price_net * tax_rate

    line_1_unit_price_net = quantize_price(
        line_1_total_price_net / line_1.quantity, currency
    )
    line_2_unit_price_net = quantize_price(
        line_2_total_price_net / line_2.quantity, currency
    )
    line_1_unit_price_gross = line_1_unit_price_net * tax_rate
    line_2_unit_price_gross = line_2_unit_price_net * tax_rate

    shipping_price_net = shipping_base_price - shipping_discount_portion
    shipping_price_gross = shipping_price_net * tax_rate
    subtotal_net = line_1_total_price_net + line_2_total_price_net
    subtotal_gross = subtotal_net * tax_rate
    total_net = subtotal_net + shipping_price_net
    total_gross = total_net * tax_rate

    tax_data = TaxData(
        shipping_price_net_amount=shipping_price_net,
        shipping_price_gross_amount=shipping_price_gross,
        shipping_tax_rate=app_tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=line_1_total_price_net,
                total_gross_amount=line_1_total_price_gross,
                tax_rate=app_tax_rate,
            ),
            TaxLineData(
                total_net_amount=line_2_total_price_net,
                total_gross_amount=line_2_total_price_gross,
                tax_rate=app_tax_rate,
            ),
        ],
    )

    manager_methods = {"get_taxes_for_order": Mock(return_value=tax_data)}
    manager = Mock(**manager_methods)

    # when
    order, lines = fetch_order_prices_if_expired(order, manager, None, True)

    # then
    line_1, line_2 = lines
    assert order.total_gross_amount == quantize_price(
        (
            undiscounted_subtotal_net
            + shipping_base_price
            - voucher_reward
            - manual_reward
        )
        * tax_rate,
        currency,
    )

    assert order.shipping_price_net_amount == shipping_price_net
    assert order.shipping_price_gross_amount == shipping_price_gross
    assert order.shipping_tax_rate == db_tax_rate
    assert order.subtotal_net_amount == subtotal_net
    assert order.subtotal_gross_amount == subtotal_gross
    assert order.total_net_amount == total_net
    assert order.total_gross_amount == total_gross

    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1_undiscounted_total_price_net
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1_undiscounted_total_price_gross
    )
    assert (
        line_1.undiscounted_unit_price_net_amount == line_1_undiscounted_unit_price_net
    )
    assert (
        line_1.undiscounted_unit_price_gross_amount
        == line_1_undiscounted_unit_price_gross
    )

    assert line_1.base_unit_price_amount == line_1_base_unit_price
    assert line_1.total_price_net_amount == line_1_total_price_net
    assert line_1.total_price_gross_amount == line_1_total_price_gross
    assert line_1.unit_price_net_amount == quantize_price(
        line_1_unit_price_net, currency
    )
    assert line_1.unit_price_gross_amount == quantize_price(
        line_1_unit_price_gross, currency
    )

    # TODO shopx-1531
    # assert (
    #     line_1.unit_discount_reason
    #     == f"Voucher code: {order.voucher_code}; {manual_discount_reason}"
    # )
    # assert line_1.unit_discount_amount == quantize_price(
    #     line_1_undiscounted_unit_price_net - line_1_unit_price_net, currency
    # )

    assert (
        line_2.undiscounted_total_price_net_amount
        == line_2_undiscounted_total_price_net
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2_undiscounted_total_price_gross
    )
    assert (
        line_2.undiscounted_unit_price_net_amount == line_2_undiscounted_unit_price_net
    )
    assert (
        line_2.undiscounted_unit_price_gross_amount
        == line_2_undiscounted_unit_price_gross
    )

    assert line_2.base_unit_price_amount == line_2_undiscounted_unit_price_net
    assert line_2.total_price_net_amount == line_2_total_price_net
    assert line_2.total_price_gross_amount == line_2_total_price_gross
    assert line_2.unit_price_net_amount == quantize_price(
        line_2_unit_price_net, currency
    )
    assert line_2.unit_price_gross_amount == quantize_price(
        line_2_unit_price_gross, currency
    )

    # TODO shopx-1531
    # assert line_2.unit_discount_reason == manual_discount_reason
    # assert line_2.unit_discount_amount == quantize_price(
    #     line_2_undiscounted_unit_price_net - line_2_unit_price_net, currency
    # )

    manual_discount.refresh_from_db()
    assert manual_discount.amount.amount == manual_reward
    voucher_discount = line_1.discounts.get()
    assert voucher_discount.amount.amount == voucher_reward


def test_fetch_order_prices_manual_line_discount_and_entire_order_voucher_tax_app(
    order_with_lines,
    voucher,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines
    currency = order.currency
    line_1, line_2 = order.lines.all()

    assert voucher.type == VoucherType.ENTIRE_ORDER
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type"])
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    voucher_reward_value = Decimal("20")
    voucher_listing.discount_value = voucher_reward_value
    voucher_listing.save(update_fields=["discount_value"])

    order.voucher = voucher
    code = voucher.codes.first().code
    order.voucher_code = code

    manual_line_discount_value = Decimal("50")
    manual_discount_reason = "Manual line discount"
    manual_line_discount = line_1.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=manual_line_discount_value,
        name="Manual line discount",
        type=DiscountType.MANUAL,
        reason=manual_discount_reason,
    )

    app_tax_rate = Decimal(10)
    db_tax_rate = app_tax_rate / Decimal(100)
    tax_rate = Decimal(1) + db_tax_rate

    line_1_undiscounted_unit_price_net = line_1.undiscounted_unit_price_net_amount
    line_2_undiscounted_unit_price_net = line_2.undiscounted_unit_price_net_amount
    line_1_undiscounted_unit_price_gross = line_1_undiscounted_unit_price_net * tax_rate
    line_2_undiscounted_unit_price_gross = line_2_undiscounted_unit_price_net * tax_rate

    line_1_undiscounted_total_price_net = (
        line_1.undiscounted_unit_price_net_amount * line_1.quantity
    )
    line_2_undiscounted_total_price_net = (
        line_2.undiscounted_unit_price_net_amount * line_2.quantity
    )
    line_1_undiscounted_total_price_gross = (
        line_1_undiscounted_total_price_net * tax_rate
    )
    line_2_undiscounted_total_price_gross = (
        line_2_undiscounted_total_price_net * tax_rate
    )

    undiscounted_subtotal_net = (
        line_1_undiscounted_total_price_net + line_2_undiscounted_total_price_net
    )
    undiscounted_shipping_net = order.undiscounted_base_shipping_price_amount
    undiscounted_total_net = undiscounted_subtotal_net + undiscounted_shipping_net
    undiscounted_total_gross = undiscounted_total_net * tax_rate

    line_1_base_unit_price = line_1.undiscounted_unit_price_net_amount * (
        1 - manual_line_discount_value / 100
    )
    line_2_base_unit_price = line_2.undiscounted_unit_price_net_amount
    line_1_base_total_price = line_1_base_unit_price * line_1.quantity
    line_2_base_total_price = line_2_base_unit_price * line_2.quantity
    manual_line_discount_amount = (
        line_1_undiscounted_total_price_net - line_1_base_total_price
    )

    line_1_voucher_discount_portion = (
        line_1_base_total_price * voucher_reward_value / 100
    )
    line_2_voucher_discount_portion = (
        line_2_base_total_price * voucher_reward_value / 100
    )
    voucher_reward = line_1_voucher_discount_portion + line_2_voucher_discount_portion

    line_1_total_price_net = line_1_base_total_price - line_1_voucher_discount_portion
    line_2_total_price_net = line_2_base_total_price - line_2_voucher_discount_portion
    line_1_total_price_gross = line_1_total_price_net * tax_rate
    line_2_total_price_gross = line_2_total_price_net * tax_rate

    line_1_unit_price_net = line_1_total_price_net / line_1.quantity
    line_2_unit_price_net = line_2_total_price_net / line_2.quantity
    line_1_unit_price_gross = line_1_unit_price_net * tax_rate
    line_2_unit_price_gross = line_2_unit_price_net * tax_rate

    shipping_price_net = undiscounted_shipping_net
    shipping_price_gross = shipping_price_net * tax_rate
    subtotal_net = line_1_total_price_net + line_2_total_price_net
    subtotal_gross = subtotal_net * tax_rate
    total_net = subtotal_net + shipping_price_net
    total_gross = total_net * tax_rate

    tax_data = TaxData(
        shipping_price_net_amount=shipping_price_net,
        shipping_price_gross_amount=shipping_price_gross,
        shipping_tax_rate=app_tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=line_1_total_price_net,
                total_gross_amount=line_1_total_price_gross,
                tax_rate=app_tax_rate,
            ),
            TaxLineData(
                total_net_amount=line_2_total_price_net,
                total_gross_amount=line_2_total_price_gross,
                tax_rate=app_tax_rate,
            ),
        ],
    )

    manager_methods = {"get_taxes_for_order": Mock(return_value=tax_data)}
    manager = Mock(**manager_methods)

    # when
    order, lines = fetch_order_prices_if_expired(order, manager, None, True)

    # then
    line_1, line_2 = lines
    assert order.total_gross_amount == quantize_price(
        (
            undiscounted_subtotal_net
            + shipping_price_net
            - voucher_reward
            - manual_line_discount_amount
        )
        * tax_rate,
        currency,
    )

    assert order.shipping_price_net_amount == shipping_price_net
    assert order.shipping_price_gross_amount == shipping_price_gross
    assert order.shipping_tax_rate == db_tax_rate
    assert order.subtotal_net_amount == subtotal_net
    assert order.subtotal_gross_amount == subtotal_gross
    assert order.total_net_amount == total_net
    assert order.total_gross_amount == total_gross
    assert order.undiscounted_total_net_amount == undiscounted_total_net
    assert order.undiscounted_total_gross_amount == undiscounted_total_gross

    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1_undiscounted_total_price_net
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1_undiscounted_total_price_gross
    )
    assert (
        line_1.undiscounted_unit_price_net_amount == line_1_undiscounted_unit_price_net
    )
    assert (
        line_1.undiscounted_unit_price_gross_amount
        == line_1_undiscounted_unit_price_gross
    )

    assert line_1.base_unit_price_amount == line_1_base_unit_price
    assert line_1.total_price_net_amount == line_1_total_price_net
    assert line_1.total_price_gross_amount == line_1_total_price_gross
    assert line_1.unit_price_net_amount == quantize_price(
        line_1_unit_price_net, currency
    )
    assert line_1.unit_price_gross_amount == quantize_price(
        line_1_unit_price_gross, currency
    )

    # TODO shopx-1531
    # assert (
    #     line_1.unit_discount_reason
    #     == f"{manual_discount_reason}; Voucher code: {order.voucher_code}"
    # )
    # assert line_1.unit_discount_amount == quantize_price(
    #     line_1_undiscounted_unit_price_net - line_1_unit_price_net, currency
    # )

    assert (
        line_2.undiscounted_total_price_net_amount
        == line_2_undiscounted_total_price_net
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2_undiscounted_total_price_gross
    )
    assert (
        line_2.undiscounted_unit_price_net_amount == line_2_undiscounted_unit_price_net
    )
    assert (
        line_2.undiscounted_unit_price_gross_amount
        == line_2_undiscounted_unit_price_gross
    )

    assert line_2.base_unit_price_amount == line_2_undiscounted_unit_price_net
    assert line_2.total_price_net_amount == line_2_total_price_net
    assert line_2.total_price_gross_amount == line_2_total_price_gross
    assert line_2.unit_price_net_amount == quantize_price(
        line_2_unit_price_net, currency
    )
    assert line_2.unit_price_gross_amount == quantize_price(
        line_2_unit_price_gross, currency
    )

    # TODO shopx-1531
    # assert line_2.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    # assert line_2.unit_discount_amount == quantize_price(
    #     line_2_undiscounted_unit_price_net - line_2_unit_price_net, currency
    # )

    manual_line_discount.refresh_from_db()
    assert manual_line_discount.amount.amount == manual_line_discount_amount
    voucher_discount = order.discounts.get()
    assert voucher_discount.amount.amount == voucher_reward


def test_fetch_order_prices_shipping_voucher_and_manual_discount_tax_app(
    order_with_lines,
    voucher,
    tax_configuration_tax_app,
):
    # given
    order = order_with_lines
    currency = order.currency
    line_1, line_2 = order.lines.all()

    voucher.type = VoucherType.SHIPPING
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["type", "discount_value_type"])
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    voucher_discount_amount = Decimal("4")
    voucher_listing.discount_value = voucher_discount_amount
    voucher_listing.save(update_fields=["discount_value"])

    order.voucher = voucher
    code = voucher.codes.first().code
    order.voucher_code = code

    manual_discount_value = Decimal("10")
    manual_discount_reason = "Manual discount reason"
    order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=manual_discount_value,
        name="Manual order discount",
        type=DiscountType.MANUAL,
        currency=currency,
        reason=manual_discount_reason,
    )

    app_tax_rate = Decimal(10)
    db_tax_rate = app_tax_rate / Decimal(100)
    tax_rate = Decimal(1) + db_tax_rate

    line_1_undiscounted_unit_price_net = line_1.undiscounted_unit_price_net_amount
    line_2_undiscounted_unit_price_net = line_2.undiscounted_unit_price_net_amount
    line_1_undiscounted_unit_price_gross = line_1_undiscounted_unit_price_net * tax_rate
    line_2_undiscounted_unit_price_gross = line_2_undiscounted_unit_price_net * tax_rate

    line_1_undiscounted_total_price_net = (
        line_1.undiscounted_unit_price_net_amount * line_1.quantity
    )
    line_2_undiscounted_total_price_net = (
        line_2.undiscounted_unit_price_net_amount * line_2.quantity
    )
    line_1_undiscounted_total_price_gross = (
        line_1_undiscounted_total_price_net * tax_rate
    )
    line_2_undiscounted_total_price_gross = (
        line_2_undiscounted_total_price_net * tax_rate
    )

    undiscounted_subtotal_net = (
        line_1_undiscounted_total_price_net + line_2_undiscounted_total_price_net
    )
    undiscounted_shipping_price_net = order.undiscounted_base_shipping_price_amount
    undiscounted_total_net = undiscounted_shipping_price_net + undiscounted_subtotal_net
    undiscounted_total_gross = undiscounted_total_net * tax_rate

    base_shipping_price = undiscounted_shipping_price_net - voucher_discount_amount
    line_1_base_unit_price = line_1.undiscounted_unit_price_net_amount
    line_2_base_unit_price = line_2.undiscounted_unit_price_net_amount
    line_1_base_total_price = line_1_base_unit_price * line_1.quantity
    line_2_base_total_price = line_2_base_unit_price * line_2.quantity

    base_subtotal = line_1_base_total_price + line_2_base_total_price
    subtotal_discount_portion = manual_discount_value / 100 * base_subtotal
    shipping_discount_portion = manual_discount_value / 100 * base_shipping_price
    manual_discount_amount = subtotal_discount_portion + shipping_discount_portion
    line_1_manual_discount_portion = (
        subtotal_discount_portion * line_1_base_total_price / base_subtotal
    )
    line_2_manual_discount_portion = (
        subtotal_discount_portion - line_1_manual_discount_portion
    )

    line_1_total_price_net = line_1_base_total_price - line_1_manual_discount_portion
    line_2_total_price_net = line_2_base_total_price - line_2_manual_discount_portion
    line_1_total_price_gross = line_1_total_price_net * tax_rate
    line_2_total_price_gross = line_2_total_price_net * tax_rate

    line_1_unit_price_net = line_1_total_price_net / line_1.quantity
    line_2_unit_price_net = line_2_total_price_net / line_2.quantity
    line_1_unit_price_gross = line_1_unit_price_net * tax_rate
    line_2_unit_price_gross = line_2_unit_price_net * tax_rate

    shipping_price_net = base_shipping_price - shipping_discount_portion
    shipping_price_gross = shipping_price_net * tax_rate
    subtotal_net = line_1_total_price_net + line_2_total_price_net
    subtotal_gross = subtotal_net * tax_rate
    total_net = subtotal_net + shipping_price_net
    total_gross = total_net * tax_rate

    tax_data = TaxData(
        shipping_price_net_amount=shipping_price_net,
        shipping_price_gross_amount=shipping_price_gross,
        shipping_tax_rate=app_tax_rate,
        lines=[
            TaxLineData(
                total_net_amount=line_1_total_price_net,
                total_gross_amount=line_1_total_price_gross,
                tax_rate=app_tax_rate,
            ),
            TaxLineData(
                total_net_amount=line_2_total_price_net,
                total_gross_amount=line_2_total_price_gross,
                tax_rate=app_tax_rate,
            ),
        ],
    )

    manager_methods = {"get_taxes_for_order": Mock(return_value=tax_data)}
    manager = Mock(**manager_methods)

    # when
    order, lines = fetch_order_prices_if_expired(order, manager, None, True)

    # then
    line_1, line_2 = lines
    assert order.total_gross_amount == quantize_price(
        (
            undiscounted_subtotal_net
            + undiscounted_shipping_price_net
            - voucher_discount_amount
            - manual_discount_amount
        )
        * tax_rate,
        currency,
    )

    assert order.shipping_price_net_amount == shipping_price_net
    assert order.shipping_price_gross_amount == shipping_price_gross
    assert order.shipping_tax_rate == db_tax_rate
    assert order.subtotal_net_amount == subtotal_net
    assert order.subtotal_gross_amount == subtotal_gross
    assert order.total_net_amount == total_net
    assert order.total_gross_amount == total_gross
    assert order.undiscounted_total_net_amount == undiscounted_total_net
    assert order.undiscounted_total_gross_amount == undiscounted_total_gross

    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1_undiscounted_total_price_net
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1_undiscounted_total_price_gross
    )
    assert (
        line_1.undiscounted_unit_price_net_amount == line_1_undiscounted_unit_price_net
    )
    assert (
        line_1.undiscounted_unit_price_gross_amount
        == line_1_undiscounted_unit_price_gross
    )

    assert line_1.base_unit_price_amount == line_1_base_unit_price
    assert line_1.total_price_net_amount == line_1_total_price_net
    assert line_1.total_price_gross_amount == line_1_total_price_gross
    assert line_1.unit_price_net_amount == quantize_price(
        line_1_unit_price_net, currency
    )
    assert line_1.unit_price_gross_amount == quantize_price(
        line_1_unit_price_gross, currency
    )

    # TODO shopx-1531
    # assert line_1.unit_discount_reason == manual_discount_reason
    # assert line_1.unit_discount_amount == quantize_price(
    #     line_1_undiscounted_unit_price_net - line_1_unit_price_net, currency
    # )

    assert (
        line_2.undiscounted_total_price_net_amount
        == line_2_undiscounted_total_price_net
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2_undiscounted_total_price_gross
    )
    assert (
        line_2.undiscounted_unit_price_net_amount == line_2_undiscounted_unit_price_net
    )
    assert (
        line_2.undiscounted_unit_price_gross_amount
        == line_2_undiscounted_unit_price_gross
    )

    assert line_2.base_unit_price_amount == line_2_undiscounted_unit_price_net
    assert line_2.total_price_net_amount == line_2_total_price_net
    assert line_2.total_price_gross_amount == line_2_total_price_gross
    assert line_2.unit_price_net_amount == quantize_price(
        line_2_unit_price_net, currency
    )
    assert line_2.unit_price_gross_amount == quantize_price(
        line_2_unit_price_gross, currency
    )

    # TODO shopx-1531
    # assert line_2.unit_discount_reason == manual_discount_reason
    # assert line_2.unit_discount_amount == quantize_price(
    #     line_2_undiscounted_unit_price_net - line_2_unit_price_net, currency
    # )

    manual_discount = order.discounts.get(type=DiscountType.MANUAL)
    assert manual_discount.amount.amount == manual_discount_amount

    shipping_voucher_discount = order.discounts.get(type=DiscountType.VOUCHER)
    assert shipping_voucher_discount.amount.amount == voucher_discount_amount


def test_fetch_order_prices_entire_order_voucher_no_tax_data_tax_app(
    order_with_lines,
    voucher,
    tax_configuration_tax_app,
):
    """Test if for empty tax data, Saleor apply correctly net values."""
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    currency = order.currency
    line_1, line_2 = order.lines.all()

    assert voucher.type == VoucherType.ENTIRE_ORDER
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type"])
    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    voucher_reward_value = Decimal("20")
    voucher_listing.discount_value = voucher_reward_value
    voucher_listing.save(update_fields=["discount_value"])

    order.voucher = voucher
    code = voucher.codes.first().code
    order.voucher_code = code

    line_1_undiscounted_unit_price_net = line_1.undiscounted_unit_price_net_amount
    line_2_undiscounted_unit_price_net = line_2.undiscounted_unit_price_net_amount

    line_1_undiscounted_total_price_net = (
        line_1.undiscounted_unit_price_net_amount * line_1.quantity
    )
    line_2_undiscounted_total_price_net = (
        line_2.undiscounted_unit_price_net_amount * line_2.quantity
    )

    undiscounted_subtotal_net = (
        line_1_undiscounted_total_price_net + line_2_undiscounted_total_price_net
    )
    undiscounted_shipping_net = order.undiscounted_base_shipping_price_amount
    undiscounted_total_net = undiscounted_subtotal_net + undiscounted_shipping_net

    line_1_base_unit_price = line_1.undiscounted_unit_price_net_amount
    line_2_base_unit_price = line_2.undiscounted_unit_price_net_amount
    line_1_base_total_price = line_1_base_unit_price * line_1.quantity
    line_2_base_total_price = line_2_base_unit_price * line_2.quantity

    line_1_voucher_discount_portion = (
        line_1_base_total_price * voucher_reward_value / 100
    )
    line_2_voucher_discount_portion = (
        line_2_base_total_price * voucher_reward_value / 100
    )
    voucher_reward = line_1_voucher_discount_portion + line_2_voucher_discount_portion

    line_1_total_price_net = line_1_base_total_price - line_1_voucher_discount_portion
    line_2_total_price_net = line_2_base_total_price - line_2_voucher_discount_portion

    line_1_unit_price_net = line_1_total_price_net / line_1.quantity
    line_2_unit_price_net = line_2_total_price_net / line_2.quantity

    shipping_price_net = undiscounted_shipping_net
    subtotal_net = line_1_total_price_net + line_2_total_price_net
    total_net = subtotal_net + shipping_price_net

    tax_data = {}

    manager_methods = {"get_taxes_for_order": Mock(return_value=tax_data)}
    manager = Mock(**manager_methods)

    # when
    order, lines = fetch_order_prices_if_expired(order, manager, None, True)

    # then
    line_1, line_2 = lines
    assert order.total_gross_amount == quantize_price(
        (undiscounted_subtotal_net + shipping_price_net - voucher_reward),
        currency,
    )

    assert order.shipping_price_net_amount == shipping_price_net
    assert order.shipping_price_gross_amount == shipping_price_net
    assert order.subtotal_net_amount == subtotal_net
    assert order.subtotal_gross_amount == subtotal_net
    assert order.total_net_amount == total_net
    assert order.total_gross_amount == total_net
    assert order.undiscounted_total_net_amount == undiscounted_total_net
    assert order.undiscounted_total_gross_amount == undiscounted_total_net

    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1_undiscounted_total_price_net
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1_undiscounted_total_price_net
    )
    assert (
        line_1.undiscounted_unit_price_net_amount == line_1_undiscounted_unit_price_net
    )
    assert (
        line_1.undiscounted_unit_price_gross_amount
        == line_1_undiscounted_unit_price_net
    )

    assert line_1.base_unit_price_amount == line_1_base_unit_price
    assert line_1.total_price_net_amount == line_1_total_price_net
    assert line_1.total_price_gross_amount == line_1_total_price_net
    assert line_1.unit_price_net_amount == quantize_price(
        line_1_unit_price_net, currency
    )
    assert line_1.unit_price_gross_amount == quantize_price(
        line_1_unit_price_net, currency
    )

    assert (
        line_2.undiscounted_total_price_net_amount
        == line_2_undiscounted_total_price_net
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2_undiscounted_total_price_net
    )
    assert (
        line_2.undiscounted_unit_price_net_amount == line_2_undiscounted_unit_price_net
    )
    assert (
        line_2.undiscounted_unit_price_gross_amount
        == line_2_undiscounted_unit_price_net
    )

    assert line_2.base_unit_price_amount == line_2_undiscounted_unit_price_net
    assert line_2.total_price_net_amount == line_2_total_price_net
    assert line_2.total_price_gross_amount == line_2_total_price_net
    assert line_2.unit_price_net_amount == quantize_price(
        line_2_unit_price_net, currency
    )
    assert line_2.unit_price_gross_amount == quantize_price(
        line_2_unit_price_net, currency
    )

    voucher_discount = order.discounts.get()
    assert voucher_discount.amount.amount == voucher_reward
