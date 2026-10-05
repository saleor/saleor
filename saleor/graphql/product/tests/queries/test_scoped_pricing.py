import datetime
from decimal import Decimal

import graphene
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from .....product.models import Product, VariantChannelListingPrice
from .....product.utils.variant_prices import update_discounted_prices_for_promotion
from .....product.utils.variants import fetch_variants_for_promotion_rules
from ....core.enums import OrderDirection
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...sorters import ProductOrderField

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


PRODUCTS_BY_MINIMAL_PRICE_QUERY = """
query Products($channel: String!, $where: ProductWhereInput, $sortBy: ProductOrder) {
  products(first: 10, channel: $channel, where: $where, sortBy: $sortBy) {
    edges {
      node {
        slug
        pricing {
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
  }
}
"""


def _store_window_price(product, channel, price_amount):
    """Give the product's first variant an open window price and store it."""
    listing = product.variants.first().channel_listings.get(channel=channel)
    now = timezone.now()
    VariantChannelListingPrice.objects.create(
        variant_channel_listing=listing,
        currency=listing.currency,
        price_amount=price_amount,
        valid_from=now - datetime.timedelta(days=1),
        valid_to=now + datetime.timedelta(days=1),
    )
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))


def test_products_sort_by_minimal_price_uses_the_stored_window_price(
    api_client, product_list, channel_USD
):
    # given
    cheapest_amount = Decimal(1)
    product_with_window = product_list[-1]
    _store_window_price(product_with_window, channel_USD, cheapest_amount)
    variables = {
        "channel": channel_USD.slug,
        "sortBy": {
            "field": ProductOrderField.MINIMAL_PRICE.name,
            "direction": OrderDirection.ASC.name,
        },
    }

    # when
    response = api_client.post_graphql(PRODUCTS_BY_MINIMAL_PRICE_QUERY, variables)

    # then
    edges = get_graphql_content(response)["data"]["products"]["edges"]
    assert len(edges) == len(product_list)
    first_node = edges[0]["node"]
    assert first_node["slug"] == product_with_window.slug
    assert first_node["pricing"]["priceRange"]["start"]["net"]["amount"] == (
        cheapest_amount
    )


def test_products_filter_by_minimal_price_uses_the_stored_window_price(
    api_client, product_list, channel_USD
):
    # given
    cheapest_amount = Decimal(1)
    product_with_window = product_list[-1]
    _store_window_price(product_with_window, channel_USD, cheapest_amount)
    variables = {
        "channel": channel_USD.slug,
        "where": {"minimalPrice": {"range": {"lte": cheapest_amount}}},
    }

    # when
    response = api_client.post_graphql(PRODUCTS_BY_MINIMAL_PRICE_QUERY, variables)

    # then
    edges = get_graphql_content(response)["data"]["products"]["edges"]
    assert [edge["node"]["slug"] for edge in edges] == [product_with_window.slug]


def test_product_pricing_for_a_guest_agrees_with_the_stored_window_price(
    api_client, product, variant, channel_USD, variant_channel_listing_price
):
    # given
    window_price = variant_channel_listing_price.price
    update_discounted_prices_for_promotion(Product.objects.filter(pk=product.pk))
    listing = variant.channel_listings.get(channel=channel_USD)
    listing.refresh_from_db(fields=["discounted_price_amount"])
    assert listing.discounted_price == window_price
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(PRODUCT_PRICING_QUERY, variables)

    # then
    pricing = get_graphql_content(response)["data"]["product"]["pricing"]
    assert pricing["priceRange"]["start"]["net"]["amount"] == window_price.amount
    assert (
        pricing["priceRangeUndiscounted"]["start"]["net"]["amount"]
        == window_price.amount
    )


VARIANT_PRICING_PREVIEW_QUERY = """
query VariantPricingPreview($id: ID!, $channel: String!, $customer: ID) {
  productVariant(id: $id, channel: $channel) {
    pricing(customer: $customer) {
      priceUndiscounted {
        net {
          amount
        }
      }
    }
  }
}
"""

PRODUCT_PRICING_PREVIEW_QUERY = """
query ProductPricingPreview($id: ID!, $channel: String!, $customer: ID) {
  product(id: $id, channel: $channel) {
    pricing(customer: $customer) {
      priceRangeUndiscounted {
        start {
          net {
            amount
          }
        }
      }
    }
    channelListings {
      pricing(customer: $customer) {
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
}
"""


def _preview_variables(variant, channel, customer):
    return {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel.slug,
        "customer": graphene.Node.to_global_id("User", customer.pk),
    }


@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixtures", "is_allowed"),
    [
        ("Unauthenticated user should be rejected", "api_client", [], False),
        (
            "Authenticated unprivileged user (non-staff) should be rejected",
            "user_api_client",
            [],
            False,
        ),
        (
            "Authenticated user w/o any permission should be rejected",
            "staff_api_client",
            [],
            False,
        ),
        (
            "Authenticated user w/ only the product permission should be rejected",
            "staff_api_client",
            ["permission_manage_products"],
            False,
        ),
        (
            "Authenticated user w/ only the user permission should be rejected",
            "staff_api_client",
            ["permission_manage_users"],
            False,
        ),
        (
            "Authenticated user w/ both permissions should be allowed",
            "staff_api_client",
            ["permission_manage_products", "permission_manage_users"],
            True,
        ),
        (
            "App w/ both permissions should be allowed",
            "app_api_client",
            ["permission_manage_products", "permission_manage_users"],
            True,
        ),
    ],
)
def test_variant_pricing_preview_authorization(
    _case,
    client_fixture,
    permission_fixtures,
    is_allowed,
    request,
    variant,
    channel_USD,
    b2b_customer_user,
    variant_channel_listing_price_for_customer_type,
):
    # given
    client = request.getfixturevalue(client_fixture)
    for permission_fixture in permission_fixtures:
        permission = request.getfixturevalue(permission_fixture)
        if client.app:
            client.app.permissions.add(permission)
        else:
            client.user.user_permissions.add(permission)
    scoped_price = variant_channel_listing_price_for_customer_type.price_amount
    variables = _preview_variables(variant, channel_USD, b2b_customer_user)

    # when
    response = client.post_graphql(VARIANT_PRICING_PREVIEW_QUERY, variables)

    # then
    if is_allowed:
        pricing = get_graphql_content(response)["data"]["productVariant"]["pricing"]
        assert pricing["priceUndiscounted"]["net"]["amount"] == scoped_price
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["productVariant"]["pricing"] is None


def test_variant_pricing_preview_resolves_the_price_of_the_given_customer(
    staff_api_client,
    permission_manage_products,
    permission_manage_users,
    variant,
    channel_USD,
    customer_user,
    gold_customer_user,
    variant_channel_listing_price_for_attribute_value,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_users
    )
    scoped_price = variant_channel_listing_price_for_attribute_value.price_amount
    listing_price = variant.channel_listings.get().price_amount
    assert scoped_price != listing_price
    assert customer_user == gold_customer_user

    # when
    preview_variables = _preview_variables(variant, channel_USD, gold_customer_user)
    preview_response = staff_api_client.post_graphql(
        VARIANT_PRICING_PREVIEW_QUERY, preview_variables
    )
    own_variables = {**preview_variables, "customer": None}
    own_response = staff_api_client.post_graphql(
        VARIANT_PRICING_PREVIEW_QUERY, own_variables
    )

    # then
    preview_pricing = get_graphql_content(preview_response)["data"]["productVariant"][
        "pricing"
    ]
    own_pricing = get_graphql_content(own_response)["data"]["productVariant"]["pricing"]
    assert preview_pricing["priceUndiscounted"]["net"]["amount"] == scoped_price
    assert own_pricing["priceUndiscounted"]["net"]["amount"] == listing_price


def test_product_pricing_preview_resolves_the_price_of_the_given_customer(
    staff_api_client,
    permission_manage_products,
    permission_manage_users,
    product,
    variant,
    channel_USD,
    b2b_customer_user,
    variant_channel_listing_price_for_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_users
    )
    scoped_price = variant_channel_listing_price_for_customer_type.price_amount
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
        "customer": graphene.Node.to_global_id("User", b2b_customer_user.pk),
    }

    # when
    response = staff_api_client.post_graphql(PRODUCT_PRICING_PREVIEW_QUERY, variables)

    # then
    product_data = get_graphql_content(response)["data"]["product"]
    assert (
        product_data["pricing"]["priceRangeUndiscounted"]["start"]["net"]["amount"]
        == scoped_price
    )
    [listing_data] = product_data["channelListings"]
    assert (
        listing_data["pricing"]["priceRangeUndiscounted"]["start"]["net"]["amount"]
        == scoped_price
    )


def test_variant_pricing_preview_rejects_an_unknown_customer(
    staff_api_client,
    permission_manage_products,
    permission_manage_users,
    variant,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_products, permission_manage_users
    )
    unknown_id = graphene.Node.to_global_id("User", -1)
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
        "customer": unknown_id,
    }

    # when
    response = staff_api_client.post_graphql(VARIANT_PRICING_PREVIEW_QUERY, variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert content["data"]["productVariant"]["pricing"] is None
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == (
        f"Couldn't resolve to a node: {unknown_id}"
    )
