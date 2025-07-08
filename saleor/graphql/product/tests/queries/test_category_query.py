import logging
from unittest.mock import MagicMock

import graphene
from django.core.files import File

from .....product.models import Category, Product
from .....product.utils.costs import get_product_costs_data
from .....tests.utils import dummy_editorjs
from .....thumbnail.models import Thumbnail
from ....core.enums import LanguageCodeEnum, ThumbnailFormatEnum
from ....tests.utils import (
    get_graphql_content,
    get_graphql_content_from_response,
)

QUERY_CATEGORY = """
    query ($id: ID, $slug: String, $channel: String, $slugLanguageCode: LanguageCodeEnum){
        category(
            id: $id,
            slug: $slug,
            slugLanguageCode: $slugLanguageCode
        ) {
            id
            name
            ancestors(first: 20) {
                edges {
                    node {
                        name
                    }
                }
            }
            children(first: 20) {
                edges {
                    node {
                        name
                    }
                }
            }
            products(first: 10, channel: $channel) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
"""


def test_category_query_by_id(user_api_client, product, channel_USD):
    category = Category.objects.first()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data is not None
    assert category_data["name"] == category.name
    assert len(category_data["ancestors"]["edges"]) == category.get_ancestors().count()
    assert len(category_data["children"]["edges"]) == category.get_children().count()


def test_category_query_with_ancestors(user_api_client, product, channel_USD):
    # given
    category = Category.objects.first()
    child = Category.objects.create(
        name="Child Category", slug="child-category", parent=category
    )

    # when
    variables = {
        "id": graphene.Node.to_global_id("Category", child.pk),
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]

    # then
    assert category_data is not None
    assert len(category_data["ancestors"]["edges"]) == child.get_ancestors().count()
    assert len(category_data["children"]["edges"]) == child.get_children().count()


def test_category_query_invalid_id(user_api_client, product, channel_USD):
    category_id = "'"
    variables = {
        "id": category_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == f"Invalid ID: {category_id}. Expected: Category."
    )
    assert content["data"]["category"] is None


def test_category_query_object_with_given_id_does_not_exist(
    user_api_client, product, channel_USD
):
    category_id = graphene.Node.to_global_id("Category", -1)
    variables = {
        "id": category_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables)
    content = get_graphql_content(response)
    assert content["data"]["category"] is None


def test_category_query_object_with_invalid_object_type(
    user_api_client, product, channel_USD
):
    category = Category.objects.first()
    category_id = graphene.Node.to_global_id("Product", category.pk)
    variables = {
        "id": category_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables)
    content = get_graphql_content(response)
    assert content["data"]["category"] is None


def test_category_query_doesnt_show_not_available_products(
    user_api_client, product, channel_USD
):
    category = Category.objects.first()
    variant = product.variants.get()
    # Set product as not visible due to lack of price.
    variant.channel_listings.update(price_amount=None)

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data is not None
    assert category_data["name"] == category.name
    assert not category_data["products"]["edges"]


def test_category_query_description(user_api_client, product, channel_USD):
    category = Category.objects.first()
    description = dummy_editorjs("Test description.", json_format=True)
    category.description = dummy_editorjs("Test description.")
    category.save()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }
    query = """
    query ($id: ID, $slug: String){
        category(
            id: $id,
            slug: $slug,
        ) {
            id
            name
            description
            descriptionJson
        }
    }
    """
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data["description"] == description
    assert category_data["descriptionJson"] == description


def test_category_query_without_description(user_api_client, product, channel_USD):
    category = Category.objects.first()
    category.save()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }
    query = """
    query ($id: ID, $slug: String){
        category(
            id: $id,
            slug: $slug,
        ) {
            id
            name
            description
            descriptionJson
        }
    }
    """
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data["description"] is None
    assert category_data["descriptionJson"] == "{}"


def test_category_query_by_slug(user_api_client, product, channel_USD):
    category = Category.objects.first()
    variables = {"slug": category.slug, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data is not None
    assert category_data["name"] == category.name
    assert len(category_data["ancestors"]["edges"]) == category.get_ancestors().count()
    assert len(category_data["children"]["edges"]) == category.get_children().count()


def test_category_query_by_translated_slug(
    user_api_client, category, category_translation_with_slug_pl, channel_USD
):
    variables = {
        "slug": category_translation_with_slug_pl.slug,
        "channel": channel_USD.slug,
        "slugLanguageCode": LanguageCodeEnum.PL.name,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    content = get_graphql_content(response)
    data = content["data"]["category"]
    assert data is not None
    assert data["name"] == category.name


def test_category_query_error_when_id_and_slug_provided(
    user_api_client, product, graphql_log_handler, channel_USD
):
    # given
    handled_errors_logger = logging.getLogger("saleor.graphql.errors.handled")
    handled_errors_logger.setLevel(logging.DEBUG)
    category = Category.objects.first()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "slug": category.slug,
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[DEBUG].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_category_query_error_when_no_param(
    user_api_client, product, graphql_log_handler
):
    # given
    handled_errors_logger = logging.getLogger("saleor.graphql.errors.handled")
    handled_errors_logger.setLevel(logging.DEBUG)
    variables = {}

    # when
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[DEBUG].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_query_category_product_only_visible_in_listings_as_customer(
    user_api_client, product_list, channel_USD
):
    # given
    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["data"]["category"]["products"]["edges"]) == product_count - 1


def test_query_category_product_visible_in_listings_as_staff_without_manage_products(
    staff_api_client, product_list, channel_USD
):
    # given
    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert (
        len(content["data"]["category"]["products"]["edges"]) == product_count - 1
    )  # invisible doesn't count


def test_query_category_product_only_visible_in_listings_as_staff_with_perm(
    staff_api_client, product_list, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = staff_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["data"]["category"]["products"]["edges"]) == product_count


def test_query_category_product_only_visible_in_listings_as_app_without_manage_products(
    app_api_client, product_list, channel_USD
):
    # given
    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert (
        len(content["data"]["category"]["products"]["edges"]) == product_count - 1
    )  # invisible doesn't count


def test_query_category_product_only_visible_in_listings_as_app_with_perm(
    app_api_client, product_list, permission_manage_products
):
    # given
    app_api_client.app.permissions.add(permission_manage_products)

    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = app_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["data"]["category"]["products"]["edges"]) == product_count


FETCH_CATEGORY_IMAGE_QUERY = """
    query fetchCategory($id: ID!, $size: Int, $format: ThumbnailFormatEnum){
        category(id: $id) {
            name
            backgroundImage(size: $size, format: $format) {
                url
                alt
            }
        }
    }
    """


def test_category_image_query_with_size_and_format_proxy_url_returned(
    user_api_client, non_default_category, media_root, site_settings
):
    # given
    alt_text = "Alt text for an image."
    category = non_default_category
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    format = ThumbnailFormatEnum.WEBP.name

    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "size": 120,
        "format": format,
    }

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["category"]
    assert data["backgroundImage"]["alt"] == alt_text
    domain = site_settings.site.domain
    assert (
        data["backgroundImage"]["url"]
        == f"http://{domain}/thumbnail/{category_id}/128/{format.lower()}/"
    )


def test_category_image_query_with_size_proxy_url_returned(
    user_api_client, non_default_category, media_root, site_settings
):
    # given
    alt_text = "Alt text for an image."
    category = non_default_category
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    size = 128
    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "size": size,
    }

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["category"]
    assert data["backgroundImage"]["alt"] == alt_text
    assert (
        data["backgroundImage"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{category_id}/{size}/"
    )


def test_category_image_query_with_size_thumbnail_url_returned(
    user_api_client, non_default_category, media_root, site_settings
):
    # given
    alt_text = "Alt text for an image."
    category = non_default_category
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(category=category, size=size, image=thumbnail_mock)

    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "size": 120,
    }

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["category"]
    assert data["backgroundImage"]["alt"] == alt_text
    assert (
        data["backgroundImage"]["url"]
        == f"http://{site_settings.site.domain}/media/thumbnails/{thumbnail_mock.name}"
    )


def test_category_image_query_zero_size_custom_format_provided_original_image_returned(
    user_api_client, non_default_category, media_root, site_settings
):
    # given
    alt_text = "Alt text for an image."
    category = non_default_category
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    format = ThumbnailFormatEnum.WEBP.name

    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "format": format,
        "size": 0,
    }

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["category"]
    assert data["backgroundImage"]["alt"] == alt_text
    domain = site_settings.site.domain
    expected_url = f"http://{domain}/media/category-backgrounds/{background_mock.name}"
    assert data["backgroundImage"]["url"] == expected_url


def test_category_image_query_zero_size_value_original_image_returned(
    user_api_client, non_default_category, media_root, site_settings
):
    # given
    alt_text = "Alt text for an image."
    category = non_default_category
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "size": 0,
    }

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["category"]
    assert data["backgroundImage"]["alt"] == alt_text
    domain = site_settings.site.domain
    expected_url = f"http://{domain}/media/category-backgrounds/{background_mock.name}"
    assert data["backgroundImage"]["url"] == expected_url


def test_category_image_query_without_associated_file(
    user_api_client, non_default_category
):
    # given
    category = non_default_category
    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {"id": category_id}

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_IMAGE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["category"]
    assert data["name"] == category.name
    assert data["backgroundImage"] is None


def test_query_category_for_federation(api_client, non_default_category):
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    variables = {
        "representations": [
            {
                "__typename": "Category",
                "id": category_id,
            },
        ],
    }
    query = """
      query GetCategoryInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on Category {
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
            "__typename": "Category",
            "id": category_id,
            "name": non_default_category.name,
        }
    ]


def test_query_products_no_channel_shipping_zones(
    staff_api_client, product, permission_manage_products, stock, channel_USD
):
    channel_USD.shipping_zones.clear()
    category = Category.objects.first()
    product = category.products.first()
    query = """
    query CategoryProducts($id: ID, $channel: String, $address: AddressInput) {
        category(id: $id) {
            products(first: 20, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        isAvailable(address: $address)
                    }
                }
            }
        }
    }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Category", category.id),
        "channel": channel_USD.slug,
        "address": {"country": "US"},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["category"] is not None
    product_edges_data = content["data"]["category"]["products"]["edges"]
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]["node"]
    assert product_data["name"] == product.name
    assert product_data["isAvailable"] is False


def test_fetch_product_from_category_query(
    staff_api_client, product, permission_manage_products, stock, channel_USD
):
    category = Category.objects.first()
    product = category.products.first()
    query = """
    query CategoryProducts($id: ID, $channel: String, $address: AddressInput) {
        category(id: $id) {
            products(first: 20, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        slug
                        thumbnail{
                            url
                            alt
                        }
                        media {
                            url
                        }
                        variants {
                            name
                            channelListings {
                                costPrice {
                                    amount
                                }
                            }
                        }
                        channelListings {
                            purchaseCost {
                                start {
                                    amount
                                }
                                stop {
                                    amount
                                }
                            }
                            margin {
                                start
                                stop
                            }
                        }
                        isAvailable(address: $address)
                        pricing(address: $address) {
                            priceRange {
                                start {
                                    gross {
                                        amount
                                        currency
                                    }
                                    net {
                                        amount
                                        currency
                                    }
                                    currency
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Category", category.id),
        "channel": channel_USD.slug,
        "address": {"country": "US"},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["category"] is not None
    product_edges_data = content["data"]["category"]["products"]["edges"]
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]["node"]
    assert product_data["name"] == product.name
    assert product_data["slug"] == product.slug

    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.filter(channel_id=channel_USD.id)
    purchase_cost, margin = get_product_costs_data(
        variant_channel_listing, True, channel_USD.currency_code
    )
    cost_start = product_data["channelListings"][0]["purchaseCost"]["start"]["amount"]
    cost_stop = product_data["channelListings"][0]["purchaseCost"]["stop"]["amount"]

    assert purchase_cost.start.amount == cost_start
    assert purchase_cost.stop.amount == cost_stop
    assert product_data["isAvailable"] is True
    assert margin[0] == product_data["channelListings"][0]["margin"]["start"]
    assert margin[1] == product_data["channelListings"][0]["margin"]["stop"]

    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    variant_channel_data = product_data["variants"][0]["channelListings"][0]
    variant_cost = variant_channel_data["costPrice"]["amount"]

    assert variant_channel_listing.cost_price.amount == variant_cost
