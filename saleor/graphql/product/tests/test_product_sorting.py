import random
from datetime import datetime, timedelta

import graphene
import pytest
import pytz
from django.utils import timezone
from freezegun import freeze_time

from ....product.models import CollectionProduct, Product, ProductChannelListing
from ...core.connection import to_global_cursor
from ...tests.utils import get_graphql_content

COLLECTION_RESORT_QUERY = """
mutation ReorderCollectionProducts($collectionId: ID!, $moves: [MoveProductInput!]!) {
  collectionReorderProducts(collectionId: $collectionId, moves: $moves) {
    collection {
      id
      products(first: 10, sortBy:{field:COLLECTION, direction:ASC}) {
        edges {
          node {
            name
            id
          }
        }
      }
    }
    errors {
      field
      message
    }
  }
}
"""


def test_sort_products_within_collection_invalid_collection_id(
    staff_api_client, collection, product, permission_manage_products
):
    collection_id = graphene.Node.to_global_id("Collection", -1)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    moves = [{"productId": product_id, "sortOrder": 1}]

    content = get_graphql_content(
        staff_api_client.post_graphql(
            COLLECTION_RESORT_QUERY,
            {"collectionId": collection_id, "moves": moves},
            permissions=[permission_manage_products],
        )
    )["data"]["collectionReorderProducts"]

    assert content["errors"] == [
        {
            "field": "collectionId",
            "message": f"Couldn't resolve to a collection: {collection_id}",
        }
    ]


def test_sort_products_within_collection_invalid_product_id(
    staff_api_client, collection, product, permission_manage_products
):
    # Remove the products from the collection to make the product invalid
    collection.products.clear()
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    # The move should be targeting an invalid product
    product_id = graphene.Node.to_global_id("Product", product.pk)
    moves = [{"productId": product_id, "sortOrder": 1}]

    content = get_graphql_content(
        staff_api_client.post_graphql(
            COLLECTION_RESORT_QUERY,
            {"collectionId": collection_id, "moves": moves},
            permissions=[permission_manage_products],
        )
    )["data"]["collectionReorderProducts"]

    assert content["errors"] == [
        {"field": "moves", "message": f"Couldn't resolve to a product: {product_id}"}
    ]


def test_sort_products_within_collection(
    staff_api_client,
    staff_user,
    published_collection,
    collection_with_products,
    permission_manage_products,
    channel_USD,
):

    staff_api_client.user.user_permissions.add(permission_manage_products)
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)

    products = collection_with_products
    collection = products[0].collections.first()
    collection_products = list(collection.collectionproduct.all())

    collection_prod_1 = collection_products[0]
    collection_prod_2 = collection_products[1]
    collection_prod_3 = collection_products[2]

    collection_prod_1.sort_order = 0
    collection_prod_2.sort_order = 1
    collection_prod_3.sort_order = 2

    CollectionProduct.objects.bulk_update(collection_products, ["sort_order"])

    product = graphene.Node.to_global_id("Product", collection_prod_1.product_id)
    second_product = graphene.Node.to_global_id("Product", collection_prod_2.product_id)
    third_product = graphene.Node.to_global_id("Product", collection_prod_3.product_id)

    variables = {
        "collectionId": collection_id,
        "moves": [{"productId": third_product, "sortOrder": -1}],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(COLLECTION_RESORT_QUERY, variables)
    )["data"]["collectionReorderProducts"]
    assert not content["errors"]

    assert content["collection"]["id"] == collection_id

    products = content["collection"]["products"]["edges"]
    assert products[0]["node"]["id"] == product
    assert products[1]["node"]["id"] == third_product
    assert products[2]["node"]["id"] == second_product

    variables = {
        "collectionId": collection_id,
        "moves": [
            {"productId": product, "sortOrder": 1},
            {"productId": second_product, "sortOrder": -1},
        ],
    }
    content = get_graphql_content(
        staff_api_client.post_graphql(COLLECTION_RESORT_QUERY, variables)
    )["data"]["collectionReorderProducts"]

    products = content["collection"]["products"]["edges"]
    assert products[0]["node"]["id"] == third_product
    assert products[1]["node"]["id"] == second_product
    assert products[2]["node"]["id"] == product


GET_SORTED_PRODUCTS_QUERY = """
query Products($sortBy: ProductOrder, $channel: String) {
    products(first: 10, sortBy: $sortBy, channel: $channel) {
      edges {
        node {
          id
        }
      }
    }
}
"""


@freeze_time("2020-03-18 12:00:00")
@pytest.mark.parametrize(
    "direction, order_direction",
    (("ASC", "published_at"), ("DESC", "-published_at")),
)
def test_sort_products_by_published_at(
    direction, order_direction, api_client, product_list, channel_USD
):
    product_channel_listings = []
    for iter_value, product in enumerate(product_list):
        product_channel_listing = product.channel_listings.get(channel=channel_USD)
        product_channel_listing.published_at = timezone.now() - timedelta(
            days=iter_value
        )
        product_channel_listings.append(product_channel_listing)
    ProductChannelListing.objects.bulk_update(
        product_channel_listings, ["published_at"]
    )

    variables = {
        "sortBy": {
            "direction": direction,
            "field": "PUBLISHED_AT",
        },
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(GET_SORTED_PRODUCTS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["products"]["edges"]

    if direction == "ASC":
        product_list.reverse()

    assert [node["node"]["id"] for node in data] == [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]


@pytest.mark.parametrize(
    "direction, order_direction",
    (("ASC", "rating"), ("DESC", "-rating")),
)
def test_sort_products_by_rating(
    direction, order_direction, api_client, product_list, channel_USD
):

    for product in product_list:
        product.rating = random.uniform(1, 10)
    Product.objects.bulk_update(product_list, ["rating"])

    variables = {
        "sortBy": {"direction": direction, "field": "RATING"},
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(GET_SORTED_PRODUCTS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["products"]["edges"]

    sorted_products = Product.objects.order_by(order_direction)
    expected_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in sorted_products
    ]
    assert [node["node"]["id"] for node in data] == expected_ids


QUERY_PAGINATED_SORTED_PRODUCTS = """
    query Products(
        $first: Int, $sortBy: ProductOrder, $channel: String, $after: String
    ) {
        products(first: $first, sortBy: $sortBy, after: $after, channel: $channel) {
            edges {
                node {
                    id
                    slug
                }
            }
            pageInfo{
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
        }
    }
"""


def test_pagination_for_sorting_products_by_published_at_date(
    api_client, channel_USD, product_list
):
    """Ensure that using the cursor in sorting products by published at date works
    properly."""
    # given
    channel_listings = ProductChannelListing.objects.filter(channel_id=channel_USD.id)
    listings_in_bulk = {listing.product_id: listing for listing in channel_listings}
    for product in product_list:
        listing = listings_in_bulk.get(product.id)
        listing.published_at = datetime.now(pytz.UTC)

    ProductChannelListing.objects.bulk_update(channel_listings, ["published_at"])

    first = 2
    variables = {
        "sortBy": {"direction": "ASC", "field": "PUBLISHED_AT"},
        "channel": channel_USD.slug,
        "first": first,
    }

    # first request
    response = api_client.post_graphql(QUERY_PAGINATED_SORTED_PRODUCTS, variables)

    content = get_graphql_content(response)
    data = content["data"]["products"]
    assert len(data["edges"]) == first
    assert [node["node"]["slug"] for node in data["edges"]] == [
        product.slug for product in product_list[:first]
    ]
    end_cursor = data["pageInfo"]["endCursor"]

    variables["after"] = end_cursor

    # when
    # second request
    response = api_client.post_graphql(QUERY_PAGINATED_SORTED_PRODUCTS, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["products"]
    expected_count = len(product_list) - first
    assert len(data["edges"]) == expected_count
    assert [node["node"]["slug"] for node in data["edges"]] == [
        product.slug for product in product_list[first:]
    ]


QUERY_SORT_BY_COLLECTION = """
query CollectionProducts($id: ID, $channel: String, $after: String) {
  collection(id: $id channel: $channel) {
    id
    products(first: 2, sortBy: {field: COLLECTION, direction: ASC},after: $after) {
      totalCount
      edges {
        node {
          id
          category {
            id
            name
          }
        }
      }
      pageInfo {
        endCursor
        hasNextPage
        hasPreviousPage
        startCursor
      }
    }
  }
}
"""


def test_query_products_sorted_by_collection(
    staff_api_client,
    staff_user,
    published_collection,
    collection_with_products,
    permission_manage_products,
    channel_USD,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)

    products = collection_with_products
    collection = products[0].collections.first()
    collection_products = list(collection.collectionproduct.all())

    collection_prod_1 = collection_products[0]
    collection_prod_2 = collection_products[1]
    collection_prod_3 = collection_products[2]

    collection_prod_1.sort_order = 0
    collection_prod_2.sort_order = 1
    collection_prod_3.sort_order = 2

    CollectionProduct.objects.bulk_update(collection_products, ["sort_order"])

    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
        "after": to_global_cursor(
            (collection_prod_2.sort_order, collection_prod_2.product.pk)
        ),
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(QUERY_SORT_BY_COLLECTION, variables)
    )

    products = content["data"]["collection"]["products"]
    assert products["totalCount"] == 3
    assert len(products["edges"]) == 1
    assert not products["pageInfo"]["hasNextPage"]
    assert products["pageInfo"]["hasPreviousPage"]
    assert products["edges"][0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", collection_prod_3.product_id
    )
