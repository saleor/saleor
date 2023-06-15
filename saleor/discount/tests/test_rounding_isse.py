from decimal import Decimal

import pytest

from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...checkout.utils import add_variant_to_checkout
from ...plugins.manager import get_plugins_manager
from ...product.models import ProductVariantChannelListing
from .. import DiscountInfo, DiscountValueType
from ..models import Sale, SaleChannelListing
from ..utils import (
    create_or_update_discount_objects_from_sale_for_checkout,
    fetch_sale_channel_listings,
)


@pytest.fixture
def sale_10_percentage(channel_USD):
    sale = Sale.objects.create(name="Sale 10%", type=DiscountValueType.PERCENTAGE)
    SaleChannelListing.objects.create(
        sale=sale,
        channel=channel_USD,
        discount_value=10,
        currency=channel_USD.currency_code,
    )
    return sale


@pytest.mark.parametrize(
    "variant_prices, expected_discounts",
    [
        (
            [Decimal("1.06"), Decimal("2.06"), Decimal("3.06"), Decimal("4.06")],
            [Decimal("0.11"), Decimal("0.2"), Decimal("0.31"), Decimal("0.4")],
        ),
        (
            [Decimal("1.04"), Decimal("2.04"), Decimal("3.04"), Decimal("4.04")],
            [Decimal("0.1"), Decimal("0.21"), Decimal("0.3"), Decimal("0.41")],
        ),
    ],
)
def test_rounding_issue_with_percentage_sale(
    product_list,
    product,
    checkout,
    channel_USD,
    sale_10_percentage,
    variant_prices,
    expected_discounts,
):
    """Test checking that a rounding issue may appear in calculations.

    We want to test a scenario where a percentage sale is applied to each line
    separately, resulting in a total discount that is different from applying
    the same percentage sale to the sum of qualified lines.

    If we calculate 10% discount for first example we got:
    +-------+-------------+----------+----------+
    | Line  | Line total  | New flow | Old flow |
    +-------+-------------+----------+----------+
    | Line1 | 1.06        | 0.11     | 0.11     |
    | Line2 | 2.06        | 0.2      | 0.21     |
    | Line3 | 3.06        | 0.31     | 0.31     |
    | Line4 | 4.06        | 0.4      | 0.41     |
    +-------+-------------+----------+----------+
    | Sum   | 10.24       | 1.02     | 1.04     |
    +-------+-------------+----------+----------+
    """

    # given
    product_list.append(product)
    sale = sale_10_percentage
    variants = []
    variant_channel_listings = []
    total_amount = Decimal("0")
    for product, price in zip(product_list, variant_prices):
        variant = product.variants.get()
        variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
        variant_channel_listing.price_amount = price
        variant_channel_listings.append(variant_channel_listing)
        variants.append(variant)
        total_amount += price
        sale.variants.add(variant)
    ProductVariantChannelListing.objects.bulk_update(
        variant_channel_listings, ["price_amount"]
    )
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())
    for variant in variants:
        add_variant_to_checkout(checkout_info, variant, 1)

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, [], get_plugins_manager())

    sale_channel_listings = fetch_sale_channel_listings([sale.pk])[sale.pk]
    sale_info = DiscountInfo(
        sale=sale,
        category_ids=set(),
        channel_listings=sale_channel_listings,
        collection_ids=set(),
        product_ids=set(),
        variants_ids=set([variant.id for variant in variants]),
    )

    # when
    create_or_update_discount_objects_from_sale_for_checkout(
        checkout_info, lines_info, [sale_info]
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
