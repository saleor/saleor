from decimal import Decimal

import graphene
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from .....product.models import Product
from .....product.utils.variant_prices import update_discounted_prices_for_promotion
from .....product.utils.variants import fetch_variants_for_promotion_rules
from ....tests.utils import get_graphql_content

VARIANT_PRICING_QUERY = """
query VariantPricing($id: ID!, $channel: String!) {
  productVariant(id: $id, channel: $channel) {
    pricing {
      onSale
      priceUndiscounted {
        net {
          amount
        }
      }
      price {
        net {
          amount
        }
      }
    }
  }
}
"""

PRODUCT_PRICING_QUERY = """
query ProductPricing($id: ID!, $channel: String!) {
  product(id: $id, channel: $channel) {
    pricing {
      priceRangeUndiscounted {
        start {
          net {
            amount
          }
        }
        stop {
          net {
            amount
          }
        }
      }
      priceRange {
        start {
          net {
            amount
          }
        }
      }
    }
  }
}
"""


def _query_variant_pricing(client, variant, channel):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel.slug,
    }
    response = client.post_graphql(VARIANT_PRICING_QUERY, variables)
    return get_graphql_content(response)["data"]["productVariant"]["pricing"]


@pytest.mark.parametrize(
    ("_case", "client_fixture", "user_fixture", "expected_amount"),
    [
        ("guest_sees_the_listing_price", "api_client", None, 10),
        (
            "customer_of_the_default_type_sees_the_listing_price",
            "user_api_client",
            "customer_user",
            10,
        ),
        (
            "customer_of_the_listed_type_sees_the_scoped_price",
            "user_api_client",
            "b2b_customer_user",
            8,
        ),
    ],
)
def test_variant_pricing_with_a_customer_type_row(
    _case,
    client_fixture,
    user_fixture,
    expected_amount,
    request,
    variant,
    channel_USD,
    variant_channel_listing_price_for_customer_type,
):
    # given
    client = request.getfixturevalue(client_fixture)
    if user_fixture:
        request.getfixturevalue(user_fixture)
    assert variant_channel_listing_price_for_customer_type.price_amount == Decimal(8)

    # when
    pricing = _query_variant_pricing(client, variant, channel_USD)

    # then
    assert pricing["priceUndiscounted"]["net"]["amount"] == expected_amount
    assert pricing["price"]["net"]["amount"] == expected_amount
    assert pricing["onSale"] is False


def test_variant_pricing_with_an_attribute_value_row(
    user_api_client,
    gold_customer_user,
    variant,
    channel_USD,
    variant_channel_listing_price_for_attribute_value,
):
    # given
    assert variant_channel_listing_price_for_attribute_value.price_amount == Decimal(7)

    # when
    pricing = _query_variant_pricing(user_api_client, variant, channel_USD)

    # then
    assert pricing["priceUndiscounted"]["net"]["amount"] == 7
    assert pricing["price"]["net"]["amount"] == 7


def test_variant_pricing_with_a_window_row_for_a_guest(
    api_client, variant, channel_USD, variant_channel_listing_price
):
    # given
    assert variant_channel_listing_price.price_amount == Decimal(9)

    # when
    pricing = _query_variant_pricing(api_client, variant, channel_USD)

    # then
    assert pricing["priceUndiscounted"]["net"]["amount"] == 9
    assert pricing["price"]["net"]["amount"] == 9


def test_variant_pricing_reapplies_the_promotion_on_the_scoped_price(
    user_api_client,
    b2b_customer_user,
    variant,
    product,
    channel_USD,
    variant_channel_listing_price_for_customer_type,
    catalogue_promotion_with_single_rule,
):
    # given
    # the fixed rule of 5 is applied to the listing price of 10
    fetch_variants_for_promotion_rules(catalogue_promotion_with_single_rule.rules.all())
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))
    listing = variant.channel_listings.get()
    assert listing.discounted_price_amount == Decimal(5)

    # when
    pricing = _query_variant_pricing(user_api_client, variant, channel_USD)

    # then
    assert pricing["priceUndiscounted"]["net"]["amount"] == 8
    assert pricing["price"]["net"]["amount"] == 3
    assert pricing["onSale"] is True


def test_variant_pricing_keeps_the_stored_promotion_price_for_a_guest(
    api_client,
    variant,
    product,
    channel_USD,
    variant_channel_listing_price_for_customer_type,
    catalogue_promotion_with_single_rule,
):
    # given
    fetch_variants_for_promotion_rules(catalogue_promotion_with_single_rule.rules.all())
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))

    # when
    pricing = _query_variant_pricing(api_client, variant, channel_USD)

    # then
    assert pricing["priceUndiscounted"]["net"]["amount"] == 10
    assert pricing["price"]["net"]["amount"] == 5
    assert pricing["onSale"] is True


def test_product_pricing_range_uses_the_scoped_price(
    user_api_client,
    b2b_customer_user,
    product,
    variant,
    channel_USD,
    variant_channel_listing_price_for_customer_type,
):
    # given
    # the product has two variants listed at 10, one of them scoped to 8 for B2B
    listing_prices = sorted(
        product.variants.values_list("channel_listings__price_amount", flat=True)
    )
    assert listing_prices == [Decimal(10), Decimal(10)]
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(PRODUCT_PRICING_QUERY, variables)

    # then
    pricing = get_graphql_content(response)["data"]["product"]["pricing"]
    assert pricing["priceRangeUndiscounted"]["start"]["net"]["amount"] == 8
    assert pricing["priceRangeUndiscounted"]["stop"]["net"]["amount"] == 10
    assert pricing["priceRange"]["start"]["net"]["amount"] == 8


def test_product_pricing_range_for_a_guest_ignores_the_scoped_price(
    api_client,
    product,
    variant,
    channel_USD,
    variant_channel_listing_price_for_customer_type,
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(PRODUCT_PRICING_QUERY, variables)

    # then
    pricing = get_graphql_content(response)["data"]["product"]["pricing"]
    assert pricing["priceRangeUndiscounted"]["start"]["net"]["amount"] == 10
    assert pricing["priceRangeUndiscounted"]["stop"]["net"]["amount"] == 10
    assert pricing["priceRange"]["start"]["net"]["amount"] == 10


def test_variant_pricing_without_rows_queries_the_rows_table_once(
    api_client, variant, channel_USD
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }

    # when
    with CaptureQueriesContext(connection) as context:
        response = api_client.post_graphql(VARIANT_PRICING_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["productVariant"]["pricing"]["price"]["net"]["amount"] == 10
    tables_hit = [
        table
        for table in (
            "product_variantchannellistingprice",
            "product_variantchannellistingpricecustomertype",
            "product_variantchannellistingpriceattributevalue",
            "attribute_assigneduserattributevalue",
        )
        for query in context.captured_queries
        if table in query["sql"]
    ]
    assert tables_hit == ["product_variantchannellistingprice"]
