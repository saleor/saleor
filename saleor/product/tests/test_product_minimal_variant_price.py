from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import before_after
import graphene
import pytest
import pytz
from django.core.management import call_command
from prices import Money

from ...discount import RewardValueType
from ...discount.models import Promotion, PromotionRule
from ...product.models import Product, VariantChannelListingPromotionRule
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

    reward_value = Decimal("2")
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

    reward_value = Decimal("10")
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

    percentage_reward_value = Decimal("10")
    reward_value = Decimal("2")
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

    reward_value = Decimal("2")
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

    reward_value = Decimal("2")
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
        discount_amount=Decimal("1"),
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

    reward_value = Decimal("2")
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
        discount_amount=Decimal("1"),
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

    percentage_reward_value = Decimal("10")
    reward_value = Decimal("2")
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
                discount_amount=Decimal("1"),
                currency=channel_USD.currency_code,
            ),
            VariantChannelListingPromotionRule(
                variant_channel_listing=variant_channel_listing,
                promotion_rule=rule_2,
                discount_amount=Decimal("1"),
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
    for (args, kwargs), product in zip(call_args_list, product_list):
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

    reward_value = Decimal("2")
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
    with before_after.before(
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

    reward_value = Decimal("2")
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
        discount_amount=Decimal("1"),
        currency=channel_USD.currency_code,
    )

    def delete_promotion_rule(*args, **kwargs):
        rule.delete()

    # when
    with before_after.before(
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
        available_for_purchase_at=(datetime(1999, 1, 1, tzinfo=pytz.UTC)),
        discounted_price_dirty=False,
    )

    variant_price = Money("9.99", "USD")
    variant_channel_listing.price = variant_price
    variant_channel_listing.discounted_price = variant_price
    variant_channel_listing.save()
    product_channel_listing.refresh_from_db()

    reward_value = Decimal("2")
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
