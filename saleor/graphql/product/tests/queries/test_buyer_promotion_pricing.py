from decimal import Decimal

import graphene
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from .....product.models import Product
from .....product.utils.variant_prices import update_discounted_prices_for_promotion
from ....tests.utils import get_graphql_content

VARIANT_PRICING_QUERY = """
query VariantPricing($id: ID!, $channel: String!, $customer: ID) {
  productVariant(id: $id, channel: $channel) {
    pricing(customer: $customer) {
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
      priceRange {
        start {
          net {
            amount
          }
        }
      }
      priceRangeUndiscounted {
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

RULE_VARIANTS_TABLE = '"discount_promotionrule_variants"'
RULE_TYPE_CONDITIONS_TABLE = '"discount_promotionrulecustomertype"'


def _query_variant_pricing(client, variant, channel, customer=None):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel.slug,
        "customer": customer,
    }
    response = client.post_graphql(VARIANT_PRICING_QUERY, variables)
    return get_graphql_content(response)["data"]["productVariant"]["pricing"]


def _store_guest_price(product):
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))


@pytest.mark.parametrize(
    ("_case", "client_fixture", "user_fixture", "expected_amount"),
    [
        ("guest_gets_the_stored_public_discount", "api_client", None, 9),
        (
            "customer_of_another_type_gets_the_stored_public_discount",
            "user_api_client",
            "customer_user",
            9,
        ),
        (
            "customer_of_the_listed_type_gets_the_buyer_rule",
            "user_api_client",
            "b2b_customer_user",
            7.5,
        ),
    ],
)
def test_variant_pricing_with_a_buyer_rule(
    _case,
    client_fixture,
    user_fixture,
    expected_amount,
    request,
    variant,
    product,
    channel_USD,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    # the public 10% rule is stored, the 25% B2B rule is resolved per buyer
    _store_guest_price(product)
    client = request.getfixturevalue(client_fixture)
    if user_fixture:
        request.getfixturevalue(user_fixture)

    # when
    pricing = _query_variant_pricing(client, variant, channel_USD)

    # then
    assert pricing["priceUndiscounted"]["net"]["amount"] == 10
    assert pricing["price"]["net"]["amount"] == expected_amount
    assert pricing["onSale"] is True


def test_variant_pricing_applies_the_buyer_rule_on_the_scoped_price(
    user_api_client,
    b2b_customer_user,
    variant,
    product,
    channel_USD,
    catalogue_promotion,
    promotion_rule_for_customer_type,
    variant_channel_listing_price_for_customer_type,
):
    # given
    _store_guest_price(product)
    assert variant_channel_listing_price_for_customer_type.price_amount == Decimal(8)

    # when
    pricing = _query_variant_pricing(user_api_client, variant, channel_USD)

    # then
    assert pricing["priceUndiscounted"]["net"]["amount"] == 8
    assert pricing["price"]["net"]["amount"] == 6


def test_product_pricing_range_uses_the_buyer_rule(
    user_api_client,
    b2b_customer_user,
    product,
    channel_USD,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    _store_guest_price(product)
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(PRODUCT_PRICING_QUERY, variables)

    # then
    pricing = get_graphql_content(response)["data"]["product"]["pricing"]
    assert pricing["priceRangeUndiscounted"]["start"]["net"]["amount"] == 10
    assert pricing["priceRange"]["start"]["net"]["amount"] == 7.5


def test_variant_pricing_preview_shows_the_buyer_rule_of_the_customer(
    staff_api_client,
    permission_manage_products,
    permission_manage_users,
    b2b_customer_user,
    variant,
    product,
    channel_USD,
    catalogue_promotion,
    promotion_rule_for_customer_type,
):
    # given
    _store_guest_price(product)
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_users
    )
    customer_id = graphene.Node.to_global_id("User", b2b_customer_user.pk)

    # when
    pricing = _query_variant_pricing(
        staff_api_client, variant, channel_USD, customer=customer_id
    )

    # then
    assert pricing["price"]["net"]["amount"] == 7.5


def test_variant_pricing_for_a_customer_queries_the_rule_variants_once(
    user_api_client, b2b_customer_user, variant, product, channel_USD
):
    # given
    assert product.channel_listings.filter(channel=channel_USD).exists()

    # when
    with CaptureQueriesContext(connection) as context:
        pricing = _query_variant_pricing(user_api_client, variant, channel_USD)

    # then
    assert pricing["price"]["net"]["amount"] == 10
    rule_variant_queries = [
        query
        for query in context.captured_queries
        if RULE_VARIANTS_TABLE in query["sql"]
    ]
    assert len(rule_variant_queries) == 1
    condition_queries = [
        query
        for query in context.captured_queries
        if RULE_TYPE_CONDITIONS_TABLE in query["sql"]
        and RULE_VARIANTS_TABLE not in query["sql"]
    ]
    assert condition_queries == []


def test_variant_pricing_for_a_guest_does_not_query_the_rule_variants(
    api_client, variant, product, channel_USD, promotion_rule_for_customer_type
):
    # when
    with CaptureQueriesContext(connection) as context:
        _query_variant_pricing(api_client, variant, channel_USD)

    # then
    rule_variant_queries = [
        query
        for query in context.captured_queries
        if RULE_VARIANTS_TABLE in query["sql"]
    ]
    assert rule_variant_queries == []
