import math
from decimal import Decimal

import graphene
import pytest

from ...core.prices import quantize_price
from ...discount import DiscountType, DiscountValueType
from ...discount.models import (
    OrderDiscount,
    OrderLineDiscount,
    PromotionRule,
)
from ...tax import TaxCalculationStrategy
from .. import OrderStatus, calculations


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.status = OrderStatus.UNCONFIRMED
    return order_with_lines


def round_down(price: Decimal) -> Decimal:
    return Decimal(math.floor(price * 100)) / 100


def round_up(price: Decimal) -> Decimal:
    return Decimal(math.ceil(price * 100)) / 100


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
