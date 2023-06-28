from decimal import Decimal

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from ....product.models import VariantChannelListingPromotionRule
from ... import DiscountType, RewardValueType
from ...models import CheckoutLineDiscount, PromotionRule
from ...utils import create_or_update_discount_objects_from_promotion_for_checkout


def test_create_or_update_discount_objects_from_promotion_for_checkout_no_discount(
    checkout_lines_info,
):
    # when
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_lines_info)

    # then
    for checkout_line_info in checkout_lines_info:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_create_fixed_discount(checkout_lines_info, promotion_without_rules):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("2")
    rule = promotion_without_rules.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product_line1.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(line_info1.channel)

    listing = line_info1.channel_listing
    discounted_price = listing.price.amount - reward_value
    listing.discounted_price_amount = discounted_price
    listing.save(update_fields=["discounted_price_amount"])

    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=line_info1.channel.currency_code,
    )

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_lines_info)

    # then
    assert len(line_info1.discounts) == 1
    now = timezone.now()
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.created_at == discount_from_db.created_at == now
    assert discount_from_info.type == discount_from_db.type == DiscountType.PROMOTION
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == RewardValueType.FIXED
    )
    assert discount_from_info.value == discount_from_db.value == rule.reward_value
    assert (
        discount_from_info.amount_value == discount_from_db.amount_value == reward_value
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == rule.name
    assert discount_from_info.reason == discount_from_db.reason is None
    assert discount_from_info.promotion_rule == discount_from_db.promotion_rule == rule
    assert discount_from_info.voucher == discount_from_db.voucher is None
    assert discount_from_info.sale == discount_from_db.sale is None

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_create_fixed_discount_multiple_quantity_in_lines(
    checkout_lines_with_multiple_quantity_info, promotion_without_rules
):
    # given
    line_info1 = checkout_lines_with_multiple_quantity_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("2")
    rule = promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product_line1.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(line_info1.channel)

    listing = line_info1.channel_listing
    discounted_price = listing.price.amount - reward_value
    listing.discounted_price_amount = discounted_price
    listing.save(update_fields=["discounted_price_amount"])

    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=line_info1.channel.currency_code,
    )
    expected_discount_amount = reward_value * line_info1.line.quantity

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_lines_with_multiple_quantity_info
    )

    # then
    assert len(line_info1.discounts) == 1
    now = timezone.now()
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.created_at == discount_from_db.created_at == now
    assert discount_from_info.type == discount_from_db.type == DiscountType.PROMOTION
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == RewardValueType.FIXED
    )
    assert discount_from_info.value == discount_from_db.value == rule.reward_value
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert (
        discount_from_info.name == discount_from_db.name == promotion_without_rules.name
    )
    assert discount_from_info.reason == discount_from_db.reason is None
    assert discount_from_info.promotion_rule == discount_from_db.promotion_rule == rule
    assert discount_from_info.voucher == discount_from_db.voucher is None
    assert discount_from_info.sale == discount_from_db.sale is None

    for checkout_line_info in checkout_lines_with_multiple_quantity_info[1:]:
        assert not checkout_line_info.discounts


def test_create_fixed_discount_multiple_quantity_in_lines_discount_bigger_than_total(
    checkout_lines_with_multiple_quantity_info, promotion_without_rules
):
    # given
    line_info1 = checkout_lines_with_multiple_quantity_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal(15)
    rule = promotion_without_rules.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product_line1.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(line_info1.channel)

    listing = line_info1.channel_listing
    discounted_price = Decimal("0")
    listing.discounted_price_amount = discounted_price
    listing.save(update_fields=["discounted_price_amount"])

    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=min(reward_value, listing.price.amount),
        currency=line_info1.channel.currency_code,
    )
    expected_discount_amount = (listing.price * line_info1.line.quantity).amount

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_lines_with_multiple_quantity_info
    )

    # then
    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.type == discount_from_db.type == DiscountType.PROMOTION
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == RewardValueType.FIXED
    )
    assert discount_from_info.value == discount_from_db.value == rule.reward_value
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )

    for checkout_line_info in checkout_lines_with_multiple_quantity_info[1:]:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_create_percentage_discount(checkout_lines_info, promotion_without_rules):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("10")
    rule = promotion_without_rules.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product_line1.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=reward_value,
    )
    rule.channels.add(line_info1.channel)

    listing = line_info1.channel_listing
    discount_amount = reward_value / 100 * listing.price.amount
    discounted_price = listing.price.amount - discount_amount
    listing.discounted_price_amount = discounted_price
    listing.save(update_fields=["discounted_price_amount"])

    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=discount_amount,
        currency=line_info1.channel.currency_code,
    )

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_lines_info)

    # then
    assert len(line_info1.discounts) == 1
    now = timezone.now()
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.created_at == discount_from_db.created_at == now
    assert discount_from_info.type == discount_from_db.type == DiscountType.PROMOTION
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == RewardValueType.PERCENTAGE
    )
    assert discount_from_info.value == discount_from_db.value == rule.reward_value
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == rule.name
    assert discount_from_info.reason == discount_from_db.reason is None
    assert discount_from_info.promotion_rule == discount_from_db.promotion_rule == rule
    assert discount_from_info.voucher == discount_from_db.voucher is None
    assert discount_from_info.sale == discount_from_db.sale is None

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_create_percentage_discount_multiple_quantity_in_lines(
    checkout_lines_with_multiple_quantity_info, promotion_without_rules
):
    # given
    line_info1 = checkout_lines_with_multiple_quantity_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("10")
    rule = promotion_without_rules.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product_line1.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=reward_value,
    )
    rule.channels.add(line_info1.channel)

    listing = line_info1.channel_listing
    discount_amount = reward_value / 100 * listing.price.amount
    discounted_price = listing.price.amount - discount_amount
    listing.discounted_price_amount = discounted_price
    listing.save(update_fields=["discounted_price_amount"])

    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=discount_amount,
        currency=line_info1.channel.currency_code,
    )

    expected_discount_amount = discount_amount * line_info1.line.quantity

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_lines_with_multiple_quantity_info
    )

    # then
    assert len(line_info1.discounts) == 1
    now = timezone.now()
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert discount_from_info.created_at == discount_from_db.created_at == now
    assert discount_from_info.type == discount_from_db.type == DiscountType.PROMOTION
    assert (
        discount_from_info.value_type
        == discount_from_db.value_type
        == RewardValueType.PERCENTAGE
    )
    assert discount_from_info.value == discount_from_db.value == rule.reward_value
    assert (
        discount_from_info.amount_value
        == discount_from_db.amount_value
        == expected_discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert discount_from_info.name == discount_from_db.name == rule.name
    assert discount_from_info.reason == discount_from_db.reason is None
    assert discount_from_info.promotion_rule == discount_from_db.promotion_rule == rule
    assert discount_from_info.voucher == discount_from_db.voucher is None
    assert discount_from_info.sale == discount_from_db.sale is None

    for checkout_line_info in checkout_lines_with_multiple_quantity_info[1:]:
        assert not checkout_line_info.discounts


def test_create_discount_multiple_rules_applied(
    checkout_lines_info, promotion_without_rules
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value_1 = Decimal("2")
    reward_value_2 = Decimal("10")
    rule_1, rule_2 = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Percentage promotion rule 1",
                promotion=promotion_without_rules,
                reward_value_type=RewardValueType.FIXED,
                reward_value=reward_value_1,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product_line1.id)]
                    }
                },
            ),
            PromotionRule(
                name="Percentage promotion rule 2",
                promotion=promotion_without_rules,
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=reward_value_2,
                catalogue_predicate={
                    "variantPredicate": {
                        "ids": [
                            graphene.Node.to_global_id(
                                "ProductVariant", line_info1.variant.id
                            )
                        ]
                    }
                },
            ),
        ]
    )

    rule_1.channels.add(line_info1.channel)
    rule_2.channels.add(line_info1.channel)

    listing = line_info1.channel_listing
    discount_amount_2 = reward_value_2 / 100 * listing.price.amount
    discounted_price = listing.price.amount - reward_value_1 - discount_amount_2
    listing.discounted_price_amount = discounted_price
    listing.save(update_fields=["discounted_price_amount"])

    VariantChannelListingPromotionRule.objects.bulk_create(
        [
            VariantChannelListingPromotionRule(
                variant_channel_listing=listing,
                promotion_rule=rule_1,
                discount_amount=reward_value_1,
                currency=line_info1.channel.currency_code,
            ),
            VariantChannelListingPromotionRule(
                variant_channel_listing=listing,
                promotion_rule=rule_2,
                discount_amount=discount_amount_2,
                currency=line_info1.channel.currency_code,
            ),
        ]
    )

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_lines_info)

    # then
    assert len(line_info1.discounts) == 2
    discount_for_rule_1 = line_info1.line.discounts.get(promotion_rule=rule_1)
    discount_for_rule_2 = line_info1.line.discounts.get(promotion_rule=rule_2)

    assert discount_for_rule_1.line == line_info1.line
    assert discount_for_rule_2.line == line_info1.line

    assert discount_for_rule_1.type == DiscountType.PROMOTION
    assert discount_for_rule_2.type == DiscountType.PROMOTION

    assert discount_for_rule_1.value_type == RewardValueType.FIXED
    assert discount_for_rule_2.value_type == RewardValueType.PERCENTAGE

    assert discount_for_rule_1.value == reward_value_1
    assert discount_for_rule_2.value == reward_value_2

    assert discount_for_rule_1.amount_value == reward_value_1
    assert discount_for_rule_2.amount_value == discount_amount_2

    assert discount_for_rule_1.currency == "USD"
    assert discount_for_rule_2.currency == "USD"

    assert discount_for_rule_1.promotion_rule == rule_1
    assert discount_for_rule_2.promotion_rule == rule_2

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_two_promotions_applied_to_two_different_lines(
    checkout_lines_info, promotion_without_rules
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    line_info2 = checkout_lines_info[1]
    product_line2 = line_info2.product

    reward_value_1 = Decimal("2")
    reward_value_2 = Decimal("1")
    rule_1, rule_2 = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Percentage promotion rule 1",
                promotion=promotion_without_rules,
                reward_value_type=RewardValueType.FIXED,
                reward_value=reward_value_1,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product_line1.id)]
                    }
                },
            ),
            PromotionRule(
                name="Percentage promotion rule 2",
                promotion=promotion_without_rules,
                reward_value_type=RewardValueType.FIXED,
                reward_value=reward_value_2,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product_line2.id)]
                    }
                },
            ),
        ]
    )

    rule_1.channels.add(line_info1.channel)
    rule_2.channels.add(line_info2.channel)

    listing_1 = line_info1.channel_listing
    discounted_price = listing_1.price.amount - reward_value_1
    listing_1.discounted_price_amount = discounted_price
    listing_1.save(update_fields=["discounted_price_amount"])

    listing_2 = line_info2.channel_listing
    discounted_price = listing_2.price.amount - reward_value_2
    listing_2.discounted_price_amount = discounted_price
    listing_2.save(update_fields=["discounted_price_amount"])

    VariantChannelListingPromotionRule.objects.bulk_create(
        [
            VariantChannelListingPromotionRule(
                variant_channel_listing=listing_1,
                promotion_rule=rule_1,
                discount_amount=reward_value_1,
                currency=line_info1.channel.currency_code,
            ),
            VariantChannelListingPromotionRule(
                variant_channel_listing=listing_2,
                promotion_rule=rule_2,
                discount_amount=reward_value_2,
                currency=line_info1.channel.currency_code,
            ),
        ]
    )

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_lines_info)

    # then
    assert len(line_info1.discounts) == 1
    discount_from_info_1 = line_info1.discounts[0]
    discount_from_db_1 = line_info1.line.discounts.get()
    assert discount_from_info_1.line == discount_from_db_1.line == line_info1.line
    assert (
        discount_from_info_1.type == discount_from_db_1.type == DiscountType.PROMOTION
    )
    assert (
        discount_from_info_1.value_type
        == discount_from_db_1.value_type
        == RewardValueType.FIXED
    )
    assert discount_from_info_1.value == discount_from_db_1.value == rule_1.reward_value
    assert (
        discount_from_info_1.amount_value
        == discount_from_db_1.amount_value
        == reward_value_1
    )
    assert discount_from_info_1.currency == discount_from_db_1.currency == "USD"
    assert discount_from_info_1.name == discount_from_db_1.name == rule_1.name
    assert discount_from_info_1.reason == discount_from_db_1.reason is None
    assert (
        discount_from_info_1.promotion_rule
        == discount_from_db_1.promotion_rule
        == rule_1
    )

    assert len(line_info2.discounts) == 1
    discount_from_info_2 = line_info2.discounts[0]
    discount_from_db_2 = line_info2.line.discounts.get()
    assert discount_from_info_2.line == discount_from_db_2.line == line_info2.line
    assert (
        discount_from_info_2.type == discount_from_db_2.type == DiscountType.PROMOTION
    )
    assert (
        discount_from_info_2.value_type
        == discount_from_db_2.value_type
        == RewardValueType.FIXED
    )
    assert discount_from_info_2.value == discount_from_db_2.value == rule_2.reward_value
    assert (
        discount_from_info_2.amount_value
        == discount_from_db_2.amount_value
        == reward_value_2
    )
    assert discount_from_info_2.currency == discount_from_db_2.currency == "USD"
    assert discount_from_info_2.name == discount_from_db_2.name == rule_2.name
    assert discount_from_info_2.reason == discount_from_db_2.reason is None
    assert (
        discount_from_info_2.promotion_rule
        == discount_from_db_2.promotion_rule
        == rule_2
    )


def test_promotion_not_valid_anymore(checkout_lines_info, promotion_without_rules):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("2")
    rule = promotion_without_rules.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product_line1.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )

    listing = line_info1.channel_listing

    listing.discounted_price_amount = listing.price.amount
    listing.save(update_fields=["discounted_price_amount"])

    line_discount = CheckoutLineDiscount.objects.create(
        line=line_info1.line,
        value_type=RewardValueType.FIXED,
        value=reward_value,
        currency=line_info1.channel.currency_code,
        type=DiscountType.PROMOTION,
        promotion_rule=rule,
    )

    line_info1.discounts = [line_discount]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_lines_info)

    # then
    assert len(line_info1.discounts) == 0
    with pytest.raises(CheckoutLineDiscount.DoesNotExist):
        line_discount.refresh_from_db()


def test_one_of_promotion_rule_not_valid_anymore_one_updated(
    checkout_lines_info, promotion_without_rules
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value_1 = Decimal("2")
    reward_value_2 = Decimal("10")
    rule_1, rule_2 = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Percentage promotion rule 1",
                promotion=promotion_without_rules,
                reward_value_type=RewardValueType.FIXED,
                reward_value=reward_value_1,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product_line1.id)]
                    }
                },
            ),
            PromotionRule(
                name="Percentage promotion rule 2",
                promotion=promotion_without_rules,
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=reward_value_2,
                catalogue_predicate={
                    "variantPredicate": {
                        "ids": [
                            graphene.Node.to_global_id(
                                "ProductVariant", line_info1.variant.id
                            )
                        ]
                    }
                },
            ),
        ]
    )

    rule_1.channels.add(line_info1.channel)

    listing = line_info1.channel_listing
    discount_amount_2 = reward_value_2 / 100 * listing.price.amount
    discounted_price = listing.price.amount - reward_value_1 - discount_amount_2
    listing.discounted_price_amount = discounted_price
    listing.save(update_fields=["discounted_price_amount"])

    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule_1,
        discount_amount=reward_value_1,
        currency=line_info1.channel.currency_code,
    )

    line_discount_1, line_discount_2 = CheckoutLineDiscount.objects.bulk_create(
        [
            CheckoutLineDiscount(
                line=line_info1.line,
                value_type=RewardValueType.PERCENTAGE,
                value=Decimal("10"),
                currency=line_info1.channel.currency_code,
                type=DiscountType.PROMOTION,
                promotion_rule=rule_1,
            ),
            CheckoutLineDiscount(
                line=line_info1.line,
                value_type=RewardValueType.FIXED,
                value=reward_value_2,
                currency=line_info1.channel.currency_code,
                type=DiscountType.PROMOTION,
                promotion_rule=rule_2,
            ),
        ]
    )
    line_info1.discounts = [line_discount_1, line_discount_2]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_lines_info)

    # then
    assert len(line_info1.discounts) == 1

    with pytest.raises(CheckoutLineDiscount.DoesNotExist):
        line_discount_2.refresh_from_db()

    discount_from_info = line_info1.discounts[0]
    line_discount_1.refresh_from_db()
    assert discount_from_info.line == line_discount_1.line == line_info1.line
    assert discount_from_info.type == line_discount_1.type == DiscountType.PROMOTION
    assert (
        discount_from_info.value_type
        == line_discount_1.value_type
        == RewardValueType.FIXED
    )
    assert discount_from_info.value == line_discount_1.value == rule_1.reward_value
    assert discount_from_info.name == line_discount_1.name == rule_1.name
    assert (
        discount_from_info.amount_value
        == line_discount_1.amount_value
        == reward_value_1
    )

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_discounts_updated(
    checkout_lines_info,
    checkout_info,
    new_sale_percentage,
    sale_1_usd,
):
    pass
