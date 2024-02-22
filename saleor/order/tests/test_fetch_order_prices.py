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

    tc = channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

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

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=channel)
    variant_1_unit_price = variant_1_listing.discounted_price_amount
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    assert variant_1_undiscounted_unit_price - variant_1_unit_price == rule.reward_value
    assert rule.reward_value == Decimal(3)

    assert line_1.undiscounted_total_price_net_amount == Decimal("30.00")
    assert line_1.undiscounted_total_price_gross_amount == Decimal("36.90")
    assert line_1.undiscounted_unit_price_net_amount == Decimal("10.00")
    assert line_1.undiscounted_unit_price_gross_amount == Decimal("12.30")
    assert line_1.total_price_net_amount == Decimal("21.00")
    assert line_1.total_price_gross_amount == Decimal("25.83")
    assert line_1.base_unit_price_amount == Decimal("7.00")
    assert line_1.unit_price_net_amount == Decimal("7.00")
    assert line_1.unit_price_gross_amount == Decimal("8.61")

    assert line_2.undiscounted_total_price_net_amount == Decimal("40.00")
    assert line_2.undiscounted_total_price_gross_amount == Decimal("49.20")
    assert line_2.undiscounted_unit_price_net_amount == Decimal("20.00")
    assert line_2.undiscounted_unit_price_gross_amount == Decimal("24.60")
    assert line_2.total_price_net_amount == Decimal("40.00")
    assert line_2.total_price_gross_amount == Decimal("49.20")
    assert line_2.base_unit_price_amount == Decimal("20.00")
    assert line_2.unit_price_net_amount == Decimal("20.00")
    assert line_2.unit_price_gross_amount == Decimal("24.60")

    assert order.shipping_price_net_amount == Decimal("10.00")
    assert order.shipping_price_gross_amount == Decimal("12.30")
    assert order.undiscounted_total_net_amount == Decimal("80.00")
    assert order.undiscounted_total_gross_amount == Decimal("98.40")
    assert order.total_net_amount == Decimal("71.00")
    assert order.total_gross_amount == Decimal("87.33")
    assert order.subtotal_net_amount == Decimal("61.00")
    assert order.subtotal_gross_amount == Decimal("75.03")

    assert discount.amount_value == Decimal("9.00")
    assert discount.value == Decimal("3.00")
    assert discount.value_type == DiscountValueType.FIXED
    assert discount.type == DiscountType.PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"

    assert line_1.unit_discount_amount == Decimal("3.00")
    assert line_1.unit_discount_reason == f"Promotion: {promotion_id}"
    assert line_1.unit_discount_type == DiscountValueType.FIXED
    assert line_1.unit_discount_value == Decimal("3.00")


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
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

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
    line_1_order_discount_portion = (
        discount.amount_value * line_1_base_total / base_total
    )
    line_2_order_discount_portion = (
        discount.amount_value - line_1_order_discount_portion
    )

    assert order.shipping_price_net_amount == Decimal("10.00")
    assert order.shipping_price_gross_amount == Decimal("12.30")
    assert order.undiscounted_total_net_amount == Decimal("80.00")
    assert order.undiscounted_total_gross_amount == Decimal("98.40")
    assert order.total_net_amount == Decimal("55.00")
    assert order.total_gross_amount == Decimal("67.65")
    assert order.subtotal_net_amount == Decimal("45.00")
    assert order.subtotal_gross_amount == Decimal("55.35")

    assert line_1.undiscounted_total_price_net_amount == Decimal("30.00")
    assert line_1.undiscounted_total_price_gross_amount == Decimal("36.90")
    assert line_1.undiscounted_unit_price_net_amount == Decimal("10.00")
    assert line_1.undiscounted_unit_price_gross_amount == Decimal("12.30")
    assert (
        quantize_price(
            line_1.undiscounted_total_price_net_amount - line_1_order_discount_portion,
            currency,
        )
        == line_1.total_price_net_amount
    )
    assert line_1.total_price_net_amount == Decimal("19.29")
    assert line_1.total_price_gross_amount == Decimal("23.72")
    assert line_1.base_unit_price_amount == Decimal("10.00")
    assert line_1.unit_price_net_amount == Decimal("6.43")
    assert line_1.unit_price_gross_amount == Decimal("7.91")
    assert (
        quantize_price(
            line_2.undiscounted_total_price_net_amount - line_2_order_discount_portion,
            currency,
        )
        == line_2.total_price_net_amount
    )
    assert line_2.undiscounted_total_price_net_amount == Decimal("40.00")
    assert line_2.undiscounted_total_price_gross_amount == Decimal("49.20")
    assert line_2.undiscounted_unit_price_net_amount == Decimal("20.00")
    assert line_2.undiscounted_unit_price_gross_amount == Decimal("24.60")
    assert line_2.total_price_net_amount == Decimal("25.71")
    assert line_2.total_price_gross_amount == Decimal("31.63")
    assert line_2.base_unit_price_amount == Decimal("20.00")
    assert line_2.unit_price_net_amount == Decimal("12.86")
    assert line_2.unit_price_gross_amount == Decimal("15.81")

    assert discount.order == order
    assert discount.amount_value == Decimal("25.00")
    assert discount.value == Decimal("25.00")
    assert discount.value_type == DiscountValueType.FIXED
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"


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

    assert order.shipping_price_net_amount == Decimal("10.00")
    assert order.shipping_price_gross_amount == Decimal("12.30")
    assert order.undiscounted_total_net_amount == Decimal("80.00")
    assert order.undiscounted_total_gross_amount == Decimal("98.40")
    assert order.total_net_amount == Decimal("80.00")
    assert order.total_gross_amount == Decimal("98.40")
    assert order.subtotal_net_amount == Decimal("70.00")
    assert order.subtotal_gross_amount == Decimal("86.10")

    assert line_1.undiscounted_total_price_net_amount == Decimal("30.00")
    assert line_1.undiscounted_total_price_gross_amount == Decimal("36.90")
    assert line_1.undiscounted_unit_price_net_amount == Decimal("10.00")
    assert line_1.undiscounted_unit_price_gross_amount == Decimal("12.30")
    assert line_1.total_price_net_amount == Decimal("30.00")
    assert line_1.total_price_gross_amount == Decimal("36.90")
    assert line_1.base_unit_price_amount == Decimal("10.00")
    assert line_1.unit_price_net_amount == Decimal("10.00")
    assert line_1.unit_price_gross_amount == Decimal("12.30")

    assert line_2.undiscounted_total_price_net_amount == Decimal("40.00")
    assert line_2.undiscounted_total_price_gross_amount == Decimal("49.20")
    assert line_2.undiscounted_unit_price_net_amount == Decimal("20.00")
    assert line_2.undiscounted_unit_price_gross_amount == Decimal("24.60")
    assert line_2.total_price_net_amount == Decimal("40.00")
    assert line_2.total_price_gross_amount == Decimal("49.20")
    assert line_2.base_unit_price_amount == Decimal("20.00")
    assert line_2.unit_price_net_amount == Decimal("20.00")
    assert line_2.unit_price_gross_amount == Decimal("24.60")

    assert discount.line == gift_line
    assert discount.amount_value == Decimal("10.00")
    assert discount.value == Decimal("10.00")
    assert discount.value_type == DiscountValueType.FIXED
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.reason == f"Promotion: {promotion_id}"

    assert gift_line.unit_discount_amount == Decimal("10.00")
    assert gift_line.unit_discount_reason == f"Promotion: {promotion_id}"
    assert gift_line.unit_discount_type == DiscountValueType.FIXED
    assert gift_line.unit_discount_value == Decimal("10.00")


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
    currency = order.currency

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

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
    line_1_order_discount_portion = (
        order_discount.amount_value * line_1_base_total / base_total
    )
    line_2_order_discount_portion = (
        order_discount.amount_value - line_1_order_discount_portion
    )

    assert not line_1.discounts.exists()
    assert line_1.undiscounted_total_price_net_amount == Decimal("30.00")
    assert line_1.undiscounted_total_price_gross_amount == Decimal("36.90")
    assert line_1.undiscounted_unit_price_net_amount == Decimal("10.00")
    assert line_1.undiscounted_unit_price_gross_amount == Decimal("12.30")
    assert line_1.base_unit_price_amount == Decimal("10.00")
    assert (
        quantize_price(
            line_1.undiscounted_total_price_net_amount - line_1_order_discount_portion,
            currency,
        )
        == line_1.total_price_net_amount
    )
    assert line_1.total_price_net_amount == Decimal("18.28")
    assert line_1.total_price_gross_amount == Decimal("22.49")
    assert line_1.unit_price_net_amount == Decimal("6.09")
    assert line_1.unit_price_gross_amount == Decimal("7.50")

    assert catalogue_discount.line == line_2
    assert catalogue_discount.amount_value == Decimal("6.00")
    assert catalogue_discount.value == Decimal("3.00")
    assert catalogue_discount.value_type == DiscountValueType.FIXED
    assert catalogue_discount.type == DiscountType.PROMOTION
    assert catalogue_discount.reason == f"Promotion: {catalogue_promotion_id}"

    assert line_2.undiscounted_total_price_net_amount == Decimal("40.00")
    assert line_2.undiscounted_total_price_gross_amount == Decimal("49.20")
    assert line_2.undiscounted_unit_price_net_amount == Decimal("20.00")
    assert line_2.undiscounted_unit_price_gross_amount == Decimal("24.60")
    assert line_2.base_unit_price_amount == Decimal("17.00")
    assert (
        quantize_price(
            line_2.undiscounted_total_price_net_amount
            - line_2_order_discount_portion
            - catalogue_discount.amount_value,
            currency,
        )
        == line_2.total_price_net_amount
    )
    assert line_2.total_price_net_amount == Decimal("20.72")
    assert line_2.total_price_gross_amount == Decimal("25.48")
    assert line_2.unit_price_net_amount == Decimal("10.36")
    assert line_2.unit_price_gross_amount == Decimal("12.74")

    assert order_discount.order == order
    assert order_discount.amount_value == Decimal("25.00")
    assert order_discount.value == Decimal("25.00")
    assert order_discount.value_type == DiscountValueType.FIXED
    assert order_discount.type == DiscountType.ORDER_PROMOTION
    assert order_discount.reason == f"Promotion: {order_promotion_id}"

    assert order.shipping_price_net_amount == Decimal("10.00")
    assert order.shipping_price_gross_amount == Decimal("12.30")
    assert order.undiscounted_total_net_amount == Decimal("80.00")
    assert order.undiscounted_total_gross_amount == Decimal("98.40")
    assert (
        quantize_price(
            order.undiscounted_total_net_amount
            - order_discount.amount_value
            - catalogue_discount.amount_value,
            currency,
        )
        == order.total_net_amount
    )
    assert order.total_net_amount == Decimal("49.00")
    assert order.total_gross_amount == Decimal("60.27")
    assert order.subtotal_net_amount == Decimal("39.00")
    assert order.subtotal_gross_amount == Decimal("47.97")


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
    currency = order.currency

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

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

    assert not line_1.discounts.exists()
    assert line_1.undiscounted_total_price_net_amount == Decimal("30.00")
    assert line_1.undiscounted_total_price_gross_amount == Decimal("36.90")
    assert line_1.undiscounted_unit_price_net_amount == Decimal("10.00")
    assert line_1.undiscounted_unit_price_gross_amount == Decimal("12.30")
    assert line_1.total_price_net_amount == Decimal("30.00")
    assert line_1.total_price_gross_amount == Decimal("36.90")
    assert line_1.base_unit_price_amount == Decimal("10.00")
    assert line_1.unit_price_net_amount == Decimal("10.00")
    assert line_1.unit_price_gross_amount == Decimal("12.30")

    assert catalogue_discount.line == line_2
    assert catalogue_discount.amount_value == Decimal("6.00")
    assert catalogue_discount.value == Decimal("3.00")
    assert catalogue_discount.value_type == DiscountValueType.FIXED
    assert catalogue_discount.type == DiscountType.PROMOTION
    assert catalogue_discount.reason == f"Promotion: {catalogue_promotion_id}"

    assert line_2.undiscounted_total_price_net_amount == Decimal("40.00")
    assert line_2.undiscounted_total_price_gross_amount == Decimal("49.20")
    assert line_2.undiscounted_unit_price_net_amount == Decimal("20.00")
    assert line_2.undiscounted_unit_price_gross_amount == Decimal("24.60")
    assert line_2.base_unit_price_amount == Decimal("17.00")
    assert (
        quantize_price(
            line_2.undiscounted_total_price_net_amount
            - catalogue_discount.amount_value,
            currency,
        )
        == line_2.total_price_net_amount
    )
    assert line_2.total_price_net_amount == Decimal("34.00")
    assert line_2.total_price_gross_amount == Decimal("41.82")
    assert line_2.unit_price_net_amount == Decimal("17.00")
    assert line_2.unit_price_gross_amount == Decimal("20.91")

    assert gift_discount.line == gift_line
    assert gift_discount.amount_value == Decimal("20.00")
    assert gift_discount.value == Decimal("20.00")
    assert gift_discount.value_type == DiscountValueType.FIXED
    assert gift_discount.type == DiscountType.ORDER_PROMOTION
    assert gift_discount.reason == f"Promotion: {gift_promotion_id}"

    assert order.shipping_price_net_amount == Decimal("10.00")
    assert order.shipping_price_gross_amount == Decimal("12.30")
    assert order.undiscounted_total_net_amount == Decimal("80.00")
    assert order.undiscounted_total_gross_amount == Decimal("98.40")
    assert (
        quantize_price(
            order.undiscounted_total_net_amount - catalogue_discount.amount_value,
            currency,
        )
        == order.total_net_amount
    )
    assert order.total_net_amount == Decimal("74.00")
    assert order.total_gross_amount == Decimal("91.02")
    assert order.subtotal_net_amount == Decimal("64.00")
    assert order.subtotal_gross_amount == Decimal("78.72")


def test_fetch_order_prices_catalogue_and_order_discounts_exceed_total_flat_rates(
    draft_order_and_promotions,
    plugins_manager,
):
    # given
    order, rule_catalogue, rule_total, _ = draft_order_and_promotions
    rule_total.reward_value = Decimal(100000)
    rule_total.save(update_fields=["reward_value"])
    currency = order.currency

    tc = order.channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

    # when
    order, lines = calculations.fetch_order_prices_if_expired(
        order, plugins_manager, None, True
    )

    # then
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]
    catalogue_discount = OrderLineDiscount.objects.get()
    order_discount = OrderDiscount.objects.get()

    assert not line_1.discounts.exists()
    assert line_1.base_unit_price_amount == Decimal("10.00")
    assert line_1.total_price_net_amount == Decimal("0.00")
    assert line_1.total_price_gross_amount == Decimal("0.00")

    assert catalogue_discount.line == line_2
    assert catalogue_discount.amount_value == Decimal("6.00")
    assert catalogue_discount.value == Decimal("3.00")
    assert line_2.base_unit_price_amount == Decimal("17.00")
    assert line_2.total_price_net_amount == Decimal("0.00")
    assert line_2.total_price_gross_amount == Decimal("0.00")

    assert order_discount.amount_value == Decimal("64.00")

    assert quantize_price(
        order.undiscounted_total_net_amount
        - catalogue_discount.amount_value
        - order_discount.amount_value
        - order.shipping_price_net_amount,
        currency,
    ) == Decimal("0.00")
    assert order.total_net_amount == order.shipping_price_net_amount
    assert order.total_gross_amount == order.shipping_price_gross_amount
