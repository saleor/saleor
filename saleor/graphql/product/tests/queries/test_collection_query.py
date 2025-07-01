import logging
from unittest.mock import MagicMock

import graphene
from django.core.files import File

from .....product.tests.utils import create_image
from .....thumbnail.models import Thumbnail
from ....core.enums import LanguageCodeEnum, ThumbnailFormatEnum
from ....tests.utils import (
    get_graphql_content,
    get_graphql_content_from_response,
)

QUERY_COLLECTION = """
    query ($id: ID, $slug: String, $channel: String, $slugLanguageCode: LanguageCodeEnum){
        collection(
            id: $id,
            slug: $slug,
            channel: $channel,
            slugLanguageCode: $slugLanguageCode,
        ) {
            id
            name
        }
    }
    """


def test_collection_query_by_id(user_api_client, published_collection, channel_USD):
    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(QUERY_COLLECTION, variables=variables)
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is not None
    assert collection_data["name"] == published_collection.name


def test_collection_query_unpublished_collection_by_id_as_app(
    app_api_client, unpublished_collection, permission_manage_products, channel_USD
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Collection", unpublished_collection.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_COLLECTION,
        variables=variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is not None
    assert collection_data["name"] == unpublished_collection.name


def test_collection_query_by_slug(user_api_client, published_collection, channel_USD):
    variables = {
        "slug": published_collection.slug,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_COLLECTION, variables=variables)
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is not None
    assert collection_data["name"] == published_collection.name


def test_collection_query_by_translated_slug(
    user_api_client, published_collection, collection_translation_fr, channel_USD
):
    variables = {
        "slug": collection_translation_fr.slug,
        "channel": channel_USD.slug,
        "slugLanguageCode": LanguageCodeEnum.FR.name,
    }
    response = user_api_client.post_graphql(QUERY_COLLECTION, variables=variables)
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is not None
    assert collection_data["name"] == published_collection.name


def test_collection_query_unpublished_collection_by_slug_as_staff(
    staff_api_client, unpublished_collection, permission_manage_products, channel_USD
):
    # given
    user = staff_api_client.user
    user.user_permissions.add(permission_manage_products)

    variables = {"slug": unpublished_collection.slug, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(QUERY_COLLECTION, variables=variables)

    # then
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is not None
    assert collection_data["name"] == unpublished_collection.name


def test_collection_query_unpublished_collection_by_slug_and_anonymous_user(
    api_client, unpublished_collection, channel_USD
):
    # given
    variables = {"slug": unpublished_collection.slug, "channel": channel_USD.slug}

    # when
    response = api_client.post_graphql(QUERY_COLLECTION, variables=variables)

    # then
    content = get_graphql_content(response)
    collection_data = content["data"]["collection"]
    assert collection_data is None


def test_collection_query_error_when_id_and_slug_provided(
    user_api_client,
    collection,
    graphql_log_handler,
):
    # given
    handled_errors_logger = logging.getLogger("saleor.graphql.errors.handled")
    handled_errors_logger.setLevel(logging.DEBUG)
    variables = {
        "id": graphene.Node.to_global_id("Collection", collection.pk),
        "slug": collection.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_COLLECTION, variables=variables)

    # then
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[DEBUG].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_collection_query_error_when_no_param(
    user_api_client,
    collection,
    graphql_log_handler,
):
    # given
    handled_errors_logger = logging.getLogger("saleor.graphql.errors.handled")
    handled_errors_logger.setLevel(logging.DEBUG)
    variables = {}

    # when
    response = user_api_client.post_graphql(QUERY_COLLECTION, variables=variables)

    # then
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[DEBUG].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


GET_FILTERED_PRODUCTS_COLLECTION_QUERY = """
query CollectionProducts(
    $id: ID!,
    $channel: String,
    $filters: ProductFilterInput,
    $where: ProductWhereInput,
    $search: String,
) {
  collection(id: $id, channel: $channel) {
    products(first: 10, filter: $filters, where: $where, search: $search) {
      edges {
        node {
          id
          attributes {
            attribute {
              choices(first: 10) {
                edges {
                  node {
                    slug
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


def test_filter_collection_products(
    user_api_client, product_list, published_collection, channel_USD, channel_PLN
):
    # given
    query = GET_FILTERED_PRODUCTS_COLLECTION_QUERY

    for product in product_list:
        published_collection.products.add(product)

    product = product_list[0]

    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "filters": {"search": product.name},
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["collection"]["products"]["edges"][0]["node"]

    assert product_data["id"] == graphene.Node.to_global_id("Product", product.pk)


def test_filter_collection_published_products(
    user_api_client, product_list, published_collection, channel_USD, channel_PLN
):
    # given
    query = GET_FILTERED_PRODUCTS_COLLECTION_QUERY

    for product in product_list:
        published_collection.products.add(product)

    product = product_list[0]
    listing = product.channel_listings.first()
    listing.is_published = False
    listing.save(update_fields=["is_published"])

    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "filters": {"isPublished": True},
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["collection"]["products"]["edges"]

    assert len(products) == len(product_list) - 1
    assert product_id not in {node["node"]["id"] for node in products}


def test_filter_collection_products_by_multiple_attributes(
    user_api_client,
    published_collection,
    product_with_two_variants,
    product_with_multiple_values_attributes,
    channel_USD,
):
    # given
    published_collection.products.set(
        [product_with_two_variants, product_with_multiple_values_attributes]
    )
    assert published_collection.products.count() == 2

    filters = {
        "attributes": [{"slug": "modes", "values": ["eco"]}],
    }
    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "filters": filters,
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(
        GET_FILTERED_PRODUCTS_COLLECTION_QUERY, variables
    )

    # then
    content = get_graphql_content(response)
    products_data = content["data"]["collection"]["products"]["edges"]
    product = products_data[0]["node"]

    _, _id = graphene.Node.from_global_id(product["id"])

    assert len(products_data) == 1
    assert product["id"] == graphene.Node.to_global_id(
        "Product", product_with_multiple_values_attributes.pk
    )
    assert product["attributes"] == [
        {
            "attribute": {
                "choices": {
                    "edges": [
                        {"node": {"slug": "eco"}},
                        {"node": {"slug": "power"}},
                    ]
                }
            }
        }
    ]


def test_filter_where_collection_products(
    user_api_client, product_list, published_collection, channel_USD, channel_PLN
):
    # given
    query = GET_FILTERED_PRODUCTS_COLLECTION_QUERY

    for product in product_list:
        published_collection.products.add(product)

    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "channel": channel_USD.slug,
        "where": {
            "AND": [
                {"slug": {"oneOf": ["test-product-a", "test-product-b"]}},
                {"price": {"range": {"gte": 15}}},
            ]
        },
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["collection"]["products"]["edges"]
    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_list[1].pk
    )


def test_search_collection_products(
    user_api_client, product_list, published_collection, channel_USD, channel_PLN
):
    # given
    query = GET_FILTERED_PRODUCTS_COLLECTION_QUERY

    for product in product_list:
        published_collection.products.add(product)

    product = product_list[0]

    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "search": product.name,
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["collection"]["products"]["edges"][0]["node"]

    assert product_data["id"] == graphene.Node.to_global_id("Product", product.pk)


FETCH_COLLECTION_IMAGE_QUERY = """
    query fetchCollection(
        $id: ID!, $channel: String,  $size: Int, $format: ThumbnailFormatEnum
    ){
        collection(id: $id, channel: $channel) {
            name
            backgroundImage(size: $size, format: $format) {
               url
               alt
            }
        }
    }
"""


def test_collection_image_query_with_size_and_format_proxy_url_returned(
    user_api_client, published_collection, media_root, channel_USD, site_settings
):
    # given
    alt_text = "Alt text for an image."
    collection = published_collection
    image_file, image_name = create_image()
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    collection.background_image = background_mock
    collection.background_image_alt = alt_text
    collection.save(update_fields=["background_image", "background_image_alt"])

    format = ThumbnailFormatEnum.WEBP.name

    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
        "size": 120,
        "format": format,
    }

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["collection"]
    assert data["backgroundImage"]["alt"] == alt_text
    domain = site_settings.site.domain
    expected_url = f"http://{domain}/thumbnail/{collection_id}/128/{format.lower()}/"
    assert data["backgroundImage"]["url"] == expected_url


def test_collection_image_query_with_size_proxy_url_returned(
    user_api_client, published_collection, media_root, channel_USD, site_settings
):
    # given
    alt_text = "Alt text for an image."
    collection = published_collection
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    collection.background_image = background_mock
    collection.background_image_alt = alt_text
    collection.save(update_fields=["background_image", "background_image_alt"])

    size = 128
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
        "size": size,
    }

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["collection"]
    assert data["backgroundImage"]["alt"] == alt_text
    assert (
        data["backgroundImage"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{collection_id}/{size}/"
    )


def test_collection_image_query_with_size_thumbnail_url_returned(
    user_api_client, published_collection, media_root, channel_USD, site_settings
):
    # given
    alt_text = "Alt text for an image."
    collection = published_collection
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    collection.background_image = background_mock
    collection.background_image_alt = alt_text
    collection.save(update_fields=["background_image", "background_image_alt"])

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(collection=collection, size=size, image=thumbnail_mock)

    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
        "size": 120,
    }

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["collection"]
    assert data["backgroundImage"]["alt"] == alt_text
    assert (
        data["backgroundImage"]["url"]
        == f"http://{site_settings.site.domain}/media/thumbnails/{thumbnail_mock.name}"
    )


def test_collection_image_query_zero_size_custom_format_provided(
    user_api_client, published_collection, media_root, channel_USD, site_settings
):
    # given
    alt_text = "Alt text for an image."
    collection = published_collection
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    collection.background_image = background_mock
    collection.background_image_alt = alt_text
    collection.save(update_fields=["background_image", "background_image_alt"])

    format = ThumbnailFormatEnum.WEBP.name

    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
        "format": format,
        "size": 0,
    }

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["collection"]
    assert data["backgroundImage"]["alt"] == alt_text
    expected_url = (
        f"http://{site_settings.site.domain}"
        f"/media/collection-backgrounds/{background_mock.name}"
    )
    assert data["backgroundImage"]["url"] == expected_url


def test_collection_image_query_zero_size_value_original_image_returned(
    user_api_client, published_collection, media_root, channel_USD, site_settings
):
    # given
    alt_text = "Alt text for an image."
    collection = published_collection
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    collection.background_image = background_mock
    collection.background_image_alt = alt_text
    collection.save(update_fields=["background_image", "background_image_alt"])

    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
        "size": 0,
    }

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["collection"]
    assert data["backgroundImage"]["alt"] == alt_text
    expected_url = (
        f"http://{site_settings.site.domain}"
        f"/media/collection-backgrounds/{background_mock.name}"
    )
    assert data["backgroundImage"]["url"] == expected_url


def test_collection_image_query_without_associated_file(
    user_api_client, published_collection, channel_USD
):
    # given
    collection = published_collection
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    variables = {"id": collection_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(FETCH_COLLECTION_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["collection"]
    assert data["name"] == collection.name
    assert data["backgroundImage"] is None


def test_collection_query_invalid_id(
    user_api_client, published_collection, channel_USD
):
    collection_id = "'"
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(FETCH_COLLECTION_IMAGE_QUERY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == f"Invalid ID: {collection_id}. Expected: Collection."
    )
    assert content["data"]["collection"] is None


def test_collection_query_object_with_given_id_does_not_exist(
    user_api_client, published_collection, channel_USD
):
    collection_id = graphene.Node.to_global_id("Collection", -1)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(FETCH_COLLECTION_IMAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["collection"] is None


def test_collection_query_object_with_invalid_object_type(
    user_api_client, published_collection, channel_USD
):
    collection_id = graphene.Node.to_global_id("Product", published_collection.pk)
    variables = {
        "id": collection_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(FETCH_COLLECTION_IMAGE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["collection"] is None


def _fetch_collection(client, collection, channel_slug, permissions=None):
    query = """
    query fetchCollection($id: ID!, $channel: String){
        collection(id: $id, channel: $channel) {
            name,
            channelListings {
                isPublished
            }
        }
    }
    """
    variables = {
        "id": graphene.Node.to_global_id("Collection", collection.id),
        "channel": channel_slug,
    }
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False
    )
    content = get_graphql_content(response)
    return content["data"]["collection"]


def test_fetch_unpublished_collection_staff_user(
    staff_api_client, unpublished_collection, permission_manage_products, channel_USD
):
    collection_data = _fetch_collection(
        staff_api_client,
        unpublished_collection,
        channel_USD.slug,
        permissions=[permission_manage_products],
    )
    assert collection_data["name"] == unpublished_collection.name
    assert collection_data["channelListings"][0]["isPublished"] is False


def test_fetch_unpublished_collection_customer(
    user_api_client, unpublished_collection, channel_USD
):
    collection_data = _fetch_collection(
        user_api_client, unpublished_collection, channel_USD.slug
    )
    assert collection_data is None


def test_fetch_unpublished_collection_anonymous_user(
    api_client, unpublished_collection, channel_USD
):
    collection_data = _fetch_collection(
        api_client, unpublished_collection, channel_USD.slug
    )
    assert collection_data is None
