from unittest.mock import patch

import graphene
import pytest

from ....tests.utils import get_graphql_content
from ...mutations.collection.collection_create import CollectionCreate
from ...mutations.collection.collection_delete import CollectionDelete


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_collection_view(api_client, published_collection, count_queries, channel_USD):
    query = """
        fragment BasicProductFields on Product {
          id
          name
          thumbnail {
            url
            alt
          }
          thumbnail2x: thumbnail(size: 510) {
            url
          }
        }

        fragment Price on TaxedMoney {
          gross {
            amount
            currency
          }
          net {
            amount
            currency
          }
        }

        fragment ProductPricingField on Product {
          pricing {
            onSale
            priceRangeUndiscounted {
              start {
                ...Price
              }
              stop {
                ...Price
              }
            }
            priceRange {
              start {
                ...Price
              }
              stop {
                ...Price
              }
            }
          }
        }

        query Collection($id: ID!, $pageSize: Int, $channel: String) {
          collection(id: $id, channel: $channel) {
            id
            slug
            name
            seoDescription
            seoTitle
            backgroundImage {
              url
            }
          }
          products (
            first: $pageSize,
            filter: {collections: [$id]},
            channel: $channel
          ) {
            totalCount
            edges {
              node {
                ...BasicProductFields
                ...ProductPricingField
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
          attributes(filter: {inCollection: $id}, channel: $channel, first: 100) {
            edges {
              node {
                id
                name
                slug
                choices(first: 10) {
                  edges {
                    node {
                      id
                      name
                      slug
                    }
                  }
                }
              }
            }
          }
        }
    """
    variables = {
        "pageSize": 100,
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "channel": channel_USD.slug,
    }
    get_graphql_content(api_client.post_graphql(query, variables))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_collection_channel_listings(
    product_list_with_many_channels,
    staff_api_client,
    count_queries,
    permission_manage_products,
    channel_USD,
):
    query = """
        query($channel: String) {
          collections(first: 10, channel: $channel) {
            edges {
              node {
                id
                channelListings {
                  publicationDate
                  isPublished
                  channel{
                    slug
                    currencyCode
                    name
                    isActive
                  }
                }
              }
            }
          }
        }
    """

    variables = {"channel": channel_USD.slug}
    get_graphql_content(
        staff_api_client.post_graphql(
            query,
            variables,
            permissions=(permission_manage_products,),
            check_no_permissions=False,
        )
    )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_create_collection(
    settings,
    staff_api_client,
    product_list_with_many_channels,
    permission_manage_products,
    count_queries,
):
    query = """
        mutation createCollection(
                $name: String!, $slug: String,
                $description: JSONString, $products: [ID!],
                $backgroundImage: Upload, $backgroundImageAlt: String) {
            collectionCreate(
                input: {
                    name: $name,
                    slug: $slug,
                    description: $description,
                    products: $products,
                    backgroundImage: $backgroundImage,
                    backgroundImageAlt: $backgroundImageAlt}) {
                collection {
                    name
                    slug
                    description
                    products {
                        totalCount
                    }
                    backgroundImage{
                        alt
                    }
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk)
        for product in product_list_with_many_channels
    ]
    name = "test-name"
    slug = "test-slug"
    variables = {
        "name": name,
        "slug": slug,
        "products": product_ids,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    errors = content["data"]["collectionCreate"]["errors"]
    assert not errors


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_delete_collection(
    settings,
    staff_api_client,
    collection_with_products,
    permission_manage_products,
    count_queries,
):
    query = """
        mutation deleteCollection($id: ID!) {
            collectionDelete(id: $id) {
                collection {
                    name
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    collection = collection_with_products[0].collections.first()
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    collection_id = graphene.Node.to_global_id("Collection", collection.id)

    variables = {
        "id": collection_id,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    errors = content["data"]["collectionDelete"]["errors"]
    assert not errors


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_collection_add_products(
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
    settings,
    count_queries,
):
    query = """
        mutation collectionAddProducts(
            $id: ID!, $products: [ID!]!) {
            collectionAddProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    errors = content["data"]["collectionAddProducts"]["errors"]
    assert not errors


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_remove_products_from_collection(
    staff_api_client,
    collection_with_products,
    permission_manage_products,
    settings,
    count_queries,
):
    query = """
        mutation collectionRemoveProducts(
            $id: ID!, $products: [ID!]!) {
            collectionRemoveProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    collection = collection_with_products[0].collections.first()
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk)
        for product in collection_with_products
    ]
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    errors = content["data"]["collectionRemoveProducts"]["errors"]
    assert not errors


def test_collection_bulk_delete(
    staff_api_client,
    collection_list,
    product_list,
    permission_manage_products,
    count_queries,
    settings,
):
    query = """
    mutation collectionBulkDelete($ids: [ID!]!) {
        collectionBulkDelete(ids: $ids) {
            count
            errors {
                field
                message
                code
            }
        }
    }
    """
    for collection in collection_list:
        collection.products.add(*product_list)
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variables = {
        "ids": [
            graphene.Node.to_global_id("Collection", collection.id)
            for collection in collection_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert not content["data"]["collectionBulkDelete"]["errors"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_collections_for_federation_query_count(
    api_client,
    published_collections,
    channel_USD,
    django_assert_num_queries,
    count_queries,
):
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

    variables = {
        "representations": [
            {
                "__typename": "Collection",
                "id": graphene.Node.to_global_id(
                    "Collection", published_collections[0].pk
                ),
                "channel": channel_USD.slug,
            },
        ],
    }

    with django_assert_num_queries(2):
        response = api_client.post_graphql(query, variables)
        content = get_graphql_content(response)
        assert len(content["data"]["_entities"]) == 1
        for collection_data in content["data"]["_entities"]:
            assert collection_data is not None

    variables = {
        "representations": [
            {
                "__typename": "Collection",
                "id": graphene.Node.to_global_id("Collection", collection.pk),
                "channel": channel_USD.slug,
            }
            for collection in published_collections
        ],
    }

    with django_assert_num_queries(2):
        response = api_client.post_graphql(query, variables)
        content = get_graphql_content(response)
        assert len(content["data"]["_entities"]) == 3
        for collection_data in content["data"]["_entities"]:
            assert collection_data is not None


@patch(
    "saleor.graphql.product.mutations.collection.collection_delete."
    "PRODUCTS_BATCH_SIZE",
    2,
)
@patch(
    "saleor.graphql.product.mutations.collection.collection_create."
    "PRODUCTS_BATCH_SIZE",
    2,
)
@pytest.mark.parametrize(
    "mutation_class",
    [
        CollectionCreate,
        CollectionDelete,
    ],
)
def test_collection_batching_not_even(mutation_class):
    ids = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    batches = list(mutation_class.batch_product_ids(ids))
    assert batches == [[1, 2], [3, 4], [5, 6], [7, 8], [9]]


@patch(
    "saleor.graphql.product.mutations.collection.collection_delete."
    "PRODUCTS_BATCH_SIZE",
    2,
)
@patch(
    "saleor.graphql.product.mutations.collection.collection_create."
    "PRODUCTS_BATCH_SIZE",
    2,
)
@pytest.mark.parametrize(
    "mutation_class",
    [
        CollectionCreate,
        CollectionDelete,
    ],
)
def test_collection_batching_even(mutation_class):
    ids = [1, 2, 3, 4, 5, 6, 7, 8]
    batches = list(mutation_class.batch_product_ids(ids))
    assert batches == [[1, 2], [3, 4], [5, 6], [7, 8]]


@patch(
    "saleor.graphql.product.mutations.collection.collection_delete."
    "PRODUCTS_BATCH_SIZE",
    2,
)
@patch(
    "saleor.graphql.product.mutations.collection.collection_create."
    "PRODUCTS_BATCH_SIZE",
    2,
)
@pytest.mark.parametrize(
    "mutation_class",
    [
        CollectionCreate,
        CollectionDelete,
    ],
)
def test_collection_batching_smaller_than_batch_size(mutation_class):
    ids = [1]
    batches = list(mutation_class.batch_product_ids(ids))
    assert batches == [[1]]


@patch(
    "saleor.graphql.product.mutations.collection.collection_delete."
    "PRODUCTS_BATCH_SIZE",
    2,
)
@patch(
    "saleor.graphql.product.mutations.collection.collection_create."
    "PRODUCTS_BATCH_SIZE",
    2,
)
@pytest.mark.parametrize(
    "mutation_class",
    [
        CollectionCreate,
        CollectionDelete,
    ],
)
def test_collection_batching_no_ids(mutation_class):
    ids = []
    batches = list(mutation_class.batch_product_ids(ids))
    assert batches == []
