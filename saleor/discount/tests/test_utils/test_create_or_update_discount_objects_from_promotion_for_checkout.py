from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import before_after
import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time
from prices import Money, TaxedMoney

from ....checkout.base_calculations import base_checkout_total
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....discount.interface import VariantPromotionRuleInfo
from ....plugins.manager import get_plugins_manager
from ....product.models import (
    ProductChannelListing,
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
)
from ... import DiscountType, RewardType, RewardValueType
from ...models import CheckoutDiscount, CheckoutLineDiscount, PromotionRule
from ...utils.checkout import (
    create_checkout_discount_objects_for_order_promotions,
    create_checkout_line_discount_objects_for_catalogue_promotions,
    create_or_update_discount_objects_from_promotion_for_checkout,
)
from ...utils.promotion import (
    _get_best_gift_reward,
)


def test_create_or_update_discount_objects_from_promotion_for_checkout_no_discount(
    checkout_info,
    checkout_lines_info,
):
    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    for checkout_line_info in checkout_lines_info:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_create_fixed_discount(
    checkout_info,
    checkout_lines_info,
    catalogue_promotion_without_rules,
    promotion_translation_fr,
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("2")
    rule = catalogue_promotion_without_rules.rules.create(
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

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=line_info1.channel.currency_code,
    )
    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=promotion_translation_fr,
            rule_translation=None,
        )
    ]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
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
        discount_from_info.amount_value == discount_from_db.amount_value == reward_value
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert (
        discount_from_info.name
        == discount_from_db.name
        == f"{catalogue_promotion_without_rules.name}: {rule.name}"
    )
    promotion_id = graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.pk
    )
    assert (
        discount_from_info.reason
        == discount_from_db.reason
        == f"Promotion: {promotion_id}"
    )
    assert discount_from_info.promotion_rule == discount_from_db.promotion_rule == rule
    assert discount_from_info.voucher == discount_from_db.voucher is None
    assert (
        discount_from_info.translated_name
        == discount_from_db.translated_name
        == promotion_translation_fr.name
    )
    assert (
        discount_from_info.unique_type
        == discount_from_db.unique_type
        == DiscountType.PROMOTION
    )

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_update_catalogue_discount(
    checkout_info,
    checkout_lines_info,
    catalogue_promotion_without_rules,
    promotion_translation_fr,
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    actual_reward_value = Decimal("5")
    discount_to_update = line_info1.line.discounts.create(
        type=DiscountType.PROMOTION,
        value_type=RewardValueType.FIXED,
        value=actual_reward_value,
        name="Fixed 5 catalogue discount",
        currency=line_info1.channel.currency_code,
        amount_value=actual_reward_value * line_info1.line.quantity,
    )
    checkout_lines_info[0].discounts.append(discount_to_update)

    reward_value = Decimal("7")
    assert reward_value > actual_reward_value
    rule = catalogue_promotion_without_rules.rules.create(
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

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=line_info1.channel.currency_code,
    )
    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=promotion_translation_fr,
            rule_translation=None,
        )
    ]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert len(line_info1.discounts) == 1
    assert CheckoutLineDiscount.objects.count() == 1

    discount = line_info1.discounts[0]
    assert discount.id == discount_to_update.id
    assert discount.value == reward_value
    assert discount.promotion_rule_id == rule.id
    assert discount.amount_value == reward_value * line_info1.line.quantity
    assert discount.unique_type == DiscountType.PROMOTION


@freeze_time("2020-12-12 12:00:00")
def test_create_fixed_discount_multiple_quantity_in_lines(
    checkout_info,
    checkout_lines_with_multiple_quantity_info,
    catalogue_promotion_without_rules,
):
    # given
    line_info1 = checkout_lines_with_multiple_quantity_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("2")
    rule = catalogue_promotion_without_rules.rules.create(
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

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=line_info1.channel.currency_code,
    )
    expected_discount_amount = reward_value * line_info1.line.quantity

    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_with_multiple_quantity_info
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
        discount_from_info.name
        == discount_from_db.name
        == catalogue_promotion_without_rules.name
    )
    promotion_id = graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.pk
    )
    assert (
        discount_from_info.reason
        == discount_from_db.reason
        == f"Promotion: {promotion_id}"
    )
    assert discount_from_info.promotion_rule == discount_from_db.promotion_rule == rule
    assert discount_from_info.voucher == discount_from_db.voucher is None

    for checkout_line_info in checkout_lines_with_multiple_quantity_info[1:]:
        assert not checkout_line_info.discounts


def test_create_fixed_discount_multiple_quantity_in_lines_discount_bigger_than_total(
    checkout_info,
    checkout_lines_with_multiple_quantity_info,
    catalogue_promotion_without_rules,
):
    # given
    line_info1 = checkout_lines_with_multiple_quantity_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal(15)
    rule = catalogue_promotion_without_rules.rules.create(
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

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=min(reward_value, listing.price.amount),
        currency=line_info1.channel.currency_code,
    )

    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]

    expected_discount_amount = (listing.price * line_info1.line.quantity).amount

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_with_multiple_quantity_info
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
def test_create_percentage_discount(
    checkout_info, checkout_lines_info, catalogue_promotion_without_rules
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("10")
    rule = catalogue_promotion_without_rules.rules.create(
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

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=discount_amount,
        currency=line_info1.channel.currency_code,
    )

    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
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
        == discount_amount
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert (
        discount_from_info.name
        == discount_from_db.name
        == f"{catalogue_promotion_without_rules.name}: {rule.name}"
    )
    promotion_id = graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.pk
    )
    assert (
        discount_from_info.reason
        == discount_from_db.reason
        == f"Promotion: {promotion_id}"
    )
    assert discount_from_info.promotion_rule == discount_from_db.promotion_rule == rule
    assert discount_from_info.voucher == discount_from_db.voucher is None

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


@freeze_time("2020-12-12 12:00:00")
def test_create_percentage_discount_multiple_quantity_in_lines(
    checkout_info,
    checkout_lines_with_multiple_quantity_info,
    catalogue_promotion_without_rules,
):
    # given
    line_info1 = checkout_lines_with_multiple_quantity_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("10")
    rule = catalogue_promotion_without_rules.rules.create(
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

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=discount_amount,
        currency=line_info1.channel.currency_code,
    )

    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]

    expected_discount_amount = discount_amount * line_info1.line.quantity

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_with_multiple_quantity_info
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
    discount_name = f"{catalogue_promotion_without_rules.name}: {rule.name}"
    assert discount_from_info.name == discount_from_db.name == discount_name
    promotion_id = graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.pk
    )
    assert (
        discount_from_info.reason
        == discount_from_db.reason
        == f"Promotion: {promotion_id}"
    )
    assert discount_from_info.promotion_rule == discount_from_db.promotion_rule == rule
    assert discount_from_info.voucher == discount_from_db.voucher is None

    for checkout_line_info in checkout_lines_with_multiple_quantity_info[1:]:
        assert not checkout_line_info.discounts


def test_two_promotions_applied_to_two_different_lines(
    checkout_info, checkout_lines_info, catalogue_promotion_without_rules
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
                promotion=catalogue_promotion_without_rules,
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
                promotion=catalogue_promotion_without_rules,
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

    (
        listing_promotion_rule_1,
        listing_promotion_rule_2,
    ) = VariantChannelListingPromotionRule.objects.bulk_create(
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

    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule_1,
            variant_listing_promotion_rule=listing_promotion_rule_1,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]
    line_info2.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule_2,
            variant_listing_promotion_rule=listing_promotion_rule_2,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

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
    assert (
        discount_from_info_1.name
        == discount_from_db_1.name
        == f"{catalogue_promotion_without_rules.name}: {rule_1.name}"
    )
    promotion_id = graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.pk
    )
    assert (
        discount_from_info_1.reason
        == discount_from_db_1.reason
        == f"Promotion: {promotion_id}"
    )
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
    assert (
        discount_from_info_2.name
        == discount_from_db_2.name
        == f"{catalogue_promotion_without_rules.name}: {rule_2.name}"
    )
    promotion_id = graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.pk
    )
    assert (
        discount_from_info_2.reason
        == discount_from_db_2.reason
        == f"Promotion: {promotion_id}"
    )
    assert (
        discount_from_info_2.promotion_rule
        == discount_from_db_2.promotion_rule
        == rule_2
    )


@freeze_time("2020-12-12 12:00:00")
def test_create_percentage_discount_1_cent_variant_on_10_percentage_discount(
    checkout_info, checkout_lines_info, catalogue_promotion_without_rules
):
    # given
    line_info1 = checkout_lines_info[0]
    quantity = 10
    line_info1.line.quantity = quantity
    line_info1.line.save(update_fields=["quantity"])

    product_line1 = line_info1.product

    reward_value = Decimal("10")
    rule = catalogue_promotion_without_rules.rules.create(
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

    # Set product price to 0.01 USD
    variant_price = Decimal("0.01")
    listing.price_amount = variant_price
    listing.discounted_price_amount = variant_price
    listing.save()

    discount_amount = reward_value / 100 * listing.price.amount
    discounted_price = listing.price.amount - discount_amount
    listing.discounted_price_amount = discounted_price
    listing.save(update_fields=["discounted_price_amount"])

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=discount_amount,
        currency=line_info1.channel.currency_code,
    )

    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
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
        == discount_amount * quantity
    )
    assert discount_from_info.currency == discount_from_db.currency == "USD"
    assert (
        discount_from_info.name
        == discount_from_db.name
        == f"{catalogue_promotion_without_rules.name}: {rule.name}"
    )
    promotion_id = graphene.Node.to_global_id(
        "Promotion", catalogue_promotion_without_rules.pk
    )
    assert (
        discount_from_info.reason
        == discount_from_db.reason
        == f"Promotion: {promotion_id}"
    )
    assert discount_from_info.promotion_rule == discount_from_db.promotion_rule == rule
    assert discount_from_info.voucher == discount_from_db.voucher is None

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_promotion_not_valid_anymore(
    checkout_info, checkout_lines_info, catalogue_promotion_without_rules
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("2")
    rule = catalogue_promotion_without_rules.rules.create(
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
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert len(line_info1.discounts) == 0
    with pytest.raises(CheckoutLineDiscount.DoesNotExist):
        line_discount.refresh_from_db()


def test_one_of_promotion_rule_not_valid_anymore_one_updated(
    checkout_info, checkout_lines_info, catalogue_promotion_without_rules
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
                promotion=catalogue_promotion_without_rules,
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
                promotion=catalogue_promotion_without_rules,
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

    listing_promotion_rule_1 = VariantChannelListingPromotionRule.objects.create(
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

    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule_1,
            variant_listing_promotion_rule=listing_promotion_rule_1,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

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
    assert (
        discount_from_info.name
        == line_discount_1.name
        == f"{catalogue_promotion_without_rules.name}: {rule_1.name}"
    )
    assert (
        discount_from_info.amount_value
        == line_discount_1.amount_value
        == reward_value_1
    )

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_gift_promotion_not_valid_anymore(
    checkout_with_item_and_gift_promotion,
):
    # given
    checkout = checkout_with_item_and_gift_promotion

    # reduce quantity so the checkout will not apply for gift promotion anymore
    line = checkout.lines.get(is_gift=False)
    line.quantity = 1
    line.save(update_fields=["quantity"])

    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)

    gift_line_info = [line_info for line_info in lines if line_info.line.is_gift][0]
    line_discount = gift_line_info.discounts[0]
    gift_line = line_discount.line

    lines_count = len(lines)

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_info, lines)

    # then
    assert len(lines) == lines_count - 1 == checkout.lines.count()
    with pytest.raises(line_discount._meta.model.DoesNotExist):
        line_discount.refresh_from_db()
    with pytest.raises(gift_line._meta.model.DoesNotExist):
        gift_line.refresh_from_db()


def test_create_discount_with_promotion_translation(
    checkout_info,
    checkout_lines_info,
    catalogue_promotion_without_rules,
    promotion_translation_fr,
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("2")
    rule = catalogue_promotion_without_rules.rules.create(
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

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=line_info1.channel.currency_code,
    )
    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=promotion_translation_fr,
            rule_translation=None,
        )
    ]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert (
        discount_from_info.translated_name
        == discount_from_db.translated_name
        == promotion_translation_fr.name
    )

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_discount_with_rule_translation(
    checkout_info,
    checkout_lines_info,
    catalogue_promotion_without_rules,
    promotion_rule_translation_fr,
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("2")
    rule = catalogue_promotion_without_rules.rules.create(
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

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=line_info1.channel.currency_code,
    )
    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=promotion_rule_translation_fr,
        )
    ]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert (
        discount_from_info.translated_name
        == discount_from_db.translated_name
        == promotion_rule_translation_fr.name
    )

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_discount_with_promotion_and_rule_translation(
    checkout_info,
    checkout_lines_info,
    catalogue_promotion_without_rules,
    promotion_translation_fr,
    promotion_rule_translation_fr,
):
    # given
    line_info1 = checkout_lines_info[0]
    product_line1 = line_info1.product

    reward_value = Decimal("2")
    rule = catalogue_promotion_without_rules.rules.create(
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

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=line_info1.channel.currency_code,
    )
    line_info1.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=promotion_translation_fr,
            rule_translation=promotion_rule_translation_fr,
        )
    ]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert len(line_info1.discounts) == 1
    discount_from_info = line_info1.discounts[0]
    discount_from_db = line_info1.line.discounts.get()
    assert discount_from_info.line == discount_from_db.line == line_info1.line
    assert (
        discount_from_info.translated_name
        == discount_from_db.translated_name
        == f"{promotion_translation_fr.name}: {promotion_rule_translation_fr.name}"
    )

    for checkout_line_info in checkout_lines_info[1:]:
        assert not checkout_line_info.discounts


def test_create_or_update_discount_for_gift_promotion_line(
    checkout_with_item_and_gift_promotion,
    catalogue_promotion_without_rules,
):
    # given
    checkout = checkout_with_item_and_gift_promotion
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    gift_line_info = [line_info for line_info in lines if line_info.line.is_gift][0]
    gift_line_discount = gift_line_info.line.discounts.first()
    gift_product = gift_line_info.line.variant.product

    reward_value = Decimal("2")
    rule = catalogue_promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", gift_product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(checkout.channel)

    listing = gift_line_info.channel_listing
    discounted_price = listing.price.amount - reward_value
    listing.discounted_price_amount = discounted_price
    listing.save(update_fields=["discounted_price_amount"])

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=gift_line_info.channel.currency_code,
    )

    gift_line_info.rules_info = [
        VariantPromotionRuleInfo(
            rule=rule,
            variant_listing_promotion_rule=listing_promotion_rule,
            promotion=catalogue_promotion_without_rules,
            promotion_translation=None,
            rule_translation=None,
        )
    ]
    gift_line_info.discounts = [gift_line_discount]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(checkout_info, lines)

    # then
    assert len(gift_line_info.discounts) == 1
    discount_from_info = gift_line_info.discounts[0]
    assert gift_line_info.line.discounts.count() == 1
    assert discount_from_info == gift_line_discount
    assert discount_from_info.line == gift_line_info.line
    assert discount_from_info.type == DiscountType.ORDER_PROMOTION


def test_create_or_update_discount_objects_from_promotion_for_checkout_voucher_set(
    checkout_info, checkout_lines_info, order_promotion_rule, voucher
):
    # given
    checkout_info.voucher = voucher
    checkout_info.checkout.voucher_code = voucher.code

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert not checkout_info.discounts
    assert not checkout_info.checkout.discounts.all()


@patch("saleor.discount.utils.checkout.base_checkout_delivery_price")
@patch("saleor.discount.utils.checkout.base_checkout_subtotal")
def test_create_or_update_discount_objects_from_promotion_no_applicable_rules(
    base_checkout_subtotal_mock,
    base_checkout_delivery_price_mock,
    checkout_info,
    checkout_lines_info,
    order_promotion_rule,
    voucher,
):
    # given
    checkout = checkout_info.checkout
    currency = checkout.currency
    price = Money("10", currency)
    base_checkout_subtotal_mock.return_value = price
    base_checkout_delivery_price_mock.return_value = Money("0", currency)
    checkout.total = TaxedMoney(net=price, gross=price)

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert not checkout_info.discounts
    assert not checkout_info.checkout.discounts.all()


def test_create_or_update_discount_objects_from_promotion(
    checkout_info,
    checkout_lines_info,
    order_promotion_without_rules,
):
    # given
    promotion = order_promotion_without_rules
    checkout = checkout_info.checkout
    price = Money("30", checkout_info.checkout.currency)
    checkout.total = TaxedMoney(net=price, gross=price)
    checkout.subtotal = TaxedMoney(net=price, gross=price)
    checkout.save(
        update_fields=[
            "total_net_amount",
            "total_gross_amount",
            "subtotal_net_amount",
            "subtotal_gross_amount",
        ]
    )

    rules = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Order promotion rule 1",
                promotion=promotion,
                order_predicate={
                    "discountedObjectPredicate": {
                        "baseTotalPrice": {
                            "range": {
                                "gte": 10,
                            }
                        }
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("25"),
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
            PromotionRule(
                name="Order promotion rule 2",
                promotion=promotion,
                order_predicate={
                    "discountedObjectPredicate": {
                        "baseTotalPrice": {
                            "range": {
                                "gte": 20,
                            }
                        }
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("50"),
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
        ]
    )
    for rule in rules:
        rule.channels.add(checkout_info.channel)

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert checkout_info.checkout.discounts.count() == 1
    assert len(checkout_info.discounts) == 1
    assert checkout_info.discounts[0].promotion_rule == rules[1]


@patch("saleor.discount.utils.checkout.base_checkout_delivery_price")
@patch("saleor.discount.utils.checkout.base_checkout_subtotal")
def test_create_or_update_discount_objects_from_promotion_best_rule_applies(
    subtotal_mock,
    delivery_price_mock,
    checkout_info,
    checkout_lines_info,
    order_promotion_without_rules,
):
    # given
    promotion = order_promotion_without_rules
    checkout = checkout_info.checkout

    delivery_price = Money("10", checkout_info.checkout.currency)
    price = Money("30", checkout_info.checkout.currency)
    checkout.total = TaxedMoney(net=price, gross=price)
    checkout.subtotal = TaxedMoney(net=price, gross=price)
    checkout.save(
        update_fields=[
            "total_net_amount",
            "total_gross_amount",
            "subtotal_net_amount",
            "subtotal_gross_amount",
        ]
    )

    subtotal_mock.return_value = price
    delivery_price_mock.return_value = delivery_price

    rules = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Order promotion rule 1",
                promotion=promotion,
                order_predicate={
                    "discountedObjectPredicate": {
                        "baseTotalPrice": {
                            "range": {
                                "gte": 10,
                            }
                        }
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=Decimal("12"),
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
            PromotionRule(
                name="Order promotion rule 2",
                promotion=promotion,
                order_predicate={
                    "discountedObjectPredicate": {
                        "baseTotalPrice": {
                            "range": {
                                "gte": 20,
                            }
                        }
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("25"),
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
            PromotionRule(
                name="Order promotion rule 1",
                promotion=promotion,
                order_predicate={
                    "discountedObjectPredicate": {
                        "baseTotalPrice": {
                            "range": {
                                "gte": 100,
                            }
                        }
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("50"),
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
        ]
    )
    for rule in rules:
        rule.channels.add(checkout_info.channel)

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    checkout = checkout_info.checkout
    assert checkout.discounts.count() == 1
    assert checkout.discount_amount == rules[0].reward_value
    assert len(checkout_info.discounts) == 1
    assert checkout_info.discounts[0].promotion_rule == rules[0]
    discount = checkout_info.discounts[0]
    assert discount.promotion_rule == rules[0]
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.value_type == RewardValueType.FIXED
    assert discount.value == rules[0].reward_value
    assert discount.amount_value == rules[0].reward_value
    assert discount.name == f"{promotion.name}: {rules[0].name}"
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    assert discount.reason == f"Promotion: {promotion_id}"


@patch("saleor.discount.utils.checkout.base_checkout_delivery_price")
@patch("saleor.discount.utils.checkout.base_checkout_subtotal")
def test_create_or_update_discount_objects_from_promotion_subtotal_price_discount(
    subtotal_mock,
    delivery_price_mock,
    checkout_info,
    checkout_lines_info,
    order_promotion_without_rules,
):
    # given
    promotion = order_promotion_without_rules
    checkout = checkout_info.checkout
    lines_count = len(checkout_lines_info)

    delivery_price = Money("10", checkout_info.checkout.currency)
    price = Money("30", checkout_info.checkout.currency)
    checkout.base_subtotal = price
    checkout.base_total = price + delivery_price
    checkout.save(
        update_fields=[
            "base_total_amount",
            "base_subtotal_amount",
        ]
    )

    subtotal_mock.return_value = price
    delivery_price_mock.return_value = delivery_price

    rules = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Order promotion rule 2",
                promotion=promotion,
                order_predicate={
                    "discountedObjectPredicate": {
                        "baseTotalPrice": {
                            "range": {
                                "gte": 20,
                            }
                        }
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("50"),
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
        ]
    )
    for rule in rules:
        rule.channels.add(checkout_info.channel)

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert checkout_info.checkout.discounts.count() == 1
    assert len(checkout_info.discounts) == 1
    assert checkout_info.discounts[0].promotion_rule == rules[0]
    discount = checkout_info.discounts[0]
    assert discount.amount_value == checkout.base_subtotal.amount * Decimal("0.5")
    checkout.refresh_from_db()
    assert checkout.lines.count() == lines_count


def test_create_gift_discount(
    checkout_info,
    checkout_lines_info,
    gift_promotion_rule,
):
    # given
    rule = gift_promotion_rule
    promotion = rule.promotion
    variants = rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_price, variant_id = max(
        variant_listings.values_list("discounted_price_amount", "variant")
    )

    lines_count = len(checkout_lines_info)

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    checkout = checkout_info.checkout
    assert checkout.discounts.count() == 0
    assert checkout.discount_amount == 0
    assert checkout.lines.count() == lines_count + 1
    gift_line = checkout.lines.filter(is_gift=True).first()
    assert gift_line
    assert gift_line.variant_id == variant_id
    discount = gift_line.discounts.first()
    assert discount.promotion_rule == rule
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.value_type == RewardValueType.FIXED
    assert discount.value == top_price
    assert discount.amount_value == top_price
    assert discount.name == f"{promotion.name}: {rule.name}"
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    assert discount.reason == f"Promotion: {promotion_id}"

    assert len(checkout_lines_info) == lines_count + 1
    assert checkout_lines_info[-1].discounts == [discount]


def test_update_gift_discount(
    checkout_with_item_and_gift_promotion, variant, gift_promotion_rule
):
    # given
    checkout = checkout_with_item_and_gift_promotion

    gift_line = checkout.lines.get(is_gift=True)
    gift_line.variant = variant
    gift_line.save(update_fields=["variant"])

    gift_discount = gift_line.discounts.first()
    gift_discount.value = Decimal("2")
    gift_discount.save(update_fields=["value"])

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines_info, get_plugins_manager(allow_replica=False)
    )
    lines_count = len(lines_info)

    rule = gift_promotion_rule
    variants = rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_price, variant_id = max(
        variant_listings.values_list("discounted_price_amount", "variant")
    )

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, lines_info
    )

    # then
    checkout = checkout_info.checkout
    assert checkout.discounts.count() == 0
    assert checkout.discount_amount == 0
    assert len(lines_info) == checkout.lines.count() == lines_count
    gift_line.refresh_from_db()
    assert gift_line
    assert gift_line.variant_id == variant_id
    discount = gift_line.discounts.first()
    assert discount.promotion_rule == rule
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.value_type == RewardValueType.FIXED
    assert discount.value == top_price
    assert discount.amount_value == top_price
    assert discount.name == f"{rule.promotion.name}: {rule.name}"
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion.id)
    assert discount.reason == f"Promotion: {promotion_id}"

    assert lines_info[-1].discounts == [discount]


@patch("saleor.discount.utils.checkout.base_checkout_delivery_price")
@patch("saleor.discount.utils.checkout.base_checkout_subtotal")
def test_create_or_update_discount_objects_from_promotion_gift_rule_applies(
    subtotal_mock,
    delivery_price_mock,
    checkout_info,
    checkout_lines_info,
    gift_promotion_rule,
):
    # given
    checkout = checkout_info.checkout

    promotion = gift_promotion_rule.promotion
    variants = gift_promotion_rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_price, variant_id = max(
        variant_listings.values_list("discounted_price_amount", "variant")
    )
    lines_count = len(checkout_lines_info)
    delivery_price = Money("10", checkout_info.checkout.currency)
    price = Money("30", checkout_info.checkout.currency)
    checkout.total = TaxedMoney(net=price, gross=price)
    checkout.subtotal = TaxedMoney(net=price, gross=price)
    checkout.save(
        update_fields=[
            "total_net_amount",
            "total_gross_amount",
            "subtotal_net_amount",
            "subtotal_gross_amount",
        ]
    )

    subtotal_mock.return_value = price
    delivery_price_mock.return_value = delivery_price

    rules = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Order promotion rule 1",
                promotion=promotion,
                order_predicate={
                    "base_total_price": {
                        "range": {
                            "gte": 10,
                        }
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=top_price - Decimal("1"),
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
            PromotionRule(
                name="Order promotion rule 2",
                promotion=promotion,
                order_predicate={
                    "base_subtotal_price": {
                        "range": {
                            "gte": 20,
                        }
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=top_price - Decimal("2"),
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
            PromotionRule(
                name="Order promotion rule 1",
                promotion=promotion,
                order_predicate={
                    "base_total_price": {
                        "range": {
                            "gte": 100,
                        }
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=top_price + Decimal("10"),
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
        ]
    )
    for rule in rules:
        rule.channels.add(checkout_info.channel)

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    checkout = checkout_info.checkout
    assert checkout.discounts.count() == 0
    assert checkout.discount_amount == 0
    assert checkout.lines.count() == lines_count + 1
    gift_line = checkout.lines.filter(is_gift=True).first()
    assert gift_line
    assert gift_line.variant_id == variant_id
    discount = gift_line.discounts.first()
    assert discount.promotion_rule == gift_promotion_rule
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.value_type == RewardValueType.FIXED
    assert discount.value == top_price
    assert discount.amount_value == top_price
    assert discount.name == f"{promotion.name}: {gift_promotion_rule.name}"
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    assert discount.reason == f"Promotion: {promotion_id}"


@patch("saleor.discount.utils.checkout.base_checkout_delivery_price")
@patch("saleor.discount.utils.checkout.base_checkout_subtotal")
def test_create_or_update_discount_objects_from_promotion_gift_line_removed(
    subtotal_mock,
    delivery_price_mock,
    checkout_with_item_and_gift_promotion,
    gift_promotion_rule,
):
    """Ensure that gift line is removed when there is better discount available."""
    # given
    checkout = checkout_with_item_and_gift_promotion

    promotion = gift_promotion_rule.promotion
    variants = gift_promotion_rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_price, variant_id = max(
        variant_listings.values_list("discounted_price_amount", "variant")
    )
    delivery_price = Money("10", checkout.currency)
    price = Money("30", checkout.currency)
    checkout.total = TaxedMoney(net=price, gross=price)
    checkout.subtotal = TaxedMoney(net=price, gross=price)
    checkout.save(
        update_fields=[
            "total_net_amount",
            "total_gross_amount",
            "subtotal_net_amount",
            "subtotal_gross_amount",
        ]
    )

    subtotal_mock.return_value = price
    delivery_price_mock.return_value = delivery_price

    reward_value_1 = top_price + Decimal("2")
    reward_value_2 = top_price + Decimal("10")
    rules = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Order promotion rule 1",
                promotion=promotion,
                order_predicate={
                    "base_total_price": {
                        "range": {
                            "gte": 10,
                        }
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=reward_value_1,
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
            PromotionRule(
                name="Order promotion rule 1",
                promotion=promotion,
                order_predicate={
                    "base_total_price": {
                        "range": {
                            "gte": 100,
                        }
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=reward_value_2,
                reward_type=RewardType.SUBTOTAL_DISCOUNT,
            ),
        ]
    )
    for rule in rules:
        rule.channels.add(checkout.channel)

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines_info, get_plugins_manager(allow_replica=False)
    )
    lines_count = len(lines_info)

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, lines_info
    )

    # then
    checkout = checkout_info.checkout
    assert checkout.discounts.count() == 1
    assert checkout.discount_amount == reward_value_1
    assert len(lines_info) == checkout.lines.count() == lines_count - 1
    assert not [line_info for line_info in lines_info if line_info.line.is_gift]
    assert not checkout.lines.filter(is_gift=True).first()
    discount = checkout.discounts.first()
    assert discount.promotion_rule == rules[0]
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.value_type == RewardValueType.FIXED
    assert discount.value == reward_value_1
    assert discount.amount_value == reward_value_1
    assert discount.name == f"{promotion.name}: {rules[0].name}"
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    assert discount.reason == f"Promotion: {promotion_id}"


def test_create_or_update_discount_from_promotion_voucher_code_set_checkout_discount(
    checkout_info,
    checkout_lines_info,
    catalogue_promotion_without_rules,
    voucher,
):
    # given
    promotion = catalogue_promotion_without_rules
    checkout = checkout_info.checkout
    checkout_info.voucher = voucher
    checkout_info.checkout.voucher_code = voucher.code

    price = Money("30", checkout_info.checkout.currency)
    checkout.total = TaxedMoney(net=price, gross=price)
    checkout.subtotal = TaxedMoney(net=price, gross=price)
    checkout.save(
        update_fields=[
            "total_net_amount",
            "total_gross_amount",
            "subtotal_net_amount",
            "subtotal_gross_amount",
        ]
    )

    rule = PromotionRule.objects.create(
        name="Order promotion rule 1",
        promotion=promotion,
        order_predicate={
            "discountedObjectPredicate": {
                "baseTotalPrice": {
                    "range": {
                        "gte": 10,
                    }
                }
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("25"),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(checkout_info.channel)
    discount = CheckoutDiscount.objects.create(
        checkout=checkout,
        promotion_rule=rule,
        type=DiscountType.ORDER_PROMOTION,
    )
    checkout_info.discounts = [discount]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert checkout_info.discounts == []
    assert not checkout.discounts.all()
    with pytest.raises(CheckoutDiscount.DoesNotExist):
        discount.refresh_from_db()


def test_create_or_update_discount_from_promotion_checkout_discount_updated(
    checkout_info,
    checkout_lines_info,
    catalogue_promotion_without_rules,
    promotion_rule,
):
    # given
    promotion = catalogue_promotion_without_rules
    checkout = checkout_info.checkout

    checkout_total = base_checkout_total(checkout_info, checkout_lines_info)
    checkout.total = TaxedMoney(net=checkout_total, gross=checkout_total)
    checkout.subtotal = TaxedMoney(net=checkout_total, gross=checkout_total)
    checkout.save(
        update_fields=[
            "total_net_amount",
            "total_gross_amount",
            "subtotal_net_amount",
            "subtotal_gross_amount",
        ]
    )

    rule = PromotionRule.objects.create(
        name="Order promotion rule 1",
        promotion=promotion,
        order_predicate={
            "discountedObjectPredicate": {
                "baseTotalPrice": {
                    "range": {
                        "gte": 10,
                    }
                }
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("25"),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(checkout_info.channel)
    discount = CheckoutDiscount.objects.create(
        checkout=checkout,
        promotion_rule=promotion_rule,
        type=DiscountType.ORDER_PROMOTION,
    )
    checkout_info.discounts = [discount]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert checkout_info.discounts == [discount]
    assert checkout.discounts.count() == 1
    discount = checkout_info.discounts[0]
    assert discount.promotion_rule_id == rule.id
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.value_type == rule.reward_value_type
    assert discount.value == rule.reward_value
    assert discount.amount_value == (checkout_total * rule.reward_value / 100).amount
    assert discount.name == f"{promotion.name}: {rule.name}"
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    assert discount.reason == f"Promotion: {promotion_id}"


def test_create_or_update_discount_from_promotion_rule_not_applies_anymore(
    checkout_info,
    checkout_lines_info,
    catalogue_promotion_without_rules,
    promotion_rule,
):
    # given
    promotion = catalogue_promotion_without_rules
    checkout = checkout_info.checkout

    checkout_total = base_checkout_total(checkout_info, checkout_lines_info)
    checkout.total = TaxedMoney(net=checkout_total, gross=checkout_total)
    checkout.subtotal = TaxedMoney(net=checkout_total, gross=checkout_total)
    checkout.save(
        update_fields=[
            "total_net_amount",
            "total_gross_amount",
            "subtotal_net_amount",
            "subtotal_gross_amount",
        ]
    )

    rule = PromotionRule.objects.create(
        name="Order promotion rule 1",
        promotion=promotion,
        order_predicate={
            "discountedObjectPredicate": {
                "baseTotalPrice": {
                    "range": {
                        "gte": 200,
                    }
                }
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("25"),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(checkout_info.channel)
    discount = CheckoutDiscount.objects.create(
        checkout=checkout,
        promotion_rule=promotion_rule,
        type=DiscountType.ORDER_PROMOTION,
    )
    checkout_info.discounts = [discount]

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, checkout_lines_info
    )

    # then
    assert checkout_info.discounts == []
    assert not checkout.discounts.all()
    with pytest.raises(CheckoutDiscount.DoesNotExist):
        discount.refresh_from_db()


def test_create_discount_objects_for_order_promotions_race_condition(
    checkout_info,
    checkout_lines_info,
    catalogue_promotion_without_rules,
):
    # given
    promotion = catalogue_promotion_without_rules
    checkout = checkout_info.checkout
    channel = checkout_info.channel

    reward_value = Decimal("2")
    rule = promotion.rules.create(
        order_predicate={
            "total_price": {
                "range": {
                    "gte": 20,
                }
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(channel)

    rule0 = promotion.rules.create(
        order_predicate={
            "total_price": {
                "range": {
                    "gte": 20,
                }
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal("1"),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule0.channels.add(channel)

    # when
    def call_before_creating_discount_object(*args, **kwargs):
        CheckoutDiscount.objects.create(
            checkout=checkout,
            promotion_rule=rule0,
            type=DiscountType.ORDER_PROMOTION,
            value_type=rule0.reward_value_type,
            value=rule0.reward_value,
            amount_value=rule0.reward_value,
            currency=channel.currency_code,
        )

    with before_after.before(
        "saleor.discount.utils.checkout.create_checkout_discount_objects_for_order_promotions",
        call_before_creating_discount_object,
    ):
        create_checkout_discount_objects_for_order_promotions(
            checkout_info, checkout_lines_info
        )

    # then
    discounts = list(checkout_info.checkout.discounts.all())
    assert len(discounts) == 1
    assert discounts[0].amount_value == reward_value


def test_create_or_update_order_discount_race_condition(
    checkout_info,
    checkout_lines_info,
    catalogue_promotion_without_rules,
):
    # given
    promotion = catalogue_promotion_without_rules
    channel = checkout_info.channel

    reward_value = Decimal("2")
    rule = promotion.rules.create(
        order_predicate={
            "total_price": {
                "range": {
                    "gte": 20,
                }
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(channel)

    def call_update(*args, **kwargs):
        create_checkout_discount_objects_for_order_promotions(
            checkout_info,
            checkout_lines_info,
            save=True,
        )

    with before_after.before(
        "saleor.discount.utils.checkout._set_checkout_base_prices", call_update
    ):
        call_update()

    # then
    discounts = list(checkout_info.checkout.discounts.all())
    assert len(discounts) == 1


def test_create_or_update_order_discount_gift_reward_race_condition(
    checkout_info,
    checkout_lines_info,
    gift_promotion_rule,
):
    # given
    checkout = checkout_info.checkout

    def call_update(*args, **kwargs):
        create_checkout_discount_objects_for_order_promotions(
            checkout_info,
            checkout_lines_info,
            save=True,
        )

    with before_after.before(
        "saleor.discount.utils.checkout._set_checkout_base_prices", call_update
    ):
        call_update()

    # then
    assert checkout_info.checkout.discounts.count() == 0
    assert checkout.lines.filter(is_gift=True).count() == 1
    line = checkout.lines.filter(is_gift=True).first()
    assert line.discounts.count() == 1


def test_get_best_gift_reward(
    gift_promotion_rule, order_promotion_without_rules, channel_USD, product
):
    # given
    gift_rule_2 = PromotionRule.objects.create(
        name="Order promotion rule",
        promotion=order_promotion_without_rules,
        order_predicate={
            "base_total_price": {
                "range": {
                    "gte": 20,
                }
            }
        },
        reward_type=RewardType.GIFT,
    )
    gift_rule_2.channels.add(channel_USD)
    gift_rule_2_variant = product.variants.first()
    gift_rule_2.gifts.set([gift_rule_2_variant])
    price_amount = gift_rule_2_variant.channel_listings.get(
        channel=channel_USD
    ).discounted_price_amount

    variants = gift_promotion_rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_listing = max(list(variant_listings), key=lambda x: x.discounted_price_amount)
    assert price_amount < top_listing.discounted_price_amount

    rules = [gift_rule_2, gift_promotion_rule]
    country = "US"

    # when
    rule, listing = _get_best_gift_reward(rules, channel_USD, country)

    # then
    assert rule.id == gift_promotion_rule.id
    assert listing.id == top_listing.id


def test_get_best_gift_reward_insufficient_stock(
    gift_promotion_rule, channel_USD, product
):
    # given
    variant = product.variants.first()
    variant.stocks.all().delete()
    gift_promotion_rule.gifts.set([variant])

    rules = [gift_promotion_rule]
    country = "US"

    # when
    rule, listing = _get_best_gift_reward(rules, channel_USD, country)

    # then
    assert rule is None
    assert listing is None


def test_get_best_gift_reward_no_available_for_purchase_variants(
    gift_promotion_rule, channel_USD
):
    # given
    variants = gift_promotion_rule.gifts.all()
    product_ids = [variant.product_id for variant in variants]
    ProductChannelListing.objects.filter(product__in=product_ids[:1]).update(
        available_for_purchase_at=timezone.now() + timedelta(days=1)
    )
    ProductChannelListing.objects.filter(product__in=product_ids[1:]).delete()

    rules = [gift_promotion_rule]
    country = "US"

    # when
    rule, listing = _get_best_gift_reward(rules, channel_USD, country)

    # then
    assert rule is None
    assert listing is None


def test_get_best_gift_reward_no_variants_in_channel(gift_promotion_rule, channel_USD):
    # given
    variants = gift_promotion_rule.gifts.all()
    ProductVariantChannelListing.objects.filter(variant__in=variants).delete()

    rules = [gift_promotion_rule]
    country = "US"

    # when
    rule, listing = _get_best_gift_reward(rules, channel_USD, country)

    # then
    assert rule is None
    assert listing is None


def test_create_checkout_line_discount_objects_for_catalogue_promotions_race_condition(
    checkout_with_item_on_promotion,
    plugins_manager,
):
    # given
    checkout = checkout_with_item_on_promotion
    CheckoutLineDiscount.objects.all().delete()

    # when
    def call_before_creating_catalogue_line_discount(*args, **kwargs):
        lines_info, _ = fetch_checkout_lines(checkout)
        create_checkout_line_discount_objects_for_catalogue_promotions(lines_info)

    with before_after.before(
        "saleor.discount.utils.promotion.prepare_line_discount_objects_for_catalogue_promotions",
        call_before_creating_catalogue_line_discount,
    ):
        lines_info, _ = fetch_checkout_lines(checkout)
        create_checkout_line_discount_objects_for_catalogue_promotions(lines_info)

    # then
    assert CheckoutLineDiscount.objects.count() == 1
