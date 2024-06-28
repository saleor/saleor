from decimal import Decimal

import before_after
import graphene
import pytest

from ...core.prices import quantize_price
from ...core.taxes import zero_money
from ...discount import DiscountType, DiscountValueType
from ...discount.models import (
    OrderDiscount,
    OrderLineDiscount,
    PromotionRule,
)
from ...tax import TaxCalculationStrategy
from ...tests.utils import round_down, round_up
from .. import OrderStatus, calculations


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.status = OrderStatus.UNCONFIRMED
    return order_with_lines


@pytest.mark.parametrize("create_new_discounts", [True, False])
def test_fetch_order_prices_catalogue_discount_flat_rates(
    order_with_lines_and_catalogue_promotion,
    plugins_manager,
    create_new_discounts,
):
    # given
    if create_new_discounts:
        OrderLineDiscount.objects.all().delete()

    order = order_with_lines_and_catalogue_promotion
    channel = order.channel
    rule = PromotionRule.objects.get()
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    reward_value = rule.reward_value

    tc = channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()
    tax_rate = Decimal("1.23")

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    assert OrderLineDiscount.objects.count() == 1
    assert not OrderDiscount.objects.exists()
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]

    discount = line_1.discounts.get()
    reward_amount = reward_value * line_1.quantity
    assert discount.amount_value == reward_amount
    assert discount.value == reward_value
    assert discount.value_type == DiscountValueType.FIXED
    assert discount.type == DiscountType.PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=channel)
    variant_1_unit_price = variant_1_listing.discounted_price_amount
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    assert variant_1_undiscounted_unit_price - variant_1_unit_price == reward_value

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
    assert (
        line_1.base_unit_price_amount
        == variant_1_undiscounted_unit_price - reward_value
    )
    assert (
        line_1.unit_price_net_amount == variant_1_undiscounted_unit_price - reward_value
    )
    assert line_1.unit_price_gross_amount == line_1.unit_price_net_amount * tax_rate
    assert (
        line_1.total_price_net_amount == line_1.unit_price_net_amount * line_1.quantity
    )
    assert line_1.total_price_gross_amount == line_1.total_price_net_amount * tax_rate

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
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
    assert line_2.base_unit_price_amount == variant_2_undiscounted_unit_price
    assert line_2.unit_price_net_amount == variant_2_undiscounted_unit_price
    assert (
        line_2.unit_price_gross_amount == variant_2_undiscounted_unit_price * tax_rate
    )
    assert line_2.total_price_net_amount == line_2.undiscounted_total_price_net_amount
    assert (
        line_2.total_price_gross_amount == line_2.undiscounted_total_price_gross_amount
    )

    shipping_net_price = order.shipping_price_net_amount
    assert (
        order.undiscounted_total_net_amount
        == line_1.undiscounted_total_price_net_amount
        + line_2.undiscounted_total_price_net_amount
        + shipping_net_price
    )
    assert (
        order.undiscounted_total_gross_amount
        == order.undiscounted_total_net_amount * tax_rate
    )
    assert order.total_net_amount == order.undiscounted_total_net_amount - reward_amount
    assert order.total_gross_amount == order.total_net_amount * tax_rate
    assert order.subtotal_net_amount == order.total_net_amount - shipping_net_price
    assert order.subtotal_gross_amount == order.subtotal_net_amount * tax_rate

    assert line_1.unit_discount_amount == reward_value
    assert line_1.unit_discount_reason == f"Promotion: {promotion_id}"
    assert line_1.unit_discount_type == DiscountValueType.FIXED
    assert line_1.unit_discount_value == reward_value


@pytest.mark.parametrize("create_new_discounts", [True, False])
def test_fetch_order_prices_order_discount_flat_rates(
    order_with_lines_and_order_promotion,
    plugins_manager,
    create_new_discounts,
):
    # given
    if create_new_discounts:
        OrderDiscount.objects.all().delete()

    order = order_with_lines_and_order_promotion
    currency = order.currency
    rule = PromotionRule.objects.get()
    reward_amount = rule.reward_value
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()
    tax_rate = Decimal("1.23")

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    assert not OrderLineDiscount.objects.exists()
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]
    discount = OrderDiscount.objects.get()

    line_1_base_total = line_1.quantity * line_1.base_unit_price_amount
    line_2_base_total = line_2.quantity * line_2.base_unit_price_amount
    base_total = line_1_base_total + line_2_base_total
    line_1_order_discount_portion = reward_amount * line_1_base_total / base_total
    line_2_order_discount_portion = reward_amount - line_1_order_discount_portion

    assert discount.order == order
    assert discount.amount_value == reward_amount
    assert discount.value == reward_amount
    assert discount.value_type == DiscountValueType.FIXED
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    line_1_total_net_amount = quantize_price(
        line_1.undiscounted_total_price_net_amount - line_1_order_discount_portion,
        currency,
    )
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
    assert line_1.total_price_net_amount == line_1_total_net_amount
    assert line_1.total_price_gross_amount == round_down(
        line_1_total_net_amount * tax_rate
    )
    assert line_1.base_unit_price_amount == variant_1_undiscounted_unit_price
    assert line_1.unit_price_net_amount == line_1_total_net_amount / line_1.quantity
    assert line_1.unit_price_gross_amount == quantize_price(
        line_1.unit_price_net_amount * tax_rate, currency
    )

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=order.channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
    line_2_total_net_amount = quantize_price(
        line_2.undiscounted_total_price_net_amount - line_2_order_discount_portion,
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
    assert line_2.total_price_net_amount == line_2_total_net_amount
    assert line_2.total_price_gross_amount == round_up(
        line_2_total_net_amount * tax_rate
    )
    assert line_2.base_unit_price_amount == variant_2_undiscounted_unit_price
    assert line_2.unit_price_net_amount == quantize_price(
        line_2_total_net_amount / line_2.quantity, currency
    )
    assert line_2.unit_price_gross_amount == round_down(
        line_2.unit_price_net_amount * tax_rate
    )

    shipping_price = order.shipping_price_net_amount
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
    assert (
        order.total_net_amount
        == line_1_total_net_amount + line_2_total_net_amount + shipping_price
    )
    assert order.total_gross_amount == order.total_net_amount * tax_rate
    assert (
        order.subtotal_net_amount == line_1_total_net_amount + line_2_total_net_amount
    )
    assert order.subtotal_gross_amount == order.subtotal_net_amount * tax_rate


@pytest.mark.parametrize("create_new_discounts", [True, False])
def test_fetch_order_prices_gift_discount_flat_rates(
    order_with_lines_and_gift_promotion,
    plugins_manager,
    create_new_discounts,
):
    # given
    if create_new_discounts:
        OrderLineDiscount.objects.all().delete()

    order = order_with_lines_and_gift_promotion
    rule = PromotionRule.objects.get()
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()
    tax_rate = Decimal("1.23")

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    assert len(lines) == 3
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]
    gift_line = [line for line in lines if line.is_gift][0]
    assert not line_1.discounts.exists()
    assert not line_2.discounts.exists()
    discount = OrderLineDiscount.objects.get()

    variant_gift = gift_line.variant
    variant_gift_listing = variant_gift.channel_listings.get(channel=order.channel)
    variant_gift_undiscounted_unit_price = variant_gift_listing.price_amount

    assert discount.line == gift_line
    assert discount.amount_value == variant_gift_undiscounted_unit_price
    assert discount.value == variant_gift_undiscounted_unit_price
    assert discount.value_type == DiscountValueType.FIXED
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"

    assert gift_line.unit_discount_amount == variant_gift_undiscounted_unit_price
    assert gift_line.unit_discount_reason == f"Promotion: {promotion_id}"
    assert gift_line.unit_discount_type == DiscountValueType.FIXED
    assert gift_line.unit_discount_value == variant_gift_undiscounted_unit_price
    assert gift_line.undiscounted_total_price_net_amount == Decimal(0)
    assert gift_line.undiscounted_total_price_gross_amount == Decimal(0)
    assert gift_line.undiscounted_unit_price_net_amount == Decimal(0)
    assert gift_line.undiscounted_unit_price_gross_amount == Decimal(0)
    assert gift_line.total_price_net_amount == Decimal(0)
    assert gift_line.total_price_gross_amount == Decimal(0)
    assert gift_line.base_unit_price_amount == Decimal(0)
    assert gift_line.unit_price_net_amount == Decimal(0)
    assert gift_line.unit_price_gross_amount == Decimal(0)

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
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
    assert line_1.total_price_net_amount == line_1.undiscounted_total_price_net_amount
    assert (
        line_1.total_price_gross_amount == line_1.undiscounted_total_price_gross_amount
    )
    assert line_1.base_unit_price_amount == line_1.undiscounted_unit_price_net_amount
    assert line_1.unit_price_net_amount == line_1.undiscounted_unit_price_net_amount
    assert line_1.unit_price_gross_amount == line_1.undiscounted_unit_price_gross_amount

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=order.channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
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
    assert line_2.total_price_net_amount == line_2.undiscounted_total_price_net_amount
    assert (
        line_2.total_price_gross_amount == line_2.undiscounted_total_price_gross_amount
    )
    assert line_2.base_unit_price_amount == line_2.undiscounted_unit_price_net_amount
    assert line_2.unit_price_net_amount == line_2.undiscounted_unit_price_net_amount
    assert line_2.unit_price_gross_amount == line_2.undiscounted_unit_price_gross_amount

    shipping_price = order.shipping_price_net_amount
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
    assert order.total_net_amount == order.undiscounted_total_net_amount
    assert order.total_gross_amount == order.undiscounted_total_gross_amount
    assert (
        order.subtotal_net_amount
        == line_1.undiscounted_total_price_net_amount
        + line_2.undiscounted_total_price_net_amount
    )
    assert order.subtotal_gross_amount == order.subtotal_net_amount * tax_rate


def test_fetch_order_prices_catalogue_and_order_discounts_flat_rates(
    draft_order_and_promotions,
    plugins_manager,
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

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()
    tax_rate = Decimal("1.23")

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]
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
    assert line_1.total_price_gross_amount == round_up(
        line_1_total_net_amount * tax_rate
    )
    assert line_1.unit_price_net_amount == quantize_price(
        line_1_total_net_amount / line_1.quantity, currency
    )
    assert line_1.unit_price_gross_amount == round_up(
        line_1.unit_price_net_amount * tax_rate
    )

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
    assert line_2.total_price_gross_amount == round_down(
        line_2_total_net_amount * tax_rate
    )
    assert line_2.unit_price_net_amount == quantize_price(
        line_2_total_net_amount / line_2.quantity, currency
    )
    assert line_2.unit_price_gross_amount == quantize_price(
        line_2.unit_price_net_amount * tax_rate, currency
    )

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


def test_fetch_order_prices_catalogue_and_gift_discounts_flat_rates(
    draft_order_and_promotions,
    plugins_manager,
):
    # given
    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    rule_total.reward_value = Decimal(0)
    rule_total.save(update_fields=["reward_value"])

    catalogue_promotion_id = graphene.Node.to_global_id(
        "Promotion", rule_catalogue.promotion_id
    )
    gift_promotion_id = graphene.Node.to_global_id("Promotion", rule_gift.promotion_id)
    rule_catalogue_reward = rule_catalogue.reward_value
    currency = order.currency

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()
    tax_rate = Decimal("1.23")

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    assert len(lines) == 3
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]
    gift_line = [line for line in lines if line.is_gift][0]

    assert OrderLineDiscount.objects.count() == 2
    gift_discount = gift_line.discounts.get()
    catalogue_discount = line_2.discounts.get()

    variant_gift = gift_line.variant
    variant_gift_listing = variant_gift.channel_listings.get(channel=order.channel)
    variant_gift_undiscounted_unit_price = variant_gift_listing.price_amount

    assert gift_discount.line == gift_line
    assert gift_discount.amount_value == variant_gift_undiscounted_unit_price
    assert gift_discount.value == variant_gift_undiscounted_unit_price
    assert gift_discount.value_type == DiscountValueType.FIXED
    assert gift_discount.type == DiscountType.ORDER_PROMOTION
    assert gift_discount.reason == f"Promotion: {gift_promotion_id}"

    assert gift_line.unit_discount_amount == variant_gift_undiscounted_unit_price
    assert gift_line.unit_discount_reason == f"Promotion: {gift_promotion_id}"
    assert gift_line.unit_discount_type == DiscountValueType.FIXED
    assert gift_line.unit_discount_value == variant_gift_undiscounted_unit_price
    assert gift_line.undiscounted_total_price_net_amount == Decimal(0)
    assert gift_line.undiscounted_total_price_gross_amount == Decimal(0)
    assert gift_line.undiscounted_unit_price_net_amount == Decimal(0)
    assert gift_line.undiscounted_unit_price_gross_amount == Decimal(0)
    assert gift_line.total_price_net_amount == Decimal(0)
    assert gift_line.total_price_gross_amount == Decimal(0)
    assert gift_line.base_unit_price_amount == Decimal(0)
    assert gift_line.unit_price_net_amount == Decimal(0)
    assert gift_line.unit_price_gross_amount == Decimal(0)

    assert not line_1.discounts.exists()
    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    line_1_total_net_amount = line_1.undiscounted_total_price_net_amount
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
    assert line_1.total_price_net_amount == line_1.undiscounted_total_price_net_amount
    assert (
        line_1.total_price_gross_amount == line_1.undiscounted_total_price_gross_amount
    )
    assert line_1.base_unit_price_amount == line_1.undiscounted_unit_price_net_amount
    assert line_1.unit_price_net_amount == line_1.undiscounted_unit_price_net_amount
    assert line_1.unit_price_gross_amount == line_1.undiscounted_unit_price_gross_amount

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
        line_2.undiscounted_total_price_net_amount - catalogue_discount.amount_value,
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
    assert (
        line_2.unit_price_net_amount
        == variant_2_undiscounted_unit_price - rule_catalogue_reward
    )
    assert line_2.unit_price_gross_amount == quantize_price(
        line_2.unit_price_net_amount * tax_rate, currency
    )

    shipping_price = order.shipping_price_net_amount
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
    total_net_amount = quantize_price(
        order.undiscounted_total_net_amount - catalogue_discount.amount_value,
        currency,
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


def test_fetch_order_prices_catalogue_and_order_discounts_exceed_total_flat_rates(
    draft_order_and_promotions,
    plugins_manager,
):
    # given
    order, rule_catalogue, rule_total, _ = draft_order_and_promotions
    rule_total.reward_value = Decimal(100000)
    rule_total.save(update_fields=["reward_value"])
    catalogue_promotion_id = graphene.Node.to_global_id(
        "Promotion", rule_catalogue.promotion_id
    )
    order_promotion_id = graphene.Node.to_global_id(
        "Promotion", rule_total.promotion_id
    )
    rule_catalogue_reward = rule_catalogue.reward_value
    currency = order.currency

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()
    tax_rate = Decimal("1.23")

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]
    catalogue_discount = OrderLineDiscount.objects.get()
    order_discount = OrderDiscount.objects.get()

    shipping_price = order.shipping_price_net_amount
    rule_total_reward = quantize_price(
        order.undiscounted_total_net_amount
        - shipping_price
        - rule_catalogue_reward * line_2.quantity,
        currency,
    )
    assert order_discount.order == order
    assert order_discount.amount_value == rule_total_reward
    assert order_discount.value == rule_total.reward_value
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.type == DiscountType.ORDER_PROMOTION
    assert order_discount.reason == f"Promotion: {order_promotion_id}"

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
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
    assert line_1.total_price_net_amount == Decimal(0)
    assert line_1.total_price_gross_amount == Decimal(0)
    assert line_1.unit_price_net_amount == Decimal(0)
    assert line_1.unit_price_gross_amount == Decimal(0)

    assert catalogue_discount.line == line_2
    assert catalogue_discount.amount_value == rule_catalogue_reward * line_2.quantity
    assert catalogue_discount.value == rule_catalogue_reward
    assert catalogue_discount.value_type == DiscountValueType.FIXED
    assert catalogue_discount.type == DiscountType.PROMOTION
    assert catalogue_discount.reason == f"Promotion: {catalogue_promotion_id}"

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=order.channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
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
    assert line_2.total_price_net_amount == Decimal(0)
    assert line_2.total_price_gross_amount == Decimal(0)
    assert line_2.unit_price_net_amount == Decimal(0)
    assert line_2.unit_price_gross_amount == Decimal(0)

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
    assert order.total_net_amount == shipping_price
    assert order.total_gross_amount == shipping_price * tax_rate
    assert order.subtotal_net_amount == Decimal(0)
    assert order.subtotal_gross_amount == Decimal(0)


def test_fetch_order_prices_manual_discount_and_order_discount_flat_rates(
    order_with_lines_and_order_promotion,
    plugins_manager,
):
    # given
    order = order_with_lines_and_order_promotion
    assert OrderDiscount.objects.exists()
    currency = order.currency

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()
    tax_rate = Decimal("1.23")

    discount_value = Decimal("50")
    manual_discount = order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=discount_value,
        name="Manual order discount",
        type=DiscountType.MANUAL,
    )

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    assert not OrderLineDiscount.objects.exists()
    assert OrderDiscount.objects.count() == 1
    manual_discount.refresh_from_db()

    assert manual_discount.order == order
    assert manual_discount.amount_value == Decimal(
        order.undiscounted_total_net_amount / 2
    )
    assert manual_discount.value == discount_value
    assert manual_discount.value_type == DiscountValueType.PERCENTAGE
    assert manual_discount.type == DiscountType.MANUAL
    assert not manual_discount.reason

    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    line_1_total_net_amount = quantize_price(
        line_1.undiscounted_total_price_net_amount * discount_value / 100, currency
    )

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

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=order.channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
    line_2_total_net_amount = quantize_price(
        line_2.undiscounted_total_price_net_amount * discount_value / 100, currency
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
    assert line_2.base_unit_price_amount == variant_2_undiscounted_unit_price
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

    undiscounted_shipping_price = order.base_shipping_price_amount
    total_net_amount = quantize_price(
        order.undiscounted_total_net_amount * discount_value / 100, currency
    )
    assert (
        order.undiscounted_total_net_amount
        == line_1.undiscounted_total_price_net_amount
        + line_2.undiscounted_total_price_net_amount
        + undiscounted_shipping_price
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


def test_fetch_order_prices_manual_discount_and_gift_discount_flat_rates(
    order_with_lines_and_gift_promotion,
    plugins_manager,
):
    # given
    order = order_with_lines_and_gift_promotion
    assert OrderLineDiscount.objects.exists()
    currency = order.currency

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()
    tax_rate = Decimal("1.23")

    discount_value = Decimal("50")
    manual_discount = order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=discount_value,
        name="Manual order discount",
        type=DiscountType.MANUAL,
    )

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    assert not OrderLineDiscount.objects.exists()
    assert OrderDiscount.objects.count() == 1
    assert len(lines) == 2
    manual_discount.refresh_from_db()

    assert manual_discount.order == order
    assert manual_discount.amount_value == Decimal(
        order.undiscounted_total_net_amount / 2
    )
    assert manual_discount.value == discount_value
    assert manual_discount.value_type == DiscountValueType.PERCENTAGE
    assert manual_discount.type == DiscountType.MANUAL
    assert not manual_discount.reason

    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]
    assert not [line for line in lines if line.is_gift]

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    line_1_total_net_amount = quantize_price(
        line_1.undiscounted_total_price_net_amount * discount_value / 100, currency
    )

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

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=order.channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
    line_2_total_net_amount = quantize_price(
        line_2.undiscounted_total_price_net_amount * discount_value / 100, currency
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
    assert line_2.base_unit_price_amount == variant_2_undiscounted_unit_price
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

    undiscounted_shipping_price = order.base_shipping_price_amount
    total_net_amount = quantize_price(
        order.undiscounted_total_net_amount * discount_value / 100, currency
    )
    assert (
        order.undiscounted_total_net_amount
        == line_1.undiscounted_total_price_net_amount
        + line_2.undiscounted_total_price_net_amount
        + undiscounted_shipping_price
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
    assert (
        order.shipping_price_net_amount
        == undiscounted_shipping_price * discount_value / 100
    )
    assert order.shipping_price_gross_amount == quantize_price(
        order.shipping_price_net_amount * tax_rate, currency
    )


def test_fetch_order_prices_manual_discount_and_catalogue_discount_flat_rates(
    order_with_lines_and_catalogue_promotion,
    plugins_manager,
):
    # given
    order = order_with_lines_and_catalogue_promotion
    currency = order.currency
    rule = PromotionRule.objects.get()
    rule_catalogue_reward = rule.reward_value
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()
    tax_rate = Decimal("1.23")

    manual_discount_value = Decimal("50")
    manual_discount = order.discounts.create(
        value_type=DiscountValueType.PERCENTAGE,
        value=manual_discount_value,
        name="Manual order discount",
        type=DiscountType.MANUAL,
    )

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    catalogue_discount = OrderLineDiscount.objects.get()
    assert OrderDiscount.objects.count() == 1

    manual_discount.refresh_from_db()
    manual_discount_amount = Decimal(
        (order.undiscounted_total_net_amount - catalogue_discount.amount_value)
        * manual_discount_value
        / 100
    )
    assert manual_discount.order == order
    assert manual_discount.amount_value == manual_discount_amount
    assert manual_discount.value == manual_discount_value
    assert manual_discount.value_type == DiscountValueType.PERCENTAGE
    assert manual_discount.type == DiscountType.MANUAL
    assert not manual_discount.reason

    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]

    assert catalogue_discount.line == line_1
    assert catalogue_discount.amount_value == rule_catalogue_reward * line_1.quantity
    assert catalogue_discount.value == rule_catalogue_reward
    assert catalogue_discount.value_type == DiscountValueType.FIXED
    assert catalogue_discount.type == DiscountType.PROMOTION
    assert catalogue_discount.reason == f"Promotion: {promotion_id}"

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    line_1_total_net_amount = quantize_price(
        (variant_1_undiscounted_unit_price - rule_catalogue_reward)
        * line_1.quantity
        * manual_discount_value
        / 100,
        currency,
    )
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
    assert (
        line_1.base_unit_price_amount
        == variant_1_undiscounted_unit_price - rule_catalogue_reward
    )
    assert line_1.total_price_net_amount == line_1_total_net_amount
    assert line_1.total_price_gross_amount == quantize_price(
        line_1_total_net_amount * tax_rate, currency
    )
    assert line_1.unit_price_net_amount == quantize_price(
        line_1_total_net_amount / line_1.quantity, currency
    )
    assert line_1.unit_price_gross_amount == round_up(
        line_1.unit_price_net_amount * tax_rate
    )
    assert line_1.unit_discount_amount == rule_catalogue_reward
    assert line_1.unit_discount_reason == f"Promotion: {promotion_id}"
    assert line_1.unit_discount_value == rule_catalogue_reward
    assert line_1.unit_discount_type == DiscountValueType.FIXED

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=order.channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
    line_2_total_net_amount = quantize_price(
        line_2.undiscounted_total_price_net_amount * manual_discount_value / 100,
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
    assert line_2.base_unit_price_amount == variant_2_undiscounted_unit_price
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

    undiscounted_shipping_price = order.base_shipping_price_amount
    total_net_amount = quantize_price(
        (order.undiscounted_total_net_amount - catalogue_discount.amount_value)
        * manual_discount_value
        / 100,
        currency,
    )
    assert (
        order.undiscounted_total_net_amount
        == line_1.undiscounted_total_price_net_amount
        + line_2.undiscounted_total_price_net_amount
        + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross_amount
        == order.undiscounted_total_net_amount * tax_rate
    )
    assert order.total_net_amount == total_net_amount
    assert order.total_gross_amount == round_up(total_net_amount * tax_rate)
    assert (
        order.subtotal_net_amount == line_1_total_net_amount + line_2_total_net_amount
    )
    assert order.subtotal_gross_amount == quantize_price(
        order.subtotal_net_amount * tax_rate, currency
    )
    assert (
        order.shipping_price_net_amount
        == undiscounted_shipping_price * manual_discount_value / 100
    )
    assert order.shipping_price_gross_amount == quantize_price(
        order.shipping_price_net_amount * tax_rate, currency
    )


def test_fetch_order_prices_manual_line_discount_and_catalogue_discount_flat_rates(
    order_with_lines_and_catalogue_promotion,
    plugins_manager,
):
    # given
    order = order_with_lines_and_catalogue_promotion

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

    line_1 = order.lines.get(quantity=3)
    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)

    manual_discount_value = Decimal("5")
    manual_discount_value_type = DiscountValueType.FIXED
    manual_discount_reason = "Manual line discount"
    manual_discount = line_1.discounts.create(
        value_type=manual_discount_value_type,
        value=manual_discount_value,
        name="Manual order line discount",
        type=DiscountType.MANUAL,
        reason=manual_discount_reason,
    )

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    assert OrderLineDiscount.objects.count() == 1
    assert not OrderDiscount.objects.exists()
    manual_discount.refresh_from_db()

    line_1 = [line for line in lines if line.quantity == 3][0]

    assert (
        line_1.base_unit_price_amount
        == variant_1_listing.price_amount - manual_discount_value
    )
    assert manual_discount.line == line_1
    assert manual_discount.value == manual_discount_value
    assert manual_discount.value_type == manual_discount_value_type
    assert manual_discount.type == DiscountType.MANUAL
    assert manual_discount.reason == manual_discount_reason

    line_1_total_net_amount = quantize_price(
        (variant_1_listing.price_amount - manual_discount_value) * line_1.quantity,
        order.currency,
    )
    assert line_1.total_price_net_amount == line_1_total_net_amount


def test_fetch_order_prices_voucher_specific_product_fixed(
    order_with_lines, voucher_specific_product_type, plugins_manager
):
    # given
    order = order_with_lines
    voucher = voucher_specific_product_type

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    unit_discount_amount = Decimal("5")
    voucher_listing.discount_value = unit_discount_amount
    voucher_listing.save(update_fields=["discount_value"])
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type"])

    lines = order.lines.all()
    discounted_line, line_1 = lines
    voucher.variants.add(discounted_line.variant)
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    discounted_line, line_1 = lines
    discount_amount = unit_discount_amount * discounted_line.quantity
    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price
    assert order.subtotal_net_amount == subtotal.amount - discount_amount
    assert order.subtotal_gross_amount == subtotal.amount - discount_amount
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price

    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.base_unit_price_amount * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1
    line_discount = discounted_line.discounts.first()
    assert line_discount.amount_value == discount_amount
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == discount_amount


def test_fetch_order_prices_voucher_specific_product_discount_line_object_updated(
    order_with_lines, voucher_specific_product_type, plugins_manager
):
    # given
    order = order_with_lines
    voucher = voucher_specific_product_type

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    unit_discount_amount = Decimal("5")
    voucher_listing.discount_value = unit_discount_amount
    voucher_listing.save(update_fields=["discount_value"])
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type"])

    lines = order.lines.all()
    discounted_line, line_1 = lines
    voucher.variants.add(discounted_line.variant)
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    line_discount = discounted_line.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=Decimal("0"),
        name="Manual line discount",
        type=DiscountType.VOUCHER,
    )

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    discounted_line, line_1 = lines
    discount_amount = unit_discount_amount * discounted_line.quantity
    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price
    assert order.subtotal_net_amount == subtotal.amount - discount_amount
    assert order.subtotal_gross_amount == subtotal.amount - discount_amount
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price

    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.base_unit_price_amount * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1
    line_discount.refresh_from_db()
    assert line_discount.amount_value == discount_amount
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == discount_amount


def test_fetch_order_prices_voucher_specific_product_percentage(
    order_with_lines, voucher_specific_product_type, plugins_manager
):
    # given
    order = order_with_lines
    voucher = voucher_specific_product_type

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_value = Decimal("10")
    voucher_listing.discount_value = discount_value
    voucher_listing.save(update_fields=["discount_value"])
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type"])

    lines = order.lines.all()
    discounted_line, line_1 = lines
    voucher.variants.add(discounted_line.variant)
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    discounted_line, line_1 = lines
    discount_amount = (
        discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
        * discount_value
        / 100
    )
    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price
    assert order.subtotal_net_amount == subtotal.amount - discount_amount
    assert order.subtotal_gross_amount == subtotal.amount - discount_amount
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price

    unit_discount_amount = discount_amount / discounted_line.quantity
    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.base_unit_price_amount * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1
    line_discount = discounted_line.discounts.first()
    assert line_discount.amount_value == discount_amount
    # TODO: should be from voucher probably
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == discount_amount


def test_fetch_order_prices_voucher_apply_once_per_order_fixed(
    order_with_lines, voucher, plugins_manager
):
    # given
    order = order_with_lines

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = Decimal("5")
    voucher_listing.discount_value = discount_amount
    voucher_listing.save(update_fields=["discount_value"])

    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type", "apply_once_per_order"])

    lines = order.lines.all()
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    discounted_line, line_1 = lines
    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price
    assert order.subtotal_net_amount == subtotal.amount - discount_amount
    assert order.subtotal_gross_amount == subtotal.amount - discount_amount
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price

    unit_discount_amount = discount_amount / discounted_line.quantity
    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.base_unit_price_amount * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1
    line_discount = discounted_line.discounts.first()
    assert line_discount.amount_value == discount_amount
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == discount_amount


def test_fetch_order_prices_voucher_apply_once_per_order_percentage(
    order_with_lines, voucher, plugins_manager
):
    # given
    order = order_with_lines

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_value = Decimal("10")
    voucher_listing.discount_value = discount_value
    voucher_listing.save(update_fields=["discount_value"])

    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type", "apply_once_per_order"])

    lines = order.lines.all()
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    discounted_line, line_1 = lines
    discount_amount = (
        discounted_line.undiscounted_base_unit_price_amount * discount_value / 100
    )
    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price
    assert order.subtotal_net_amount == subtotal.amount - discount_amount
    assert order.subtotal_gross_amount == subtotal.amount - discount_amount
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price

    unit_discount_amount = discount_amount / discounted_line.quantity
    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.base_unit_price_amount * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1
    line_discount = discounted_line.discounts.first()
    assert line_discount.amount_value == discount_amount
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == discount_amount


def test_fetch_order_prices_manual_order_discount_voucher_specific_product(
    order_with_lines, voucher_specific_product_type, plugins_manager
):
    # given
    order = order_with_lines
    voucher = voucher_specific_product_type

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    unit_discount_amount = Decimal("2")
    voucher_listing.discount_value = unit_discount_amount
    voucher_listing.save(update_fields=["discount_value"])

    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type"])

    lines = order.lines.all()
    discounted_line, line_1 = lines
    voucher.variants.add(discounted_line.variant)
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    # create manual order discount
    order_discount_amount = Decimal("10")
    order_discount = order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=order_discount_amount,
        name="Manual order discount",
        type=DiscountType.MANUAL,
    )

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    discounted_line, line_1 = lines
    voucher_discount_amount = unit_discount_amount * discounted_line.quantity
    assert (
        order.total_gross_amount
        == subtotal.amount
        + shipping_price.amount
        - voucher_discount_amount
        - order_discount_amount
    )
    shipping_discount = shipping_price - order.shipping_price_gross
    subtotal_order_discount = order_discount_amount - shipping_discount.amount
    assert (
        order.subtotal_gross_amount
        == subtotal.amount - subtotal_order_discount - voucher_discount_amount
    )
    assert order.undiscounted_total_gross == subtotal + shipping_price
    assert order.shipping_price_gross == shipping_price - shipping_discount
    assert order.base_shipping_price == shipping_price

    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.unit_price_gross_amount * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == order.subtotal_gross_amount - discounted_line.total_price_gross_amount
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    order_discount.refresh_from_db()
    assert order_discount.amount_value == order_discount_amount

    assert discounted_line.discounts.count() == 1
    line_discount = discounted_line.discounts.first()
    assert line_discount.amount_value == voucher_discount_amount
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == voucher_discount_amount


def test_fetch_order_prices_manual_order_discount_and_voucher_apply_once_per_order(
    order_with_lines, voucher, plugins_manager
):
    # given
    order = order_with_lines

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = Decimal("3")
    voucher_listing.discount_value = discount_amount
    voucher_listing.save(update_fields=["discount_value"])

    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type", "apply_once_per_order"])

    lines = order.lines.all()
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    # create manual order discount
    order_discount_amount = Decimal("10")
    order_discount = order.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=order_discount_amount,
        name="Manual order discount",
        type=DiscountType.MANUAL,
    )

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    discounted_line, line_1 = lines
    voucher_discount_amount = discount_amount
    assert (
        order.total_gross_amount
        == subtotal.amount
        + shipping_price.amount
        - voucher_discount_amount
        - order_discount_amount
    )
    shipping_discount = shipping_price - order.shipping_price_gross
    subtotal_order_discount = order_discount_amount - shipping_discount.amount
    assert (
        order.subtotal_gross_amount
        == subtotal.amount - subtotal_order_discount - voucher_discount_amount
    )
    assert order.undiscounted_total_gross == subtotal + shipping_price
    assert order.shipping_price_gross == shipping_price - shipping_discount
    assert order.base_shipping_price == shipping_price

    unit_discount_amount = discount_amount / discounted_line.quantity
    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.unit_price_gross_amount * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == order.subtotal_gross_amount - discounted_line.total_price_gross_amount
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    order_discount.refresh_from_db()
    assert order_discount.amount_value == order_discount_amount

    assert discounted_line.discounts.count() == 1
    line_discount = discounted_line.discounts.first()
    assert line_discount.amount_value == voucher_discount_amount
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == voucher_discount_amount


def test_fetch_order_prices_manual_line_discount_voucher_specific_product(
    order_with_lines, voucher_specific_product_type, plugins_manager
):
    # given
    order = order_with_lines
    voucher = voucher_specific_product_type

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    unit_discount_amount = Decimal("2")
    voucher_listing.discount_value = unit_discount_amount
    voucher_listing.save(update_fields=["discount_value"])

    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type"])

    lines = order.lines.all()
    discounted_line, line_1 = lines
    voucher.variants.add(discounted_line.variant)
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    # create manual order line discount
    manual_line_discount_amount = Decimal("3")
    manual_line_discount = discounted_line.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=manual_line_discount_amount,
        name="Manual line discount",
        type=DiscountType.MANUAL,
    )

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    discounted_line.refresh_from_db()
    line_1.refresh_from_db()
    voucher_discount_amount = unit_discount_amount * discounted_line.quantity
    manual_discount_amount = manual_line_discount_amount * discounted_line.quantity
    assert (
        order.total_gross_amount
        == subtotal.amount
        + shipping_price.amount
        - voucher_discount_amount
        - manual_discount_amount
    )
    assert (
        order.subtotal_gross_amount
        == subtotal.amount - manual_discount_amount - voucher_discount_amount
    )
    assert order.undiscounted_total_gross == subtotal + shipping_price
    assert order.shipping_price_gross == shipping_price
    assert order.base_shipping_price == shipping_price

    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount
        - unit_discount_amount
        - manual_line_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.unit_price_gross_amount * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert (
        discounted_line.unit_discount_amount
        == unit_discount_amount + manual_line_discount_amount
    )
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == order.subtotal_gross_amount - discounted_line.total_price_gross_amount
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 2
    voucher_line_discount = discounted_line.discounts.get(type=DiscountType.VOUCHER)
    assert voucher_line_discount.amount_value == voucher_discount_amount
    assert voucher_line_discount.value_type == DiscountValueType.FIXED
    assert voucher_line_discount.type == DiscountType.VOUCHER
    assert voucher_line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert voucher_line_discount.value == voucher_discount_amount

    manual_line_discount.refresh_from_db()
    assert manual_line_discount.amount_value == manual_discount_amount
    assert manual_line_discount.type == DiscountType.MANUAL


def test_fetch_order_prices_manual_line_discount_and_voucher_apply_once_per_order(
    order_with_lines, voucher, plugins_manager
):
    # given
    order = order_with_lines

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = Decimal("3")
    voucher_listing.discount_value = discount_amount
    voucher_listing.save(update_fields=["discount_value"])

    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type", "apply_once_per_order"])

    lines = order.lines.all()
    discounted_line, line_1 = lines
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    # create manual order line discount
    manual_line_discount_amount = Decimal("3")
    manual_line_discount = discounted_line.discounts.create(
        value_type=DiscountValueType.FIXED,
        value=manual_line_discount_amount,
        name="Manual line discount",
        type=DiscountType.MANUAL,
        reason="Manual line discount",
    )

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    discounted_line.refresh_from_db()
    line_1.refresh_from_db()
    voucher_discount_amount = discount_amount
    manual_discount_amount = manual_line_discount_amount * discounted_line.quantity
    assert (
        order.total_gross_amount
        == subtotal.amount
        + shipping_price.amount
        - voucher_discount_amount
        - manual_discount_amount
    )
    shipping_discount = shipping_price - order.shipping_price_gross
    subtotal_order_discount = manual_discount_amount - shipping_discount.amount
    assert (
        order.subtotal_gross_amount
        == subtotal.amount - subtotal_order_discount - voucher_discount_amount
    )
    assert order.undiscounted_total_gross == subtotal + shipping_price
    assert order.shipping_price_gross == shipping_price - shipping_discount
    assert order.base_shipping_price == shipping_price

    unit_discount_amount = discount_amount / discounted_line.quantity
    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount
        - unit_discount_amount
        - manual_line_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.unit_price_gross_amount * discounted_line.quantity
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
    )
    assert (
        discounted_line.unit_discount_amount
        == manual_line_discount_amount + unit_discount_amount
    )
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert (
        discounted_line.unit_discount_reason
        == f"{manual_line_discount.reason}; Voucher code: {order.voucher_code}"
    )

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == order.subtotal_gross_amount - discounted_line.total_price_gross_amount
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 2
    voucher_line_discount = discounted_line.discounts.get(type=DiscountType.VOUCHER)
    assert voucher_line_discount.amount_value == voucher_discount_amount
    assert voucher_line_discount.value_type == DiscountValueType.FIXED
    assert voucher_line_discount.type == DiscountType.VOUCHER
    assert voucher_line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert voucher_line_discount.value == voucher_discount_amount

    manual_line_discount.refresh_from_db()
    assert manual_line_discount.amount_value == manual_discount_amount
    assert manual_line_discount.type == DiscountType.MANUAL


def test_fetch_order_prices_catalogue_discount_race_condition(
    order_with_lines_and_catalogue_promotion,
    plugins_manager,
):
    # given
    order = order_with_lines_and_catalogue_promotion
    OrderLineDiscount.objects.all().delete()

    # when
    def call_before_creating_catalogue_line_discount(*args, **kwargs):
        calculations.fetch_order_prices_if_expired(order, plugins_manager, None, True)

    with before_after.before(
        "saleor.discount.utils.promotion."
        "prepare_line_discount_objects_for_catalogue_promotions",
        call_before_creating_catalogue_line_discount,
    ):
        calculations.fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    assert OrderLineDiscount.objects.count() == 1
