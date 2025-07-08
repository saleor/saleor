import datetime

import graphene
import pytest

from .....product.models import Collection, CollectionChannelListing, Product
from .....tests.utils import dummy_editorjs
from ....tests.utils import (
    get_graphql_content,
)


def test_collections_query(
    user_api_client,
    published_collection,
    unpublished_collection,
    permission_manage_products,
    channel_USD,
):
    query = """
        query Collections ($channel: String) {
            collections(first:2, channel: $channel) {
                edges {
                    node {
                        name
                        slug
                        description
                        descriptionJson
                        products {
                            totalCount
                        }
                    }
                }
            }
        }
    """

    # query public collections only as regular user
    variables = {"channel": channel_USD.slug}
    description = dummy_editorjs("Test description.", json_format=True)
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["collections"]["edges"]
    assert len(edges) == 1
    collection_data = edges[0]["node"]
    assert collection_data["name"] == published_collection.name
    assert collection_data["slug"] == published_collection.slug
    assert collection_data["description"] == description
    assert collection_data["descriptionJson"] == description
    assert (
        collection_data["products"]["totalCount"]
        == published_collection.products.count()
    )


def test_collections_query_without_description(
    user_api_client,
    published_collection,
    unpublished_collection,
    permission_manage_products,
    channel_USD,
):
    query = """
        query Collections ($channel: String) {
            collections(first:2, channel: $channel) {
                edges {
                    node {
                        name
                        slug
                        description
                        descriptionJson
                    }
                }
            }
        }
    """

    # query public collections only as regular user
    variables = {"channel": channel_USD.slug}
    collection = published_collection
    collection.description = None
    collection.save()
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["collections"]["edges"]
    assert len(edges) == 1
    collection_data = edges[0]["node"]
    assert collection_data["name"] == collection.name
    assert collection_data["slug"] == collection.slug
    assert collection_data["description"] is None
    assert collection_data["descriptionJson"] == "{}"


def test_collections_query_as_staff(
    staff_api_client,
    published_collection,
    unpublished_collection_PLN,
    permission_manage_products,
    channel_USD,
):
    query = """
        query Collections($channel: String) {
            collections(first: 2, channel: $channel) {
                edges {
                    node {
                        name
                        slug
                        description
                        products {
                            totalCount
                        }
                    }
                }
            }
        }
    """
    # query all collections only as a staff user with proper permissions
    variables = {"channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["collections"]["edges"]
    assert len(edges) == 1


def test_collections_query_as_staff_without_channel(
    staff_api_client,
    published_collection,
    unpublished_collection_PLN,
    permission_manage_products,
    channel_USD,
):
    query = """
        query Collections($channel: String) {
            collections(first: 2, channel: $channel) {
                edges {
                    node {
                        name
                        slug
                        description
                        products {
                            totalCount
                        }
                    }
                }
            }
        }
    """
    # query all collections only as a staff user with proper permissions
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    edges = content["data"]["collections"]["edges"]
    assert len(edges) == 2


NOT_EXISTS_IDS_COLLECTIONS_QUERY = """
    query ($filter: CollectionFilterInput!, $channel: String) {
        collections(first: 5, filter: $filter, channel: $channel) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""


def test_collections_query_ids_not_exists(
    user_api_client, published_collection, channel_USD
):
    query = NOT_EXISTS_IDS_COLLECTIONS_QUERY
    variables = {
        "filter": {"ids": ["ncXc5tP7kmV6pxE=", "yMyDVE5S2LWWTqK="]},
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    message_error = '{"ids": [{"message": "Invalid ID specified.", "code": ""}]}'

    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["collections"] is None


GET_SORTED_PRODUCTS_COLLECTION_QUERY = """
query CollectionProducts($id: ID!, $channel: String, $sortBy: ProductOrder) {
  collection(id: $id, channel: $channel) {
    products(first: 10, sortBy: $sortBy) {
      edges {
        node {
          id
        }
      }
    }
  }
}
"""


def test_sort_collection_products_by_name(
    staff_api_client, published_collection, product_list, channel_USD
):
    # given
    for product in product_list:
        published_collection.products.add(product)

    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "sortBy": {"direction": "DESC", "field": "NAME"},
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        GET_SORTED_PRODUCTS_COLLECTION_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collection"]["products"]["edges"]

    assert [node["node"]["id"] for node in data] == [
        graphene.Node.to_global_id("Product", product.pk)
        for product in Product.objects.order_by("-name")
    ]


GET_SORTED_COLLECTION_QUERY = """
query Collections($sortBy: CollectionSortingInput) {
  collections(first: 10, sortBy: $sortBy) {
      edges {
        node {
          id
          publicationDate
        }
      }
  }
}
"""


def test_query_collection_for_federation(api_client, published_collection, channel_USD):
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)
    variables = {
        "representations": [
            {
                "__typename": "Collection",
                "id": collection_id,
                "channel": channel_USD.slug,
            },
        ],
    }
    query = """
      query GetCollectionInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on Collection {
            id
            name
          }
        }
      }
    """

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Collection",
            "id": collection_id,
            "name": published_collection.name,
        }
    ]


QUERY_COLLECTIONS_WITH_SORT = """
    query ($sort_by: CollectionSortingInput!, $channel: String) {
        collections(first:5, sortBy: $sort_by, channel: $channel) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    ("collection_sort", "result_order"),
    [
        ({"field": "NAME", "direction": "ASC"}, ["Coll1", "Coll2", "Coll3"]),
        ({"field": "NAME", "direction": "DESC"}, ["Coll3", "Coll2", "Coll1"]),
        ({"field": "AVAILABILITY", "direction": "ASC"}, ["Coll2", "Coll1", "Coll3"]),
        ({"field": "AVAILABILITY", "direction": "DESC"}, ["Coll3", "Coll1", "Coll2"]),
        ({"field": "PRODUCT_COUNT", "direction": "ASC"}, ["Coll1", "Coll3", "Coll2"]),
        ({"field": "PRODUCT_COUNT", "direction": "DESC"}, ["Coll2", "Coll3", "Coll1"]),
    ],
)
def test_collections_query_with_sort(
    collection_sort,
    result_order,
    staff_api_client,
    permission_manage_products,
    product,
    channel_USD,
):
    collections = Collection.objects.bulk_create(
        [
            Collection(name="Coll1", slug="collection-1"),
            Collection(name="Coll2", slug="collection-2"),
            Collection(name="Coll3", slug="collection-3"),
        ]
    )
    published = (True, False, True)
    CollectionChannelListing.objects.bulk_create(
        [
            CollectionChannelListing(
                channel=channel_USD, collection=collection, is_published=published[num]
            )
            for num, collection in enumerate(collections)
        ]
    )
    product.collections.add(Collection.objects.get(name="Coll2"))
    variables = {"sort_by": collection_sort, "channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_COLLECTIONS_WITH_SORT, variables)
    content = get_graphql_content(response)
    collections = content["data"]["collections"]["edges"]
    for order, collection_name in enumerate(result_order):
        assert collections[order]["node"]["name"] == collection_name


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


def test_pagination_for_sorting_collections_by_published_at_date(
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
    now = datetime.datetime.now(tz=datetime.UTC)
    CollectionChannelListing.objects.bulk_create(
        [
            CollectionChannelListing(
                channel=channel_USD,
                collection=collection,
                is_published=True,
                published_at=now - datetime.timedelta(days=num),
            )
            for num, collection in enumerate(collections)
        ]
    )

    first = 2
    variables = {
        "sort_by": {"direction": "DESC", "field": "PUBLISHED_AT"},
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


def test_collections_query_return_error_with_sort_by_rank_without_search(
    staff_api_client, published_collection, product_list, channel_USD
):
    # given
    for product in product_list:
        published_collection.products.add(product)

    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "sortBy": {"direction": "DESC", "field": "RANK"},
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        GET_SORTED_PRODUCTS_COLLECTION_QUERY, variables
    )
    content = get_graphql_content(response, ignore_errors=True)

    # then
    errors = content["errors"]
    expected_message = (
        "Sorting by RANK is available only when using a search filter "
        "or search argument."
    )
    assert len(errors) == 1
    assert errors[0]["message"] == expected_message
