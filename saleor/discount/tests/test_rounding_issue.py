from decimal import Decimal

import graphene
import pytest

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...checkout.utils import add_variant_to_checkout
from ...discount.models import PromotionRule
from ...plugins.manager import get_plugins_manager
from ...product.models import Product, ProductVariantChannelListing
from ...product.utils.variant_prices import update_discounted_prices_for_promotion
from ...product.utils.variants import fetch_variants_for_promotion_rules
from .. import DiscountValueType, RewardValueType
from ..models import Promotion
from ..utils.checkout import (
    create_or_update_discount_objects_from_promotion_for_checkout,
)


@pytest.fixture
def promotion_10_percentage(channel_USD, product_list, product):
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    product_list.append(product)
    rule = promotion.rules.create(
        name="10% promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id("Product", product.id)
                    for product in product_list
                ]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("10"),
    )
    rule.channels.add(channel_USD)
    return promotion


@pytest.mark.parametrize(
    ("variant_prices", "expected_discounts"),
    [
        (
            [Decimal("1.06"), Decimal("2.06"), Decimal("3.06"), Decimal("4.06")],
            [Decimal("0.11"), Decimal("0.21"), Decimal("0.31"), Decimal("0.41")],
        ),
        (
            [Decimal("1.04"), Decimal("2.04"), Decimal("3.04"), Decimal("4.04")],
            [Decimal("0.1"), Decimal("0.2"), Decimal("0.3"), Decimal("0.4")],
        ),
    ],
)
def test_rounding_issue_with_percentage_promotion(
    product_list,
    product,
    checkout,
    channel_USD,
    promotion_10_percentage,
    variant_prices,
    expected_discounts,
):
    """Test checking that a rounding issue may appear in calculations.

    We want to test a scenario where a percentage promotion is applied to each line
    separately, resulting in a total discount that is different from applying
    the same percentage sale to the sum of qualified lines.

    In the current solution the discount from promotion is applied on the variant price,
    and then the prices for each line are summed up

    If we calculate 10% discount we got:
    +-------+-------------+------------------+----------------------+
    | Line  | Line total  | Discount applied | Discount applied on  |
    |       |             | on total price   | each line separately |
    +-------+-------------+------------------+----------------------+
    | Line1 | 1.06        | 0.11             | 0.11                 |
    | Line2 | 2.06        | 0.2              | 0.21                 |
    | Line3 | 3.06        | 0.31             | 0.31                 |
    | Line4 | 4.06        | 0.4              | 0.41                 |
    +-------+-------------+------------------+----------------------+
    | Sum   | 10.24       | 1.02             | 1.04                 |
    +-------+-------------+------------------+----------------------+
    """

    # given
    product_list.append(product)
    variants = []
    variant_channel_listings = []
    for product, price in zip(product_list, variant_prices):
        variant = product.variants.get()
        variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
        variant_channel_listing.price_amount = price
        variant_channel_listing.discounted_price_amount = price
        variant_channel_listings.append(variant_channel_listing)
        variants.append(variant)

    ProductVariantChannelListing.objects.bulk_update(
        variant_channel_listings, ["price_amount"]
    )

    fetch_variants_for_promotion_rules(PromotionRule.objects.all())
    update_discounted_prices_for_promotion(Product.objects.all())

    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )

    for variant in variants:
        add_variant_to_checkout(checkout_info, variant, 1)

    lines_info, _ = fetch_checkout_lines(checkout)

    # when
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info,
        lines_info,
    )

    # then
    for line_info, expected_discount in zip(lines_info, expected_discounts):
        assert len(line_info.discounts) == 1
        discount_from_info = line_info.discounts[0]
        discount_from_db = line_info.line.discounts.get()
        assert (
            discount_from_info.value_type
            == discount_from_db.value_type
            == DiscountValueType.PERCENTAGE
        )
        assert (
            discount_from_info.amount_value
            == discount_from_db.amount_value
            == expected_discount
        )
