from datetime import timedelta
from unittest.mock import MagicMock

import graphene
import pytest
from django.contrib.sites.models import Site
from django.core.files import File
from django.utils import timezone
from measurement.measures import Weight

from .....attribute.models import AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....core.units import WeightUnits
from .....product.models import (
    Product,
    ProductChannelListing,
    ProductVariantChannelListing,
)
from .....tests.utils import dummy_editorjs
from .....thumbnail.models import Thumbnail
from .....warehouse.models import Allocation, Stock
from ....core.enums import ThumbnailFormatEnum
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

QUERY_PRODUCT = """
    query ($id: ID, $slug: String, $channel:String){
        product(
            id: $id,
            slug: $slug,
            channel: $channel
        ) {
            id
            name
            weight {
                unit
                value
            }
            availableForPurchase
            availableForPurchaseAt
            isAvailableForPurchase
            isAvailable
        }
    }
"""


def test_product_query_by_id_available_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_description(
    staff_api_client, permission_manage_products, product, channel_USD
):
    query = """
        query ($id: ID, $slug: String, $channel:String){
            product(
                id: $id,
                slug: $slug,
                channel: $channel
            ) {
                id
                name
                description
                descriptionJson
            }
        }
        """
    description = dummy_editorjs("Test description.", json_format=True)
    product.description = dummy_editorjs("Test description.")
    product.save()
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["description"] == description
    assert product_data["descriptionJson"] == description


def test_product_query_with_no_description(
    staff_api_client, permission_manage_products, product, channel_USD
):
    query = """
        query ($id: ID, $slug: String, $channel:String){
            product(
                id: $id,
                slug: $slug,
                channel: $channel
            ) {
                id
                name
                description
                descriptionJson
            }
        }
        """
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["description"] is None
    assert product_data["descriptionJson"] == "{}"


def test_product_query_by_id_not_available_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_id_not_existing_in_channel_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is None


def test_product_query_by_id_as_staff_user_without_channel_slug(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_id_available_as_app(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    response = app_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


@pytest.mark.parametrize("id", ["'", "abc"])
def test_product_query_by_invalid_id(
    id, staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "id": id,
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content_from_response(response)
    assert "errors" in content
    assert content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: Product."


QUERY_PRODUCT_BY_ID = """
    query ($id: ID, $channel: String){
        product(id: $id, channel: $channel) {
            id
            variants {
                id
            }
        }
    }
"""


def test_product_query_by_id_as_user(
    user_api_client, permission_manage_products, product, channel_USD
):
    query = QUERY_PRODUCT_BY_ID
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(
        query,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    expected_variants = [
        {
            "id": graphene.Node.to_global_id(
                "ProductVariant", product.variants.first().pk
            )
        }
    ]
    assert product_data["variants"] == expected_variants


def test_product_query_invalid_id(user_api_client, product, channel_USD):
    product_id = "'"
    variables = {
        "id": product_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_BY_ID, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == f"Invalid ID: {product_id}. Expected: Product."
    )
    assert content["data"]["product"] is None


def test_product_query_object_with_given_id_does_not_exist(
    user_api_client, product, channel_USD
):
    product_id = graphene.Node.to_global_id("Product", -1)
    variables = {
        "id": product_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_BY_ID, variables)
    content = get_graphql_content(response)
    assert content["data"]["product"] is None


def test_product_query_with_invalid_object_type(user_api_client, product, channel_USD):
    product_id = graphene.Node.to_global_id("Collection", product.pk)
    variables = {
        "id": product_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_BY_ID, variables)
    content = get_graphql_content(response)
    assert content["data"]["product"] is None


def test_product_query_by_id_not_available_as_app(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = app_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_id_not_existing_in_channel_as_app(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = app_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is None


def test_product_query_by_id_as_app_without_channel_slug(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = app_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_variants_without_sku_query_by_staff(
    staff_api_client, product, channel_USD
):
    product.variants.update(sku=None)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    variables = {
        "id": product_id,
        "channel": channel_USD.slug,
    }

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_BY_ID,
        variables=variables,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]

    assert product_data is not None
    assert product_data["id"] == product_id

    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert product_data["variants"] == [{"id": variant_id}]


def test_product_only_with_variants_without_sku_query_by_customer(
    user_api_client, product, channel_USD
):
    product.variants.update(sku=None)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    variables = {
        "id": product_id,
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(
        QUERY_PRODUCT_BY_ID,
        variables=variables,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]

    assert product_data is not None
    assert product_data["id"] == product_id

    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert product_data["variants"] == [{"id": variant_id}]


def test_product_only_with_variants_without_sku_query_by_anonymous(
    api_client, product, channel_USD
):
    product.variants.update(sku=None)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    variables = {
        "id": product_id,
        "channel": channel_USD.slug,
    }

    response = api_client.post_graphql(
        QUERY_PRODUCT_BY_ID,
        variables=variables,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]

    assert product_data is not None
    assert product_data["id"] == product_id

    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert product_data["variants"] == [{"id": variant_id}]


QUERY_PRODUCT_BY_ID_WITH_MEDIA = """
    query ($id: ID, $channel: String, $size: Int, $format: ThumbnailFormatEnum){
        product(id: $id, channel: $channel) {
            media {
                id
            }
            thumbnail(size: $size, format: $format) {
                url
                alt
            }
            variants {
                id
                name
                media {
                    id
                }
            }
        }
    }
"""


def test_query_product_thumbnail_with_size_and_format_proxy_url_returned(
    staff_api_client, product_with_image, channel_USD, site_settings
):
    # given
    format = ThumbnailFormatEnum.WEBP.name

    id = graphene.Node.to_global_id("Product", product_with_image.pk)
    variables = {
        "id": id,
        "size": 120,
        "format": format,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_PRODUCT_BY_ID_WITH_MEDIA, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["product"]
    product_media_id = graphene.Node.to_global_id(
        "ProductMedia", product_with_image.media.first().pk
    )
    expected_url = (
        f"http://{site_settings.site.domain}"
        f"/thumbnail/{product_media_id}/128/{format.lower()}/"
    )
    assert data["thumbnail"]["url"] == expected_url


def test_query_product_thumbnail_with_size_and_proxy_url_returned(
    staff_api_client, product_with_image, channel_USD, site_settings
):
    # given
    id = graphene.Node.to_global_id("Product", product_with_image.pk)
    variables = {
        "id": id,
        "size": 120,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_PRODUCT_BY_ID_WITH_MEDIA, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["product"]
    product_media_id = graphene.Node.to_global_id(
        "ProductMedia", product_with_image.media.first().pk
    )
    assert (
        data["thumbnail"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{product_media_id}/128/"
    )


def test_query_product_thumbnail_with_size_and_thumbnail_url_returned(
    staff_api_client, product_with_image, channel_USD, site_settings
):
    # given
    product_media = product_with_image.media.first()

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(
        product_media=product_media, size=128, image=thumbnail_mock
    )

    id = graphene.Node.to_global_id("Product", product_with_image.pk)
    variables = {
        "id": id,
        "size": 120,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_PRODUCT_BY_ID_WITH_MEDIA, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["product"]
    assert (
        data["thumbnail"]["url"]
        == f"http://{site_settings.site.domain}/media/thumbnails/{thumbnail_mock.name}"
    )


def test_query_product_thumbnail_only_format_provided_default_size_is_used(
    staff_api_client, product_with_image, channel_USD, site_settings
):
    # given
    format = ThumbnailFormatEnum.WEBP.name

    id = graphene.Node.to_global_id("Product", product_with_image.pk)
    variables = {
        "id": id,
        "format": format,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_PRODUCT_BY_ID_WITH_MEDIA, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["product"]
    product_media_id = graphene.Node.to_global_id(
        "ProductMedia", product_with_image.media.first().pk
    )
    expected_url = (
        f"http://{site_settings.site.domain}"
        f"/thumbnail/{product_media_id}/256/{format.lower()}/"
    )
    assert data["thumbnail"]["url"] == expected_url


def test_query_product_thumbnail_no_product_media(
    staff_api_client, product, channel_USD
):
    # given
    id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "id": id,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_PRODUCT_BY_ID_WITH_MEDIA, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["product"]
    assert not data["thumbnail"]


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


def test_get_collections_from_product_as_staff(
    staff_api_client,
    permission_manage_products,
    product_with_collections,
    channel_USD,
):
    # given
    product = product_with_collections
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_COLLECTION_FROM_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collections = content["data"]["product"]["collections"]
    assert len(collections) == 3
    for collection in product.collections.all():
        assert {"name": collection.name} in collections


def test_get_collections_from_product_as_app(
    app_api_client,
    permission_manage_products,
    product_with_collections,
    channel_USD,
):
    # given
    product = product_with_collections
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_COLLECTION_FROM_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    collections = content["data"]["product"]["collections"]
    assert len(collections) == 3
    for collection in product.collections.all():
        assert {"name": collection.name} in collections


def test_get_collections_from_product_as_customer(
    user_api_client, product_with_collections, channel_USD, published_collection
):
    # given
    product = product_with_collections
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
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


def test_get_collections_from_product_as_anonymous(
    api_client, product_with_collections, channel_USD, published_collection
):
    # given
    product = product_with_collections
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
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


def test_product_query_by_id_available_as_customer(
    user_api_client, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_id_not_available_as_customer(
    user_api_client, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is None


def test_product_unpublished_query_by_id_as_app(
    app_api_client, unavailable_product, permission_manage_products, channel_USD
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Product", unavailable_product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == unavailable_product.name


def test_product_query_by_id_weight_returned_in_default_unit(
    user_api_client, product, site_settings, channel_USD
):
    # given
    product.weight = Weight(kg=10)
    product.save(update_fields=["weight"])

    site_settings.default_weight_unit = WeightUnits.LB
    site_settings.save(update_fields=["default_weight_unit"])
    Site.objects.clear_cache()

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name
    assert product_data["weight"]["value"] == 22.046
    assert product_data["weight"]["unit"] == WeightUnits.LB.upper()


def test_product_query_by_id_weight_is_rounded(
    user_api_client, product, site_settings, channel_USD
):
    # given
    product.weight = Weight(kg=1.83456)
    product.save(update_fields=["weight"])

    site_settings.default_weight_unit = WeightUnits.KG
    site_settings.save(update_fields=["default_weight_unit"])

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name
    assert product_data["weight"]["value"] == 1.835
    assert product_data["weight"]["unit"] == WeightUnits.KG.upper()


def test_product_query_by_slug(user_api_client, product, channel_USD):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is None


def test_product_query_by_id_not_existing_in_channel_as_customer(
    user_api_client, product, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is None


def test_product_query_by_slug_available_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_slug_not_available_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_slug_not_existing_in_channel_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is None


def test_product_query_by_slug_as_staff_user_without_channel(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "slug": product.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_slug_available_as_app(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }

    response = app_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_slug_not_available_as_app(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = app_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_slug_not_existing_in_channel_as_app(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = app_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is None


def test_product_query_by_slug_as_app_without_channel(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {
        "slug": product.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = app_api_client.post_graphql(
        QUERY_PRODUCT,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_slug_available_as_customer(
    user_api_client, product, channel_USD
):
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_by_slug_not_available_as_customer(
    user_api_client, product, channel_USD
):
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is None


def test_product_query_is_available_for_purchase_true(
    user_api_client, product, channel_USD
):
    # given
    available_for_purchase = timezone.now() - timedelta(days=1)
    product.channel_listings.update(available_for_purchase_at=available_for_purchase)

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]

    assert product_data["availableForPurchase"] == available_for_purchase.strftime(
        "%Y-%m-%d"
    )
    assert product_data["availableForPurchaseAt"] == available_for_purchase.isoformat()
    assert product_data["isAvailableForPurchase"] is True


def test_product_query_is_available_for_purchase_false(
    user_api_client, product, channel_USD
):
    # given
    available_for_purchase = timezone.now() + timedelta(days=1)
    product.channel_listings.update(available_for_purchase_at=available_for_purchase)

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]

    assert product_data["availableForPurchase"] == available_for_purchase.strftime(
        "%Y-%m-%d"
    )
    assert product_data["availableForPurchaseAt"] == available_for_purchase.isoformat()
    assert product_data["isAvailableForPurchase"] is False
    assert product_data["isAvailable"] is False


def test_product_query_is_available_for_purchase_false_no_available_for_purchase_date(
    user_api_client, product, channel_USD
):
    # given
    product.channel_listings.update(available_for_purchase_at=None)

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]

    assert not product_data["availableForPurchase"]
    assert not product_data["availableForPurchaseAt"]
    assert product_data["isAvailableForPurchase"] is False
    assert product_data["isAvailable"] is False


def test_product_query_unpublished_products_by_slug(
    staff_api_client, product, permission_manage_products, channel_USD
):
    # given
    user = staff_api_client.user
    user.user_permissions.add(permission_manage_products)

    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_PRODUCT, variables=variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_unpublished_products_by_slug_and_anonymous_user(
    api_client, product, channel_USD
):
    # given
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_PRODUCT, variables=variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is None


def test_product_query_by_slug_not_existing_in_channel_as_customer(
    user_api_client, product, channel_USD
):
    variables = {
        "slug": product.slug,
        "channel": channel_USD.slug,
    }
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is None


QUERY_PRODUCT_WITHOUT_CHANNEL = """
    query ($id: ID){
        product(
            id: $id
        ) {
            id
            name
        }
    }
    """


def test_product_query_by_id_without_channel_not_available_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITHOUT_CHANNEL,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name


def test_product_query_error_when_id_and_slug_provided(
    user_api_client,
    product,
    graphql_log_handler,
):
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "slug": product.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_product_query_error_when_no_param(
    user_api_client,
    product,
    graphql_log_handler,
):
    variables = {}
    response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


QUERY_PRODUCT_IS_AVAILABLE = """
    query Product($id: ID, $channel: String, $address: AddressInput) {
        product(id: $id, channel: $channel) {
            isAvailableNoAddress: isAvailable
            isAvailableAddress: isAvailable(address: $address)
        }
    }
"""


def test_query_product_is_available(
    api_client, channel_USD, variant_with_many_stocks_different_shipping_zones
):
    # given
    variant = variant_with_many_stocks_different_shipping_zones
    product = variant.product
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_USD.slug,
        "address": {"country": "PL"},
    }

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_IS_AVAILABLE, variables)
    content = get_graphql_content(response)

    # then
    product_data = content["data"]["product"]
    assert product_data["isAvailableNoAddress"] is True
    assert product_data["isAvailableAddress"] is True


def test_query_product_is_available_with_one_variant(
    api_client, channel_USD, product_with_two_variants
):
    # given
    product = product_with_two_variants

    # remove stock for 2nd variant
    variant_2 = product.variants.all()[1]
    Stock.objects.filter(product_variant=variant_2).delete()

    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_USD.slug,
        "address": {"country": "PL"},
    }

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_IS_AVAILABLE, variables)
    content = get_graphql_content(response)

    # then
    product_data = content["data"]["product"]
    assert product_data["isAvailableNoAddress"] is True
    assert product_data["isAvailableAddress"] is True


def test_query_product_is_available_no_shipping_zones(
    api_client, channel_USD, variant_with_many_stocks_different_shipping_zones
):
    # given
    channel_USD.shipping_zones.clear()
    variant = variant_with_many_stocks_different_shipping_zones
    product = variant.product
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_USD.slug,
        "address": {"country": "PL"},
    }

    # when
    response = api_client.post_graphql(QUERY_PRODUCT_IS_AVAILABLE, variables)
    content = get_graphql_content(response)

    # then
    product_data = content["data"]["product"]
    assert product_data["isAvailableNoAddress"] is False
    assert product_data["isAvailableAddress"] is False


def test_product_restricted_fields_permissions(
    staff_api_client,
    permission_manage_products,
    permission_manage_orders,
    product,
    channel_USD,
):
    query = """
    query Product($id: ID!, $channel: String) {
        product(id: $id, channel: $channel) {
            privateMetadata { __typename}
        }
    }
    """
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "channel": channel_USD.slug,
    }
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert "privateMetadata" in content["data"]["product"]


QUERY_GET_PRODUCT_VARIANTS_PRICING = """
    query getProductVariants($id: ID!, $channel: String, $address: AddressInput) {
        product(id: $id, channel: $channel) {
            variants {
                id
                pricingNoAddress: pricing {
                    priceUndiscounted {
                        gross {
                            amount
                        }
                    }
                }
                pricing(address: $address) {
                    priceUndiscounted {
                        gross {
                            amount
                        }
                    }
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("variant_price_amount", "api_variant_price"),
    [(200, 200), (0, 0)],
)
def test_product_variant_price(
    variant_price_amount,
    api_variant_price,
    user_api_client,
    variant,
    stock,
    channel_USD,
):
    product = variant.product
    ProductVariantChannelListing.objects.filter(
        channel=channel_USD, variant__product_id=product.pk
    ).update(price_amount=variant_price_amount)

    product_id = graphene.Node.to_global_id("Product", variant.product.id)
    variables = {
        "id": product_id,
        "channel": channel_USD.slug,
        "address": {"country": "US"},
    }
    response = user_api_client.post_graphql(
        QUERY_GET_PRODUCT_VARIANTS_PRICING, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["product"]
    variant_price = data["variants"][0]["pricing"]["priceUndiscounted"]["gross"]
    assert variant_price["amount"] == api_variant_price


def test_product_variant_without_price_as_user(
    user_api_client,
    variant,
    stock,
    channel_USD,
):
    variant.channel_listings.filter(channel=channel_USD).update(price_amount=None)
    product_id = graphene.Node.to_global_id("Product", variant.product.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "id": product_id,
        "channel": channel_USD.slug,
        "address": {"country": "US"},
    }

    response = user_api_client.post_graphql(
        QUERY_GET_PRODUCT_VARIANTS_PRICING, variables
    )
    content = get_graphql_content(response)

    variants_data = content["data"]["product"]["variants"]
    assert not variants_data[0]["id"] == variant_id
    assert len(variants_data) == 1


def test_product_variant_without_price_as_staff_without_permission(
    staff_api_client,
    variant,
    stock,
    channel_USD,
):
    variant_channel_listing = variant.channel_listings.first()
    variant_channel_listing.price_amount = None
    variant_channel_listing.save()

    product_id = graphene.Node.to_global_id("Product", variant.product.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "id": product_id,
        "channel": channel_USD.slug,
        "address": {"country": "US"},
    }
    response = staff_api_client.post_graphql(
        QUERY_GET_PRODUCT_VARIANTS_PRICING, variables
    )
    content = get_graphql_content(response)
    variants_data = content["data"]["product"]["variants"]

    assert len(variants_data) == 1

    assert variants_data[0]["pricing"] is not None
    assert variants_data[0]["id"] != variant_id


def test_product_variant_without_price_as_staff_with_permission(
    staff_api_client, variant, stock, channel_USD, permission_manage_products
):
    variant_channel_listing = variant.channel_listings.first()
    variant_channel_listing.price_amount = None
    variant_channel_listing.save()

    product_id = graphene.Node.to_global_id("Product", variant.product.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "id": product_id,
        "channel": channel_USD.slug,
        "address": {"country": "US"},
    }
    response = staff_api_client.post_graphql(
        QUERY_GET_PRODUCT_VARIANTS_PRICING,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    variants_data = content["data"]["product"]["variants"]

    assert len(variants_data) == 2

    assert variants_data[0]["pricing"] is not None
    assert variants_data[1]["id"] == variant_id
    assert variants_data[1]["pricing"] is None


def test_get_product_with_sorted_attribute_values(
    staff_api_client,
    product,
    permission_manage_products,
    product_type_page_reference_attribute,
    page_list,
):
    # given
    query = """
        query getProduct($productID: ID!) {
            product(id: $productID) {
                attributes {
                    attribute {
                        name
                    }
                    values {
                        id
                        slug
                        reference
                    }
                }
            }
        }
        """
    product_type = product.product_type
    product_type.product_attributes.set([product_type_page_reference_attribute])

    attr_value_1 = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page_list[0].title,
        slug=f"{product.pk}_{page_list[0].pk}",
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page_list[1].title,
        slug=f"{product.pk}_{page_list[1].pk}",
    )

    associate_attribute_values_to_instance(
        product,
        {product_type_page_reference_attribute.pk: [attr_value_2, attr_value_1]},
    )

    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"productID": product_id}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["product"]
    assert len(data["attributes"]) == 1
    values = data["attributes"][0]["values"]
    assert len(values) == 2
    assert [value["id"] for value in values] == [
        graphene.Node.to_global_id("AttributeValue", val.pk)
        for val in [attr_value_2, attr_value_1]
    ]


QUERY_PRODUCT_IMAGE_BY_ID = """
    query productImageById($imageId: ID!, $productId: ID!, $channel: String) {
        product(id: $productId, channel: $channel) {
            imageById(id: $imageId) {
                id
                url
            }
        }
    }
"""


def test_query_product_image_by_id(user_api_client, product_with_image, channel_USD):
    query = QUERY_PRODUCT_IMAGE_BY_ID
    media = product_with_image.media.first()
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "imageId": graphene.Node.to_global_id("ProductImage", media.pk),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["imageById"]["id"]
    assert content["data"]["product"]["imageById"]["url"]


def test_query_product_image_by_id_missing_id(
    user_api_client, product_with_image, channel_USD
):
    query = QUERY_PRODUCT_IMAGE_BY_ID
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "imageId": graphene.Node.to_global_id("ProductMedia", -1),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["imageById"] is None


def test_query_product_image_by_id_not_media_id(
    user_api_client, product_with_image, channel_USD
):
    query = QUERY_PRODUCT_IMAGE_BY_ID
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "imageId": graphene.Node.to_global_id("Product", -1),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["imageById"] is None


def test_query_product_image_by_invalid_id(
    user_api_client, product_with_image, channel_USD
):
    query = QUERY_PRODUCT_IMAGE_BY_ID
    id = "mnb"
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "imageId": id,
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: ProductImage."
    )
    assert content["data"]["product"]["imageById"] is None


def test_product_with_collections(
    staff_api_client, product, published_collection, permission_manage_products
):
    query = """
        query getProduct($productID: ID!) {
            product(id: $productID) {
                collections {
                    name
                }
            }
        }
        """
    product.collections.add(published_collection)
    product.save()
    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {"productID": product_id}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["product"]
    assert data["collections"][0]["name"] == published_collection.name
    assert len(data["collections"]) == 1


QUERY_PRODUCT_MEDIA_BY_ID = """
    query productMediaById(
        $mediaId: ID!,
        $productId: ID!,
        $channel: String,
        $size: Int,
        $format: ThumbnailFormatEnum,
    ) {
        product(id: $productId, channel: $channel) {
            mediaById(id: $mediaId) {
                id
                url(size: $size, format: $format)
            }
        }
    }
"""


def test_query_product_media_by_id(user_api_client, product_with_image, channel_USD):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    media = product_with_image.media.first()
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": graphene.Node.to_global_id("ProductMedia", media.pk),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["mediaById"]["id"]
    assert content["data"]["product"]["mediaById"]["url"]


def test_query_product_media_by_id_missing_id(
    user_api_client, product_with_image, channel_USD
):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": graphene.Node.to_global_id("ProductMedia", -1),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["product"]["mediaById"] is None


def test_query_product_media_by_id_not_media_id(
    user_api_client, product_with_image, channel_USD
):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": graphene.Node.to_global_id("Product", -1),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["product"]["mediaById"] is None


def test_query_product_media_by_invalid_id(
    user_api_client, product_with_image, channel_USD
):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    id = "sks"
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": id,
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: ProductMedia."
    )
    assert content["data"]["product"]["mediaById"] is None


def test_query_product_media_by_id_with_size_and_format_proxy_url_returned(
    user_api_client, product_with_image, channel_USD, site_settings
):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    media = product_with_image.media.first()

    format = ThumbnailFormatEnum.WEBP.name
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)

    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": media_id,
        "channel": channel_USD.slug,
        "size": 120,
        "format": format,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["mediaById"]["id"]
    domain = site_settings.site.domain
    assert (
        content["data"]["product"]["mediaById"]["url"]
        == f"http://{domain}/thumbnail/{media_id}/128/{format.lower()}/"
    )


def test_query_product_media_by_id_with_size_proxy_url_returned(
    user_api_client, product_with_image, channel_USD, site_settings
):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    media = product_with_image.media.first()

    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)

    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": media_id,
        "channel": channel_USD.slug,
        "size": 120,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["mediaById"]["id"]
    assert (
        content["data"]["product"]["mediaById"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{media_id}/128/"
    )


def test_query_product_media_by_id_with_size_thumbnail_url_returned(
    user_api_client, product_with_image, channel_USD, site_settings
):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    media = product_with_image.media.first()

    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(product_media=media, size=size, image=thumbnail_mock)

    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": media_id,
        "channel": channel_USD.slug,
        "size": 120,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["mediaById"]["id"]
    assert (
        content["data"]["product"]["mediaById"]["url"]
        == f"http://{site_settings.site.domain}/media/thumbnails/{thumbnail_mock.name}"
    )


def test_query_product_media_by_id_zero_size_custom_format_provided(
    user_api_client, product_with_image, channel_USD, site_settings
):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    media = product_with_image.media.first()

    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    format = ThumbnailFormatEnum.WEBP.name

    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": media_id,
        "channel": channel_USD.slug,
        "format": format,
        "size": 0,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["mediaById"]["id"]
    assert (
        content["data"]["product"]["mediaById"]["url"]
        == f"http://{site_settings.site.domain}/media/{media.image.name}"
    )


def test_query_product_media_by_id_original_format(
    user_api_client, product_with_image, channel_USD, site_settings
):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    media = product_with_image.media.first()

    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    format = ThumbnailFormatEnum.ORIGINAL.name

    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": media_id,
        "channel": channel_USD.slug,
        "format": format,
        "size": 128,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["mediaById"]["id"]
    assert (
        content["data"]["product"]["mediaById"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{media_id}/128/"
    )


def test_query_product_media_by_id_avif_format(
    user_api_client, product_with_image, channel_USD, site_settings
):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    media = product_with_image.media.first()

    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    format = ThumbnailFormatEnum.AVIF.name

    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": media_id,
        "channel": channel_USD.slug,
        "format": format,
        "size": 128,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["mediaById"]["id"]
    assert (
        content["data"]["product"]["mediaById"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{media_id}/128/avif/"
    )


def test_query_product_media_by_id_zero_size_value_original_image_returned(
    user_api_client, product_with_image, channel_USD, site_settings
):
    query = QUERY_PRODUCT_MEDIA_BY_ID
    media = product_with_image.media.first()

    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)

    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "mediaId": media_id,
        "channel": channel_USD.slug,
        "size": 0,
    }

    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert content["data"]["product"]["mediaById"]["id"]
    assert (
        content["data"]["product"]["mediaById"]["url"]
        == f"http://{site_settings.site.domain}/media/{media.image.name}"
    )


QUERY_PRODUCT_IN_FEDERATION = """
query GetProductInFederation($representations: [_Any]) {
  _entities(representations: $representations) {
    __typename
    ... on Product {
      id
      name
    }
  }
}
"""


def test_query_product_for_federation(
    api_client,
    product,
    product_in_channel_JPY,
    shippable_gift_card_product,
    channel_USD,
    channel_JPY,
):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    shippable_gift_card_product_id = graphene.Node.to_global_id(
        "Product", shippable_gift_card_product.pk
    )
    variables = {
        "representations": [
            {
                "__typename": "Product",
                "id": product_id,
                "channel": channel_USD.slug,
            },
            {
                "__typename": "Product",
                "id": shippable_gift_card_product_id,
                "channel": channel_USD.slug,
            },
            {
                "__typename": "Product",
                "id": product_id,
                "channel": channel_JPY.slug,
            },
        ],
    }

    response = api_client.post_graphql(QUERY_PRODUCT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Product",
            "id": product_id,
            "name": product.name,
        },
        {
            "__typename": "Product",
            "id": shippable_gift_card_product_id,
            "name": shippable_gift_card_product.name,
        },
        {
            "__typename": "Product",
            "id": product_id,
            "name": product.name,
        },
    ]


def test_query_product_for_federation_as_customer_not_existing_channel(
    api_client, product, channel_USD
):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "representations": [
            {
                "__typename": "Product",
                "id": product_id,
                "channel": "not-existing-channel",
            },
        ],
    }

    response = api_client.post_graphql(QUERY_PRODUCT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_query_product_for_federation_as_customer_channel_not_active(
    api_client, product, channel_USD
):
    channel_USD.is_active = False
    channel_USD.save()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "representations": [
            {
                "__typename": "Product",
                "id": product_id,
                "channel": channel_USD.slug,
            },
        ],
    }

    response = api_client.post_graphql(QUERY_PRODUCT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_query_product_for_federation_as_customer_without_channel(api_client, product):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "representations": [
            {
                "__typename": "Product",
                "id": product_id,
            },
        ],
    }

    response = api_client.post_graphql(QUERY_PRODUCT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_query_product_for_federation_as_staff_user(
    staff_api_client,
    staff_user,
    permission_manage_products,
    product,
    product_in_channel_JPY,
    shippable_gift_card_product,
    channel_USD,
    channel_JPY,
):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    shippable_gift_card_product_id = graphene.Node.to_global_id(
        "Product", shippable_gift_card_product.pk
    )
    variables = {
        "representations": [
            {
                "__typename": "Product",
                "id": product_id,
                "channel": channel_USD.slug,
            },
            {
                "__typename": "Product",
                "id": shippable_gift_card_product_id,
                "channel": channel_USD.slug,
            },
            {
                "__typename": "Product",
                "id": product_id,
                "channel": channel_JPY.slug,
            },
        ],
    }

    staff_user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_PRODUCT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Product",
            "id": product_id,
            "name": product.name,
        },
        {
            "__typename": "Product",
            "id": shippable_gift_card_product_id,
            "name": shippable_gift_card_product.name,
        },
        {
            "__typename": "Product",
            "id": product_id,
            "name": product.name,
        },
    ]


def test_query_product_for_federation_as_staff_user_without_chanel(
    staff_api_client, staff_user, product, permission_manage_products
):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "representations": [
            {
                "__typename": "Product",
                "id": product_id,
            },
        ],
    }

    staff_user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_PRODUCT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Product",
            "id": product_id,
            "name": product.name,
        }
    ]


def test_query_product_for_federation_as_staff_user_not_existing_channel(
    staff_api_client, staff_user, product, channel_USD, permission_manage_products
):
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "representations": [
            {
                "__typename": "Product",
                "id": product_id,
                "channel": "not-existing-channel",
            },
        ],
    }

    staff_user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_PRODUCT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_query_product_for_federation_as_staff_user_channel_not_active(
    staff_api_client, staff_user, product, channel_USD, permission_manage_products
):
    channel_USD.is_active = False
    channel_USD.save()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "representations": [
            {
                "__typename": "Product",
                "id": product_id,
                "channel": "not-existing-channel",
            },
        ],
    }

    staff_user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_PRODUCT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_query_product_media_for_federation(
    api_client, product_with_image, channel_USD, site_settings
):
    media = product_with_image.media.first()
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductMedia",
                "id": media_id,
            },
        ],
    }
    query = """
      query GetProductMediaInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on ProductMedia {
            id
            url(size: 0)
          }
        }
      }
    """

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "ProductMedia",
            "id": media_id,
            "url": f"http://{site_settings.site.domain}/media/products/product.jpg",
        }
    ]


QUERY_PRODUCT_WITH_VARIANT = """
    query Product($id: ID!, $channel: String, $variant_id: ID, $sku: String){
        product(id: $id, channel: $channel){
           variant(id: $variant_id, sku: $sku){
            id
            sku
           }
        }
    }
    """


@pytest.mark.parametrize(
    ("variant_id", "sku", "result"),
    [(False, "123", "123"), (True, None, "123")],
)
def test_product_variant_field_filtering(
    staff_api_client,
    product,
    variant_id,
    sku,
    result,
    channel_USD,
):
    # given
    variant = product.variants.first()
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "variant_id": (
            graphene.Node.to_global_id("ProductVariant", variant.pk)
            if variant_id
            else None
        ),
        "sku": sku,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_VARIANT,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["product"]["variant"]["sku"] == result


def test_product_variant_field_filtering_null_response(
    staff_api_client,
    product,
    channel_USD,
):
    # given
    sku = "not_existing"
    variant_id = None

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "variant_id": variant_id,
        "sku": sku,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_VARIANT,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["product"]["variant"] is None


def test_product_variant_field_filtering_argument_required_error(
    staff_api_client,
    product,
    channel_USD,
):
    # given
    sku = None
    variant_id = None

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "variant_id": variant_id,
        "sku": sku,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_VARIANT,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    error_message = "At least one of arguments is required"
    assert error_message in content["errors"][0]["message"]


def test_product_variant_field_filtering_argument_cannot_be_combined_error(
    staff_api_client,
    product,
    channel_USD,
):
    # given
    sku = "123"
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "variant_id": variant_id,
        "sku": sku,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_VARIANT,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    error_message = "Argument 'id' cannot be combined"
    assert error_message in content["errors"][0]["message"]


QUERY_PRODUCT_WITH_SORTED_MEDIA = """
        query Product($id: ID!, $channel: String, $sort_by: MediaSortingInput){
            product(id: $id, channel: $channel){
                media(sortBy: $sort_by){
                    id
                    sortOrder
                }
            }
        }
    """


def test_query_product_media_sorting_asc(
    staff_api_client,
    product_with_image_list,
    channel_USD,
):
    # given
    sort_by = {"field": "ID", "direction": "ASC"}
    variables = {
        "id": graphene.Node.to_global_id("Product", product_with_image_list.pk),
        "channel": channel_USD.slug,
        "sort_by": sort_by,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_SORTED_MEDIA,
        variables,
    )

    # then
    content = get_graphql_content(response)
    media = content["data"]["product"]["media"]
    _, media1 = graphene.Node.from_global_id(media[0]["id"])
    _, media2 = graphene.Node.from_global_id(media[1]["id"])
    assert int(media1) < int(media2)


def test_query_product_media_sorting_desc(
    staff_api_client, product_with_image_list, channel_USD
):
    # given
    sort_by = {"field": "ID", "direction": "DESC"}
    variables = {
        "id": graphene.Node.to_global_id("Product", product_with_image_list.pk),
        "channel": channel_USD.slug,
        "sort_by": sort_by,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_SORTED_MEDIA,
        variables,
    )

    # then
    content = get_graphql_content(response)
    media = content["data"]["product"]["media"]
    _, media1 = graphene.Node.from_global_id(media[0]["id"])
    _, media2 = graphene.Node.from_global_id(media[1]["id"])
    assert int(media1) > int(media2)


def test_query_product_media_sorting_default(
    staff_api_client, product_with_image_list, channel_USD
):
    # given
    sort_by = None
    variables = {
        "id": graphene.Node.to_global_id("Product", product_with_image_list.pk),
        "channel": channel_USD.slug,
        "sort_by": sort_by,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_SORTED_MEDIA,
        variables,
    )

    # then
    content = get_graphql_content(response)
    media = content["data"]["product"]["media"]
    media1 = media[0]["sortOrder"]
    media2 = media[1]["sortOrder"]
    assert media1 <= media2


def test_query_product_media_sorting_default_and_one_sort_order_null(
    staff_api_client, product_with_image_list_and_one_null_sort_order, channel_USD
):
    # given
    sort_by = None
    variables = {
        "id": graphene.Node.to_global_id(
            "Product", product_with_image_list_and_one_null_sort_order.pk
        ),
        "channel": channel_USD.slug,
        "sort_by": sort_by,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_SORTED_MEDIA,
        variables,
    )

    # then
    content = get_graphql_content(response)
    media = content["data"]["product"]["media"]
    media1 = media[0]["sortOrder"]
    media2 = media[1]["sortOrder"]
    assert media1 is None
    assert media2 is not None


QUERY_PRODUCT_WITH_ATTRIBUTE = """
query Product($id: ID!, $channel: String, $slug: String!) {
    product(id: $id, channel: $channel) {
        attribute(slug: $slug) {
            attribute {
                id
                slug
            }
        }
        attributes {
            attribute {
                id
                slug
            }
        }
    }
}
"""


def test_product_attribute_field_filtering(staff_api_client, product, channel_USD):
    # given
    slug = "color"

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "slug": slug,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_ATTRIBUTE,
        variables,
    )

    # then
    expected_slug = "color"
    content = get_graphql_content(response)
    queried_slug = content["data"]["product"]["attribute"]["attribute"]["slug"]
    assert queried_slug == expected_slug


def test_product_attribute_field_filtering_not_found(
    staff_api_client, product, channel_USD
):
    # given
    slug = ""

    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "slug": slug,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_ATTRIBUTE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["product"]["attribute"] is None


def test_product_attribute_not_visible_in_storefront_for_customer_is_not_returned(
    user_api_client, product, channel_USD
):
    # given
    attribute = product.product_type.product_attributes.first()
    attribute.visible_in_storefront = False
    attribute.save(update_fields=["visible_in_storefront"])
    visible_attrs_count = product.product_type.product_attributes.filter(
        visible_in_storefront=True
    ).count()

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "slug": attribute.slug,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_WITH_ATTRIBUTE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["product"]["attribute"] is None
    assert len(content["data"]["product"]["attributes"]) == visible_attrs_count
    attr_data = {
        "attribute": {
            "id": graphene.Node.to_global_id("Attribute", attribute.pk),
            "slug": attribute.slug,
        }
    }
    assert attr_data not in content["data"]["product"]["attributes"]


def test_product_attribute_visible_in_storefront_for_customer_is_returned(
    user_api_client, product, channel_USD
):
    # given
    attribute = product.product_type.product_attributes.first()
    attribute.visible_in_storefront = True
    attribute.save(update_fields=["visible_in_storefront"])

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "slug": attribute.slug,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_WITH_ATTRIBUTE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert (
        content["data"]["product"]["attribute"]["attribute"]["slug"] == attribute.slug
    )


@pytest.mark.parametrize("visible_in_storefront", [False, True])
def test_product_attribute_visible_in_storefront_for_staff_is_always_returned(
    visible_in_storefront,
    staff_api_client,
    product,
    channel_USD,
    permission_manage_products,
):
    # given
    attribute = product.product_type.product_attributes.first()
    attribute.visible_in_storefront = visible_in_storefront
    attribute.save(update_fields=["visible_in_storefront"])

    # when
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "slug": attribute.slug,
        "channel": channel_USD.slug,
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_WITH_ATTRIBUTE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    assert (
        content["data"]["product"]["attribute"]["attribute"]["slug"] == attribute.slug
    )


QUERY_PRODUCTS_AVAILABILITY = """
    query ($channel:String){
        products(first: 10, channel: $channel) {
            totalCount
            edges {
                node {
                    id
                    name
                    isAvailable
                    variants {
                        quantityAvailable
                        stocks {
                            quantity
                        }
                    }
                }
            }
        }
    }
"""


def test_fetch_all_products_with_availability_data(
    staff_api_client, permission_manage_products, product_list, channel_USD, order_line
):
    # given
    product_1, product_2, product_3 = product_list
    allocations = []

    product_1_qty = 0
    product_1_qty_allocated = 1
    product_1_stock = product_1.variants.first().stocks.first()
    product_1_stock.quantity = product_1_qty
    product_1_stock.save(update_fields=["quantity"])
    allocations.append(
        Allocation(
            order_line=order_line,
            stock=product_1_stock,
            quantity_allocated=product_1_qty_allocated,
        )
    )

    product_2_qty = 15
    product_2_qty_allocated = 2
    product_2_stock = product_2.variants.first().stocks.first()
    product_2_stock.quantity = product_2_qty
    product_2_stock.save(update_fields=["quantity"])
    allocations.append(
        Allocation(
            order_line=order_line,
            stock=product_2_stock,
            quantity_allocated=product_2_qty_allocated,
        )
    )

    product_3_qty = 10
    product_3_qty_allocated = 0
    product_3_stock = product_3.variants.first().stocks.first()
    product_3_stock.quantity = product_3_qty
    product_3_stock.save(update_fields=["quantity"])

    Allocation.objects.bulk_create(allocations)

    variables = {"channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCTS_AVAILABILITY,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == num_products
    for product, quantity, quantity_allocated in zip(
        product_list,
        [product_1_qty, product_2_qty, product_3_qty],
        [product_1_qty_allocated, product_2_qty_allocated, product_3_qty_allocated],
    ):
        data = {
            "node": {
                "id": graphene.Node.to_global_id("Product", product.id),
                "name": product.name,
                "isAvailable": quantity > 0,
                "variants": [
                    {
                        "quantityAvailable": max(quantity - quantity_allocated, 0),
                        "stocks": [{"quantity": quantity}],
                    }
                ],
            }
        }
        assert data in product_data


QUERY_PRODUCT_BY_EXTERNAL_REFERENCE = """
    query ($id: ID, $externalReference: String, $slug: String, $channel:String){
        product(
            id: $id,
            slug: $slug,
            externalReference: $externalReference,
            channel: $channel
        ) {
            id
            name
            externalReference
        }
    }
"""


def test_product_query_by_external_reference(
    staff_api_client, permission_manage_products, product, channel_USD
):
    # given
    product.external_reference = "test-ext-id"
    product.save(update_fields=["external_reference"])
    variables = {
        "externalReference": product.external_reference,
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_BY_EXTERNAL_REFERENCE,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    product_data = content["data"]["product"]
    assert product_data is not None
    assert product_data["name"] == product.name
    assert product_data["externalReference"] == product.external_reference


PRODUCT_TAX_CLASS_QUERY = """
    query getProduct($id: ID!, $channel: String) {
        product(id: $id, channel: $channel) {
            id
            taxClass {
                id
            }
        }
    }
"""


def test_product_tax_class_query_by_app(app_api_client, product, channel_USD):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(PRODUCT_TAX_CLASS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]
    assert data["product"]
    assert data["product"]["id"]
    assert data["product"]["taxClass"]["id"]


def test_product_tax_class_query_by_staff(staff_api_client, product, channel_USD):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(PRODUCT_TAX_CLASS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]
    assert data["product"]
    assert data["product"]["id"]
    assert data["product"]["taxClass"]["id"]
