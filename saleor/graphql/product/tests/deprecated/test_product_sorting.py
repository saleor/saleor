from datetime import datetime, timedelta

import graphene
import pytest
import pytz
from django.utils import timezone
from freezegun import freeze_time

from .....product.models import (
    Collection,
    CollectionChannelListing,
    ProductChannelListing,
)
from ....tests.utils import assert_graphql_error_with_message, get_graphql_content

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
    ("direction", "order_direction"),
    [("ASC", "publication_date"), ("DESC", "-publication_date")],
)
def test_sort_products_by_publication_date(
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
            "field": "PUBLICATION_DATE",
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


QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING = """
    query ($sortBy: ProductOrder, $filter: ProductFilterInput, $channel: String){
        products (
            first: 10, sortBy: $sortBy, filter: $filter, channel: $channel
        ) {
            edges {
                node {
                    name
                    slug
                }
            }
        }
    }
"""


def test_products_with_sorting_and_without_channel(
    staff_api_client,
    permission_manage_products,
):
    # given
    variables = {"sortBy": {"field": "PUBLICATION_DATE", "direction": "DESC"}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_WITH_SORTING_AND_FILTERING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    assert_graphql_error_with_message(response, "A default channel does not exist.")


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


def test_pagination_for_sorting_products_by_publication_date(
    api_client, channel_USD, product_list
):
    # given
    channel_listings = ProductChannelListing.objects.filter(channel_id=channel_USD.id)
    listings_in_bulk = {listing.product_id: listing for listing in channel_listings}
    for product in product_list:
        listing = listings_in_bulk.get(product.id)
        listing.published_at = datetime.now(pytz.UTC)

    ProductChannelListing.objects.bulk_update(channel_listings, ["published_at"])

    first = 2
    variables = {
        "sortBy": {"direction": "ASC", "field": "PUBLICATION_DATE"},
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


QUERY_PAGINATED_SORTED_COLLECTIONS = """
    query (
        $first: Int, $sort_by: CollectionSortingInput!, $after: String, $channel: String
    ) {
        collections(first: $first, sortBy: $sort_by, after: $after, channel: $channel) {
                edges{
                    node{
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


def test_pagination_for_sorting_collections_by_publication_date(
    api_client, channel_USD
):
    # given
    collections = Collection.objects.bulk_create(
        [
            Collection(name="Coll1", slug="collection-1"),
            Collection(name="Coll2", slug="collection-2"),
            Collection(name="Coll3", slug="collection-3"),
        ]
    )
    now = datetime.now(pytz.UTC)
    CollectionChannelListing.objects.bulk_create(
        [
            CollectionChannelListing(
                channel=channel_USD,
                collection=collection,
                is_published=True,
                published_at=now - timedelta(days=num),
            )
            for num, collection in enumerate(collections)
        ]
    )

    first = 2
    variables = {
        "sort_by": {"direction": "DESC", "field": "PUBLICATION_DATE"},
        "channel": channel_USD.slug,
        "first": first,
    }

    # first request
    response = api_client.post_graphql(QUERY_PAGINATED_SORTED_COLLECTIONS, variables)

    content = get_graphql_content(response)
    data = content["data"]["collections"]
    assert len(data["edges"]) == first
    assert [node["node"]["slug"] for node in data["edges"]] == [
        collection.slug for collection in collections[:first]
    ]
    end_cursor = data["pageInfo"]["endCursor"]

    variables["after"] = end_cursor

    # when
    # second request
    response = api_client.post_graphql(QUERY_PAGINATED_SORTED_COLLECTIONS, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["collections"]
    expected_count = len(collections) - first
    assert len(data["edges"]) == expected_count
    assert [node["node"]["slug"] for node in data["edges"]] == [
        collection.slug for collection in collections[first:]
    ]
