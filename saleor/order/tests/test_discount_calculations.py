from decimal import Decimal

import graphene
import pytest
from prices import Money, TaxedMoney

from ...core.prices import quantize_price
from ...core.taxes import zero_money
from ...discount import DiscountType, DiscountValueType, RewardType, RewardValueType
from ...order.base_calculations import (
    apply_order_discounts,
    apply_subtotal_discount_to_order_lines,
    base_order_line_total,
    base_order_total,
)
from ...order.interface import OrderTaxedPricesData
from ...product.models import VariantChannelListingPromotionRule
from ...warehouse.models import Stock
from .. import OrderStatus
from ..calculations import fetch_order_prices_if_expired


def test_base_order_total(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    # when
    order_total = base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total


def test_base_order_line_total(order_with_lines):
    # given
    line = order_with_lines.lines.all().first()

    # when
    order_total = base_order_line_total(line)

    # then
    base_line_unit_price = line.base_unit_price
    quantity = line.quantity
    expected_price_with_discount = (
        TaxedMoney(base_line_unit_price, base_line_unit_price) * quantity
    )
    base_line_undiscounted_unit_price = line.undiscounted_base_unit_price
    expected_undiscounted_price = (
        TaxedMoney(base_line_undiscounted_unit_price, base_line_undiscounted_unit_price)
        * quantity
    )
    assert order_total == OrderTaxedPricesData(
        price_with_discounts=expected_price_with_discount,
        undiscounted_price=expected_undiscounted_price,
    )


def test_apply_order_discounts_voucher_entire_order(order_with_lines, voucher):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    discount_amount = 10
    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == shipping_price
    assert discounted_subtotal == subtotal - Money(discount_amount, currency)
    assert order.total_net == discounted_subtotal + discounted_shipping_price
    assert order.total_gross == discounted_subtotal + discounted_shipping_price
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_apply_order_discounts_voucher_entire_order_exceed_subtotal(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    discount_amount = 100
    assert Money(discount_amount, currency) > subtotal

    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == shipping_price
    assert discounted_subtotal == zero_money(currency)
    assert order.total_net == discounted_shipping_price
    assert order.total_gross == discounted_shipping_price
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount_value == subtotal.amount


def test_apply_order_discounts_voucher_entire_order_percentage(
    order_with_lines, voucher_percentage
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    discount_amount = 50
    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher_percentage,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == shipping_price
    assert discounted_subtotal == Money(subtotal.amount / 2, currency)
    assert order.total_net == discounted_subtotal + discounted_shipping_price
    assert order.total_gross == discounted_subtotal + discounted_shipping_price
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount_value == quantize_price(subtotal.amount / 2, currency)


def test_apply_order_discounts_manual_discount(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    discount_amount = 8
    order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )
    undiscounted_total = subtotal + shipping_price
    shipping_share = shipping_price / undiscounted_total
    subtotal_share = 1 - shipping_share

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == shipping_price - shipping_share * Money(
        discount_amount, currency
    )
    assert discounted_subtotal == subtotal - subtotal_share * Money(
        discount_amount, currency
    )
    assert order.total_net == discounted_subtotal + discounted_shipping_price
    assert order.total_gross == discounted_subtotal + discounted_shipping_price
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_apply_order_discounts_manual_discount_and_zero_order_total(order):
    # given
    lines = order.lines.all()
    assert not lines

    currency = order.currency
    order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=0,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_subtotal + discounted_shipping_price == zero_money(currency)


def test_apply_order_discounts_manual_discount_exceed_total(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    discount_amount = 160
    assert Money(discount_amount, currency) > undiscounted_total
    order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == zero_money(currency)
    assert discounted_subtotal == zero_money(currency)
    assert order.total_net == zero_money(currency)
    assert order.total_gross == zero_money(currency)
    assert order.shipping_price_net == zero_money(currency)
    assert order.shipping_price_gross == zero_money(currency)
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    order_discount.refresh_from_db()
    assert order_discount.amount_value == undiscounted_total.amount


def test_apply_order_discounts_manual_discount_percentage(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    discount_amount = undiscounted_total.amount * Decimal(0.5)
    order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    discounted_total = discounted_subtotal + discounted_shipping_price
    assert discounted_shipping_price == shipping_price / 2
    assert discounted_subtotal == subtotal / 2
    assert order.total_net == discounted_total
    assert order.total_gross == discounted_total
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_apply_order_discounts_voucher_entire_order_and_manual_discount_fixed(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price
    expected_subtotal = subtotal
    expected_shipping = shipping_price

    voucher_discount_amount = 10
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=voucher_discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher,
    )
    # entire order voucher is applied to subtotal only
    expected_subtotal -= Money(voucher_discount_amount, currency)

    manual_discount_amount = 8
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )
    # manual discount is applied to both subtotal and shipping price
    subtotal_share = expected_subtotal / (expected_subtotal + expected_shipping)
    subtotal_discount = subtotal_share * manual_discount_amount
    shipping_discount = manual_discount_amount - subtotal_discount
    expected_subtotal -= Money(subtotal_discount, currency)
    expected_shipping -= Money(shipping_discount, currency)

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == expected_shipping
    assert discounted_subtotal == expected_subtotal
    assert order.total_net == expected_shipping + expected_subtotal
    assert order.total_gross == expected_shipping + expected_subtotal
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount


def test_apply_order_discounts_manual_discount_fixed_and_voucher_entire_order(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price
    expected_subtotal = subtotal
    expected_shipping = shipping_price
    subtotal_share = subtotal / undiscounted_total

    manual_discount_amount = 8
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )
    # manual discount is applied to both subtotal and shipping price
    subtotal_discount = subtotal_share * manual_discount_amount
    shipping_discount = manual_discount_amount - subtotal_discount
    expected_subtotal -= Money(subtotal_discount, currency)
    expected_shipping -= Money(shipping_discount, currency)

    voucher_discount_amount = 10
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=voucher_discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher,
    )
    # entire order voucher is applied to subtotal only
    expected_subtotal -= Money(voucher_discount_amount, currency)

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == expected_shipping
    assert discounted_subtotal == expected_subtotal
    assert order.total_net == expected_shipping + expected_subtotal
    assert order.total_gross == expected_shipping + expected_subtotal
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount


def test_apply_order_discounts_voucher_entire_order_and_manual_discount_percentage(
    order_with_lines,
    voucher_percentage,
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price
    expected_subtotal = subtotal
    expected_shipping = shipping_price

    voucher_value = 50
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=voucher_value,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher_percentage,
    )
    # entire order voucher is applied to subtotal only
    voucher_discount = Decimal(voucher_value / 100) * expected_subtotal
    expected_subtotal -= voucher_discount

    manual_discount_value = 50
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=manual_discount_value,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )
    # manual discount is applied to both subtotal and shipping price
    manual_discount_subtotal = Decimal(manual_discount_value / 100) * expected_subtotal
    expected_subtotal -= manual_discount_subtotal
    manual_discount_shipping = Decimal(manual_discount_value / 100) * expected_shipping
    expected_shipping -= manual_discount_shipping
    manual_discount = manual_discount_subtotal + manual_discount_shipping

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == expected_shipping
    assert discounted_subtotal == expected_subtotal
    assert order.total_net == expected_shipping + expected_subtotal
    assert order.total_gross == expected_shipping + expected_subtotal
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount.amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount.amount


def test_apply_order_discounts_manual_discount_percentage_and_voucher_entire_order(
    order_with_lines,
    voucher_percentage,
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price
    expected_subtotal = subtotal
    expected_shipping = shipping_price

    manual_discount_value = 50
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=manual_discount_value,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )
    # manual discount is applied to both subtotal and shipping price
    manual_discount_subtotal = Decimal(manual_discount_value / 100) * expected_subtotal
    expected_subtotal -= manual_discount_subtotal
    manual_discount_shipping = Decimal(manual_discount_value / 100) * expected_shipping
    expected_shipping -= manual_discount_shipping
    manual_discount = manual_discount_subtotal + manual_discount_shipping

    voucher_value = 50
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=voucher_value,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher_percentage,
    )
    # entire order voucher is applied to subtotal only
    voucher_discount = Decimal(voucher_value / 100) * expected_subtotal
    expected_subtotal -= voucher_discount

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == expected_shipping
    assert discounted_subtotal == expected_subtotal
    assert order.total_net == expected_shipping + expected_subtotal
    assert order.total_gross == expected_shipping + expected_subtotal
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount.amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount.amount


@pytest.mark.parametrize("discount", ["10", "1", "17.3", "10000", "0"])
def test_apply_subtotal_discount_to_order_lines(
    discount,
    order_with_lines,
    voucher,
):
    # given
    order = order_with_lines
    currency = order.currency

    def _quantize(price):
        return quantize_price(price, currency)

    lines = order.lines.all()
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    subtotal_discount = Money(Decimal(discount), currency)
    expected_subtotal = max(subtotal - subtotal_discount, zero_money(currency))

    # when
    apply_subtotal_discount_to_order_lines(lines, subtotal, subtotal_discount)

    # then
    discounted_subtotal = zero_money(currency)
    for line in lines:
        discounted_subtotal += line.total_price_net
    assert discounted_subtotal == expected_subtotal

    assert (
        discounted_subtotal.amount
        == lines[0].total_price_net_amount + lines[1].total_price_net_amount
    )
    assert (
        discounted_subtotal.amount
        == lines[0].total_price_gross_amount + lines[1].total_price_gross_amount
    )

    assert lines[0].total_price_net_amount == _quantize(
        lines[0].unit_price_net_amount * lines[0].quantity
    )
    assert lines[0].total_price_gross_amount == _quantize(
        lines[0].unit_price_gross_amount * lines[0].quantity
    )
    assert lines[1].total_price_net_amount == _quantize(
        lines[1].unit_price_net_amount * lines[1].quantity
    )
    assert lines[1].total_price_gross_amount == _quantize(
        lines[1].unit_price_gross_amount * lines[1].quantity
    )
    assert (
        max(
            lines[0].base_unit_price * lines[0].quantity
            + lines[1].base_unit_price * lines[1].quantity
            - subtotal_discount,
            zero_money(currency),
        )
        == expected_subtotal
    )


@pytest.mark.parametrize("discount", ["10", "1", "17.3", "10000", "0"])
def test_apply_subtotal_discount_to_order_lines_order_with_single_line(
    discount,
    order_with_lines,
    voucher,
):
    # given
    order = order_with_lines
    currency = order.currency

    def _quantize(price):
        return quantize_price(price, currency)

    order.lines.all()[1].delete()
    line = order.lines.first()
    subtotal = line.base_unit_price * line.quantity
    subtotal_discount = Money(Decimal(discount), currency)
    expected_subtotal = max(subtotal - subtotal_discount, zero_money(currency))

    # when
    apply_subtotal_discount_to_order_lines([line], subtotal, subtotal_discount)

    # then
    discounted_subtotal = line.total_price_net
    assert discounted_subtotal == expected_subtotal
    assert discounted_subtotal.amount == line.total_price_net_amount
    assert discounted_subtotal.amount == line.total_price_gross_amount

    assert line.total_price_net_amount == _quantize(
        line.unit_price_net_amount * line.quantity
    )
    assert line.total_price_gross_amount == _quantize(
        line.unit_price_gross_amount * line.quantity
    )
    assert (
        max(
            line.base_unit_price * line.quantity - subtotal_discount,
            zero_money(currency),
        )
        == line.total_price_net
    )


def test_zedzior(
    plugins_manager,
    order_with_lines,
    order_promotion_without_rules,
    catalogue_promotion_without_rules,
    channel_USD,
    product_variant_list,
    warehouse,
):
    # given
    order = order_with_lines
    # prepare order promotions
    order_promotion = order_promotion_without_rules
    rule_total = order_promotion.rules.create(
        name="Subtotal gte 10 fixed 5 rule",
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(1),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule_gift = order_promotion.rules.create(
        name="Subtotal gte 10 gift rule",
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
        },
        reward_type=RewardType.GIFT,
    )
    rule_total.channels.add(channel_USD)
    rule_gift.channels.add(channel_USD)
    rule_gift.gifts.set([variant for variant in product_variant_list[:2]])

    Stock.objects.create(
        warehouse=warehouse, product_variant=product_variant_list[0], quantity=100
    )
    Stock.objects.create(
        warehouse=warehouse, product_variant=product_variant_list[1], quantity=100
    )

    # prepare catalogue promotions
    catalogue_promotion = catalogue_promotion_without_rules
    assert order.lines.count() == 2
    variant_1 = order.lines.first().variant
    rule_catalogue_1 = catalogue_promotion.rules.create(
        name="Catalogue rule fixed 3",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant_1.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(3),
    )
    variant_2 = order.lines.last().variant
    rule_catalogue_2 = catalogue_promotion.rules.create(
        name="Catalogue rule percentage 15",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant_2.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal(20),
    )
    rule_catalogue_1.channels.add(channel_USD)
    rule_catalogue_2.channels.add(channel_USD)

    listing_1 = variant_1.channel_listings.first()
    listing_1.discounted_price_amount = Decimal(7)
    listing_2 = variant_2.channel_listings.first()
    listing_2.discounted_price_amount = Decimal(16)
    listing_1.save(update_fields=["discounted_price_amount"])
    listing_2.save(update_fields=["discounted_price_amount"])

    currency = order.currency
    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing_1,
        promotion_rule=rule_catalogue_1,
        discount_amount=Decimal(3),
        currency=currency,
    )
    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing_2,
        promotion_rule=rule_catalogue_2,
        discount_amount=Decimal(4),
        currency=currency,
    )

    order.total = TaxedMoney(net=zero_money(currency), gross=zero_money(currency))
    order.subtotal = TaxedMoney(net=zero_money(currency), gross=zero_money(currency))
    order.undiscounted_total = TaxedMoney(
        net=zero_money(currency), gross=zero_money(currency)
    )
    order.status = OrderStatus.DRAFT
    order.save()

    for line in order.lines.all():
        line.unit_price = TaxedMoney(
            net=zero_money(currency), gross=zero_money(currency)
        )
        line.undiscounted_unit_price = TaxedMoney(
            net=zero_money(currency), gross=zero_money(currency)
        )
        line.total_price = TaxedMoney(
            net=zero_money(currency), gross=zero_money(currency)
        )
        line.undiscounted_total_price = TaxedMoney(
            net=zero_money(currency), gross=zero_money(currency)
        )
        line.undiscounted_base_unit_price_amount = Decimal(0)
        line.save()

    # when
    fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    order.refresh_from_db()
    line_1 = order.lines.filter(variant=variant_1).first()
    line_2 = order.lines.filter(variant=variant_2).first()
    assert line_1.discounts.count() == 1
    catalogue_discount_1 = line_1.discounts.first()
    assert catalogue_discount_1.type == DiscountType.PROMOTION
    assert catalogue_discount_1.amount_value == 3 * Decimal(3)
    assert line_2.discounts.count() == 1
    catalogue_discount_2 = line_2.discounts.first()
    assert catalogue_discount_2.type == DiscountType.PROMOTION
    assert catalogue_discount_2.amount_value == 2 * Decimal(4)

    # assert order.discounts.count() == 1
    # order_discount = order.discounts.first()
    # assert order_discount
    gift_discount = [line for line in order.lines.all() if line.is_gift]
    assert gift_discount
    # assert order_discount.amount_value == Decimal(5)
