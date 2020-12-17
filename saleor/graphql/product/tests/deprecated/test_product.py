import warnings

import graphene

from .....channel.utils import DEPRECATION_WARNING_MESSAGE
from .....product.models import Product
from ....tests.utils import get_graphql_content

QUERY_PRODUCT = """
    query ($id: ID, $slug: String){
        product(
            id: $id,
            slug: $slug,
        ) {
            id
            name
        }
    }
    """

QUERY_FETCH_ALL_PRODUCTS = """
    query {
        products(first: 1) {
            totalCount
            edges {
                node {
                    name
                    isAvailable
                    availableForPurchase
                    isAvailableForPurchase
                }
            }
        }
    }
"""


def test_product_query_by_id_with_default_channel(user_api_client, product):
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    with warnings.catch_warnings(record=True) as warns:
        response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
        content = get_graphql_content(response)
    collection_data = content["data"]["product"]
    assert collection_data is not None
    assert collection_data["name"] == product.name
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_product_query_by_slug_with_default_channel(user_api_client, product):
    variables = {"slug": product.slug}
    with warnings.catch_warnings(record=True) as warns:
        response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
        content = get_graphql_content(response)
    collection_data = content["data"]["product"]
    assert collection_data is not None
    assert collection_data["name"] == product.name
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_fetch_all_products(user_api_client, product):
    with warnings.catch_warnings(record=True) as warns:
        response = user_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS)
        content = get_graphql_content(response)
    product_channel_listing = product.channel_listings.get()
    num_products = Product.objects.count()
    data = content["data"]["products"]
    product_data = data["edges"][0]["node"]
    assert data["totalCount"] == num_products
    assert product_data["isAvailable"] is True
    assert product_data["isAvailableForPurchase"] is True
    assert product_data["availableForPurchase"] == str(
        product_channel_listing.available_for_purchase
    )
    assert len(content["data"]["products"]["edges"]) == num_products
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


QUERY_COLLECTION_FROM_PRODUCT = """
    query ($id: ID, $channel:String){
        product(
            id: $id,
            channel: $channel
        ) {
            collections {
                name
            }
        }
    }
    """


def test_get_collections_from_product_as_customer(
    user_api_client, product_with_collections, channel_USD, published_collection
):
    # given
    product = product_with_collections
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    with warnings.catch_warnings(record=True) as warns:
        response = user_api_client.post_graphql(
            QUERY_COLLECTION_FROM_PRODUCT,
            variables=variables,
            permissions=(),
            check_no_permissions=False,
        )

    # then
    content = get_graphql_content(response)
    collections = content["data"]["product"]["collections"]
    assert len(collections) == 1
    assert {"name": published_collection.name} in collections
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_get_collections_from_product_as_anonymous(
    api_client, product_with_collections, channel_USD, published_collection
):
    # given
    product = product_with_collections
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(
            QUERY_COLLECTION_FROM_PRODUCT,
            variables=variables,
            permissions=(),
            check_no_permissions=False,
        )

    # then
    content = get_graphql_content(response)
    collections = content["data"]["product"]["collections"]
    assert len(collections) == 1
    assert {"name": published_collection.name} in collections
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )
