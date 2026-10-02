import datetime
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest
from django.core.management import call_command
from prices import Money

from ...discount import RewardValueType
from ...discount.models import Promotion, PromotionRule
from ...product.interface import VariantDiscountedPriceChange
from ...product.models import (
    Product,
    ProductChannelListing,
    ProductVariantChannelListing,
    VariantChannelListingPrice,
    VariantChannelListingPriceCustomerType,
    VariantChannelListingPromotionRule,
)
from ...tests import race_condition
from ..utils.variant_prices import update_discounted_prices_for_promotion


def test_update_discounted_price_for_promotion_no_discount(product, channel_USD):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing.refresh_from_db()

    assert product_channel_listing.discounted_price == Money("10", "USD")

    # when
    update_discounted_prices_for_promotion(
        Product.objects.filter(id__in=[product.id]),
    )

    # then
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price == variant_channel_listing.price
    assert variant_channel_listing.discounted_price == variant_channel_listing.price
    assert not variant_channel_listing.promotion_rules.all()


def test_update_discounted_price_for_promotion_discount_on_variant(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)
    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    reward_value = Decimal(2)
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(variant_channel_listing.channel)
    rule.variants.add(variant)

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(id__in=[product.id]))

    # then
    expected_price_amount = variant_price.amount - reward_value
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.promotion_rules.first() == rule
    assert variant_channel_listing.promotion_rules.first()
    assert (
        variant_channel_listing.variantlistingpromotionrule.first().discount_amount
        == reward_value
    )


def test_update_discounted_price_for_promotion_discount_on_product(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)
    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    reward_value = Decimal(10)
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=reward_value,
    )
    rule.channels.add(variant_channel_listing.channel)
    rule.variants.set(product.variants.all())

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(id__in=[product.id]))

    # then
    expected_price_amount = round(
        variant_price.amount - variant_price.amount * reward_value / 100, 2
    )
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.promotion_rules.first() == rule
    assert (
        variant_channel_listing.variantlistingpromotionrule.first().discount_amount
        == variant_price.amount - expected_price_amount
    )


def test_update_discounted_price_for_promotion_discount_multiple_applicable_rules(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)
    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    percentage_reward_value = Decimal(10)
    reward_value = Decimal(2)
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule_1 = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=percentage_reward_value,
    )
    rule_2 = promotion.rules.create(
        name="Fixed promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule_1.channels.add(variant_channel_listing.channel)
    rule_2.channels.add(variant_channel_listing.channel)
    rule_1.variants.add(variant)
    rule_2.variants.set(product.variants.all())

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(id__in=[product.id]))

    # then
    expected_price_amount = round(variant_price.amount - reward_value, 2)
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.promotion_rules.count() == 1
    assert (
        variant_channel_listing.variantlistingpromotionrule.get(
            promotion_rule_id=rule_2.id
        ).discount_amount
        == reward_value
    )


def test_update_discounted_price_for_promotion_1_cent_variant_on_10_percentage_discount(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)

    # Set product price to 0.01 USD
    variant_price = Decimal("0.01")
    variant_channel_listing.price_amount = variant_price
    variant_channel_listing.discounted_price_amount = variant_price
    variant_channel_listing.save()

    product_channel_listing.refresh_from_db()

    reward_value = Decimal("10.00")
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=reward_value,
    )
    rule.channels.add(variant_channel_listing.channel)
    rule.variants.add(variant)

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(id__in=[product.id]))

    # then
    expected_price_amount = round(variant_price - variant_price * reward_value / 100, 2)
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.promotion_rules.first() == rule
    assert variant_channel_listing.promotion_rules.first()
    assert (
        variant_channel_listing.variantlistingpromotionrule.first().discount_amount
        == variant_price - expected_price_amount
    )


def test_update_discounted_price_for_promotion_promotion_not_applicable_for_channel(
    product, channel_USD, channel_PLN
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)
    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    reward_value = Decimal(2)
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel_PLN)
    rule.variants.add(variant)

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(id__in=[product.id]))

    # then
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price == variant_price
    assert variant_channel_listing.discounted_price == variant_price
    assert not variant_channel_listing.promotion_rules.all()


def test_update_discounted_price_for_promotion_discount_updated(product, channel_USD):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)

    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    reward_value = Decimal(2)
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(variant_channel_listing.channel)
    rule.variants.add(variant)

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=variant_channel_listing,
        promotion_rule=rule,
        discount_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(id__in=[product.id]))

    # then
    expected_price_amount = variant_price.amount - reward_value
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.promotion_rules.count() == 1
    listing_promotion_rule.refresh_from_db()
    assert listing_promotion_rule.discount_amount == reward_value


def test_update_discounted_price_for_promotion_discount_not_valid_anymore(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)

    variant_price = Money("9.99", "USD")
    discounted_price = Money("5.00", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = discounted_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    reward_value = Decimal(2)
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={},
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(variant_channel_listing.channel)

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=variant_channel_listing,
        promotion_rule=rule,
        discount_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(id__in=[product.id]))

    # then
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price_amount == variant_price.amount
    assert variant_channel_listing.discounted_price_amount == variant_price.amount
    assert variant_channel_listing.promotion_rules.count() == 0

    with pytest.raises(listing_promotion_rule._meta.model.DoesNotExist):
        listing_promotion_rule.refresh_from_db()


def test_update_discounted_price_for_promotion_discount_one_rule_not_valid_anymore(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)
    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    percentage_reward_value = Decimal(10)
    reward_value = Decimal(2)
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule_1 = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={},
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=percentage_reward_value,
    )
    rule_2 = promotion.rules.create(
        name="Fixed promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule_1.channels.add(variant_channel_listing.channel)
    rule_2.channels.add(variant_channel_listing.channel)
    rule_2.variants.set(product.variants.all())

    listing_promotion_rules = VariantChannelListingPromotionRule.objects.bulk_create(
        [
            VariantChannelListingPromotionRule(
                variant_channel_listing=variant_channel_listing,
                promotion_rule=rule_1,
                discount_amount=Decimal(1),
                currency=channel_USD.currency_code,
            ),
            VariantChannelListingPromotionRule(
                variant_channel_listing=variant_channel_listing,
                promotion_rule=rule_2,
                discount_amount=Decimal(1),
                currency=channel_USD.currency_code,
            ),
        ]
    )

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(id__in=[product.id]))

    # then
    expected_price_amount = round(variant_price.amount - reward_value, 2)
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.promotion_rules.count() == 1
    listing_promotion_rules[1].refresh_from_db()
    assert listing_promotion_rules[1].discount_amount == reward_value
    with pytest.raises(listing_promotion_rules[0]._meta.model.DoesNotExist):
        listing_promotion_rules[0].refresh_from_db()


@patch(
    "saleor.product.management.commands"
    ".update_all_products_discounted_prices"
    ".update_discounted_prices_for_promotion"
)
@patch(
    "saleor.product.management.commands.update_all_products_discounted_prices.DISCOUNTED_PRODUCT_BATCH",
    1,
)
def test_management_commmand_update_all_products_discounted_price(
    mock_update_discounted_prices_for_promotion, product_list
):
    # when
    call_command("update_all_products_discounted_prices")

    # then
    assert mock_update_discounted_prices_for_promotion.call_count == len(product_list)

    call_args_list = mock_update_discounted_prices_for_promotion.call_args_list
    for (args, _kwargs), product in zip(call_args_list, product_list, strict=False):
        assert len(args[0]) == 1
        assert args[0][0].pk == product.pk


def test_update_discounted_price_for_promotion_promotion_rule_deleted_in_meantime(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)
    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    reward_value = Decimal(2)
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(variant_channel_listing.channel)
    rule.variants.add(variant)

    def delete_promotion_rule(*args, **kwargs):
        PromotionRule.objects.all().delete()

    # when
    with race_condition.RunBefore(
        "saleor.product.utils.variant_prices._get_discounted_variants_prices_for_promotions",
        delete_promotion_rule,
    ):
        update_discounted_prices_for_promotion(
            Product.objects.filter(id__in=[product.id])
        )

    # then
    expected_price_amount = variant_price.amount - reward_value
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.discounted_price_amount == expected_price_amount
    assert not variant_channel_listing.promotion_rules.all()
    assert not variant_channel_listing.variantlistingpromotionrule.exists()


@pytest.mark.django_db(transaction=False)
def test_update_discounted_price_rule_deleted_in_meantime_promotion_listing_exist(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)
    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    reward_value = Decimal(2)
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(variant_channel_listing.channel)
    rule.variants.add(variant)

    listing_promotion_rule = VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=variant_channel_listing,
        promotion_rule=rule,
        discount_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )

    def delete_promotion_rule(*args, **kwargs):
        rule.delete()

    # when
    with race_condition.RunBefore(
        "saleor.product.utils.variant_prices._update_or_create_listings",
        delete_promotion_rule,
    ):
        update_discounted_prices_for_promotion(
            Product.objects.filter(id__in=[product.id])
        )

    # then
    expected_price_amount = variant_price.amount - reward_value
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.discounted_price_amount == expected_price_amount
    with pytest.raises(VariantChannelListingPromotionRule.DoesNotExist):
        listing_promotion_rule.refresh_from_db()
    assert not variant_channel_listing.variantlistingpromotionrule.exists()


def test_update_discounted_prices_for_promotion_only_dirty_products(
    product, channel_USD, channel_PLN
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing = product.channel_listings.get(channel_id=channel_USD.id)
    product_channel_listing.discounted_price_dirty = True
    product_channel_listing.save()
    second_channel_discounted_price = 123456
    second_listing = product.channel_listings.create(
        channel=channel_PLN,
        discounted_price_amount=second_channel_discounted_price,
        currency=channel_PLN.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=(datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC)),
        discounted_price_dirty=False,
    )

    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    reward_value = Decimal(2)
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(variant_channel_listing.channel)
    rule.variants.add(variant)

    # when
    update_discounted_prices_for_promotion(
        Product.objects.filter(id__in=[product.id]), only_dirty_products=True
    )

    # then
    expected_price_amount = variant_price.amount - reward_value
    product_channel_listing.refresh_from_db()
    variant_channel_listing.refresh_from_db()
    assert product_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.discounted_price_amount == expected_price_amount
    assert variant_channel_listing.promotion_rules.first() == rule
    assert variant_channel_listing.promotion_rules.first()
    assert (
        variant_channel_listing.variantlistingpromotionrule.first().discount_amount
        == reward_value
    )
    second_listing.refresh_from_db()
    assert second_listing.discounted_price_amount == second_channel_discounted_price


def test_update_discounted_prices_returns_changed_prices_when_discount_applied(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()

    reward_value = Decimal(2)
    promotion = Promotion.objects.create(name="Promotion")
    rule = promotion.rules.create(
        name="Fixed promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel_USD)
    rule.variants.add(variant)

    # when
    changed_prices = update_discounted_prices_for_promotion(
        Product.objects.filter(id__in=[product.id])
    )

    # then
    assert len(changed_prices) == 1
    cp = changed_prices[0]
    assert isinstance(cp, VariantDiscountedPriceChange)
    assert cp.variant_id == variant.id
    assert cp.channel_slug == channel_USD.slug
    assert cp.currency == channel_USD.currency_code
    assert cp.previous_price_amount == variant_price.amount
    assert cp.new_price_amount == variant_price.amount - reward_value


def test_update_discounted_prices_returns_empty_when_prices_unchanged(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)

    # Ensure discounted_price already equals price (no promotion)
    variant_channel_listing.discounted_price_amount = (
        variant_channel_listing.price_amount
    )
    variant_channel_listing.save()

    # when
    changed_prices = update_discounted_prices_for_promotion(
        Product.objects.filter(id__in=[product.id])
    )

    # then
    assert changed_prices == []


def test_update_discounted_prices_returns_changed_prices_for_multiple_channels(
    product, channel_USD, channel_PLN
):
    # given
    variant = product.variants.first()
    variant_channel_listing_usd = variant.channel_listings.get(
        channel_id=channel_USD.id
    )
    variant_price_usd = Money("9.99", "USD")
    variant_channel_listing_usd.price = variant_price_usd
    variant_channel_listing_usd.discounted_price = variant_price_usd
    variant_channel_listing_usd.save()

    ProductChannelListing.objects.create(
        product=product,
        channel=channel_PLN,
        is_published=True,
        discounted_price_amount=Decimal("40.00"),
        currency=channel_PLN.currency_code,
        visible_in_listings=True,
        available_for_purchase_at=datetime.datetime(1999, 1, 1, tzinfo=datetime.UTC),
    )
    variant_price_pln = Decimal("40.00")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_PLN,
        price_amount=variant_price_pln,
        discounted_price_amount=variant_price_pln,
        currency=channel_PLN.currency_code,
    )

    reward_value = Decimal(2)
    promotion = Promotion.objects.create(name="Promotion")
    rule = promotion.rules.create(
        name="Fixed promotion rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel_USD, channel_PLN)
    rule.variants.add(variant)

    # when
    changed_prices = update_discounted_prices_for_promotion(
        Product.objects.filter(id__in=[product.id])
    )

    # then
    assert len(changed_prices) == 2

    prices_by_channel = {cp.channel_slug: cp for cp in changed_prices}

    cp_usd = prices_by_channel[channel_USD.slug]
    assert cp_usd.variant_id == variant.id
    assert cp_usd.currency == channel_USD.currency_code
    assert cp_usd.previous_price_amount == variant_price_usd.amount
    assert cp_usd.new_price_amount == variant_price_usd.amount - reward_value

    cp_pln = prices_by_channel[channel_PLN.slug]
    assert cp_pln.variant_id == variant.id
    assert cp_pln.currency == channel_PLN.currency_code
    assert cp_pln.previous_price_amount == variant_price_pln
    assert cp_pln.new_price_amount == variant_price_pln - reward_value


def _create_window_row(listing, price_amount, *, days_from_now=-1, days_to_now=1):
    now = datetime.datetime.now(tz=datetime.UTC)
    return VariantChannelListingPrice.objects.create(
        variant_channel_listing=listing,
        currency=listing.currency,
        price_amount=price_amount,
        valid_from=now + datetime.timedelta(days=days_from_now),
        valid_to=now + datetime.timedelta(days=days_to_now),
    )


def _create_catalogue_rule(variant, reward_value_type, reward_value):
    promotion = Promotion.objects.create(name="Promotion")
    rule = promotion.rules.create(
        name="Rule",
        promotion=promotion,
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.pk)]
            }
        },
        reward_value_type=reward_value_type,
        reward_value=reward_value,
    )
    rule.channels.add(variant.channel_listings.get().channel)
    rule.variants.add(variant)
    return rule


def test_update_discounted_price_stores_an_open_window_price(product, channel_USD):
    # given
    variant = product.variants.first()
    variant_listing = variant.channel_listings.get(channel=channel_USD)
    product_listing = product.channel_listings.get(channel=channel_USD)
    window_price_amount = Decimal(7)
    _create_window_row(variant_listing, window_price_amount)

    # when
    changes = update_discounted_prices_for_promotion(
        Product.objects.filter(pk=product.pk)
    )

    # then
    variant_listing.refresh_from_db(fields=["discounted_price_amount"])
    product_listing.refresh_from_db(fields=["discounted_price_amount"])
    assert variant_listing.discounted_price_amount == window_price_amount
    assert product_listing.discounted_price_amount == window_price_amount
    assert changes == [
        VariantDiscountedPriceChange(
            variant_id=variant.pk,
            channel_slug=channel_USD.slug,
            previous_price_amount=variant_listing.price_amount,
            new_price_amount=window_price_amount,
            currency=channel_USD.currency_code,
        )
    ]


def test_update_discounted_price_stores_a_window_price_above_the_listing_price(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_listing = variant.channel_listings.get(channel=channel_USD)
    window_price_amount = variant_listing.price_amount + Decimal(5)
    _create_window_row(variant_listing, window_price_amount)

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))

    # then
    variant_listing.refresh_from_db(fields=["discounted_price_amount"])
    assert variant_listing.discounted_price_amount == window_price_amount


@pytest.mark.parametrize(
    ("_case", "reward_value_type", "reward_value", "expected_amount"),
    [
        ("fixed", RewardValueType.FIXED, Decimal(2), Decimal("6.00")),
        ("percentage", RewardValueType.PERCENTAGE, Decimal(50), Decimal("4.00")),
    ],
)
def test_update_discounted_price_applies_the_promotion_on_the_window_price(
    _case, reward_value_type, reward_value, expected_amount, product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_listing = variant.channel_listings.get(channel=channel_USD)
    assert variant_listing.price_amount == Decimal(10)
    window_price_amount = Decimal(8)
    _create_window_row(variant_listing, window_price_amount)
    rule = _create_catalogue_rule(variant, reward_value_type, reward_value)

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))

    # then
    variant_listing.refresh_from_db(fields=["discounted_price_amount"])
    assert variant_listing.discounted_price_amount == expected_amount
    listing_rule = variant_listing.variantlistingpromotionrule.get()
    assert listing_rule.promotion_rule == rule
    assert listing_rule.discount_amount == window_price_amount - expected_amount


@pytest.mark.parametrize(
    ("_case", "days_from_now", "days_to_now"),
    [("future window", 1, 2), ("past window", -2, -1)],
)
def test_update_discounted_price_ignores_a_closed_window(
    _case, days_from_now, days_to_now, product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_listing = variant.channel_listings.get(channel=channel_USD)
    _create_window_row(
        variant_listing,
        Decimal(7),
        days_from_now=days_from_now,
        days_to_now=days_to_now,
    )

    # when
    changes = update_discounted_prices_for_promotion(
        Product.objects.filter(pk=product.pk)
    )

    # then
    variant_listing.refresh_from_db(fields=["discounted_price_amount"])
    assert variant_listing.discounted_price_amount == variant_listing.price_amount
    assert changes == []


def test_update_discounted_price_ignores_a_window_row_with_buyer_conditions(
    product, channel_USD, customer_type
):
    # given
    variant = product.variants.first()
    variant_listing = variant.channel_listings.get(channel=channel_USD)
    row = _create_window_row(variant_listing, Decimal(7))
    VariantChannelListingPriceCustomerType.objects.create(
        listing_price=row, customer_type=customer_type
    )

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))

    # then
    variant_listing.refresh_from_db(fields=["discounted_price_amount"])
    assert variant_listing.discounted_price_amount == variant_listing.price_amount


def test_update_discounted_price_picks_the_lowest_of_overlapping_window_prices(
    product, channel_USD
):
    # given
    variant = product.variants.first()
    variant_listing = variant.channel_listings.get(channel=channel_USD)
    lowest_price_amount = Decimal(6)
    _create_window_row(variant_listing, Decimal(9))
    _create_window_row(variant_listing, lowest_price_amount)

    # when
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))

    # then
    variant_listing.refresh_from_db(fields=["discounted_price_amount"])
    assert variant_listing.discounted_price_amount == lowest_price_amount
