import graphene
import pytest

from ......product.models import ProductVariant, ProductVariantChannelListing
from .....tests.utils import get_graphql_content
from .shared import PRODUCT_VARIANTS_WHERE_QUERY

PRODUCT_PRODUCT_VARIANTS_WHERE_QUERY = """
    query($id: ID!, $channel: String, $where: ProductVariantWhereInput) {
      product(id: $id, channel: $channel) {
        productVariants(first: 10, where: $where) {
          totalCount
          edges {
            node {
              id
            }
          }
        }
      }
    }
"""


@pytest.fixture
def variants_with_mixed_channel_listings(product_with_two_variants):
    """Return (priced, unpriced, unlisted) variants of one channel-listed product."""
    priced, unpriced = product_with_two_variants.variants.order_by("pk")
    ProductVariantChannelListing.objects.filter(variant=unpriced).update(
        price_amount=None
    )
    unlisted = ProductVariant.objects.create(
        product=product_with_two_variants, sku="Product variant #unlisted"
    )
    return priced, unpriced, unlisted


def _global_ids(variants):
    return {graphene.Node.to_global_id("ProductVariant", v.pk) for v in variants}


def _returned_ids(connection):
    return {edge["node"]["id"] for edge in connection["edges"]}


@pytest.mark.parametrize(
    ("value", "expected_indexes"),
    [
        (True, [0]),
        (False, [1, 2]),
    ],
)
def test_variants_filter_by_is_available_in_channel(
    value,
    expected_indexes,
    staff_api_client,
    permission_manage_products,
    variants_with_mixed_channel_listings,
    channel_USD,
):
    # given
    variants = variants_with_mixed_channel_listings
    variables = {
        "channel": channel_USD.slug,
        "where": {"isAvailableInChannel": value},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    assert _returned_ids(content["data"]["productVariants"]) == _global_ids(
        [variants[index] for index in expected_indexes]
    )


def test_variants_filter_by_is_available_in_channel_without_channel(
    staff_api_client,
    permission_manage_products,
    variants_with_mixed_channel_listings,
):
    # given
    variables = {"where": {"isAvailableInChannel": True}}

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["productVariants"]["edges"] == []


def test_product_variants_filter_by_is_available_in_channel_as_staff(
    staff_api_client,
    permission_manage_products,
    product_with_two_variants,
    variants_with_mixed_channel_listings,
    channel_USD,
):
    # given
    priced, unpriced, unlisted = variants_with_mixed_channel_listings
    product_id = graphene.Node.to_global_id("Product", product_with_two_variants.pk)
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    unfiltered = get_graphql_content(
        staff_api_client.post_graphql(
            PRODUCT_PRODUCT_VARIANTS_WHERE_QUERY,
            {"id": product_id, "channel": channel_USD.slug},
        )
    )["data"]["product"]["productVariants"]
    filtered = get_graphql_content(
        staff_api_client.post_graphql(
            PRODUCT_PRODUCT_VARIANTS_WHERE_QUERY,
            {
                "id": product_id,
                "channel": channel_USD.slug,
                "where": {"isAvailableInChannel": True},
            },
        )
    )["data"]["product"]["productVariants"]

    # then
    # Staff scoping of Product.productVariants only checks the product's channel
    # listing, so a variant with no listing in the channel is still returned.
    assert _returned_ids(unfiltered) == _global_ids([priced, unpriced, unlisted])
    assert unfiltered["totalCount"] == 3
    assert _returned_ids(filtered) == _global_ids([priced])
    assert filtered["totalCount"] == 1
