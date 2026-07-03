from datetime import timedelta
from decimal import Decimal

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from ...core.prices import quantize_price
from ...core.taxes import zero_money
from ...discount import DiscountType, DiscountValueType, RewardValueType, VoucherType
from ...discount.models import OrderLineDiscount, Promotion, PromotionRule
from ...discount.utils.voucher import (
    create_or_update_voucher_discount_objects_for_order,
)
from ...product.models import Product
from ...product.utils.variant_prices import update_discounted_prices_for_promotion
from ...product.utils.variants import fetch_variants_for_promotion_rules
from .. import OrderStatus
from ..calculations import refresh_order_base_prices_and_discounts


@freeze_time("2020-03-18 12:00:00")
def test_refresh_order_base_prices(order_with_lines):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    line_1, line_2 = order.lines.all()
    variant_1, variant_2 = line_1.variant, line_2.variant

    initial_variant_1_price = line_1.undiscounted_base_unit_price_amount
    initial_variant_2_price = line_2.undiscounted_base_unit_price_amount

    # change variant 1 pricing
    channel_listing_1 = variant_1.channel_listings.get()
    assert initial_variant_1_price == channel_listing_1.price_amount
    assert initial_variant_1_price == channel_listing_1.discounted_price_amount
    new_variant_1_price = initial_variant_1_price + Decimal(1)
    channel_listing_1.price_amount = new_variant_1_price
    channel_listing_1.discounted_price_amount = new_variant_1_price
    channel_listing_1.save(update_fields=["price_amount", "discounted_price_amount"])

    # change variant 2 pricing
    channel_listing_2 = variant_2.channel_listings.get()
    assert initial_variant_2_price == channel_listing_2.price_amount
    assert initial_variant_2_price == channel_listing_2.discounted_price_amount
    new_variant_2_price = initial_variant_2_price - Decimal(2)
    channel_listing_2.price_amount = new_variant_2_price
    channel_listing_2.discounted_price_amount = new_variant_2_price
    channel_listing_2.save(update_fields=["price_amount", "discounted_price_amount"])

    expire_period = order.channel.draft_order_line_price_freeze_period
    assert expire_period is not None
    assert expire_period > 0
    expected_expire_time = timezone.now() + timedelta(hours=expire_period)

    line_ids_to_refresh = [line_1.id]

    # when
    refresh_order_base_prices_and_discounts(order, line_ids_to_refresh)

    # then
    line_1, line_2 = order.lines.all()
    assert line_1.undiscounted_base_unit_price_amount == new_variant_1_price
    assert line_1.base_unit_price_amount == new_variant_1_price
    assert line_1.draft_base_price_expire_at == expected_expire_time

    assert line_2.undiscounted_base_unit_price_amount == initial_variant_2_price
    assert line_2.base_unit_price_amount == initial_variant_2_price
    assert line_2.draft_base_price_expire_at is None


def test_refresh_order_base_prices_catalogue_discount(
    order_with_lines_and_catalogue_promotion,
):
    # given
    order = order_with_lines_and_catalogue_promotion
    order.status = OrderStatus.DRAFT
    channel = order.channel
    currency = order.currency
    promotion = Promotion.objects.get()
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rule_1 = promotion.rules.get()
    initial_reward_value_1 = rule_1.reward_value
    initial_reward_value_type_1 = rule_1.reward_value_type

    lines = order.lines.all()
    line_1, line_2 = lines
    variant_2 = line_2.variant
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    discount_1 = line_1.discounts.first()
    assert discount_1.value == initial_reward_value_1
    assert discount_1.value_type == initial_reward_value_type_1
    assert discount_1.amount_value == initial_reward_value_1 * line_1.quantity

    # prepare new catalog promotion rule for variant 2
    initial_reward_value_2 = Decimal(5)
    initial_reward_value_type_2 = DiscountValueType.FIXED
    rule_2 = promotion.rules.create(
        name="Rule 2",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant_2.id)]
            }
        },
        reward_value_type=initial_reward_value_type_2,
        reward_value=initial_reward_value_2,
    )
    rule_2.channels.add(channel)

    listing_2 = variant_2.channel_listings.get(channel=channel)
    listing_2.discounted_price_amount = listing_2.price_amount - initial_reward_value_2
    listing_2.save(update_fields=["discounted_price_amount"])
    listing_2.variantlistingpromotionrule.create(
        promotion_rule=rule_2,
        discount_amount=initial_reward_value_2,
        currency=currency,
    )

    discount_2 = line_2.discounts.create(
        type=DiscountType.PROMOTION,
        value_type=RewardValueType.FIXED,
        value=initial_reward_value_2,
        amount_value=initial_reward_value_2 * line_2.quantity,
        currency=currency,
        promotion_rule=rule_2,
        reason=f"Promotion: {promotion_id}",
    )

    line_2.base_unit_price_amount = (
        line_2.undiscounted_base_unit_price_amount - initial_reward_value_2
    )
    line_2.save(update_fields=["base_unit_price_amount"])

    # update promotion rules
    new_reward_value_1 = Decimal(50)
    new_reward_value_type_1 = RewardValueType.PERCENTAGE
    rule_1.reward_value = new_reward_value_1
    rule_1.reward_value_type = new_reward_value_type_1
    rule_1.save(update_fields=["reward_value", "reward_value_type"])

    new_reward_value_2 = Decimal(30)
    new_reward_value_type_2 = RewardValueType.PERCENTAGE
    rule_2.reward_value = new_reward_value_2
    rule_2.reward_value_type = new_reward_value_type_2
    rule_2.save(update_fields=["reward_value", "reward_value_type"])

    fetch_variants_for_promotion_rules(PromotionRule.objects.all())
    update_discounted_prices_for_promotion(Product.objects.all())

    undiscounted_unit_price_1 = line_1.undiscounted_base_unit_price_amount
    expected_unit_price_1 = undiscounted_unit_price_1 * (1 - new_reward_value_1 / 100)
    expected_unit_discount_1 = undiscounted_unit_price_1 - expected_unit_price_1
    expected_discount_amount_1 = expected_unit_discount_1 * line_1.quantity

    # line 2 prices shouldn't be refreshed
    undiscounted_unit_price_2 = line_2.undiscounted_base_unit_price_amount
    expected_unit_price_2 = undiscounted_unit_price_2 - initial_reward_value_2
    expected_unit_discount_2 = initial_reward_value_2
    expected_discount_amount_2 = expected_unit_discount_2 * line_2.quantity

    line_ids_to_refresh = [line_1.id]

    # when
    refresh_order_base_prices_and_discounts(order, line_ids_to_refresh)

    # then
    line_1, line_2 = order.lines.all()
    assert line_1.undiscounted_base_unit_price_amount == undiscounted_unit_price_1
    assert line_1.base_unit_price_amount == expected_unit_price_1
    assert line_1.unit_discount_amount == expected_unit_discount_1
    assert line_1.unit_discount_reason == f"Promotion: {promotion_id}"

    assert line_2.undiscounted_base_unit_price_amount == undiscounted_unit_price_2
    assert line_2.base_unit_price_amount == expected_unit_price_2
    assert line_2.unit_discount_amount == expected_unit_discount_2
    assert line_2.unit_discount_reason == f"Promotion: {promotion_id}"

    discount_1.refresh_from_db()
    assert discount_1.value == new_reward_value_1
    assert discount_1.value_type == new_reward_value_type_1
    assert discount_1.amount.amount == expected_discount_amount_1

    discount_2.refresh_from_db()
    assert discount_2.value == initial_reward_value_2
    assert discount_2.value_type == initial_reward_value_type_2
    assert discount_2.amount.amount == expected_discount_amount_2


def test_refresh_order_base_prices_manual_line_discount(order_with_lines):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    currency = order.currency
    line_1, line_2 = order.lines.all()
    variant_1, variant_2 = line_1.variant, line_2.variant

    initial_variant_1_price = line_1.undiscounted_base_unit_price_amount
    initial_variant_2_price = line_2.undiscounted_base_unit_price_amount

    # add manual discount to line 1
    discount_1_reward_value = Decimal(20)
    discount_1_unit_amount = discount_1_reward_value / 100 * initial_variant_1_price
    initial_discount_1_amount = discount_1_unit_amount * line_1.quantity
    discount_1 = line_1.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=discount_1_reward_value,
        amount_value=initial_discount_1_amount,
        currency=currency,
        unique_type=DiscountType.MANUAL,
    )
    line_1.base_unit_price_amount = (
        line_1.undiscounted_base_unit_price_amount - discount_1_unit_amount
    )
    line_1.save(update_fields=["base_unit_price_amount"])

    # add manual discount to line 2
    discount_2_reward_value = Decimal(10)
    discount_2_unit_amount = discount_2_reward_value / 100 * initial_variant_2_price
    initial_discount_2_amount = discount_2_unit_amount * line_2.quantity
    discount_2 = line_2.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=discount_2_reward_value,
        amount_value=initial_discount_2_amount,
        currency=currency,
        unique_type=DiscountType.MANUAL,
    )
    line_2.base_unit_price_amount = (
        line_2.undiscounted_base_unit_price_amount - discount_2_unit_amount
    )
    line_2.save(update_fields=["base_unit_price_amount"])

    # change variant 1 pricing
    channel_listing_1 = variant_1.channel_listings.get()
    assert initial_variant_1_price == channel_listing_1.price_amount
    assert initial_variant_1_price == channel_listing_1.discounted_price_amount
    new_variant_1_price = initial_variant_1_price + Decimal(1)
    channel_listing_1.price_amount = new_variant_1_price
    channel_listing_1.discounted_price_amount = new_variant_1_price
    channel_listing_1.save(update_fields=["price_amount", "discounted_price_amount"])

    # change variant 2 pricing
    channel_listing_2 = variant_2.channel_listings.get()
    assert initial_variant_2_price == channel_listing_2.price_amount
    assert initial_variant_2_price == channel_listing_2.discounted_price_amount
    new_variant_2_price = initial_variant_2_price - Decimal(2)
    channel_listing_2.price_amount = new_variant_2_price
    channel_listing_2.discounted_price_amount = new_variant_2_price
    channel_listing_2.save(update_fields=["price_amount", "discounted_price_amount"])

    # line 1 prices shouldn't be refreshed
    expected_unit_price_1 = initial_variant_1_price * (
        1 - discount_1_reward_value / 100
    )
    expected_unit_discount_1 = initial_variant_1_price - expected_unit_price_1
    expected_discount_amount_1 = expected_unit_discount_1 * line_1.quantity

    expected_unit_price_2 = new_variant_2_price * (1 - discount_2_reward_value / 100)
    expected_unit_discount_2 = new_variant_2_price - expected_unit_price_2
    expected_discount_amount_2 = expected_unit_discount_2 * line_2.quantity

    line_ids_to_refresh = [line_2.id]

    # when
    refresh_order_base_prices_and_discounts(order, line_ids_to_refresh)

    # then
    line_1, line_2 = order.lines.all()
    assert line_1.undiscounted_base_unit_price_amount == initial_variant_1_price
    assert line_1.base_unit_price_amount == expected_unit_price_1
    assert line_1.unit_discount_amount == expected_unit_discount_1

    assert line_2.undiscounted_base_unit_price_amount == new_variant_2_price
    assert line_2.base_unit_price_amount == expected_unit_price_2
    assert line_2.unit_discount_amount == expected_unit_discount_2

    discount_1.refresh_from_db()
    assert (
        discount_1.amount.amount
        == expected_discount_amount_1
        == initial_discount_1_amount
    )

    discount_2.refresh_from_db()
    assert discount_2.amount.amount == expected_discount_amount_2


def test_refresh_order_base_prices_specific_product_voucher(order_with_lines, voucher):
    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    line_1, line_2 = order.lines.all()
    variant_1, variant_2 = line_1.variant, line_2.variant

    initial_variant_1_price = line_1.undiscounted_base_unit_price_amount
    initial_variant_2_price = line_2.undiscounted_base_unit_price_amount

    # prepare specific product voucher which cover both line variants
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save(update_fields=["discount_value_type", "type"])
    voucher.variants.set([line_1.variant, line_2.variant])

    voucher_listing = voucher.channel_listings.get()
    initial_voucher_unit_discount = Decimal(1)
    voucher_listing.discount_value = initial_voucher_unit_discount
    voucher_listing.save(update_fields=["discount_value"])

    # apply voucher
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)

    line_1, line_2 = order.lines.all()
    discount_1 = line_1.discounts.get()
    discount_amount_1 = initial_voucher_unit_discount * line_1.quantity
    assert (
        line_1.base_unit_price_amount
        == line_1.undiscounted_base_unit_price_amount - initial_voucher_unit_discount
    )
    assert discount_1.value == initial_voucher_unit_discount
    assert discount_1.amount_value == discount_amount_1

    discount_2 = line_2.discounts.get()
    discount_amount_2 = initial_voucher_unit_discount * line_2.quantity
    assert (
        line_2.base_unit_price_amount
        == line_2.undiscounted_base_unit_price_amount - initial_voucher_unit_discount
    )
    assert discount_2.value == initial_voucher_unit_discount
    assert discount_2.amount_value == discount_amount_2

    # change variant 1 pricing
    channel_listing_1 = variant_1.channel_listings.get()
    assert initial_variant_1_price == channel_listing_1.price_amount
    assert initial_variant_1_price == channel_listing_1.discounted_price_amount
    new_variant_1_price = initial_variant_1_price + Decimal(2)
    channel_listing_1.price_amount = new_variant_1_price
    channel_listing_1.discounted_price_amount = new_variant_1_price
    channel_listing_1.save(update_fields=["price_amount", "discounted_price_amount"])

    # change variant 2 pricing
    channel_listing_2 = variant_2.channel_listings.get()
    assert initial_variant_2_price == channel_listing_2.price_amount
    assert initial_variant_2_price == channel_listing_2.discounted_price_amount
    new_variant_2_price = initial_variant_2_price - Decimal(4)
    channel_listing_2.price_amount = new_variant_2_price
    channel_listing_2.discounted_price_amount = new_variant_2_price
    channel_listing_2.save(update_fields=["price_amount", "discounted_price_amount"])

    # change voucher reward value and type
    new_voucher_unit_discount = Decimal(25)
    voucher_listing.discount_value = new_voucher_unit_discount
    voucher_listing.save(update_fields=["discount_value"])
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type"])

    expected_unit_price_1 = new_variant_1_price * (1 - new_voucher_unit_discount / 100)
    expected_unit_discount_1 = new_variant_1_price - expected_unit_price_1
    expected_discount_amount_1 = expected_unit_discount_1 * line_1.quantity

    # line 2 prices shouldn't be refreshed
    expected_unit_price_2 = initial_variant_2_price - initial_voucher_unit_discount
    expected_unit_discount_2 = initial_variant_2_price - expected_unit_price_2
    expected_discount_amount_2 = expected_unit_discount_2 * line_2.quantity

    line_ids_to_refresh = [line_1.id]

    # when
    refresh_order_base_prices_and_discounts(order, line_ids_to_refresh)

    # then
    line_1, line_2 = order.lines.all()
    assert line_1.undiscounted_base_unit_price_amount == new_variant_1_price
    assert line_1.base_unit_price_amount == expected_unit_price_1
    assert line_1.unit_discount_amount == expected_unit_discount_1

    assert line_2.undiscounted_base_unit_price_amount == initial_variant_2_price
    assert line_2.base_unit_price_amount == expected_unit_price_2
    assert line_2.unit_discount_amount == expected_unit_discount_2

    discount_1.refresh_from_db()
    assert discount_1.amount.amount == expected_discount_amount_1
    assert discount_1.value == new_voucher_unit_discount
    assert discount_1.value_type == DiscountValueType.PERCENTAGE

    discount_2.refresh_from_db()
    assert discount_2.amount.amount == expected_discount_amount_2
    assert discount_2.value == initial_voucher_unit_discount
    assert discount_2.value_type == DiscountValueType.FIXED


def test_refresh_order_base_prices_apply_once_per_order_voucher_new_cheapest(
    order_with_lines, voucher
):
    # Requesting an update of the line 2, which price has changed and is now the
    # cheapest, should apply the voucher discount to the new cheapest line 2 and delete
    # the discount from line 1, even if we didn't request update for line 1

    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    currency = order.currency
    line_1, line_2 = order.lines.all()
    variant_2 = line_2.variant

    initial_variant_1_price = line_1.undiscounted_base_unit_price_amount
    initial_variant_2_price = line_2.undiscounted_base_unit_price_amount

    # prepare apply once per order voucher
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.type = VoucherType.ENTIRE_ORDER
    voucher.apply_once_per_order = True
    voucher.save(update_fields=["discount_value_type", "type", "apply_once_per_order"])

    voucher_listing = voucher.channel_listings.get()
    initial_voucher_unit_discount = Decimal(1)
    voucher_listing.discount_value = initial_voucher_unit_discount
    voucher_listing.save(update_fields=["discount_value"])

    # apply voucher
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)

    # line 1 is the cheapest so should have the discount applied
    assert initial_variant_1_price < initial_variant_2_price
    line_1.refresh_from_db()
    discount_1 = line_1.discounts.get()
    discount_amount_1 = initial_voucher_unit_discount
    unit_discount_amount_1 = discount_amount_1 / line_1.quantity
    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - unit_discount_amount_1, currency
    )
    assert discount_1.value == initial_voucher_unit_discount
    assert discount_1.amount_value == discount_amount_1

    assert not line_2.discounts.exists()
    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount

    # change variant 2 pricing to be lower than variant 1
    channel_listing_2 = variant_2.channel_listings.get()
    assert initial_variant_2_price == channel_listing_2.price_amount
    assert initial_variant_2_price == channel_listing_2.discounted_price_amount
    new_variant_2_price = initial_variant_1_price - Decimal(1)
    channel_listing_2.price_amount = new_variant_2_price
    channel_listing_2.discounted_price_amount = new_variant_2_price
    channel_listing_2.save(update_fields=["price_amount", "discounted_price_amount"])

    # change voucher reward value and type
    new_voucher_unit_discount = Decimal(25)
    voucher_listing.discount_value = new_voucher_unit_discount
    voucher_listing.save(update_fields=["discount_value"])
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type"])

    # line 1 is not the cheapest anymore, so should not have discount applied
    assert initial_variant_1_price > new_variant_2_price
    expected_unit_discount_1 = 0

    # line 2 is now the cheapest and should have the price discounted by voucher
    expected_discount_amount_2 = new_variant_2_price * (new_voucher_unit_discount / 100)
    expected_unit_discount_2 = expected_discount_amount_2 / line_2.quantity
    expected_unit_price_2 = new_variant_2_price - expected_unit_discount_2

    line_ids_to_refresh = [line_2.id]

    # when
    refresh_order_base_prices_and_discounts(order, line_ids_to_refresh)

    # then
    line_1, line_2 = order.lines.all()
    assert line_1.undiscounted_base_unit_price_amount == initial_variant_1_price
    assert line_1.base_unit_price_amount == initial_variant_1_price
    assert line_1.unit_discount_amount == expected_unit_discount_1

    assert line_2.undiscounted_base_unit_price_amount == new_variant_2_price
    assert line_2.base_unit_price_amount == expected_unit_price_2
    assert line_2.unit_discount_amount == quantize_price(
        expected_unit_discount_2, currency
    )

    with pytest.raises(OrderLineDiscount.DoesNotExist):
        discount_1.refresh_from_db()
    assert not line_1.discounts.exists()

    discount_2 = line_2.discounts.get()
    assert discount_2.amount.amount == quantize_price(
        expected_discount_amount_2, currency
    )
    assert discount_2.value == new_voucher_unit_discount
    assert discount_2.value_type == DiscountValueType.PERCENTAGE


def test_refresh_order_base_prices_apply_once_per_order_voucher_old_cheapest(
    order_with_lines, voucher
):
    # Requesting an update of the line 1, which price has changed and is not the
    # cheapest anymore, should apply the voucher discount to the new cheapest line 2,
    # even if we didn't request to update prices for the line 2

    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    currency = order.currency
    line_1, line_2 = order.lines.all()
    variant_1 = line_1.variant

    initial_variant_1_price = line_1.undiscounted_base_unit_price_amount
    initial_variant_2_price = line_2.undiscounted_base_unit_price_amount

    # prepare apply once per order voucher
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.type = VoucherType.ENTIRE_ORDER
    voucher.apply_once_per_order = True
    voucher.save(update_fields=["discount_value_type", "type", "apply_once_per_order"])

    voucher_listing = voucher.channel_listings.get()
    initial_voucher_unit_discount = Decimal(1)
    voucher_listing.discount_value = initial_voucher_unit_discount
    voucher_listing.save(update_fields=["discount_value"])

    # apply voucher
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)

    # line 1 is the cheapest so should have the discount applied
    assert initial_variant_1_price < initial_variant_2_price
    line_1.refresh_from_db()
    discount_1 = line_1.discounts.get()
    discount_amount_1 = initial_voucher_unit_discount
    unit_discount_amount_1 = discount_amount_1 / line_1.quantity
    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - unit_discount_amount_1, currency
    )
    assert discount_1.value == initial_voucher_unit_discount
    assert discount_1.amount_value == discount_amount_1

    assert not line_2.discounts.exists()
    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount

    # change variant 1 pricing to be higher than variant 2
    channel_listing_1 = variant_1.channel_listings.get()
    assert initial_variant_1_price == channel_listing_1.price_amount
    assert initial_variant_1_price == channel_listing_1.discounted_price_amount
    new_variant_1_price = initial_variant_2_price + Decimal(1)
    channel_listing_1.price_amount = new_variant_1_price
    channel_listing_1.discounted_price_amount = new_variant_1_price
    channel_listing_1.save(update_fields=["price_amount", "discounted_price_amount"])

    # change voucher reward value and type
    new_voucher_unit_discount = Decimal(25)
    voucher_listing.discount_value = new_voucher_unit_discount
    voucher_listing.save(update_fields=["discount_value"])
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type"])

    # line 1 is not the cheapest anymore, so should not have discount applied
    assert new_variant_1_price > initial_variant_2_price
    expected_unit_discount_1 = 0

    # line 2 is now the cheapest and should have the price discounted by voucher, even there was no request to update
    # this line
    expected_discount_amount_2 = initial_variant_2_price * (
        new_voucher_unit_discount / 100
    )
    expected_unit_discount_2 = expected_discount_amount_2 / line_2.quantity
    expected_unit_price_2 = initial_variant_2_price - expected_unit_discount_2

    line_ids_to_refresh = [line_1.id]

    # when
    refresh_order_base_prices_and_discounts(order, line_ids_to_refresh)

    # then
    line_1, line_2 = order.lines.all()
    assert line_1.undiscounted_base_unit_price_amount == new_variant_1_price
    assert line_1.base_unit_price_amount == new_variant_1_price
    assert line_1.unit_discount_amount == expected_unit_discount_1

    assert line_2.undiscounted_base_unit_price_amount == initial_variant_2_price
    assert line_2.base_unit_price_amount == expected_unit_price_2
    assert line_2.unit_discount_amount == expected_unit_discount_2

    with pytest.raises(OrderLineDiscount.DoesNotExist):
        discount_1.refresh_from_db()
    assert not line_1.discounts.exists()

    discount_2 = line_2.discounts.get()
    assert discount_2.amount.amount == expected_discount_amount_2
    assert discount_2.value == new_voucher_unit_discount
    assert discount_2.value_type == DiscountValueType.PERCENTAGE


def test_refresh_order_base_prices_apply_once_per_order_voucher_same_cheapest(
    order_with_lines, voucher
):
    # Requesting an update of the line 1, which price has changed
    # and is still the cheapest, should update voucher discount

    # given
    order = order_with_lines
    order.status = OrderStatus.DRAFT
    currency = order.currency
    line_1, line_2 = order.lines.all()
    variant_1 = line_1.variant

    initial_variant_1_price = line_1.undiscounted_base_unit_price_amount
    initial_variant_2_price = line_2.undiscounted_base_unit_price_amount

    # prepare apply once per order voucher
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.type = VoucherType.ENTIRE_ORDER
    voucher.apply_once_per_order = True
    voucher.save(update_fields=["discount_value_type", "type", "apply_once_per_order"])

    voucher_listing = voucher.channel_listings.get()
    initial_voucher_unit_discount = Decimal(1)
    voucher_listing.discount_value = initial_voucher_unit_discount
    voucher_listing.save(update_fields=["discount_value"])

    # apply voucher
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)

    # line 1 is the cheapest so should have the discount applied
    assert initial_variant_1_price < initial_variant_2_price
    line_1.refresh_from_db()
    discount_1 = line_1.discounts.get()
    discount_amount_1 = initial_voucher_unit_discount
    unit_discount_amount_1 = discount_amount_1 / line_1.quantity
    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - unit_discount_amount_1, currency
    )
    assert discount_1.value == initial_voucher_unit_discount
    assert discount_1.amount_value == discount_amount_1

    assert not line_2.discounts.exists()
    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount

    # change variant 1 pricing but keep it the cheapest
    channel_listing_1 = variant_1.channel_listings.get()
    assert initial_variant_1_price == channel_listing_1.price_amount
    assert initial_variant_1_price == channel_listing_1.discounted_price_amount
    new_variant_1_price = initial_variant_1_price - Decimal(1)
    channel_listing_1.price_amount = new_variant_1_price
    channel_listing_1.discounted_price_amount = new_variant_1_price
    channel_listing_1.save(update_fields=["price_amount", "discounted_price_amount"])

    # change voucher reward value and type
    new_voucher_unit_discount = Decimal(25)
    voucher_listing.discount_value = new_voucher_unit_discount
    voucher_listing.save(update_fields=["discount_value"])
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type"])

    # line 1 is still the cheapest so should have discount applied
    assert new_variant_1_price < initial_variant_2_price
    expected_discount_amount_1 = new_variant_1_price * (new_voucher_unit_discount / 100)
    expected_unit_discount_1 = expected_discount_amount_1 / line_1.quantity
    expected_unit_price_1 = new_variant_1_price - expected_unit_discount_1

    # line 2 shouldn't have any discounts applied
    expected_unit_discount_2 = 0
    expected_unit_price_2 = initial_variant_2_price

    line_ids_to_refresh = [line_1.id]

    # when
    refresh_order_base_prices_and_discounts(order, line_ids_to_refresh)

    # then
    line_1, line_2 = order.lines.all()
    assert line_1.undiscounted_base_unit_price_amount == new_variant_1_price
    assert line_1.base_unit_price_amount == expected_unit_price_1
    assert line_1.unit_discount_amount == expected_unit_discount_1

    assert line_2.undiscounted_base_unit_price_amount == initial_variant_2_price
    assert line_2.base_unit_price_amount == expected_unit_price_2
    assert line_2.unit_discount_amount == expected_unit_discount_2

    discount_1.refresh_from_db()
    assert discount_1.amount.amount == expected_discount_amount_1
    assert discount_1.value == new_voucher_unit_discount
    assert discount_1.value_type == DiscountValueType.PERCENTAGE

    assert not line_2.discounts.exists()


def test_refresh_order_base_prices_non_draft_order(order_with_lines):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.save(update_fields=["status"])

    line_1, line_2 = order.lines.all()
    variant_1, variant_2 = line_1.variant, line_2.variant

    initial_variant_1_price = line_1.undiscounted_base_unit_price_amount
    initial_variant_2_price = line_2.undiscounted_base_unit_price_amount

    # change variant 1 pricing
    channel_listing_1 = variant_1.channel_listings.get()
    assert initial_variant_1_price == channel_listing_1.price_amount
    assert initial_variant_1_price == channel_listing_1.discounted_price_amount
    new_variant_1_price = initial_variant_1_price + Decimal(1)
    channel_listing_1.price_amount = new_variant_1_price
    channel_listing_1.discounted_price_amount = new_variant_1_price
    channel_listing_1.save(update_fields=["price_amount", "discounted_price_amount"])

    # change variant 2 pricing
    channel_listing_2 = variant_2.channel_listings.get()
    assert initial_variant_2_price == channel_listing_2.price_amount
    assert initial_variant_2_price == channel_listing_2.discounted_price_amount
    new_variant_2_price = initial_variant_2_price - Decimal(2)
    channel_listing_2.price_amount = new_variant_2_price
    channel_listing_2.discounted_price_amount = new_variant_2_price
    channel_listing_2.save(update_fields=["price_amount", "discounted_price_amount"])

    line_ids_to_refresh = [line_1.id, line_2.id]

    # when
    refresh_order_base_prices_and_discounts(order, line_ids_to_refresh)

    # then
    line_1, line_2 = order.lines.all()
    assert line_1.undiscounted_base_unit_price_amount == initial_variant_1_price
    assert line_1.base_unit_price_amount == initial_variant_1_price
    assert line_2.undiscounted_base_unit_price_amount == initial_variant_2_price
    assert line_2.base_unit_price_amount == initial_variant_2_price


def test_refresh_order_base_prices_no_lines_no_error(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    line_1, line_2 = lines
    line_ids_to_refresh = [line_1.id, line_2.id]
    lines.delete()

    # when & then
    refresh_order_base_prices_and_discounts(order, line_ids_to_refresh)
