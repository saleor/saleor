import warnings

import graphene

from .....channel.models import Channel
from .....channel.utils import DEPRECATION_WARNING_MESSAGE
from .....product.models import Collection, CollectionChannelListing, Product
from .....tests.utils import dummy_editorjs
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
                    variants{
                        id
                    }
                }
            }
        }
    }
"""

QUERY_PRODUCTS_WITH_FILTER = """
    query ($filter: ProductFilterInput!) {
        products(first:5, filter: $filter) {
            edges{
                node{
                id
                name
                }
            }
        }
    }
"""


SORT_PRODUCTS_QUERY = """
    query {
        products (
            sortBy: %(sort_by_product_order)s, first: 3
        ) {
            edges {
                node {
                    name
                    productType{
                        name
                    }
                    updatedAt
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
        product_channel_listing.available_for_purchase_at.date()
    )
    assert len(content["data"]["products"]["edges"]) == num_products
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_products_query_with_price_filter(
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
    channel_PLN,
):
    channel_PLN.delete()
    assert Channel.objects.count() == 1
    product = product_list[0]
    product.variants.first().channel_listings.filter().update(price_amount=None)

    variables = {
        "filter": {"price": {"gte": 9, "lte": 31}},
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)
    with warnings.catch_warnings(record=True) as warns:
        response = staff_api_client.post_graphql(QUERY_PRODUCTS_WITH_FILTER, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 3
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_sort_products_product_type_name(
    user_api_client, product, product_with_default_variant, channel_USD
):
    # Test sorting by TYPE, ascending
    asc_published_query = SORT_PRODUCTS_QUERY % {
        "sort_by_product_order": "{field: TYPE, direction:ASC}"
    }
    with warnings.catch_warnings(record=True) as warns:
        response = user_api_client.post_graphql(asc_published_query, {})
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    product_type_name_0 = edges[0]["node"]["productType"]["name"]
    product_type_name_1 = edges[1]["node"]["productType"]["name"]
    assert product_type_name_0 < product_type_name_1
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )

    # Test sorting by PUBLISHED, descending
    desc_published_query = SORT_PRODUCTS_QUERY % {
        "sort_by_product_order": "{field: TYPE, direction:DESC}"
    }
    with warnings.catch_warnings(record=True) as warns:
        response = user_api_client.post_graphql(desc_published_query, {})
    content = get_graphql_content(response)
    product_type_name_0 = edges[0]["node"]["productType"]["name"]
    product_type_name_1 = edges[1]["node"]["productType"]["name"]
    assert product_type_name_0 < product_type_name_1
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


QUERY_COLLECTIONS_WITH_FILTER = """
    query ($filter: CollectionFilterInput!) {
          collections(first:5, filter: $filter) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
"""


QUERY_COLLECTIONS_WITH_SORT = """
    query ($sort_by: CollectionSortingInput!) {
        collections(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
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


def test_collections_query_with_filter(
    channel_USD,
    staff_api_client,
    permission_manage_products,
):
    # given
    collections = Collection.objects.bulk_create(
        [
            Collection(
                id=1,
                name="Collection1",
                slug="collection-published1",
                description=dummy_editorjs("Test description"),
            ),
            Collection(
                id=2,
                name="Collection2",
                slug="collection-published2",
                description=dummy_editorjs("Test description"),
            ),
            Collection(
                id=3,
                name="Collection3",
                slug="collection-unpublished",
                description=dummy_editorjs("Test description"),
            ),
        ]
    )
    published = (True, True, False)
    CollectionChannelListing.objects.bulk_create(
        [
            CollectionChannelListing(
                channel=channel_USD, collection=collection, is_published=published[num]
            )
            for num, collection in enumerate(collections)
        ]
    )
    variables = {"filter": {"published": "PUBLISHED"}}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    with warnings.catch_warnings(record=True) as warns:
        response = staff_api_client.post_graphql(
            QUERY_COLLECTIONS_WITH_FILTER, variables
        )

    # then
    content = get_graphql_content(response)
    collections = content["data"]["collections"]["edges"]

    assert len(collections) == 2
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_collections_query_with_sort(
    staff_api_client,
    permission_manage_products,
    product,
    channel_USD,
):
    collections = Collection.objects.bulk_create(
        [
            Collection(name="Coll1", slug="collection-published1"),
            Collection(name="Coll2", slug="collection-unpublished2"),
            Collection(name="Coll3", slug="collection-published"),
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
    variables = {"sort_by": {"field": "AVAILABILITY", "direction": "ASC"}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    with warnings.catch_warnings(record=True) as warns:
        response = staff_api_client.post_graphql(QUERY_COLLECTIONS_WITH_SORT, variables)

    content = get_graphql_content(response)
    collections = content["data"]["collections"]["edges"]
    for order, collection_name in enumerate(["Coll2", "Coll3", "Coll1"]):
        assert collections[order]["node"]["name"] == collection_name
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


QUERY_FETCH_ALL_VARIANTS = """
    query fetchAllVariants {
        productVariants(first: 10) {
            totalCount
            edges {
                node {
                    id
                    trackInventory
                    quantityAvailable
                    sku
                    pricing {
                        price {
                            net {
                                amount
                            }
                            gross {
                                amount
                            }
                        }
                    }
                    product {
                        id
                    }
                }
            }
        }
    }
"""


def test_fetch_all_variants(api_client, product_variant_list, channel_PLN):
    channel_PLN.delete()
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(QUERY_FETCH_ALL_VARIANTS)

    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["totalCount"] == len(product_variant_list)
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )
