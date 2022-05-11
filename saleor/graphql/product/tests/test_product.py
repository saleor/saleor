import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from unittest import mock
from unittest.mock import ANY, Mock, patch

import before_after
import graphene
import pytest
import pytz
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.functional import SimpleLazyObject
from django.utils.html import strip_tags
from django.utils.text import slugify
from freezegun import freeze_time
from graphql_relay import to_global_id
from measurement.measures import Weight
from prices import Money, TaxedMoney

from ....attribute import AttributeInputType, AttributeType
from ....attribute.models import Attribute, AttributeValue
from ....attribute.utils import associate_attribute_values_to_instance
from ....core.taxes import TaxType
from ....core.units import MeasurementUnits, WeightUnits
from ....order import OrderEvents, OrderStatus
from ....order.models import OrderEvent, OrderLine
from ....plugins.manager import PluginsManager, get_plugins_manager
from ....product import ProductMediaTypes, ProductTypeKind
from ....product.error_codes import ProductErrorCode
from ....product.models import (
    Category,
    Collection,
    CollectionChannelListing,
    Product,
    ProductChannelListing,
    ProductMedia,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ....product.search import prepare_product_search_vector_value
from ....product.tasks import update_variants_names
from ....product.tests.utils import create_image, create_pdf_file_with_image_ext
from ....product.utils.availability import get_variant_availability
from ....product.utils.costs import get_product_costs_data
from ....tests.utils import dummy_editorjs, flush_post_commit_hooks
from ....warehouse.models import Allocation, Stock, Warehouse
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.payloads import generate_product_deleted_payload
from ...core.enums import AttributeErrorCode, ReportingPeriod
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
    get_multipart_request_body,
)
from ..bulk_mutations.products import ProductVariantStocksUpdate
from ..enums import ProductTypeKindEnum, VariantAttributeScope
from ..utils import create_stocks


@pytest.fixture
def query_products_with_filter():
    query = """
        query ($filter: ProductFilterInput!, $channel: String) {
          products(first:5, filter: $filter, channel: $channel) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
        """
    return query


@pytest.fixture
def query_products_with_attributes():
    query = """
        query {
          products(first:5) {
            edges{
              node{
                id
                name
                attributes {
                    attribute {
                        id
                    }
                }
              }
            }
          }
        }
        """
    return query


@pytest.fixture
def query_collections_with_filter():
    query = """
    query ($filter: CollectionFilterInput!, $channel: String) {
          collections(first:5, filter: $filter, channel: $channel) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
        """
    return query


@pytest.fixture
def query_categories_with_filter():
    query = """
    query ($filter: CategoryFilterInput!, ) {
          categories(first:5, filter: $filter) {
            totalCount
            edges{
              node{
                id
                name
              }
            }
          }
        }
        """
    return query


QUERY_FETCH_ALL_PRODUCTS = """
    query ($channel:String){
        products(first: 10, channel: $channel) {
            totalCount
            edges {
                node {
                    id
                    name
                    variants {
                        id
                    }
                }
            }
        }
    }
"""


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
    assert content["errors"][0]["message"] == (f"Couldn't resolve id: {id}.")


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
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {product_id}."
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
    query ($id: ID, $channel: String){
        product(id: $id, channel: $channel) {
            media {
                id
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


def test_product_query_with_media_to_remove(
    user_api_client, permission_manage_products, product_with_images
):
    # given
    query = QUERY_PRODUCT_BY_ID_WITH_MEDIA
    variables = {"id": graphene.Node.to_global_id("Product", product_with_images.pk)}
    ProductMedia.objects.filter(product=product_with_images.pk).update(to_remove=True)

    # when
    response = user_api_client.post_graphql(
        query,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]

    # then
    assert product_data is not None
    assert len(product_data["media"]) == 0


def test_product_variant_query_with_media_to_remove(
    user_api_client, permission_manage_products, variant_with_image
):
    # given
    query = QUERY_PRODUCT_BY_ID_WITH_MEDIA
    product = variant_with_image.product
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}
    variants_count = ProductVariant.objects.all().count()
    ProductMedia.objects.filter(product=product.pk).update(to_remove=True)

    # when
    response = user_api_client.post_graphql(
        query,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["product"]

    # then
    assert product_data is not None
    assert len(product_data["media"]) == 0
    assert len(product_data["variants"]) == variants_count
    for variant in product_data["variants"]:
        assert variant["media"] == []


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


def test_fetch_all_products_available_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_product_variants_available_as_staff_user_with_channel(
    staff_api_client, permission_manage_products, product_variant_list, channel_USD
):
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    num_products = Product.objects.count()
    num_variants = ProductVariant.objects.count()
    assert num_variants > 1

    content = get_graphql_content(response)
    products = content["data"]["products"]
    variants = products["edges"][0]["node"]["variants"]

    assert products["totalCount"] == num_products
    assert len(products["edges"]) == num_products
    assert len(variants) == num_variants - 1


def test_fetch_all_product_variants_available_as_staff_user_without_channel(
    staff_api_client, permission_manage_products, product_variant_list, channel_USD
):
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )

    num_products = Product.objects.count()
    num_variants = ProductVariant.objects.count()
    assert num_variants > 1

    content = get_graphql_content(response)
    products = content["data"]["products"]
    variants = products["edges"][0]["node"]["variants"]

    assert products["totalCount"] == num_products
    assert len(products["edges"]) == num_products
    assert len(variants) == num_variants


def test_fetch_all_products_not_available_as_staff_user(
    staff_api_client, permission_manage_products, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_not_existing_in_channel_as_staff_user(
    staff_api_client, permission_manage_products, channel_USD, product_list
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(
        product=product_list[0], channel=channel_USD
    ).delete()

    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # if channel slug is provided we return all products related to this channel
    num_products = Product.objects.count() - 1

    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_as_staff_user_without_channel_slug(
    staff_api_client, permission_manage_products, product_list, channel_USD
):
    ProductChannelListing.objects.filter(
        product=product_list[0], channel=channel_USD
    ).delete()

    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_available_as_app(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_not_available_as_app(
    app_api_client, permission_manage_products, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_not_existing_in_channel_as_app(
    app_api_client, permission_manage_products, product_list, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(
        product=product_list[0], channel=channel_USD
    ).delete()

    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    # if channel slug is provided we return all products related to this channel

    num_products = Product.objects.count() - 1
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_as_app_without_channel_slug(
    app_api_client, permission_manage_products, product_list, channel_USD
):
    ProductChannelListing.objects.filter(
        product=product_list[0], channel=channel_USD
    ).delete()

    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_available_as_customer(
    user_api_client, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    response = user_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_not_available_as_customer(
    user_api_client, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = user_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == 0
    assert not content["data"]["products"]["edges"]


def test_fetch_all_products_not_existing_in_channel_as_customer(
    user_api_client, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = user_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == 0
    assert not content["data"]["products"]["edges"]


def test_fetch_all_products_available_as_anonymous(api_client, product, channel_USD):
    variables = {"channel": channel_USD.slug}
    response = api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_not_available_as_anonymous(
    api_client, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    response = api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == 0
    assert not content["data"]["products"]["edges"]


def test_fetch_all_products_not_existing_in_channel_as_anonymous(
    api_client, product, channel_USD
):
    variables = {"channel": channel_USD.slug}
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).delete()

    response = api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == 0
    assert not content["data"]["products"]["edges"]


def test_fetch_all_products_visible_in_listings(
    user_api_client, product_list, permission_manage_products, channel_USD
):
    # given
    product_list[0].channel_listings.update(visible_in_listings=False)

    product_count = Product.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == product_count - 1
    products_ids = [product["node"]["id"] for product in product_data]
    assert graphene.Node.to_global_id("Product", product_list[0].pk) not in products_ids


def test_fetch_all_products_visible_in_listings_by_staff_with_perm(
    staff_api_client, product_list, permission_manage_products, channel_USD
):
    # given
    product_list[0].channel_listings.update(visible_in_listings=False)

    product_count = Product.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == product_count


def test_fetch_all_products_visible_in_listings_by_staff_without_manage_products(
    staff_api_client, product_list, channel_USD
):
    # given
    product_list[0].channel_listings.update(visible_in_listings=False)

    product_count = Product.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == product_count - 1  # invisible doesn't count


def test_fetch_all_products_visible_in_listings_by_app_with_perm(
    app_api_client, product_list, permission_manage_products, channel_USD
):
    # given
    product_list[0].channel_listings.update(visible_in_listings=False)

    product_count = Product.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == product_count


def test_fetch_all_products_visible_in_listings_by_app_without_manage_products(
    app_api_client, product_list, channel_USD
):
    # given
    product_list[0].channel_listings.update(visible_in_listings=False)

    product_count = Product.objects.count()
    variables = {"channel": channel_USD.slug}

    # when
    response = app_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS, variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"]
    assert len(product_data) == product_count - 1  # invisible doesn't count


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


def test_products_query_with_filter_attributes(
    query_products_with_filter,
    staff_api_client,
    product,
    permission_manage_products,
    channel_USD,
):

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        has_variants=True,
        is_shipping_required=True,
        kind=ProductTypeKind.NORMAL,
    )
    attribute = Attribute.objects.create(slug="new_attr", name="Attr")
    attribute.product_types.add(product_type)
    attr_value = AttributeValue.objects.create(
        attribute=attribute, name="First", slug="first"
    )
    second_product = product
    second_product.id = None
    second_product.product_type = product_type
    second_product.slug = "second-product"
    second_product.save()
    associate_attribute_values_to_instance(second_product, attribute, attr_value)

    variables = {
        "filter": {
            "attributes": [{"slug": attribute.slug, "values": [attr_value.slug]}],
        },
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


@pytest.mark.parametrize(
    "gte, lte, expected_products_index",
    [
        (None, 8, [1]),
        (0, 8, [1]),
        (7, 8, []),
        (5, None, [0, 1]),
        (8, 10, [0]),
        (12, None, [0]),
        (20, None, []),
        (20, 8, []),
    ],
)
def test_products_query_with_filter_numeric_attributes(
    gte,
    lte,
    expected_products_index,
    query_products_with_filter,
    staff_api_client,
    product,
    category,
    numeric_attribute,
    permission_manage_products,
):
    product.product_type.product_attributes.add(numeric_attribute)
    associate_attribute_values_to_instance(
        product, numeric_attribute, *numeric_attribute.values.all()
    )

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    numeric_attribute.product_types.add(product_type)

    second_product = Product.objects.create(
        name="Second product",
        slug="second-product",
        product_type=product_type,
        category=category,
    )
    attr_value = AttributeValue.objects.create(
        attribute=numeric_attribute, name="5.2", slug="5_2"
    )

    associate_attribute_values_to_instance(
        second_product, numeric_attribute, attr_value
    )

    second_product.refresh_from_db()
    products_instances = [product, second_product]
    products_ids = [
        graphene.Node.to_global_id("Product", p.pk) for p in products_instances
    ]
    values_range = {}
    if gte:
        values_range["gte"] = gte
    if lte:
        values_range["lte"] = lte
    variables = {
        "filter": {
            "attributes": [
                {"slug": numeric_attribute.slug, "valuesRange": values_range}
            ]
        }
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == len(expected_products_index)
    assert set(product["node"]["id"] for product in products) == {
        products_ids[index] for index in expected_products_index
    }
    assert set(product["node"]["name"] for product in products) == {
        products_instances[index].name for index in expected_products_index
    }


@pytest.mark.parametrize(
    "filter_value, expected_products_index",
    [
        (False, [0, 1]),
        (True, [0]),
    ],
)
def test_products_query_with_filter_boolean_attributes(
    filter_value,
    expected_products_index,
    query_products_with_filter,
    staff_api_client,
    product,
    category,
    boolean_attribute,
    permission_manage_products,
):
    product.product_type.product_attributes.add(boolean_attribute)

    associate_attribute_values_to_instance(
        product, boolean_attribute, boolean_attribute.values.get(boolean=filter_value)
    )

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    boolean_attribute.product_types.add(product_type)

    second_product = Product.objects.create(
        name="Second product",
        slug="second-product",
        product_type=product_type,
        category=category,
    )
    associate_attribute_values_to_instance(
        second_product, boolean_attribute, boolean_attribute.values.get(boolean=False)
    )

    second_product.refresh_from_db()
    products_instances = [product, second_product]
    products_ids = [
        graphene.Node.to_global_id("Product", p.pk) for p in products_instances
    ]

    variables = {
        "filter": {
            "attributes": [{"slug": boolean_attribute.slug, "boolean": filter_value}]
        }
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == len(expected_products_index)
    assert set(product["node"]["id"] for product in products) == {
        products_ids[index] for index in expected_products_index
    }
    assert set(product["node"]["name"] for product in products) == {
        products_instances[index].name for index in expected_products_index
    }


def test_products_query_with_filter_by_attributes_values_and_range(
    query_products_with_filter,
    staff_api_client,
    product,
    category,
    numeric_attribute,
    permission_manage_products,
):
    product_attr = product.attributes.first()
    attr_value_1 = product_attr.values.first()
    product.product_type.product_attributes.add(numeric_attribute)
    associate_attribute_values_to_instance(
        product, numeric_attribute, *numeric_attribute.values.all()
    )

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    numeric_attribute.product_types.add(product_type)

    second_product = Product.objects.create(
        name="Second product",
        slug="second-product",
        product_type=product_type,
        category=category,
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=numeric_attribute, name="5.2", slug="5_2"
    )

    associate_attribute_values_to_instance(
        second_product, numeric_attribute, attr_value_2
    )

    second_product.refresh_from_db()

    variables = {
        "filter": {
            "attributes": [
                {"slug": numeric_attribute.slug, "valuesRange": {"gte": 2}},
                {"slug": attr_value_1.attribute.slug, "values": [attr_value_1.slug]},
            ]
        }
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product.pk
    )
    assert products[0]["node"]["name"] == product.name


def test_products_query_with_filter_swatch_attributes(
    query_products_with_filter,
    staff_api_client,
    product,
    category,
    swatch_attribute,
    permission_manage_products,
):
    product.product_type.product_attributes.add(swatch_attribute)
    associate_attribute_values_to_instance(
        product, swatch_attribute, *swatch_attribute.values.all()
    )

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        has_variants=True,
        is_shipping_required=True,
    )
    swatch_attribute.product_types.add(product_type)

    second_product = Product.objects.create(
        name="Second product",
        slug="second-product",
        product_type=product_type,
        category=category,
    )
    attr_value = AttributeValue.objects.create(
        attribute=swatch_attribute, name="Dark", slug="dark"
    )

    associate_attribute_values_to_instance(second_product, swatch_attribute, attr_value)

    second_product.refresh_from_db()

    variables = {
        "filter": {
            "attributes": [
                {"slug": swatch_attribute.slug, "values": [attr_value.slug]},
            ]
        }
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_date_range_date_attributes(
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    date_attribute,
    channel_USD,
):
    """Ensure both products will be returned when filtering  attributes by date range,
    products with the same date attribute value."""

    # given
    product_type = product_list[0].product_type
    date_value = timezone.now()
    product_type.product_attributes.add(date_attribute)
    attr_value_1 = AttributeValue.objects.create(
        attribute=date_attribute, name="First", slug="first", date_time=date_value
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=date_attribute, name="Second", slug="second", date_time=date_value
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=date_attribute,
        name="Third",
        slug="third",
        date_time=date_value - timedelta(days=1),
    )

    associate_attribute_values_to_instance(
        product_list[0], date_attribute, attr_value_1
    )
    associate_attribute_values_to_instance(
        product_list[1], date_attribute, attr_value_2
    )
    associate_attribute_values_to_instance(
        product_list[2], date_attribute, attr_value_3
    )

    variables = {
        "filter": {
            "attributes": [
                {
                    "slug": date_attribute.slug,
                    "date": {"gte": date_value.date(), "lte": date_value.date()},
                }
            ],
        },
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    assert {node["node"]["id"] for node in products} == {
        graphene.Node.to_global_id("Product", instance.id)
        for instance in product_list[:2]
    }


def test_products_query_with_filter_date_range_date_variant_attributes(
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    date_attribute,
    channel_USD,
):
    """Ensure both products will be returned when filtering attributes by date range,
    variants with the same date attribute value."""

    # given
    product_type = product_list[0].product_type
    date_value = timezone.now()
    product_type.variant_attributes.add(date_attribute)
    attr_value_1 = AttributeValue.objects.create(
        attribute=date_attribute,
        name="First",
        slug="first",
        date_time=date_value - timedelta(days=1),
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=date_attribute, name="Second", slug="second", date_time=date_value
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=date_attribute, name="Third", slug="third", date_time=date_value
    )

    associate_attribute_values_to_instance(
        product_list[0].variants.first(), date_attribute, attr_value_1
    )
    associate_attribute_values_to_instance(
        product_list[1].variants.first(), date_attribute, attr_value_2
    )
    associate_attribute_values_to_instance(
        product_list[2].variants.first(), date_attribute, attr_value_3
    )

    variables = {
        "filter": {
            "attributes": [
                {
                    "slug": date_attribute.slug,
                    "date": {"gte": date_value.date(), "lte": date_value.date()},
                }
            ],
        },
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    assert {node["node"]["id"] for node in products} == {
        graphene.Node.to_global_id("Product", instance.id)
        for instance in product_list[1:]
    }


def test_products_query_with_filter_date_range_date_time_attributes(
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    date_time_attribute,
    channel_USD,
):
    """Ensure both products will be returned when filtering attributes by date time
    range, products with the same date time attribute value."""

    # given
    product_type = product_list[0].product_type
    date_value = timezone.now()
    product_type.product_attributes.add(date_time_attribute)
    attr_value_1 = AttributeValue.objects.create(
        attribute=date_time_attribute, name="First", slug="first", date_time=date_value
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=date_time_attribute,
        name="Second",
        slug="second",
        date_time=date_value,
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=date_time_attribute,
        name="Third",
        slug="third",
        date_time=date_value - timedelta(days=1),
    )

    associate_attribute_values_to_instance(
        product_list[0], date_time_attribute, attr_value_1
    )
    associate_attribute_values_to_instance(
        product_list[1], date_time_attribute, attr_value_2
    )
    associate_attribute_values_to_instance(
        product_list[2], date_time_attribute, attr_value_3
    )

    variables = {
        "filter": {
            "attributes": [
                {
                    "slug": date_time_attribute.slug,
                    "date": {"gte": date_value.date(), "lte": date_value.date()},
                }
            ],
        },
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    assert {node["node"]["id"] for node in products} == {
        graphene.Node.to_global_id("Product", instance.id)
        for instance in product_list[:2]
    }


def test_products_query_with_filter_date_range_date_time_variant_attributes(
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    date_time_attribute,
    channel_USD,
):
    """Ensure both products will be returned when filtering attributes by date time
    range, variant and product with the same date time attribute value."""

    # given
    product_type = product_list[0].product_type
    date_value = timezone.now()
    product_type.variant_attributes.add(date_time_attribute)
    attr_value_1 = AttributeValue.objects.create(
        attribute=date_time_attribute,
        name="First",
        slug="first",
        date_time=date_value - timedelta(days=1),
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=date_time_attribute,
        name="Second",
        slug="second",
        date_time=date_value,
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=date_time_attribute, name="Third", slug="third", date_time=date_value
    )

    associate_attribute_values_to_instance(
        product_list[0].variants.first(), date_time_attribute, attr_value_1
    )
    associate_attribute_values_to_instance(
        product_list[1].variants.first(), date_time_attribute, attr_value_2
    )
    associate_attribute_values_to_instance(
        product_list[2].variants.first(), date_time_attribute, attr_value_3
    )

    variables = {
        "filter": {
            "attributes": [
                {
                    "slug": date_time_attribute.slug,
                    "date": {"gte": date_value.date(), "lte": date_value.date()},
                }
            ],
        },
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    assert {node["node"]["id"] for node in products} == {
        graphene.Node.to_global_id("Product", instance.id)
        for instance in product_list[1:]
    }


def test_products_query_with_filter_date_time_range_date_time_attributes(
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    date_time_attribute,
    channel_USD,
):
    """Ensure both products will be returned when filtering by  attributes by date range
    variants with the same date attribute value."""

    # given
    product_type = product_list[0].product_type
    date_value = timezone.now()
    product_type.product_attributes.add(date_time_attribute)
    product_type.variant_attributes.add(date_time_attribute)
    attr_value_1 = AttributeValue.objects.create(
        attribute=date_time_attribute,
        name="First",
        slug="first",
        date_time=date_value - timedelta(hours=2),
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=date_time_attribute,
        name="Second",
        slug="second",
        date_time=date_value + timedelta(hours=3),
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=date_time_attribute,
        name="Third",
        slug="third",
        date_time=date_value - timedelta(hours=6),
    )

    associate_attribute_values_to_instance(
        product_list[0], date_time_attribute, attr_value_1
    )
    associate_attribute_values_to_instance(
        product_list[1].variants.first(), date_time_attribute, attr_value_2
    )
    associate_attribute_values_to_instance(
        product_list[2].variants.first(), date_time_attribute, attr_value_3
    )

    variables = {
        "filter": {
            "attributes": [
                {
                    "slug": date_time_attribute.slug,
                    "dateTime": {
                        "gte": date_value - timedelta(hours=4),
                        "lte": date_value + timedelta(hours=4),
                    },
                }
            ],
        },
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    assert {node["node"]["id"] for node in products} == {
        graphene.Node.to_global_id("Product", instance.id)
        for instance in product_list[:2]
    }


def test_products_query_filter_by_non_existing_attribute(
    query_products_with_filter, api_client, product_list, channel_USD
):
    variables = {
        "channel": channel_USD.slug,
        "filter": {"attributes": [{"slug": "i-do-not-exist", "values": ["red"]}]},
    }
    response = api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 0


def test_products_query_with_filter_category(
    query_products_with_filter, staff_api_client, product, permission_manage_products
):
    category = Category.objects.create(name="Custom", slug="custom")
    second_product = product
    second_product.id = None
    second_product.slug = "second-product"
    second_product.category = category
    second_product.save()

    category_id = graphene.Node.to_global_id("Category", category.id)
    variables = {"filter": {"categories": [category_id]}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_has_category_false(
    query_products_with_filter, staff_api_client, product, permission_manage_products
):
    second_product = product
    second_product.category = None
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()

    variables = {"filter": {"hasCategory": False}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_has_category_true(
    query_products_with_filter,
    staff_api_client,
    product_without_category,
    permission_manage_products,
):
    category = Category.objects.create(name="Custom", slug="custom")
    second_product = product_without_category
    second_product.category = category
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()

    variables = {"filter": {"hasCategory": True}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_collection(
    query_products_with_filter,
    staff_api_client,
    product,
    collection,
    permission_manage_products,
):
    second_product = product
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()
    second_product.collections.add(collection)

    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"filter": {"collections": [collection_id]}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_category_and_search(
    query_products_with_filter,
    staff_api_client,
    product,
    permission_manage_products,
):
    category = Category.objects.create(name="Custom", slug="custom")
    second_product = product
    second_product.id = None
    second_product.slug = "second-product"
    second_product.category = category
    product.category = category
    second_product.save()
    product.save()

    for pr in [product, second_product]:
        pr.search_vector = prepare_product_search_vector_value(pr)
    Product.objects.bulk_update([product, second_product], ["search_vector"])

    category_id = graphene.Node.to_global_id("Category", category.id)
    variables = {"filter": {"categories": [category_id], "search": product.name}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    product_id = graphene.Node.to_global_id("Product", product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product.name


def test_products_query_with_filter_gift_card_false(
    query_products_with_filter,
    staff_api_client,
    product,
    shippable_gift_card_product,
    permission_manage_products,
):
    # given
    variables = {"filter": {"giftCard": False}}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product.pk
    )


def test_products_query_with_filter_gift_card_true(
    query_products_with_filter,
    staff_api_client,
    product,
    shippable_gift_card_product,
    permission_manage_products,
):
    # given
    variables = {"filter": {"giftCard": True}}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", shippable_gift_card_product.pk
    )


def test_products_with_variants_query_as_app(
    query_products_with_attributes,
    app_api_client,
    product_with_multiple_values_attributes,
    permission_manage_products,
):
    product = product_with_multiple_values_attributes
    attribute = product.attributes.first().attribute
    attribute.visible_in_storefront = False
    attribute.save()
    second_product = product
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()
    product.save()

    app_api_client.app.permissions.add(permission_manage_products)
    response = app_api_client.post_graphql(query_products_with_attributes)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    for response_product in products:
        attrs = response_product["node"]["attributes"]
        assert len(attrs) == 1
        assert attrs[0]["attribute"]["id"] == attribute_id


@pytest.mark.parametrize(
    "products_filter",
    [
        {"minimalPrice": {"gte": 1.0, "lte": 2.0}},
        {"isPublished": False},
        {"search": "Juice1"},
    ],
)
def test_products_query_with_filter(
    products_filter,
    query_products_with_filter,
    staff_api_client,
    product,
    permission_manage_products,
    channel_USD,
):
    assert "Juice1" not in product.name

    second_product = product
    second_product.id = None
    second_product.name = "Apple Juice1"
    second_product.slug = "apple-juice1"
    second_product.save()
    variant_second_product = second_product.variants.create(
        product=second_product,
        sku=second_product.slug,
    )
    ProductVariantChannelListing.objects.create(
        variant=variant_second_product,
        channel=channel_USD,
        price_amount=Decimal(1.99),
        cost_price_amount=Decimal(1),
        currency=channel_USD.currency_code,
    )
    ProductChannelListing.objects.create(
        product=second_product,
        discounted_price_amount=Decimal(1.99),
        channel=channel_USD,
        is_published=False,
    )
    second_product.search_vector = prepare_product_search_vector_value(second_product)
    second_product.save(update_fields=["search_vector"])
    variables = {"filter": products_filter, "channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_price_filter_as_staff(
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
):
    product = product_list[0]
    product.variants.first().channel_listings.filter().update(price_amount=None)

    variables = {
        "filter": {"price": {"gte": 9, "lte": 31}},
        "channel": channel_USD.slug,
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 3


def test_products_query_with_price_filter_as_user(
    query_products_with_filter,
    user_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
):
    product = product_list[0]
    product.variants.first().channel_listings.filter().update(price_amount=None)
    second_product_id = graphene.Node.to_global_id("Product", product_list[1].id)
    third_product_id = graphene.Node.to_global_id("Product", product_list[2].id)
    variables = {
        "filter": {"price": {"gte": 9, "lte": 31}},
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 2
    assert products[0]["node"]["id"] == second_product_id
    assert products[1]["node"]["id"] == third_product_id


@pytest.mark.parametrize("is_published", [(True), (False)])
def test_products_query_with_filter_search_by_sku(
    is_published,
    query_products_with_filter,
    staff_api_client,
    product_with_two_variants,
    product_with_default_variant,
    permission_manage_products,
    channel_USD,
):
    ProductChannelListing.objects.filter(
        product=product_with_default_variant, channel=channel_USD
    ).update(is_published=is_published)
    variables = {"filter": {"search": "1234"}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    product_id = graphene.Node.to_global_id("Product", product_with_default_variant.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product_with_default_variant.name


@pytest.mark.parametrize("search_value", ["new", "NEW color", "Color"])
def test_products_query_with_filter_search_by_dropdown_attribute_value(
    search_value,
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
    color_attribute,
):
    # given
    product_with_dropdown_attr = product_list[1]

    product_type = product_with_dropdown_attr.product_type
    product_type.product_attributes.add(color_attribute)

    dropdown_attr_value = color_attribute.values.first()
    dropdown_attr_value.name = "New color"
    dropdown_attr_value.save(update_fields=["name"])

    associate_attribute_values_to_instance(
        product_with_dropdown_attr, color_attribute, dropdown_attr_value
    )

    product_with_dropdown_attr.refresh_from_db()

    product_with_dropdown_attr.search_vector = prepare_product_search_vector_value(
        product_with_dropdown_attr
    )
    product_with_dropdown_attr.save(update_fields=["search_document", "search_vector"])

    variables = {"filter": {"search": search_value}, "channel": channel_USD.slug}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # then
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_with_dropdown_attr.id
    )
    assert products[0]["node"]["name"] == product_with_dropdown_attr.name


@pytest.mark.parametrize(
    "search_value", ["eco mode", "ECO Performance", "performant*", "modes"]
)
def test_products_query_with_filter_search_by_multiselect_attribute_value(
    search_value,
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
):
    # given
    product_with_multiselect_attr = product_list[2]

    multiselect_attribute = Attribute.objects.create(
        slug="modes",
        name="Available Modes",
        input_type=AttributeInputType.MULTISELECT,
        type=AttributeType.PRODUCT_TYPE,
    )

    multiselect_attr_val_1 = AttributeValue.objects.create(
        attribute=multiselect_attribute, name="Eco Mode", slug="eco"
    )
    multiselect_attr_val_2 = AttributeValue.objects.create(
        attribute=multiselect_attribute, name="Performance Mode", slug="power"
    )

    product_type = product_with_multiselect_attr.product_type
    product_type.product_attributes.add(multiselect_attribute)

    associate_attribute_values_to_instance(
        product_with_multiselect_attr,
        multiselect_attribute,
        multiselect_attr_val_1,
        multiselect_attr_val_2,
    )

    product_with_multiselect_attr.refresh_from_db()

    product_with_multiselect_attr.search_vector = prepare_product_search_vector_value(
        product_with_multiselect_attr
    )
    product_with_multiselect_attr.save(update_fields=["search_vector"])

    variables = {"filter": {"search": search_value}, "channel": channel_USD.slug}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # then
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_with_multiselect_attr.id
    )
    assert products[0]["node"]["name"] == product_with_multiselect_attr.name


@pytest.mark.parametrize("search_value", ["rich", "test rich", "RICH text"])
def test_products_query_with_filter_search_by_rich_text_attribute(
    search_value,
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
    rich_text_attribute,
):
    # given
    product_with_rich_text_attr = product_list[1]

    product_type = product_with_rich_text_attr.product_type
    product_type.product_attributes.add(rich_text_attribute)

    rich_text_value = rich_text_attribute.values.first()
    rich_text_value.rich_text = dummy_editorjs("Test rich text.")
    rich_text_value.save(update_fields=["rich_text"])

    associate_attribute_values_to_instance(
        product_with_rich_text_attr, rich_text_attribute, rich_text_value
    )

    product_with_rich_text_attr.refresh_from_db()

    product_with_rich_text_attr.search_vector = prepare_product_search_vector_value(
        product_with_rich_text_attr
    )
    product_with_rich_text_attr.save(update_fields=["search_vector"])

    variables = {"filter": {"search": search_value}, "channel": channel_USD.slug}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # then
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_with_rich_text_attr.id
    )
    assert products[0]["node"]["name"] == product_with_rich_text_attr.name


@pytest.mark.parametrize("search_value", ["13456", "13456 cm"])
def test_products_query_with_filter_search_by_numeric_attribute_value(
    search_value,
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
    numeric_attribute,
):
    # given
    product_with_numeric_attr = product_list[1]

    product_type = product_with_numeric_attr.product_type
    product_type.product_attributes.add(numeric_attribute)

    numeric_attribute.unit = MeasurementUnits.CM
    numeric_attribute.save(update_fields=["unit"])

    numeric_attr_value = numeric_attribute.values.first()
    numeric_attr_value.name = "13456"
    numeric_attr_value.save(update_fields=["name"])

    associate_attribute_values_to_instance(
        product_with_numeric_attr, numeric_attribute, numeric_attr_value
    )

    product_with_numeric_attr.refresh_from_db()

    product_with_numeric_attr.search_vector = prepare_product_search_vector_value(
        product_with_numeric_attr
    )
    product_with_numeric_attr.save(update_fields=["search_vector"])

    variables = {"filter": {"search": search_value}, "channel": channel_USD.slug}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # then
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_with_numeric_attr.id
    )
    assert products[0]["node"]["name"] == product_with_numeric_attr.name


def test_products_query_with_filter_search_by_numeric_attribute_value_without_unit(
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
    numeric_attribute_without_unit,
):
    # given
    numeric_attribute = numeric_attribute_without_unit
    product_with_numeric_attr = product_list[1]

    product_type = product_with_numeric_attr.product_type
    product_type.product_attributes.add(numeric_attribute)

    numeric_attr_value = numeric_attribute.values.first()
    numeric_attr_value.name = "13456"
    numeric_attr_value.save(update_fields=["name"])

    associate_attribute_values_to_instance(
        product_with_numeric_attr, numeric_attribute, numeric_attr_value
    )

    product_with_numeric_attr.refresh_from_db()

    product_with_numeric_attr.search_vector = prepare_product_search_vector_value(
        product_with_numeric_attr
    )
    product_with_numeric_attr.save(update_fields=["search_vector"])

    variables = {"filter": {"search": "13456"}, "channel": channel_USD.slug}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # then
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_with_numeric_attr.id
    )
    assert products[0]["node"]["name"] == product_with_numeric_attr.name


@pytest.mark.parametrize("search_value", ["2020", "2020-10-10"])
def test_products_query_with_filter_search_by_date_attribute_value(
    search_value,
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
    date_attribute,
):
    # given
    product_with_date_attr = product_list[2]

    product_type = product_with_date_attr.product_type
    product_type.product_attributes.add(date_attribute)

    date_attr_value = date_attribute.values.first()
    date_attr_value.date_time = datetime(2020, 10, 10, tzinfo=pytz.utc)
    date_attr_value.save(update_fields=["date_time"])

    associate_attribute_values_to_instance(
        product_with_date_attr, date_attribute, date_attr_value
    )

    product_with_date_attr.refresh_from_db()

    product_with_date_attr.search_vector = prepare_product_search_vector_value(
        product_with_date_attr
    )
    product_with_date_attr.save(update_fields=["search_vector"])

    variables = {"filter": {"search": search_value}, "channel": channel_USD.slug}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # then
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_with_date_attr.id
    )
    assert products[0]["node"]["name"] == product_with_date_attr.name


@pytest.mark.parametrize("search_value", ["2020", "2020-10-10", "22:20"])
def test_products_query_with_filter_search_by_date_time_attribute_value(
    search_value,
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
    date_time_attribute,
):
    # given
    product_with_date_time_attr = product_list[0]

    product_type = product_with_date_time_attr.product_type
    product_type.product_attributes.add(date_time_attribute)

    date_time_attr_value = date_time_attribute.values.first()
    date_time_attr_value.date_time = datetime(2020, 10, 10, 22, 20, tzinfo=pytz.utc)
    date_time_attr_value.save(update_fields=["date_time"])

    associate_attribute_values_to_instance(
        product_with_date_time_attr, date_time_attribute, date_time_attr_value
    )

    product_with_date_time_attr.refresh_from_db()

    product_with_date_time_attr.search_vector = prepare_product_search_vector_value(
        product_with_date_time_attr
    )
    product_with_date_time_attr.save(update_fields=["search_vector"])

    variables = {"filter": {"search": search_value}, "channel": channel_USD.slug}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # then
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_with_date_time_attr.id
    )
    assert products[0]["node"]["name"] == product_with_date_time_attr.name


def test_products_query_with_is_published_filter_variants_without_prices(
    query_products_with_filter,
    staff_api_client,
    variant,
    permission_manage_products,
    channel_USD,
):
    ProductVariantChannelListing.objects.filter(
        variant__product=variant.product
    ).update(price_amount=None)

    variables = {"channel": channel_USD.slug, "filter": {"isPublished": True}}
    response = staff_api_client.post_graphql(
        query_products_with_filter,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 0


def test_products_query_with_is_published_filter_one_variant_without_price(
    query_products_with_filter,
    staff_api_client,
    variant,
    permission_manage_products,
    channel_USD,
):
    variant.channel_listings.update(price_amount=None)

    variables = {"channel": channel_USD.slug, "filter": {"isPublished": True}}
    response = staff_api_client.post_graphql(
        query_products_with_filter,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1


def test_products_query_with_filter_stock_availability_as_staff(
    query_products_with_filter,
    staff_api_client,
    product_list,
    order_line,
    permission_manage_products,
    channel_USD,
):

    for product in product_list:
        stock = product.variants.first().stocks.first()
        Allocation.objects.create(
            order_line=order_line, stock=stock, quantity_allocated=stock.quantity
        )
    product = product_list[0]
    product.variants.first().channel_listings.filter(channel=channel_USD).update(
        price_amount=None
    )
    variables = {
        "filter": {"stockAvailability": "OUT_OF_STOCK"},
        "channel": channel_USD.slug,
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 3


def test_products_query_with_filter_stock_availability_as_user(
    query_products_with_filter,
    user_api_client,
    product_list,
    order_line,
    permission_manage_products,
    channel_USD,
):

    for product in product_list:
        stock = product.variants.first().stocks.first()
        Allocation.objects.create(
            order_line=order_line, stock=stock, quantity_allocated=stock.quantity
        )
    product = product_list[0]
    product.variants.first().channel_listings.filter(channel=channel_USD).update(
        price_amount=None
    )
    variables = {
        "filter": {"stockAvailability": "OUT_OF_STOCK"},
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    product_id = graphene.Node.to_global_id("Product", product_list[1].id)
    second_product_id = graphene.Node.to_global_id("Product", product_list[2].id)

    products = content["data"]["products"]["edges"]

    assert len(products) == 2
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product_list[1].name
    assert products[1]["node"]["id"] == second_product_id
    assert products[1]["node"]["name"] == product_list[2].name


def test_products_query_with_filter_stock_availability_channel_without_shipping_zones(
    query_products_with_filter,
    staff_api_client,
    product,
    permission_manage_products,
    channel_USD,
):
    channel_USD.shipping_zones.clear()
    variables = {
        "filter": {"stockAvailability": "OUT_OF_STOCK"},
        "channel": channel_USD.slug,
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    product_id = graphene.Node.to_global_id("Product", product.id)

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id


@pytest.mark.parametrize(
    "quantity_input, warehouse_indexes, count, indexes_of_products_in_result",
    [
        ({"lte": "80", "gte": "20"}, [1, 2], 1, [1]),
        ({"lte": "120", "gte": "40"}, [1, 2], 1, [0]),
        ({"gte": "10"}, [1], 1, [1]),
        ({"gte": "110"}, [2], 0, []),
        (None, [1], 1, [1]),
        (None, [2], 2, [0, 1]),
        ({"lte": "210", "gte": "70"}, [], 1, [0]),
        ({"lte": "90"}, [], 1, [1]),
        ({"lte": "90", "gte": "75"}, [], 0, []),
    ],
)
def test_products_query_with_filter_stocks(
    quantity_input,
    warehouse_indexes,
    count,
    indexes_of_products_in_result,
    query_products_with_filter,
    staff_api_client,
    product_with_single_variant,
    product_with_two_variants,
    warehouse,
    channel_USD,
):
    product1 = product_with_single_variant
    product2 = product_with_two_variants
    products = [product1, product2]

    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    third_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    third_warehouse.slug = "third warehouse"
    third_warehouse.pk = None
    third_warehouse.save()

    warehouses = [warehouse, second_warehouse, third_warehouse]
    warehouse_pks = [
        graphene.Node.to_global_id("Warehouse", warehouses[index].pk)
        for index in warehouse_indexes
    ]

    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=third_warehouse,
                product_variant=product1.variants.first(),
                quantity=100,
            ),
            Stock(
                warehouse=second_warehouse,
                product_variant=product2.variants.first(),
                quantity=10,
            ),
            Stock(
                warehouse=third_warehouse,
                product_variant=product2.variants.first(),
                quantity=25,
            ),
            Stock(
                warehouse=third_warehouse,
                product_variant=product2.variants.last(),
                quantity=30,
            ),
        ]
    )

    variables = {
        "filter": {
            "stocks": {"quantity": quantity_input, "warehouseIds": warehouse_pks}
        },
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        query_products_with_filter, variables, check_no_permissions=False
    )
    content = get_graphql_content(response)
    products_data = content["data"]["products"]["edges"]

    product_ids = {
        graphene.Node.to_global_id("Product", products[index].pk)
        for index in indexes_of_products_in_result
    }

    assert len(products_data) == count
    assert {node["node"]["id"] for node in products_data} == product_ids


def test_query_products_with_filter_ids(
    api_client, product_list, query_products_with_filter, channel_USD
):
    # given
    product_ids = [
        graphene.Node.to_global_id("Product", product.id) for product in product_list
    ][:2]
    variables = {
        "filter": {"ids": product_ids},
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products_data = content["data"]["products"]["edges"]

    assert len(products_data) == 2
    assert [node["node"]["id"] for node in products_data] == product_ids


def test_products_query_with_filter_has_preordered_variants_false(
    query_products_with_filter,
    staff_api_client,
    preorder_variant_global_threshold,
    product_without_shipping,
    permission_manage_products,
):
    product = product_without_shipping
    variables = {"filter": {"hasPreorderedVariants": False}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    product_id = graphene.Node.to_global_id("Product", product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product.name


def test_products_query_with_filter_has_preordered_variants_true(
    query_products_with_filter,
    staff_api_client,
    preorder_variant_global_threshold,
    product_without_shipping,
    permission_manage_products,
):
    product = preorder_variant_global_threshold.product
    variables = {"filter": {"hasPreorderedVariants": True}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    product_id = graphene.Node.to_global_id("Product", product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product.name


def test_products_query_with_filter_has_preordered_variants_before_end_date(
    query_products_with_filter,
    staff_api_client,
    preorder_variant_global_threshold,
    permission_manage_products,
):
    variant = preorder_variant_global_threshold
    variant.preorder_end_date = timezone.now() + timedelta(days=3)
    variant.save(update_fields=["preorder_end_date"])

    product = preorder_variant_global_threshold.product
    variables = {"filter": {"hasPreorderedVariants": True}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    product_id = graphene.Node.to_global_id("Product", product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product.name


def test_products_query_with_filter_has_preordered_variants_after_end_date(
    query_products_with_filter,
    staff_api_client,
    preorder_variant_global_threshold,
    permission_manage_products,
):
    variant = preorder_variant_global_threshold
    variant.preorder_end_date = timezone.now() - timedelta(days=3)
    variant.save(update_fields=["preorder_end_date"])

    variables = {"filter": {"hasPreorderedVariants": True}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 0


QUERY_PRODUCT_MEDIA_BY_ID = """
    query productMediaById($mediaId: ID!, $productId: ID!, $channel: String) {
        product(id: $productId, channel: $channel) {
            mediaById(id: $mediaId) {
                id
                url(size: 200)
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
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["product"]["mediaById"] is None


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
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
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
        product, product_type_page_reference_attribute, attr_value_2, attr_value_1
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


def test_filter_products_by_wrong_attributes(user_api_client, product, channel_USD):
    product_attr = product.product_type.product_attributes.get(slug="color")
    attr_value = product.product_type.variant_attributes.get(slug="size").values.first()
    query = """
    query ($channel: String, $filter: ProductFilterInput){
        products(
            filter: $filter,
            first: 1,
            channel: $channel
        ) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """

    variables = {
        "channel": channel_USD.slug,
        "filter": {
            "attributes": [{"slug": product_attr.slug, "values": [attr_value.slug]}]
        },
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert products == []


def test_filter_products_with_unavailable_variants_attributes_as_user(
    user_api_client, product_list, channel_USD
):
    product_attr = product_list[0].product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    query = """
    query Products($attributesFilter: [AttributeInput!], $channel: String) {
        products(
            first: 5,
            filter: {attributes: $attributesFilter},
            channel: $channel
        ) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    second_product_id = graphene.Node.to_global_id("Product", product_list[1].id)
    third_product_id = graphene.Node.to_global_id("Product", product_list[2].id)
    variables = {
        "channel": channel_USD.slug,
        "attributesFilter": [
            {"slug": f"{product_attr.slug}", "values": [f"{attr_value.slug}"]}
        ],
    }
    product_list[0].variants.first().channel_listings.filter(
        channel=channel_USD
    ).update(price_amount=None)

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 2
    assert products[0]["node"]["id"] == second_product_id
    assert products[1]["node"]["id"] == third_product_id


def test_filter_products_with_unavailable_variants_attributes_as_staff(
    staff_api_client, product_list, channel_USD, permission_manage_products
):
    product_attr = product_list[0].product_type.product_attributes.first()
    attr_value = product_attr.values.first()
    staff_api_client.user.user_permissions.add(permission_manage_products)

    query = """
    query Products($attributesFilter: [AttributeInput!], $channel: String) {
        products(
            first: 5,
            filter: {attributes: $attributesFilter},
            channel: $channel
        ) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """

    variables = {
        "channel": channel_USD.slug,
        "attributesFilter": [
            {"slug": f"{product_attr.slug}", "values": [f"{attr_value.slug}"]}
        ],
    }
    product_list[0].variants.first().channel_listings.filter(
        channel=channel_USD
    ).update(price_amount=None)

    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 3


SORT_PRODUCTS_QUERY = """
    query ($channel:String) {
        products (
            sortBy: %(sort_by_product_order)s, first: 3, channel: $channel
        ) {
            edges {
                node {
                    name
                    productType{
                        name
                    }
                    pricing {
                        priceRangeUndiscounted {
                            start {
                                gross {
                                    amount
                                }
                            }
                        }
                        priceRange {
                            start {
                                gross {
                                    amount
                                }
                            }
                        }
                    }
                    updatedAt
                }
            }
        }
    }
"""


def test_sort_products(user_api_client, product, channel_USD):
    product.updated_at = datetime.utcnow()
    product.save()

    product.pk = None
    product.slug = "second-product"
    product.updated_at = datetime.utcnow()
    product.save()
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant = ProductVariant.objects.create(product=product, sku="1234")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(20),
        cost_price_amount=Decimal(2),
        currency=channel_USD.currency_code,
    )
    product.pk = None
    product.slug = "third-product"
    product.updated_at = datetime.utcnow()
    product.save()
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant_second = ProductVariant.objects.create(product=product, sku="12345")
    ProductVariantChannelListing.objects.create(
        variant=variant_second,
        channel=channel_USD,
        currency=channel_USD.currency_code,
    )
    variables = {"channel": channel_USD.slug}
    query = SORT_PRODUCTS_QUERY

    # Test sorting by PRICE, ascending
    sort_by = "{field: PRICE, direction: ASC}"
    asc_price_query = query % {"sort_by_product_order": sort_by}
    response = user_api_client.post_graphql(asc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    assert len(edges) == 2
    price1 = edges[0]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert price1 < price2

    # Test sorting by PRICE, descending
    sort_by = "{field: PRICE, direction:DESC}"
    desc_price_query = query % {"sort_by_product_order": sort_by}
    response = user_api_client.post_graphql(desc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert price1 > price2

    # Test sorting by MINIMAL_PRICE, ascending
    sort_by = "{field: MINIMAL_PRICE, direction:ASC}"
    asc_price_query = query % {"sort_by_product_order": sort_by}
    response = user_api_client.post_graphql(asc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    price2 = edges[1]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    assert price1 < price2

    # Test sorting by MINIMAL_PRICE, descending
    sort_by = "{field: MINIMAL_PRICE, direction:DESC}"
    desc_price_query = query % {"sort_by_product_order": sort_by}
    response = user_api_client.post_graphql(desc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    price2 = edges[1]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    assert price1 > price2

    # Test sorting by DATE, ascending
    asc_date_query = query % {"sort_by_product_order": "{field: DATE, direction:ASC}"}
    response = user_api_client.post_graphql(asc_date_query, variables)
    content = get_graphql_content(response)
    date_0 = content["data"]["products"]["edges"][0]["node"]["updatedAt"]
    date_1 = content["data"]["products"]["edges"][1]["node"]["updatedAt"]
    assert parse_datetime(date_0) < parse_datetime(date_1)

    # Test sorting by DATE, descending
    desc_date_query = query % {"sort_by_product_order": "{field: DATE, direction:DESC}"}
    response = user_api_client.post_graphql(desc_date_query, variables)
    content = get_graphql_content(response)
    date_0 = content["data"]["products"]["edges"][0]["node"]["updatedAt"]
    date_1 = content["data"]["products"]["edges"][1]["node"]["updatedAt"]
    assert parse_datetime(date_0) > parse_datetime(date_1)


def test_sort_products_by_price_as_staff(
    staff_api_client, product, channel_USD, permission_manage_products
):
    product.updated_at = datetime.utcnow()
    product.save()
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product.pk = None
    product.slug = "second-product"
    product.updated_at = datetime.utcnow()
    product.save()
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant = ProductVariant.objects.create(product=product, sku="1234")
    ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(20),
        cost_price_amount=Decimal(2),
        currency=channel_USD.currency_code,
    )
    product.pk = None
    product.slug = "third-product"
    product.updated_at = datetime.utcnow()
    product.save()
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant_second = ProductVariant.objects.create(product=product, sku="12345")
    ProductVariantChannelListing.objects.create(
        variant=variant_second,
        channel=channel_USD,
        currency=channel_USD.currency_code,
    )
    variables = {"channel": channel_USD.slug}
    query = SORT_PRODUCTS_QUERY

    # Test sorting by PRICE, ascending
    sort_by = "{field: PRICE, direction: ASC}"
    asc_price_query = query % {"sort_by_product_order": sort_by}
    response = staff_api_client.post_graphql(asc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    assert len(edges) == 3
    price1 = edges[0]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert edges[2]["node"]["pricing"] is None
    assert price1 < price2

    # Test sorting by PRICE, descending
    sort_by = "{field: PRICE, direction:DESC}"
    desc_price_query = query % {"sort_by_product_order": sort_by}
    response = staff_api_client.post_graphql(desc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[2]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert edges[0]["node"]["pricing"] is None
    assert price1 > price2


def test_sort_products_product_type_name(
    user_api_client, product, product_with_default_variant, channel_USD
):
    variables = {"channel": channel_USD.slug}

    # Test sorting by TYPE, ascending
    asc_published_query = SORT_PRODUCTS_QUERY % {
        "sort_by_product_order": "{field: TYPE, direction:ASC}"
    }
    response = user_api_client.post_graphql(asc_published_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    product_type_name_0 = edges[0]["node"]["productType"]["name"]
    product_type_name_1 = edges[1]["node"]["productType"]["name"]
    assert product_type_name_0 < product_type_name_1

    # Test sorting by PUBLISHED, descending
    desc_published_query = SORT_PRODUCTS_QUERY % {
        "sort_by_product_order": "{field: TYPE, direction:DESC}"
    }
    response = user_api_client.post_graphql(desc_published_query, variables)
    content = get_graphql_content(response)
    product_type_name_0 = edges[0]["node"]["productType"]["name"]
    product_type_name_1 = edges[1]["node"]["productType"]["name"]
    assert product_type_name_0 < product_type_name_1


QUERY_PRODUCT_TYPE = """
    query ($id: ID!){
        productType(
            id: $id,
        ) {
            id
            name
            weight {
                unit
                value
            }
        }
    }
    """


def test_product_type_query_by_id_weight_returned_in_default_unit(
    user_api_client, product_type, site_settings
):
    # given
    product_type.weight = Weight(kg=10)
    product_type.save(update_fields=["weight"])

    site_settings.default_weight_unit = WeightUnits.OZ
    site_settings.save(update_fields=["default_weight_unit"])

    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_PRODUCT_TYPE, variables=variables)

    # then
    content = get_graphql_content(response)
    product_data = content["data"]["productType"]
    assert product_data is not None
    assert product_data["name"] == product_type.name
    assert product_data["weight"]["value"] == 352.73999999999995
    assert product_data["weight"]["unit"] == WeightUnits.OZ.upper()


CREATE_PRODUCT_MUTATION = """
       mutation createProduct(
           $input: ProductCreateInput!
       ) {
                productCreate(
                    input: $input) {
                        product {
                            id
                            category {
                                name
                            }
                            description
                            chargeTaxes
                            taxType {
                                taxCode
                                description
                            }
                            name
                            slug
                            rating
                            productType {
                                name
                            }
                            attributes {
                                attribute {
                                    slug
                                }
                                values {
                                    slug
                                    name
                                    reference
                                    richText
                                    boolean
                                    dateTime
                                    date
                                    file {
                                        url
                                        contentType
                                    }
                                }
                            }
                          }
                          errors {
                            field
                            code
                            message
                            attributes
                          }
                        }
                      }
"""


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_created")
def test_create_product(
    created_webhook_mock,
    updated_webhook_mock,
    staff_api_client,
    product_type,
    category,
    size_attribute,
    description_json,
    permission_manage_products,
    monkeypatch,
):
    query = CREATE_PRODUCT_MUTATION

    description_json = json.dumps(description_json)

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"
    product_charge_taxes = True
    product_tax_rate = "STANDARD"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    # Default attribute defined in product_type fixture
    color_attr = product_type.product_attributes.get(name="Color")
    color_value_slug = color_attr.values.first().slug
    color_attr_id = graphene.Node.to_global_id("Attribute", color_attr.id)

    # Add second attribute
    product_type.product_attributes.add(size_attribute)
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    non_existent_attr_value = "The cake is a lie"

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "description": description_json,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
            "attributes": [
                {"id": color_attr_id, "values": [color_value_slug]},
                {"id": size_attr_id, "values": [non_existent_attr_value]},
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["description"] == description_json
    assert data["product"]["chargeTaxes"] == product_charge_taxes
    assert data["product"]["taxType"]["taxCode"] == product_tax_rate
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    values = (
        data["product"]["attributes"][0]["values"][0]["slug"],
        data["product"]["attributes"][1]["values"][0]["slug"],
    )
    assert slugify(non_existent_attr_value) in values
    assert color_value_slug in values

    product = Product.objects.first()
    created_webhook_mock.assert_called_once_with(product)
    updated_webhook_mock.assert_not_called()


def test_create_product_description_plaintext(
    staff_api_client,
    product_type,
    category,
    size_attribute,
    permission_manage_products,
    monkeypatch,
):
    query = CREATE_PRODUCT_MUTATION
    description = "some test description"
    description_json = dummy_editorjs(description, json_format=True)

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"
    product_charge_taxes = True
    product_tax_rate = "STANDARD"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "description": description_json,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert not data["errors"]

    product = Product.objects.all().first()
    assert product.description_plaintext == description


def test_create_product_with_rich_text_attribute(
    staff_api_client,
    product_type,
    category,
    rich_text_attribute,
    color_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(rich_text_attribute)
    rich_text_attribute_id = graphene.Node.to_global_id(
        "Attribute", rich_text_attribute.id
    )
    rich_text_value = dummy_editorjs("test product" * 5)
    rich_text = json.dumps(rich_text_value)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [
                {
                    "id": rich_text_attribute_id,
                    "richText": rich_text,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])

    expected_attributes_data = [
        {"attribute": {"slug": "color"}, "values": []},
        {
            "attribute": {"slug": "text"},
            "values": [
                {
                    "slug": f"{product_id}_{rich_text_attribute.id}",
                    "name": (
                        "test producttest producttest producttest producttest product"
                    ),
                    "reference": None,
                    "richText": rich_text,
                    "file": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
    ]

    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data


def test_create_product_no_value_for_rich_text_attribute(
    staff_api_client,
    product_type,
    rich_text_attribute,
    permission_manage_products,
):
    """Ensure mutation not fail when as attributes input only rich text attribute id
    is provided."""
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(rich_text_attribute)
    rich_text_attribute_id = graphene.Node.to_global_id(
        "Attribute", rich_text_attribute.id
    )

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": rich_text_attribute_id,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    expected_attributes_data = {
        "attribute": {"slug": rich_text_attribute.slug},
        "values": [],
    }
    assert expected_attributes_data in data["product"]["attributes"]


@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
def test_create_product_with_date_time_attribute(
    staff_api_client,
    product_type,
    date_time_attribute,
    color_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(date_time_attribute)
    date_time_attribute_id = graphene.Node.to_global_id(
        "Attribute", date_time_attribute.id
    )
    value = datetime.now(tz=pytz.utc)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": date_time_attribute_id,
                    "dateTime": value,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])

    expected_attributes_data = {
        "attribute": {"slug": "release-date-time"},
        "values": [
            {
                "slug": f"{product_id}_{date_time_attribute.id}",
                "name": str(value),
                "reference": None,
                "richText": None,
                "boolean": None,
                "file": None,
                "date": None,
                "dateTime": str(value.isoformat()),
            }
        ],
    }

    assert expected_attributes_data in data["product"]["attributes"]


@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
def test_create_product_with_date_attribute(
    staff_api_client,
    product_type,
    date_attribute,
    color_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(date_attribute)
    date_attribute_id = graphene.Node.to_global_id("Attribute", date_attribute.id)
    value = datetime.now(tz=pytz.utc).date()

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": date_attribute_id,
                    "date": value,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])

    expected_attributes_data = {
        "attribute": {"slug": "release-date"},
        "values": [
            {
                "slug": f"{product_id}_{date_attribute.id}",
                "name": str(value),
                "reference": None,
                "richText": None,
                "boolean": None,
                "file": None,
                "date": str(value),
                "dateTime": None,
            }
        ],
    }

    assert expected_attributes_data in data["product"]["attributes"]


def test_create_product_no_value_for_date_attribute(
    staff_api_client,
    product_type,
    date_attribute,
    permission_manage_products,
):
    """Ensure mutation not fail when as attributes input only date attribute id
    is provided."""
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(date_attribute)
    date_attribute_id = graphene.Node.to_global_id("Attribute", date_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": date_attribute_id,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    expected_attributes_data = {
        "attribute": {"slug": date_attribute.slug},
        "values": [],
    }
    assert expected_attributes_data in data["product"]["attributes"]


def test_create_product_with_boolean_attribute(
    staff_api_client,
    product_type,
    category,
    boolean_attribute,
    permission_manage_products,
    product,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(boolean_attribute)
    boolean_attribute_id = graphene.Node.to_global_id("Attribute", boolean_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "attributes": [
                {
                    "id": boolean_attribute_id,
                    "boolean": False,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name

    expected_attributes_data = {
        "attribute": {"slug": "boolean"},
        "values": [
            {
                "slug": f"{boolean_attribute.id}_false",
                "name": "Boolean: No",
                "reference": None,
                "richText": None,
                "boolean": False,
                "date": None,
                "dateTime": None,
                "file": None,
            }
        ],
    }
    assert expected_attributes_data in data["product"]["attributes"]


def test_create_product_no_value_for_boolean_attribute(
    staff_api_client,
    product_type,
    boolean_attribute,
    permission_manage_products,
):
    """Ensure mutation not fail when as attributes input only boolean attribute id
    is provided."""
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"

    # Add second attribute
    product_type.product_attributes.add(boolean_attribute)
    boolean_attribute_id = graphene.Node.to_global_id("Attribute", boolean_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "attributes": [
                {
                    "id": boolean_attribute_id,
                }
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["productType"]["name"] == product_type.name
    expected_attributes_data = {
        "attribute": {"slug": boolean_attribute.slug},
        "values": [],
    }
    assert expected_attributes_data in data["product"]["attributes"]


SEARCH_PRODUCTS_QUERY = """
    query Products(
        $filters: ProductFilterInput,
        $sortBy: ProductOrder,
        $channel: String,
        $after: String,
    ) {
        products(
            first: 5,
            filter: $filters,
            sortBy: $sortBy,
            channel: $channel,
            after: $after,
        ) {
            edges {
                node {
                    id
                    name
                }
                cursor
            }
        }
    }
"""


def test_search_product_by_description(user_api_client, product_list, channel_USD):

    variables = {"filters": {"search": "big"}, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)
    assert len(content["data"]["products"]["edges"]) == 2

    variables = {"filters": {"search": "small"}, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)

    assert len(content["data"]["products"]["edges"]) == 1


def test_search_product_by_description_and_name(
    user_api_client, product_list, product, channel_USD, category, product_type
):
    product.description_plaintext = "new big new product"

    product_2 = product_list[1]
    product_2.name = "new product"
    product_1 = product_list[0]
    product_1.description_plaintext = "some new product"
    product_3 = product_list[2]
    product_3.description_plaintext = "desc without searched word"

    product_list.append(product)
    for prod in product_list:
        prod.search_vector = prepare_product_search_vector_value(prod)

    Product.objects.bulk_update(
        product_list,
        ["search_document", "search_vector", "name", "description_plaintext"],
    )

    variables = {
        "filters": {
            "search": "new",
        },
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["products"]["edges"]

    assert len(data) == 3
    assert {node["node"]["name"] for node in data} == {
        product.name,
        product_1.name,
        product_2.name,
    }


def test_sort_product_by_rank_without_search(
    user_api_client, product_list, channel_USD
):
    variables = {
        "sortBy": {"field": "RANK", "direction": "DESC"},
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert (
        content["errors"][0]["message"]
        == "Sorting by RANK is available only when using a search filter."
    )


def test_search_product_by_description_and_name_without_sort_by(
    user_api_client, product_list, product, channel_USD
):
    product.description_plaintext = "new big new product"

    product_2 = product_list[1]
    product_2.name = "new product"
    product_1 = product_list[0]
    product_1.description_plaintext = "some new product"

    product_list.append(product)
    for prod in product_list:
        prod.search_vector = prepare_product_search_vector_value(prod)

    Product.objects.bulk_update(
        product_list,
        ["search_vector", "name", "description_plaintext"],
    )

    variables = {
        "filters": {
            "search": "new",
        },
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["products"]["edges"]

    assert len(data) == 3
    assert {node["node"]["name"] for node in data} == {
        product.name,
        product_1.name,
        product_2.name,
    }


def test_search_product_by_description_and_name_and_use_cursor(
    user_api_client, product_list, product, channel_USD, category, product_type
):
    product.description_plaintext = "new big new product"

    product_2 = product_list[1]
    product_2.name = "new product"
    product_1 = product_list[0]
    product_1.description_plaintext = "some new product"

    product_list.append(product)
    for prod in product_list:
        prod.search_vector = prepare_product_search_vector_value(prod)

    Product.objects.bulk_update(
        product_list,
        ["search_vector", "name", "description_plaintext"],
    )

    variables = {
        "filters": {
            "search": "new",
        },
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)
    cursor = content["data"]["products"]["edges"][0]["cursor"]

    variables = {
        "filters": {
            "search": "new",
        },
        "after": cursor,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(SEARCH_PRODUCTS_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["products"]["edges"]

    assert len(data) == 2


@freeze_time("2020-03-18 12:00:00")
def test_create_product_with_rating(
    staff_api_client,
    product_type,
    category,
    permission_manage_products,
    settings,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"
    expected_rating = 4.57

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "rating": expected_rating,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["rating"] == expected_rating
    assert Product.objects.get().rating == expected_rating


def test_create_product_with_file_attribute(
    staff_api_client,
    product_type,
    category,
    file_attribute,
    color_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = file_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)
    existing_value = file_attribute.values.first()

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": file_attr_id, "file": existing_value.file_url}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 2
    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {
            "attribute": {"slug": file_attribute.slug},
            "values": [
                {
                    "name": existing_value.name,
                    "slug": f"{existing_value.slug}-2",
                    "file": {
                        "url": f"http://testserver/media/{existing_value.file_url}",
                        "contentType": None,
                    },
                    "reference": None,
                    "richText": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count + 1


def test_create_product_with_page_reference_attribute(
    staff_api_client,
    product_type,
    category,
    color_attribute,
    product_type_page_reference_attribute,
    permission_manage_products,
    page,
):
    query = CREATE_PRODUCT_MUTATION

    values_count = product_type_page_reference_attribute.values.count()

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_page_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )
    reference = graphene.Node.to_global_id("Page", page.pk)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": [reference]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])
    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {
            "attribute": {"slug": product_type_page_reference_attribute.slug},
            "values": [
                {
                    "slug": f"{product_id}_{page.id}",
                    "name": page.title,
                    "file": None,
                    "richText": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                    "reference": reference,
                }
            ],
        },
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count + 1


def test_create_product_with_product_reference_attribute(
    staff_api_client,
    product_type,
    category,
    color_attribute,
    product_type_product_reference_attribute,
    permission_manage_products,
    product,
):
    query = CREATE_PRODUCT_MUTATION

    values_count = product_type_product_reference_attribute.values.count()

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_product_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.id
    )
    reference = graphene.Node.to_global_id("Product", product.pk)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": [reference]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])
    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {
            "attribute": {"slug": product_type_product_reference_attribute.slug},
            "values": [
                {
                    "slug": f"{product_id}_{product.id}",
                    "name": product.name,
                    "file": None,
                    "richText": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                    "reference": reference,
                }
            ],
        },
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count + 1


def test_create_product_with_product_reference_attribute_values_saved_in_order(
    staff_api_client,
    product_type,
    category,
    color_attribute,
    product_type_product_reference_attribute,
    permission_manage_products,
    product_list,
):
    query = CREATE_PRODUCT_MUTATION

    values_count = product_type_product_reference_attribute.values.count()

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.set([product_type_product_reference_attribute])
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.id
    )
    reference_1 = graphene.Node.to_global_id("Product", product_list[0].pk)
    reference_2 = graphene.Node.to_global_id("Product", product_list[1].pk)
    reference_3 = graphene.Node.to_global_id("Product", product_list[2].pk)

    # test creating root product
    reference_ids = [reference_3, reference_1, reference_2]
    reference_instances = [product_list[2], product_list[0], product_list[1]]
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": reference_ids}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    _, product_id = graphene.Node.from_global_id(data["product"]["id"])
    expected_values = [
        {
            "slug": f"{product_id}_{product.id}",
            "name": product.name,
            "file": None,
            "richText": None,
            "boolean": None,
            "date": None,
            "dateTime": None,
            "reference": reference,
        }
        for product, reference in zip(reference_instances, reference_ids)
    ]

    assert len(data["product"]["attributes"]) == 1
    attribute_data = data["product"]["attributes"][0]
    assert (
        attribute_data["attribute"]["slug"]
        == product_type_product_reference_attribute.slug
    )
    assert len(attribute_data["values"]) == 3
    assert attribute_data["values"] == expected_values

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count + 3


def test_create_product_with_page_reference_attribute_and_invalid_product_one(
    staff_api_client,
    product_type,
    product,
    category,
    color_attribute,
    product_type_page_reference_attribute,
    product_type_product_reference_attribute,
    permission_manage_products,
    page,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_page_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )

    reference = graphene.Node.to_global_id("Page", page.pk)
    invalid_reference = graphene.Node.to_global_id("Product", product.pk)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [
                {"id": reference_attr_id, "references": [reference]},
                {"id": reference_attr_id, "references": [invalid_reference]},
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"][0]["message"] == "Invalid reference type."
    assert data["errors"][0]["field"] == "attributes"
    assert data["errors"][0]["code"] == ProductErrorCode.INVALID.name


def test_create_product_with_file_attribute_new_attribute_value(
    staff_api_client,
    product_type,
    category,
    file_attribute,
    color_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = file_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)
    non_existing_value = "new_test.jpg"

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": file_attr_id, "file": non_existing_value}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 2
    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {
            "attribute": {"slug": file_attribute.slug},
            "values": [
                {
                    "name": non_existing_value,
                    "slug": slugify(non_existing_value, allow_unicode=True),
                    "reference": None,
                    "richText": None,
                    "boolean": None,
                    "date": None,
                    "dateTime": None,
                    "file": {
                        "url": "http://testserver/media/" + non_existing_value,
                        "contentType": None,
                    },
                }
            ],
        },
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count + 1


def test_create_product_with_file_attribute_not_required_no_file_url_given(
    staff_api_client,
    product_type,
    category,
    file_attribute,
    color_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    file_attribute.value_required = False
    file_attribute.save(update_fields=["value_required"])

    # Add second attribute
    product_type.product_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": file_attr_id, "values": ["test.txt"]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 2
    expected_attributes_data = [
        {"attribute": {"slug": color_attribute.slug}, "values": []},
        {"attribute": {"slug": file_attribute.slug}, "values": []},
    ]
    for attr_data in data["product"]["attributes"]:
        assert attr_data in expected_attributes_data

    file_attribute.refresh_from_db()


def test_create_product_with_file_attribute_required_no_file_url_given(
    staff_api_client,
    product_type,
    category,
    file_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    file_attribute.value_required = True
    file_attribute.save(update_fields=["value_required"])

    # Add second attribute
    product_type.product_attributes.add(file_attribute)
    file_attr_id = graphene.Node.to_global_id("Attribute", file_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": file_attr_id, "values": ["test.txt"]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    errors = data["errors"]
    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id("Attribute", file_attribute.pk)
    ]


def test_create_product_with_page_reference_attribute_required_no_references(
    staff_api_client,
    product_type,
    category,
    product_type_page_reference_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_page_reference_attribute.value_required = True
    product_type_page_reference_attribute.save(update_fields=["value_required"])

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_page_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.id
    )

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": []}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    errors = data["errors"]
    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id(
            "Attribute", product_type_page_reference_attribute.pk
        )
    ]


def test_create_product_with_product_reference_attribute_required_no_references(
    staff_api_client,
    product_type,
    category,
    product_type_product_reference_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_product_reference_attribute.value_required = True
    product_type_product_reference_attribute.save(update_fields=["value_required"])

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Add second attribute
    product_type.product_attributes.add(product_type_product_reference_attribute)
    reference_attr_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.id
    )

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": reference_attr_id, "references": []}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    errors = data["errors"]
    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id(
            "Attribute", product_type_product_reference_attribute.pk
        )
    ]


def test_create_product_no_values_given(
    staff_api_client,
    product_type,
    category,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    # Default attribute defined in product_type fixture
    color_attr = product_type.product_attributes.get(name="Color")
    color_attr_id = graphene.Node.to_global_id("Attribute", color_attr.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": color_attr_id, "file": "test.jpg"}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert data["product"]["attributes"][0]["values"] == []


@pytest.mark.parametrize(
    "value, expected_name, expected_slug",
    [(20.1, "20.1", "20_1"), (20, "20", "20"), ("1", "1", "1")],
)
def test_create_product_with_numeric_attribute_new_attribute_value(
    value,
    expected_name,
    expected_slug,
    staff_api_client,
    product_type,
    category,
    numeric_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = numeric_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.set([numeric_attribute])
    attr_id = graphene.Node.to_global_id("Attribute", numeric_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": attr_id, "values": [value]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    product_pk = graphene.Node.from_global_id(data["product"]["id"])[1]
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert (
        data["product"]["attributes"][0]["attribute"]["slug"] == numeric_attribute.slug
    )
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 1
    assert values[0]["name"] == expected_name
    assert values[0]["slug"] == f"{product_pk}_{numeric_attribute.id}"

    numeric_attribute.refresh_from_db()
    assert numeric_attribute.values.count() == values_count + 1


def test_create_product_with_numeric_attribute_existing_value(
    staff_api_client,
    product_type,
    category,
    numeric_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = numeric_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.set([numeric_attribute])
    attr_id = graphene.Node.to_global_id("Attribute", numeric_attribute.id)
    existing_value = numeric_attribute.values.first()

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": attr_id, "values": [existing_value.name]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    product_pk = graphene.Node.from_global_id(data["product"]["id"])[1]
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert (
        data["product"]["attributes"][0]["attribute"]["slug"] == numeric_attribute.slug
    )
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 1
    assert values[0]["name"] == existing_value.name
    assert values[0]["slug"] == f"{product_pk}_{numeric_attribute.id}"

    numeric_attribute.refresh_from_db()
    assert numeric_attribute.values.count() == values_count + 1


def test_create_product_with_swatch_attribute_new_attribute_value(
    staff_api_client,
    product_type,
    category,
    swatch_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = swatch_attribute.values.count()
    new_value = "Yellow"

    # Add second attribute
    product_type.product_attributes.set([swatch_attribute])
    attr_id = graphene.Node.to_global_id("Attribute", swatch_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": attr_id, "values": [new_value]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert (
        data["product"]["attributes"][0]["attribute"]["slug"] == swatch_attribute.slug
    )
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 1
    assert values[0]["name"] == new_value
    assert values[0]["slug"] == slugify(new_value)

    swatch_attribute.refresh_from_db()
    assert swatch_attribute.values.count() == values_count + 1


def test_create_product_with_swatch_attribute_existing_value(
    staff_api_client,
    product_type,
    category,
    swatch_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = swatch_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.set([swatch_attribute])
    attr_id = graphene.Node.to_global_id("Attribute", swatch_attribute.id)
    existing_value = swatch_attribute.values.first()

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": attr_id, "values": [existing_value.name]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert (
        data["product"]["attributes"][0]["attribute"]["slug"] == swatch_attribute.slug
    )
    values = data["product"]["attributes"][0]["values"]
    assert len(values) == 1
    assert values[0]["name"] == existing_value.name
    assert values[0]["slug"] == existing_value.slug

    swatch_attribute.refresh_from_db()
    assert swatch_attribute.values.count() == values_count


def test_create_product_with_numeric_attribute_not_numeric_value_given(
    staff_api_client,
    product_type,
    category,
    numeric_attribute,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    values_count = numeric_attribute.values.count()

    # Add second attribute
    product_type.product_attributes.set([numeric_attribute])
    attr_id = graphene.Node.to_global_id("Attribute", numeric_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "attributes": [{"id": attr_id, "values": ["abd"]}],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert not data["product"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "attributes"
    assert data["errors"][0]["code"] == AttributeErrorCode.INVALID.name

    numeric_attribute.refresh_from_db()
    assert numeric_attribute.values.count() == values_count


PRODUCT_VARIANT_SET_DEFAULT_MUTATION = """
    mutation Prod($productId: ID!, $variantId: ID!) {
        productVariantSetDefault(productId: $productId, variantId: $variantId) {
            product {
                defaultVariant {
                    id
                }
            }
            errors {
                code
                field
            }
        }
    }
"""


REORDER_PRODUCT_VARIANTS_MUTATION = """
    mutation ProductVariantReorder($product: ID!, $moves: [ReorderInput!]!) {
        productVariantReorder(productId: $product, moves: $moves) {
            errors {
                code
                field
            }
            product {
                id
            }
        }
    }
"""


def test_product_variant_set_default(
    staff_api_client, permission_manage_products, product_with_two_variants
):
    assert not product_with_two_variants.default_variant

    first_variant = product_with_two_variants.variants.first()
    first_variant_id = graphene.Node.to_global_id("ProductVariant", first_variant.pk)

    variables = {
        "productId": graphene.Node.to_global_id(
            "Product", product_with_two_variants.pk
        ),
        "variantId": first_variant_id,
    }

    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_SET_DEFAULT_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    product_with_two_variants.refresh_from_db()
    assert product_with_two_variants.default_variant == first_variant
    content = get_graphql_content(response)
    data = content["data"]["productVariantSetDefault"]
    assert not data["errors"]
    assert data["product"]["defaultVariant"]["id"] == first_variant_id


def test_product_variant_set_default_invalid_id(
    staff_api_client, permission_manage_products, product_with_two_variants
):
    assert not product_with_two_variants.default_variant

    first_variant = product_with_two_variants.variants.first()

    variables = {
        "productId": graphene.Node.to_global_id(
            "Product", product_with_two_variants.pk
        ),
        "variantId": graphene.Node.to_global_id("Product", first_variant.pk),
    }

    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_SET_DEFAULT_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    product_with_two_variants.refresh_from_db()
    assert not product_with_two_variants.default_variant
    content = get_graphql_content(response)
    data = content["data"]["productVariantSetDefault"]
    assert data["errors"][0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["field"] == "variantId"


def test_product_variant_set_default_not_products_variant(
    staff_api_client,
    permission_manage_products,
    product_with_two_variants,
    product_with_single_variant,
):
    assert not product_with_two_variants.default_variant

    foreign_variant = product_with_single_variant.variants.first()

    variables = {
        "productId": graphene.Node.to_global_id(
            "Product", product_with_two_variants.pk
        ),
        "variantId": graphene.Node.to_global_id("ProductVariant", foreign_variant.pk),
    }

    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_SET_DEFAULT_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    product_with_two_variants.refresh_from_db()
    assert not product_with_two_variants.default_variant
    content = get_graphql_content(response)
    data = content["data"]["productVariantSetDefault"]
    assert data["errors"][0]["code"] == ProductErrorCode.NOT_PRODUCTS_VARIANT.name
    assert data["errors"][0]["field"] == "variantId"


def test_reorder_variants(
    staff_api_client,
    product_with_two_variants,
    permission_manage_products,
):
    default_variants = product_with_two_variants.variants.all()
    new_variants = [default_variants[1], default_variants[0]]

    variables = {
        "product": graphene.Node.to_global_id("Product", product_with_two_variants.pk),
        "moves": [
            {
                "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
                "sortOrder": _order + 1,
            }
            for _order, variant in enumerate(new_variants)
        ],
    }

    response = staff_api_client.post_graphql(
        REORDER_PRODUCT_VARIANTS_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantReorder"]
    assert not data["errors"]
    product_with_two_variants.refresh_from_db()
    assert list(product_with_two_variants.variants.all()) == new_variants


def test_reorder_variants_invalid_variants(
    staff_api_client,
    product,
    product_with_two_variants,
    permission_manage_products,
):
    default_variants = product_with_two_variants.variants.all()
    new_variants = [product.variants.first(), default_variants[1]]

    variables = {
        "product": graphene.Node.to_global_id("Product", product_with_two_variants.pk),
        "moves": [
            {
                "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
                "sortOrder": _order + 1,
            }
            for _order, variant in enumerate(new_variants)
        ],
    }

    response = staff_api_client.post_graphql(
        REORDER_PRODUCT_VARIANTS_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantReorder"]
    assert data["errors"][0]["field"] == "moves"
    assert data["errors"][0]["code"] == ProductErrorCode.NOT_FOUND.name


@pytest.mark.parametrize("input_slug", ["", None])
def test_create_product_no_slug_in_input(
    staff_api_client,
    product_type,
    category,
    description_json,
    permission_manage_products,
    monkeypatch,
    input_slug,
):
    query = CREATE_PRODUCT_MUTATION

    description_json = json.dumps(description_json)

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_tax_rate = "STANDARD"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": input_slug,
            "taxCode": product_tax_rate,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == "test-name"
    assert data["product"]["taxType"]["taxCode"] == product_tax_rate
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name


def test_create_product_no_category_id(
    staff_api_client,
    product_type,
    permission_manage_products,
    monkeypatch,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"
    product_tax_rate = "STANDARD"
    input_slug = "test-slug"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "slug": input_slug,
            "taxCode": product_tax_rate,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == input_slug
    assert data["product"]["taxType"]["taxCode"] == product_tax_rate
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"] is None


def test_create_product_with_negative_weight(
    staff_api_client,
    product_type,
    category,
    description_json,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    description_json = json.dumps(description_json)

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "weight": -1,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    error = data["errors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_create_product_with_unicode_in_slug_and_name(
    staff_api_client,
    product_type,
    category,
    description_json,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    description_json = json.dumps(description_json)

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "わたし-わ にっぽん です"
    slug = "わたし-わ-にっぽん-です-2"

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": slug,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    error = data["errors"]
    assert not error
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == slug


def test_create_product_invalid_product_attributes(
    staff_api_client,
    product_type,
    category,
    size_attribute,
    weight_attribute,
    description_json,
    permission_manage_products,
    monkeypatch,
):
    query = CREATE_PRODUCT_MUTATION

    description_json = json.dumps(description_json)

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"
    product_charge_taxes = True
    product_tax_rate = "STANDARD"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    # Default attribute defined in product_type fixture
    color_attr = product_type.product_attributes.get(name="Color")
    color_value_slug = color_attr.values.first().slug
    color_attr_id = graphene.Node.to_global_id("Attribute", color_attr.id)

    # Add second attribute
    product_type.product_attributes.add(size_attribute)
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    non_existent_attr_value = "The cake is a lie"

    # Add third attribute
    product_type.product_attributes.add(weight_attribute)
    weight_attr_id = graphene.Node.to_global_id("Attribute", weight_attribute.id)

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "description": description_json,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
            "attributes": [
                {"id": color_attr_id, "values": [" "]},
                {"id": weight_attr_id, "values": ["  "]},
                {
                    "id": size_attr_id,
                    "values": [non_existent_attr_value, color_value_slug],
                },
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 2

    expected_errors = [
        {
            "attributes": [color_attr_id, weight_attr_id],
            "code": ProductErrorCode.REQUIRED.name,
            "field": "attributes",
            "message": ANY,
        },
        {
            "attributes": [size_attr_id],
            "code": ProductErrorCode.INVALID.name,
            "field": "attributes",
            "message": ANY,
        },
    ]
    for error in expected_errors:
        assert error in errors


QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS = """
    mutation createProduct(
        $productTypeId: ID!,
        $categoryId: ID!
        $name: String!)
    {
        productCreate(
            input: {
                category: $categoryId,
                productType: $productTypeId,
                name: $name,
            })
        {
            product {
                id
                name
                slug
                rating
                category {
                    name
                }
                productType {
                    name
                }
            }
            errors {
                message
                field
            }
        }
    }
    """


def test_create_product_without_variants(
    staff_api_client, product_type_without_variant, category, permission_manage_products
):
    query = QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS

    product_type = product_type_without_variant
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "test-name"

    variables = {
        "productTypeId": product_type_id,
        "categoryId": category_id,
        "name": product_name,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name


def test_product_create_without_product_type(
    staff_api_client, category, permission_manage_products
):
    query = """
    mutation createProduct($categoryId: ID!) {
        productCreate(input: {
                name: "Product",
                productType: "",
                category: $categoryId}) {
            product {
                id
            }
            errors {
                message
                field
            }
        }
    }
    """

    category_id = graphene.Node.to_global_id("Category", category.id)
    response = staff_api_client.post_graphql(
        query, {"categoryId": category_id}, permissions=[permission_manage_products]
    )
    errors = get_graphql_content(response)["data"]["productCreate"]["errors"]

    assert errors[0]["field"] == "productType"
    assert errors[0]["message"] == "This field cannot be null."


def test_product_create_with_collections_webhook(
    staff_api_client,
    permission_manage_products,
    published_collection,
    product_type,
    category,
    monkeypatch,
):
    query = """
    mutation createProduct($productTypeId: ID!, $collectionId: ID!, $categoryId: ID!) {
        productCreate(input: {
                name: "Product",
                productType: $productTypeId,
                collections: [$collectionId],
                category: $categoryId
            }) {
            product {
                id,
                collections {
                    slug
                },
                category {
                    slug
                }
            }
            errors {
                message
                field
            }
        }
    }

    """

    def assert_product_has_collections(product):
        assert product.collections.count() > 0
        assert product.collections.first() == published_collection

    monkeypatch.setattr(
        "saleor.plugins.manager.PluginsManager.product_created",
        lambda _, product: assert_product_has_collections(product),
    )

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)

    response = staff_api_client.post_graphql(
        query,
        {
            "productTypeId": product_type_id,
            "categoryId": category_id,
            "collectionId": collection_id,
        },
        permissions=[permission_manage_products],
    )

    get_graphql_content(response)


def test_product_create_with_invalid_json_description(staff_api_client):
    query = """
        mutation ProductCreate {
            productCreate(
                input: {
                    description: "I'm not a valid JSON"
                    category: "Q2F0ZWdvcnk6MjQ="
                    name: "Breaky McErrorface"
                    productType: "UHJvZHVjdFR5cGU6NTE="
                }
            ) {
            errors {
                field
                message
            }
        }
    }
    """

    response = staff_api_client.post_graphql(query)
    content = get_graphql_content_from_response(response)

    assert content["errors"]
    assert len(content["errors"]) == 1
    assert content["errors"][0]["extensions"]["exception"]["code"] == "GraphQLError"
    assert "is not a valid JSONString" in content["errors"][0]["message"]


MUTATION_UPDATE_PRODUCT = """
    mutation updateProduct($productId: ID!, $input: ProductInput!) {
        productUpdate(id: $productId, input: $input) {
                product {
                    category {
                        name
                    }
                    rating
                    description
                    chargeTaxes
                    variants {
                        name
                    }
                    taxType {
                        taxCode
                        description
                    }
                    name
                    slug
                    productType {
                        name
                    }
                    attributes {
                        attribute {
                            id
                            name
                        }
                        values {
                            id
                            name
                            slug
                            boolean
                            reference
                            file {
                                url
                                contentType
                            }
                        }
                    }
                }
                errors {
                    message
                    field
                    code
                }
            }
        }
"""


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_created")
def test_update_product(
    created_webhook_mock,
    updated_webhook_mock,
    staff_api_client,
    category,
    non_default_category,
    product,
    other_description_json,
    permission_manage_products,
    monkeypatch,
    color_attribute,
):
    query = MUTATION_UPDATE_PRODUCT
    expected_other_description_json = other_description_json
    text = expected_other_description_json["blocks"][0]["data"]["text"]
    expected_other_description_json["blocks"][0]["data"]["text"] = strip_tags(text)
    other_description_json = json.dumps(other_description_json)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    product_name = "updated name"
    product_slug = "updated-product"
    product_charge_taxes = True
    product_tax_rate = "STANDARD"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    attr_value = "Rainbow"

    variables = {
        "productId": product_id,
        "input": {
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "description": other_description_json,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
            "attributes": [{"id": attribute_id, "values": [attr_value]}],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["description"] == json.dumps(expected_other_description_json)
    assert data["product"]["chargeTaxes"] == product_charge_taxes
    assert data["product"]["taxType"]["taxCode"] == product_tax_rate
    assert not data["product"]["category"]["name"] == category.name

    attributes = data["product"]["attributes"]

    assert len(attributes) == 1
    assert len(attributes[0]["values"]) == 1

    assert attributes[0]["attribute"]["id"] == attribute_id
    assert attributes[0]["values"][0]["name"] == "Rainbow"
    assert attributes[0]["values"][0]["slug"] == "rainbow"

    updated_webhook_mock.assert_called_once_with(product)
    created_webhook_mock.assert_not_called()


def test_update_and_search_product_by_description(
    staff_api_client,
    category,
    non_default_category,
    product,
    other_description_json,
    permission_manage_products,
    color_attribute,
):
    query = MUTATION_UPDATE_PRODUCT
    other_description_json = json.dumps(other_description_json)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    product_name = "updated name"
    product_slug = "updated-product"

    variables = {
        "productId": product_id,
        "input": {
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "description": other_description_json,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert not data["errors"]
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["description"] == other_description_json


def test_update_product_without_description_clear_description_plaintext(
    staff_api_client,
    category,
    non_default_category,
    product,
    other_description_json,
    permission_manage_products,
    color_attribute,
):
    query = MUTATION_UPDATE_PRODUCT
    description_plaintext = "some desc"
    product.description_plaintext = description_plaintext
    product.save()
    product_id = graphene.Node.to_global_id("Product", product.pk)
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    product_name = "updated name"
    product_slug = "updated-product"

    variables = {
        "productId": product_id,
        "input": {
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert not data["errors"]
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["description"] is None

    product.refresh_from_db()
    assert product.description_plaintext == ""


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_boolean_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    boolean_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", boolean_attribute.pk)
    product_type.product_attributes.add(boolean_attribute)

    new_value = False

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "boolean": new_value}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": boolean_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": "Boolean: No",
                "boolean": new_value,
                "slug": f"{boolean_attribute.id}_false",
                "reference": None,
                "file": None,
            }
        ],
    }
    assert expected_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_file_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    file_attribute,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)
    product_type.product_attributes.add(file_attribute)

    new_value = "new_file.json"

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "file": new_value}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {"id": attribute_id, "name": file_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": new_value,
                "slug": slugify(new_value),
                "reference": None,
                "file": {
                    "url": "http://testserver/media/" + new_value,
                    "contentType": None,
                },
                "boolean": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_file_attribute_value_new_value_is_not_created(
    updated_webhook_mock,
    staff_api_client,
    file_attribute,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)
    product_type.product_attributes.add(file_attribute)
    existing_value = file_attribute.values.first()
    associate_attribute_values_to_instance(product, file_attribute, existing_value)

    values_count = file_attribute.values.count()

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [{"id": attribute_id, "file": existing_value.file_url}]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {"id": attribute_id, "name": file_attribute.name},
        "values": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", existing_value.pk),
                "name": existing_value.name,
                "slug": existing_value.slug,
                "reference": None,
                "file": {
                    "url": f"http://testserver/media/{existing_value.file_url}",
                    "contentType": existing_value.content_type,
                },
                "boolean": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_numeric_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    numeric_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    product_type.product_attributes.add(numeric_attribute)

    new_value = "45.2"

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": [new_value]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": numeric_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": new_value,
                "slug": slugify(
                    f"{product.id}_{numeric_attribute.id}", allow_unicode=True
                ),
                "reference": None,
                "file": None,
                "boolean": None,
            }
        ],
    }
    assert expected_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_numeric_attribute_value_new_value_is_not_created(
    updated_webhook_mock,
    staff_api_client,
    numeric_attribute,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    product_type.product_attributes.add(numeric_attribute)
    slug_value = slugify(f"{product.id}_{numeric_attribute.id}", allow_unicode=True)
    value = AttributeValue.objects.create(
        attribute=numeric_attribute, slug=slug_value, name="20.0"
    )
    associate_attribute_values_to_instance(product, numeric_attribute, value)

    value_count = AttributeValue.objects.count()

    new_value = "45.2"

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": [new_value]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": numeric_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": new_value,
                "slug": slug_value,
                "reference": None,
                "file": None,
                "boolean": None,
            }
        ],
    }
    assert expected_att_data in attributes

    assert AttributeValue.objects.count() == value_count
    value.refresh_from_db()
    assert value.name == new_value


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_clear_attribute_values(
    updated_webhook_mock,
    staff_api_client,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    product_attr = product.attributes.first()
    attribute = product_attr.assignment.attribute
    attribute.value_required = False
    attribute.save(update_fields=["value_required"])

    attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": []}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 1
    assert not attributes[0]["values"]
    with pytest.raises(product_attr._meta.model.DoesNotExist):
        product_attr.refresh_from_db()

    updated_webhook_mock.assert_called_once_with(product)


def test_update_product_clean_boolean_attribute_value(
    staff_api_client,
    product,
    product_type,
    boolean_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", boolean_attribute.pk)

    product_type.product_attributes.add(boolean_attribute)
    associate_attribute_values_to_instance(
        product, boolean_attribute, boolean_attribute.values.first()
    )

    product_attr = product.attributes.get(assignment__attribute_id=boolean_attribute.id)
    assert product_attr.values.count() == 1

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": []}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": boolean_attribute.name},
        "values": [],
    }
    assert expected_att_data in attributes
    assert product_attr.values.count() == 0


def test_update_product_clean_file_attribute_value(
    staff_api_client,
    product,
    product_type,
    file_attribute,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)
    attribute_id = graphene.Node.to_global_id("Attribute", file_attribute.pk)

    product_type.product_attributes.add(file_attribute)
    associate_attribute_values_to_instance(
        product, file_attribute, file_attribute.values.first()
    )

    product_attr = product.attributes.get(assignment__attribute_id=file_attribute.id)
    assert product_attr.values.count() == 1

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": []}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]
    assert len(attributes) == 2
    expected_att_data = {
        "attribute": {"id": attribute_id, "name": file_attribute.name},
        "values": [],
    }
    assert expected_att_data in attributes
    assert product_attr.values.count() == 0


@freeze_time("2020-03-18 12:00:00")
def test_update_product_rating(
    staff_api_client,
    product,
    permission_manage_products,
):
    query = MUTATION_UPDATE_PRODUCT

    product.rating = 5.5
    product.save(update_fields=["rating"])
    product_id = graphene.Node.to_global_id("Product", product.pk)
    expected_rating = 9.57
    variables = {"productId": product_id, "input": {"rating": expected_rating}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []
    assert data["product"]["rating"] == expected_rating
    product.refresh_from_db()
    assert product.rating == expected_rating


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_page_reference_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    product_type_page_reference_attribute,
    product,
    product_type,
    page,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_page_reference_attribute)

    values_count = product_type_page_reference_attribute.values.count()

    reference = graphene.Node.to_global_id("Page", page.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {
            "id": attribute_id,
            "name": product_type_page_reference_attribute.name,
        },
        "values": [
            {
                "id": ANY,
                "name": page.title,
                "slug": f"{product.id}_{page.id}",
                "file": None,
                "reference": reference,
                "boolean": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count + 1


def test_update_product_without_supplying_required_product_attribute(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensure assigning an existing value to a product doesn't create a new
    attribute value."""

    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = product.product_type
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    # Create and assign a new attribute requiring a value to be always supplied
    required_attribute = Attribute.objects.create(
        name="Required One", slug="required-one", value_required=True
    )
    product_type.product_attributes.add(required_attribute)
    required_attribute_id = graphene.Node.to_global_id(
        "Attribute", required_attribute.id
    )

    value = "Blue"
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "input": {"attributes": [{"id": color_attribute_id, "values": [value]}]},
    }

    # when
    data = get_graphql_content(
        staff_api_client.post_graphql(MUTATION_UPDATE_PRODUCT, variables)
    )["data"]["productUpdate"]

    # then
    assert not data["errors"]
    attributes_data = data["product"]["attributes"]
    assert len(attributes_data) == 2
    assert {
        "attribute": {"id": required_attribute_id, "name": required_attribute.name},
        "values": [],
    } in attributes_data
    assert {
        "attribute": {"id": color_attribute_id, "name": color_attribute.name},
        "values": [
            {
                "id": ANY,
                "name": value,
                "slug": value.lower(),
                "file": None,
                "reference": None,
                "boolean": None,
            }
        ],
    } in attributes_data


def test_update_product_with_empty_input_collections(
    product, permission_manage_products, staff_api_client
):
    # given
    query = """
    mutation updateProduct($productId: ID!, $input: ProductInput!) {
      productUpdate(id: $productId, input: $input) {
        productErrors {
          field
          message
          code
        }
        product {
          id
        }
      }
    }

    """
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "productId": product_id,
        "input": {"collections": [""]},
    }
    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert len(data["productErrors"]) == 1
    product_errors = data["productErrors"][0]
    assert product_errors["code"] == ProductErrorCode.GRAPHQL_ERROR.name


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_page_reference_attribute_existing_value(
    updated_webhook_mock,
    staff_api_client,
    product_type_page_reference_attribute,
    product,
    product_type,
    page,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_page_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page.title,
        slug=f"{product.pk}_{page.pk}",
        reference_page=page,
    )
    associate_attribute_values_to_instance(
        product, product_type_page_reference_attribute, attr_value
    )

    values_count = product_type_page_reference_attribute.values.count()

    reference = graphene.Node.to_global_id("Page", page.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {
            "id": attribute_id,
            "name": product_type_page_reference_attribute.name,
        },
        "values": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_value.pk),
                "name": page.title,
                "slug": f"{product.id}_{page.id}",
                "file": None,
                "reference": reference,
                "boolean": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_page_reference_attribute_value_not_given(
    updated_webhook_mock,
    staff_api_client,
    product_type_page_reference_attribute,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_type_page_reference_attribute.value_required = True
    product_type_page_reference_attribute.save(update_fields=["value_required"])

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_page_reference_attribute)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": ["test"]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == AttributeErrorCode.REQUIRED.name

    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_product_reference_attribute_value(
    updated_webhook_mock,
    staff_api_client,
    product_type_product_reference_attribute,
    product_list,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_list[0]
    product_id = graphene.Node.to_global_id("Product", product.pk)
    product_ref = product_list[1]

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_product_reference_attribute)

    values_count = product_type_product_reference_attribute.values.count()

    reference = graphene.Node.to_global_id("Product", product_ref.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {
            "id": attribute_id,
            "name": product_type_product_reference_attribute.name,
        },
        "values": [
            {
                "id": ANY,
                "name": product_ref.name,
                "slug": f"{product.id}_{product_ref.id}",
                "file": None,
                "reference": reference,
                "boolean": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count + 1


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_product_reference_attribute_existing_value(
    updated_webhook_mock,
    staff_api_client,
    product_type_product_reference_attribute,
    product_list,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product = product_list[0]
    product_id = graphene.Node.to_global_id("Product", product.pk)
    product_ref = product_list[1]

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_product_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_ref.name,
        slug=f"{product.pk}_{product_ref.pk}",
        reference_product=product_ref,
    )
    associate_attribute_values_to_instance(
        product, product_type_product_reference_attribute, attr_value
    )

    values_count = product_type_product_reference_attribute.values.count()

    reference = graphene.Node.to_global_id("Product", product_ref.pk)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 2
    expected_file_att_data = {
        "attribute": {
            "id": attribute_id,
            "name": product_type_product_reference_attribute.name,
        },
        "values": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_value.pk),
                "name": product_ref.name,
                "slug": f"{product.id}_{product_ref.id}",
                "file": None,
                "reference": reference,
                "boolean": None,
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)

    product_type_product_reference_attribute.refresh_from_db()
    assert product_type_product_reference_attribute.values.count() == values_count


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_with_product_reference_attribute_value_not_given(
    updated_webhook_mock,
    staff_api_client,
    product_type_product_reference_attribute,
    product,
    product_type,
    permission_manage_products,
):
    # given
    query = MUTATION_UPDATE_PRODUCT

    product_type_product_reference_attribute.value_required = True
    product_type_product_reference_attribute.save(update_fields=["value_required"])

    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_product_reference_attribute.pk
    )
    product_type.product_attributes.add(product_type_product_reference_attribute)

    variables = {
        "productId": product_id,
        "input": {"attributes": [{"id": attribute_id, "values": ["test"]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]

    assert not data["product"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == AttributeErrorCode.REQUIRED.name

    updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product_change_values_ordering(
    updated_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
    page_list,
    product_type_page_reference_attribute,
):
    # given
    query = MUTATION_UPDATE_PRODUCT
    product_id = graphene.Node.to_global_id("Product", product.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", product_type_page_reference_attribute.pk
    )

    product_type = product.product_type
    product_type.product_attributes.set([product_type_page_reference_attribute])

    attr_value_1 = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page_list[0].title,
        slug=f"{product.pk}_{page_list[0].pk}",
        reference_page=page_list[0],
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page_list[1].title,
        slug=f"{product.pk}_{page_list[1].pk}",
        reference_page=page_list[1],
    )

    associate_attribute_values_to_instance(
        product, product_type_page_reference_attribute, attr_value_2, attr_value_1
    )

    assert list(
        product.attributes.first().productvalueassignment.values_list(
            "value_id", flat=True
        )
    ) == [attr_value_2.pk, attr_value_1.pk]

    variables = {
        "productId": product_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "references": [
                        graphene.Node.to_global_id("Page", page_list[0].pk),
                        graphene.Node.to_global_id("Page", page_list[1].pk),
                    ],
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    attributes = data["product"]["attributes"]

    assert len(attributes) == 1
    values = attributes[0]["values"]
    assert len(values) == 2
    assert [value["id"] for value in values] == [
        graphene.Node.to_global_id("AttributeValue", val.pk)
        for val in [attr_value_1, attr_value_2]
    ]
    product.refresh_from_db()
    assert list(
        product.attributes.first().productvalueassignment.values_list(
            "value_id", flat=True
        )
    ) == [attr_value_1.pk, attr_value_2.pk]

    updated_webhook_mock.assert_called_once_with(product)


UPDATE_PRODUCT_SLUG_MUTATION = """
    mutation($id: ID!, $slug: String) {
        productUpdate(
            id: $id
            input: {
                slug: $slug
            }
        ) {
            product{
                name
                slug
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
def test_update_product_slug(
    staff_api_client,
    product,
    permission_manage_products,
    input_slug,
    expected_slug,
    error_message,
):
    query = UPDATE_PRODUCT_SLUG_MUTATION
    old_slug = product.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]
    if not error_message:
        assert not errors
        assert data["product"]["slug"] == expected_slug
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_product_slug_exists(
    staff_api_client, product, permission_manage_products
):
    query = UPDATE_PRODUCT_SLUG_MUTATION
    input_slug = "test-slug"

    second_product = Product.objects.get(pk=product.pk)
    second_product.pk = None
    second_product.slug = input_slug
    second_product.save()

    assert input_slug != product.slug

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", None, None),
        ("", "", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", "This field cannot be blank.", "name"),
        (None, None, None, "Slug value cannot be blank.", "slug"),
    ],
)
def test_update_product_slug_and_name(
    staff_api_client,
    product,
    permission_manage_products,
    input_slug,
    expected_slug,
    input_name,
    error_message,
    error_field,
):
    query = """
            mutation($id: ID!, $name: String, $slug: String) {
            productUpdate(
                id: $id
                input: {
                    name: $name
                    slug: $slug
                }
            ) {
                product{
                    name
                    slug
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """

    old_name = product.name
    old_slug = product.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"slug": input_slug, "name": input_name, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    product.refresh_from_db()
    data = content["data"]["productUpdate"]
    errors = data["errors"]
    if not error_message:
        assert data["product"]["name"] == input_name == product.name
        assert data["product"]["slug"] == input_slug == product.slug
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


SET_ATTRIBUTES_TO_PRODUCT_QUERY = """
    mutation updateProduct($productId: ID!, $attributes: [AttributeValueInput!]) {
      productUpdate(id: $productId, input: { attributes: $attributes }) {
        errors {
          message
          field
          code
          attributes
        }
      }
    }
"""


def test_update_product_can_only_assign_multiple_values_to_valid_input_types(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensures you cannot assign multiple values to input types
    that are not multi-select. This also ensures multi-select types
    can be assigned multiple values as intended."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    multi_values_attr = Attribute.objects.create(
        name="multi", slug="multi-vals", input_type=AttributeInputType.MULTISELECT
    )
    multi_values_attr.product_types.add(product.product_type)
    multi_values_attr_id = graphene.Node.to_global_id("Attribute", multi_values_attr.id)

    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": color_attribute_id, "values": ["red", "blue"]}],
    }
    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert data["errors"] == [
        {
            "field": "attributes",
            "code": ProductErrorCode.INVALID.name,
            "message": ANY,
            "attributes": [color_attribute_id],
        }
    ]

    # Try to assign multiple values from a valid attribute
    variables["attributes"] = [{"id": multi_values_attr_id, "values": ["a", "b"]}]
    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert not data["errors"]


def test_update_product_with_existing_attribute_value(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensure assigning an existing value to a product doesn't create a new
    attribute value."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    expected_attribute_values_count = color_attribute.values.count()
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    color = color_attribute.values.only("name").first()

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": color_attribute_id, "values": [color.name]}],
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert not data["errors"]

    assert (
        color_attribute.values.count() == expected_attribute_values_count
    ), "A new attribute value shouldn't have been created"


def test_update_product_with_non_existing_attribute(
    staff_api_client, product, permission_manage_products, color_attribute
):
    non_existent_attribute_pk = 0
    invalid_attribute_id = graphene.Node.to_global_id(
        "Attribute", non_existent_attribute_pk
    )

    """Ensure assigning an existing value to a product doesn't create a new
    attribute value."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": invalid_attribute_id, "values": ["hello"]}],
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert data["errors"] == [
        {
            "field": "attributes",
            "code": ProductErrorCode.NOT_FOUND.name,
            "message": ANY,
            "attributes": None,
        }
    ]


def test_update_product_with_no_attribute_slug_or_id(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensure only supplying values triggers a validation error."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"values": ["Oopsie!"]}],
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert data["errors"] == [
        {
            "field": "attributes",
            "code": ProductErrorCode.REQUIRED.name,
            "message": ANY,
            "attributes": None,
        }
    ]


def test_update_product_with_negative_weight(
    staff_api_client, product_with_default_variant, permission_manage_products, product
):
    query = """
        mutation updateProduct(
            $productId: ID!,
            $weight: WeightScalar)
        {
            productUpdate(
                id: $productId,
                input: {
                    weight: $weight
                })
            {
                product {
                    id
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    product = product_with_default_variant
    product_id = graphene.Node.to_global_id("Product", product.pk)

    variables = {"productId": product_id, "weight": -1}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    error = data["errors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


UPDATE_PRODUCT = """
    mutation updateProduct(
        $productId: ID!,
        $input: ProductInput!)
    {
        productUpdate(
            id: $productId,
            input: $input)
        {
            product {
                id
                name
                slug
            }
            errors {
                message
                field
            }
        }
    }"""


def test_update_product_name(staff_api_client, permission_manage_products, product):
    query = UPDATE_PRODUCT

    product_slug = product.slug
    new_name = "example-product"
    assert new_name != product.name

    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"productId": product_id, "input": {"name": new_name}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    data = get_graphql_content(response)["data"]["productUpdate"]
    assert data["product"]["name"] == new_name
    assert data["product"]["slug"] == product_slug


def test_update_product_slug_with_existing_value(
    staff_api_client, permission_manage_products, product
):
    query = UPDATE_PRODUCT
    second_product = Product.objects.get(pk=product.pk)
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()

    assert product.slug != second_product.slug

    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"productId": product_id, "input": {"slug": second_product.slug}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    data = get_graphql_content(response)["data"]["productUpdate"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["message"] == "Product with this Slug already exists."


DELETE_PRODUCT_MUTATION = """
    mutation DeleteProduct($id: ID!) {
        productDelete(id: $id) {
            product {
                name
                id
                attributes {
                    values {
                        value
                        name
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


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    query = DELETE_PRODUCT_MUTATION
    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.product.signals.delete_product_media_task.delay")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_with_image(
    mocked_recalculate_orders_task,
    delete_product_media_task_mock,
    staff_api_client,
    product_with_image,
    variant_with_image,
    permission_manage_products,
    media_root,
):
    """Ensure deleting product delete also product and variants images from storage."""

    # given
    query = DELETE_PRODUCT_MUTATION
    product = product_with_image
    variant = product.variants.first()
    node_id = graphene.Node.to_global_id("Product", product.id)

    product_img_paths = [media.image for media in product.media.all()]
    variant_img_paths = [media.image for media in variant.media.all()]
    product_media_ids = [media.id for media in product.media.all()]
    images = product_img_paths + variant_img_paths

    variables = {"id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]

    assert delete_product_media_task_mock.call_count == len(images)
    assert {
        call_args.args[0] for call_args in delete_product_media_task_mock.call_args_list
    } == set(product_media_ids)
    mocked_recalculate_orders_task.assert_not_called()


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_trigger_webhook(
    mocked_recalculate_orders_task,
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    product,
    permission_manage_products,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    query = DELETE_PRODUCT_MUTATION
    node_id = graphene.Node.to_global_id("Product", product.id)
    variants_id = list(product.variants.all().values_list("id", flat=True))
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]
    expected_data = generate_product_deleted_payload(
        product, variants_id, staff_api_client.user
    )
    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.PRODUCT_DELETED,
        [any_webhook],
        product,
        SimpleLazyObject(lambda: staff_api_client.user),
    )
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_with_file_attribute(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
    file_attribute,
):
    query = DELETE_PRODUCT_MUTATION
    product_type = product.product_type
    product_type.product_attributes.add(file_attribute)
    existing_value = file_attribute.values.first()
    associate_attribute_values_to_instance(product, file_attribute, existing_value)

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]
    mocked_recalculate_orders_task.assert_not_called()
    with pytest.raises(existing_value._meta.model.DoesNotExist):
        existing_value.refresh_from_db()


def test_delete_product_removes_checkout_lines(
    staff_api_client,
    checkout_with_items,
    permission_manage_products,
    settings,
):
    query = DELETE_PRODUCT_MUTATION
    checkout = checkout_with_items
    line = checkout.lines.first()
    product = line.variant.product
    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name

    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()

    with pytest.raises(line._meta.model.DoesNotExist):
        line.refresh_from_db()
    assert checkout.lines.all().exists()

    checkout.refresh_from_db()

    assert node_id == data["product"]["id"]


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_variant_in_draft_order(
    mocked_recalculate_orders_task,
    staff_api_client,
    product_with_two_variants,
    permission_manage_products,
    order_list,
    channel_USD,
):
    query = DELETE_PRODUCT_MUTATION
    product = product_with_two_variants

    not_draft_order = order_list[1]
    draft_order = order_list[0]
    draft_order.status = OrderStatus.DRAFT
    draft_order.save(update_fields=["status"])

    draft_order_lines_pks = []
    not_draft_order_lines_pks = []
    for variant in product.variants.all():
        variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
        net = variant.get_price(product, [], channel_USD, variant_channel_listing, None)
        gross = Money(amount=net.amount, currency=net.currency)
        unit_price = TaxedMoney(net=net, gross=gross)
        quantity = 3
        total_price = unit_price * quantity

        order_line = OrderLine.objects.create(
            variant=variant,
            order=draft_order,
            product_name=str(variant.product),
            variant_name=str(variant),
            product_sku=variant.sku,
            product_variant_id=variant.get_global_id(),
            is_shipping_required=variant.is_shipping_required(),
            is_gift_card=variant.is_gift_card(),
            unit_price=TaxedMoney(net=net, gross=gross),
            total_price=total_price,
            quantity=quantity,
        )
        draft_order_lines_pks.append(order_line.pk)

        order_line_not_draft = OrderLine.objects.create(
            variant=variant,
            order=not_draft_order,
            product_name=str(variant.product),
            variant_name=str(variant),
            product_sku=variant.sku,
            product_variant_id=variant.get_global_id(),
            is_shipping_required=variant.is_shipping_required(),
            is_gift_card=variant.is_gift_card(),
            unit_price=TaxedMoney(net=net, gross=gross),
            total_price=total_price,
            quantity=quantity,
        )
        not_draft_order_lines_pks.append(order_line_not_draft.pk)

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]

    assert not OrderLine.objects.filter(pk__in=draft_order_lines_pks).exists()

    assert OrderLine.objects.filter(pk__in=not_draft_order_lines_pks).exists()
    mocked_recalculate_orders_task.assert_called_once_with([draft_order.id])

    event = OrderEvent.objects.filter(
        type=OrderEvents.ORDER_LINE_PRODUCT_DELETED
    ).last()
    assert event
    assert event.order == draft_order
    assert event.user == staff_api_client.user
    expected_params = [
        {
            "item": str(line),
            "line_pk": line.pk,
            "quantity": line.quantity,
        }
        for line in draft_order.lines.all()
    ]
    for param in expected_params:
        assert param in event.parameters


def test_product_delete_removes_reference_to_product(
    staff_api_client,
    product_type_product_reference_attribute,
    product_list,
    product_type,
    permission_manage_products,
):
    # given
    query = DELETE_PRODUCT_MUTATION

    product = product_list[0]
    product_ref = product_list[1]

    product_type.product_attributes.add(product_type_product_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_ref.name,
        slug=f"{product.pk}_{product_ref.pk}",
        reference_product=product_ref,
    )
    associate_attribute_values_to_instance(
        product, product_type_product_reference_attribute, attr_value
    )

    reference_id = graphene.Node.to_global_id("Product", product_ref.pk)

    variables = {"id": reference_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(product_ref._meta.model.DoesNotExist):
        product_ref.refresh_from_db()

    assert not data["errors"]


def test_product_delete_removes_reference_to_product_variant(
    staff_api_client,
    variant,
    product_type_product_reference_attribute,
    permission_manage_products,
    product_list,
):
    query = DELETE_PRODUCT_MUTATION
    product_type = variant.product.product_type
    product_type.variant_attributes.set([product_type_product_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[0].name,
        slug=f"{variant.pk}_{product_list[0].pk}",
        reference_product=product_list[0],
    )

    associate_attribute_values_to_instance(
        variant,
        product_type_product_reference_attribute,
        attr_value,
    )
    reference_id = graphene.Node.to_global_id("Product", product_list[0].pk)

    variables = {"id": reference_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(product_list[0]._meta.model.DoesNotExist):
        product_list[0].refresh_from_db()

    assert not data["errors"]


def test_product_delete_removes_reference_to_page(
    staff_api_client,
    permission_manage_products,
    page,
    page_type_product_reference_attribute,
    product,
):
    query = DELETE_PRODUCT_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_product_reference_attribute)

    attr_value = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=page.title,
        slug=f"{page.pk}_{product.pk}",
        reference_product=product,
    )
    associate_attribute_values_to_instance(
        page, page_type_product_reference_attribute, attr_value
    )

    reference_id = graphene.Node.to_global_id("Product", product.pk)

    variables = {"id": reference_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()

    assert not data["errors"]


def test_product_type(user_api_client, product_type, channel_USD):
    query = """
    query ($channel: String){
        productTypes(first: 20) {
            totalCount
            edges {
                node {
                    id
                    name
                    products(first: 1, channel: $channel) {
                        edges {
                            node {
                                id
                            }
                        }
                    }
                }
            }
        }
    }
    """
    variables = {"channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    no_product_types = ProductType.objects.count()
    assert content["data"]["productTypes"]["totalCount"] == no_product_types
    assert len(content["data"]["productTypes"]["edges"]) == no_product_types


PRODUCT_TYPE_QUERY = """
    query getProductType(
        $id: ID!, $variantSelection: VariantAttributeScope, $channel: String
    ) {
        productType(id: $id) {
            name
            variantAttributes(variantSelection: $variantSelection) {
                slug
            }
            products(first: 20, channel:$channel) {
                totalCount
                edges {
                    node {
                        name
                    }
                }
            }
            taxType {
                taxCode
                description
            }
        }
    }
"""


def test_product_type_query(
    user_api_client,
    staff_api_client,
    product_type,
    file_attribute_with_file_input_type_without_values,
    product,
    permission_manage_products,
    monkeypatch,
    channel_USD,
):
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(code="123", description="Standard Taxes"),
    )

    query = PRODUCT_TYPE_QUERY

    no_products = Product.objects.count()
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    product_type.variant_attributes.add(
        file_attribute_with_file_input_type_without_values
    )
    variant_attributes_count = product_type.variant_attributes.count()

    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.id),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products - 1

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products
    assert data["productType"]["taxType"]["taxCode"] == "123"
    assert data["productType"]["taxType"]["description"] == "Standard Taxes"
    assert len(data["productType"]["variantAttributes"]) == variant_attributes_count


def test_product_type_query_invalid_id(
    staff_api_client, product, channel_USD, permission_manage_products
):
    product_type_id = "'"
    variables = {
        "id": product_type_id,
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(PRODUCT_TYPE_QUERY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {product_type_id}."
    assert content["data"]["productType"] is None


def test_product_type_query_object_with_given_id_does_not_exist(
    staff_api_client, product, channel_USD, permission_manage_products
):
    product_type_id = graphene.Node.to_global_id("ProductType", -1)
    variables = {
        "id": product_type_id,
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(PRODUCT_TYPE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["productType"] is None


def test_product_type_query_with_invalid_object_type(
    staff_api_client, product, channel_USD, permission_manage_products
):
    product_type_id = graphene.Node.to_global_id("Product", product.product_type.pk)
    variables = {
        "id": product_type_id,
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(PRODUCT_TYPE_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["productType"] is None


@pytest.mark.parametrize(
    "variant_selection",
    [
        VariantAttributeScope.ALL.name,
        VariantAttributeScope.VARIANT_SELECTION.name,
        VariantAttributeScope.NOT_VARIANT_SELECTION.name,
    ],
)
def test_product_type_query_only_variant_selections_value_set(
    variant_selection,
    user_api_client,
    staff_api_client,
    product_type,
    file_attribute_with_file_input_type_without_values,
    author_page_attribute,
    product_type_page_reference_attribute,
    product,
    permission_manage_products,
    monkeypatch,
    channel_USD,
):
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(code="123", description="Standard Taxes"),
    )
    query = PRODUCT_TYPE_QUERY

    no_products = Product.objects.count()
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    product_type.variant_attributes.add(
        file_attribute_with_file_input_type_without_values,
        author_page_attribute,
        product_type_page_reference_attribute,
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.id),
        "variantSelection": variant_selection,
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products - 1

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products
    assert data["productType"]["taxType"]["taxCode"] == "123"
    assert data["productType"]["taxType"]["description"] == "Standard Taxes"

    if variant_selection == VariantAttributeScope.VARIANT_SELECTION.name:
        assert (
            len(data["productType"]["variantAttributes"])
            == product_type.variant_attributes.filter(
                input_type=AttributeInputType.DROPDOWN, type=AttributeType.PRODUCT_TYPE
            ).count()
        )
    elif variant_selection == VariantAttributeScope.NOT_VARIANT_SELECTION.name:
        assert (
            len(data["productType"]["variantAttributes"])
            == product_type.variant_attributes.exclude(
                input_type=AttributeInputType.DROPDOWN, type=AttributeType.PRODUCT_TYPE
            ).count()
        )
    else:
        assert (
            len(data["productType"]["variantAttributes"])
            == product_type.variant_attributes.count()
        )


PRODUCT_TYPE_QUERY_ASSIGNED_VARIANT_ATTRIBUTES = """
    query getProductType(
        $id: ID!, $variantSelection: VariantAttributeScope, $channel: String
    ) {
        productType(id: $id) {
            name
            assignedVariantAttributes(variantSelection: $variantSelection) {
                attribute {
                    slug
                }
                variantSelection
            }
            products(first: 20, channel:$channel) {
                totalCount
                edges {
                    node {
                        name
                    }
                }
            }
            taxType {
                taxCode
                description
            }
        }
    }
"""


@pytest.mark.parametrize(
    "variant_selection",
    [
        VariantAttributeScope.ALL.name,
        VariantAttributeScope.VARIANT_SELECTION.name,
        VariantAttributeScope.NOT_VARIANT_SELECTION.name,
    ],
)
def test_product_type_query_only_assigned_variant_selections_value_set(
    variant_selection,
    user_api_client,
    staff_api_client,
    product_type,
    file_attribute_with_file_input_type_without_values,
    author_page_attribute,
    product_type_page_reference_attribute,
    product,
    permission_manage_products,
    monkeypatch,
    channel_USD,
):
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(code="123", description="Standard Taxes"),
    )
    query = PRODUCT_TYPE_QUERY_ASSIGNED_VARIANT_ATTRIBUTES

    no_products = Product.objects.count()
    ProductChannelListing.objects.filter(product=product, channel=channel_USD).update(
        is_published=False
    )

    product_type.variant_attributes.add(
        file_attribute_with_file_input_type_without_values,
        author_page_attribute,
        product_type_page_reference_attribute,
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductType", product_type.id),
        "variantSelection": variant_selection,
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products - 1

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products
    assert data["productType"]["taxType"]["taxCode"] == "123"
    assert data["productType"]["taxType"]["description"] == "Standard Taxes"

    if variant_selection == VariantAttributeScope.VARIANT_SELECTION.name:
        assert (
            len(data["productType"]["assignedVariantAttributes"])
            == product_type.variant_attributes.filter(
                input_type=AttributeInputType.DROPDOWN, type=AttributeType.PRODUCT_TYPE
            ).count()
        )
        assert all(
            assign["variantSelection"]
            for assign in data["productType"]["assignedVariantAttributes"]
        )
    elif variant_selection == VariantAttributeScope.NOT_VARIANT_SELECTION.name:
        assert (
            len(data["productType"]["assignedVariantAttributes"])
            == product_type.variant_attributes.exclude(
                input_type=AttributeInputType.DROPDOWN, type=AttributeType.PRODUCT_TYPE
            ).count()
        )
        assert not any(
            assign["variantSelection"]
            for assign in data["productType"]["assignedVariantAttributes"]
        )

    else:
        assert (
            len(data["productType"]["assignedVariantAttributes"])
            == product_type.variant_attributes.count()
        )


PRODUCT_TYPE_CREATE_MUTATION = """
    mutation createProductType(
        $name: String,
        $slug: String,
        $kind: ProductTypeKindEnum,
        $taxCode: String,
        $hasVariants: Boolean,
        $isShippingRequired: Boolean,
        $productAttributes: [ID!],
        $variantAttributes: [ID!],
        $weight: WeightScalar) {
        productTypeCreate(
            input: {
                name: $name,
                slug: $slug,
                kind: $kind,
                taxCode: $taxCode,
                hasVariants: $hasVariants,
                isShippingRequired: $isShippingRequired,
                productAttributes: $productAttributes,
                variantAttributes: $variantAttributes,
                weight: $weight}) {
            productType {
                name
                slug
                kind
                isShippingRequired
                hasVariants
                variantAttributes {
                    name
                    choices(first: 10) {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                }
                productAttributes {
                    name
                    choices(first: 10) {
                        edges {
                            node {
                                name
                                richText
                                boolean
                                date
                                dateTime
                            }
                        }

                    }
                }
            }
            errors {
                field
                message
                code
                attributes
            }
        }

    }
"""


def test_product_type_create_mutation(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    monkeypatch,
    setup_vatlayer,
):
    manager = PluginsManager(plugins=setup_vatlayer.PLUGINS)

    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"
    kind = ProductTypeKindEnum.NORMAL.name
    has_variants = True
    require_shipping = True
    product_attributes = product_type.product_attributes.all()
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in product_attributes
    ]
    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in variant_attributes
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": kind,
        "hasVariants": has_variants,
        "taxCode": "wine",
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
        "variantAttributes": variant_attributes_ids,
    }
    initial_count = ProductType.objects.count()
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    assert ProductType.objects.count() == initial_count + 1
    data = content["data"]["productTypeCreate"]["productType"]
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["kind"] == kind
    assert data["hasVariants"] == has_variants
    assert data["isShippingRequired"] == require_shipping

    pa = product_attributes[0]
    assert data["productAttributes"][0]["name"] == pa.name
    pa_values = data["productAttributes"][0]["choices"]["edges"]
    assert sorted([value["node"]["name"] for value in pa_values]) == sorted(
        [value.name for value in pa.values.all()]
    )

    va = variant_attributes[0]
    assert data["variantAttributes"][0]["name"] == va.name
    va_values = data["variantAttributes"][0]["choices"]["edges"]
    assert sorted([value["node"]["name"] for value in va_values]) == sorted(
        [value.name for value in va.values.all()]
    )

    new_instance = ProductType.objects.latest("pk")
    tax_code = manager.get_tax_code_from_object_meta(new_instance).code
    assert tax_code == "wine"


def test_product_type_create_mutation_optional_kind(
    staff_api_client, permission_manage_product_types_and_attributes
):
    variables = {"name": "Default Kind Test"}
    response = staff_api_client.post_graphql(
        PRODUCT_TYPE_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)
    assert (
        content["data"]["productTypeCreate"]["productType"]["kind"]
        == ProductTypeKindEnum.NORMAL.name
    )


def test_create_gift_card_product_type(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    monkeypatch,
    setup_vatlayer,
):
    manager = PluginsManager(plugins=setup_vatlayer.PLUGINS)

    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"
    kind = ProductTypeKindEnum.GIFT_CARD.name
    has_variants = True
    require_shipping = True
    product_attributes = product_type.product_attributes.all()
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in product_attributes
    ]
    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in variant_attributes
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": kind,
        "hasVariants": has_variants,
        "taxCode": "wine",
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
        "variantAttributes": variant_attributes_ids,
    }
    initial_count = ProductType.objects.count()
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    assert ProductType.objects.count() == initial_count + 1
    data = content["data"]["productTypeCreate"]["productType"]
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["kind"] == kind
    assert data["hasVariants"] == has_variants
    assert data["isShippingRequired"] == require_shipping

    pa = product_attributes[0]
    assert data["productAttributes"][0]["name"] == pa.name
    pa_values = data["productAttributes"][0]["choices"]["edges"]
    assert sorted([value["node"]["name"] for value in pa_values]) == sorted(
        [value.name for value in pa.values.all()]
    )

    va = variant_attributes[0]
    assert data["variantAttributes"][0]["name"] == va.name
    va_values = data["variantAttributes"][0]["choices"]["edges"]
    assert sorted([value["node"]["name"] for value in va_values]) == sorted(
        [value.name for value in va.values.all()]
    )

    new_instance = ProductType.objects.latest("pk")
    tax_code = manager.get_tax_code_from_object_meta(new_instance).code
    assert tax_code == "wine"


def test_create_product_type_with_rich_text_attribute(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    rich_text_attribute,
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"

    product_type.product_attributes.add(rich_text_attribute)
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", attr.id)
        for attr in product_type.product_attributes.all()
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": ProductTypeKindEnum.NORMAL.name,
        "productAttributes": product_attributes_ids,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]["productType"]
    errors = content["data"]["productTypeCreate"]["errors"]

    assert not errors
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    expected_attributes = [
        {
            "name": "Color",
            "choices": {
                "edges": [
                    {
                        "node": {
                            "name": "Red",
                            "richText": None,
                            "boolean": None,
                            "date": None,
                            "dateTime": None,
                        }
                    },
                    {
                        "node": {
                            "name": "Blue",
                            "richText": None,
                            "boolean": None,
                            "date": None,
                            "dateTime": None,
                        }
                    },
                ]
            },
        },
        {
            "name": "Text",
            "choices": {"edges": []},
        },
    ]
    for attribute in data["productAttributes"]:
        assert attribute in expected_attributes


def test_create_product_type_with_date_attribute(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    date_attribute,
    date_time_attribute,
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"
    kind = ProductTypeKindEnum.NORMAL.name

    product_type.product_attributes.add(date_attribute)
    product_type.product_attributes.add(date_time_attribute)

    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", attr.id)
        for attr in product_type.product_attributes.all()
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": kind,
        "productAttributes": product_attributes_ids,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]["productType"]
    errors = content["data"]["productTypeCreate"]["errors"]
    expected_attribute = [
        {"choices": {"edges": []}, "name": "Release date"},
        {"choices": {"edges": []}, "name": "Release date time"},
    ]

    assert not errors
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["kind"] == kind

    for attribute in expected_attribute:
        assert attribute in data["productAttributes"]


def test_create_product_type_with_boolean_attribute(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    boolean_attribute,
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"
    kind = ProductTypeKindEnum.NORMAL.name

    product_type.product_attributes.add(boolean_attribute)
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", attr.id)
        for attr in product_type.product_attributes.all()
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": kind,
        "productAttributes": product_attributes_ids,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]["productType"]
    errors = content["data"]["productTypeCreate"]["errors"]

    assert not errors
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["kind"] == kind
    assert {"choices": {"edges": []}, "name": "Boolean"} in data["productAttributes"]


@pytest.mark.parametrize(
    "input_slug, expected_slug",
    (
        ("test-slug", "test-slug"),
        (None, "test-product-type"),
        ("", "test-product-type"),
        ("わたし-わ-にっぽん-です", "わたし-わ-にっぽん-です"),
    ),
)
def test_create_product_type_with_given_slug(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    input_slug,
    expected_slug,
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    name = "Test product type"
    variables = {
        "name": name,
        "slug": input_slug,
        "kind": ProductTypeKindEnum.NORMAL.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    assert not data["errors"]
    assert data["productType"]["slug"] == expected_slug


def test_create_product_type_with_unicode_in_name(
    staff_api_client, permission_manage_product_types_and_attributes
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    name = "わたし わ にっぽん です"
    kind = ProductTypeKindEnum.NORMAL.name
    variables = {
        "name": name,
        "kind": kind,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    assert not data["errors"]
    assert data["productType"]["name"] == name
    assert data["productType"]["slug"] == "わたし-わ-にっぽん-です"
    assert data["productType"]["kind"] == kind


def test_create_product_type_create_with_negative_weight(
    staff_api_client, permission_manage_product_types_and_attributes
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    name = "Test product type"
    variables = {
        "name": name,
        "weight": -1.1,
        "type": ProductTypeKindEnum.NORMAL.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    error = data["errors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_product_type_create_mutation_not_valid_attributes(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    monkeypatch,
    setup_vatlayer,
):
    # given
    query = PRODUCT_TYPE_CREATE_MUTATION
    product_type_name = "test type"
    slug = "test-type"
    has_variants = True
    require_shipping = True

    product_attributes = product_type.product_attributes.all()
    product_page_attribute = product_attributes.last()
    product_page_attribute.type = AttributeType.PAGE_TYPE
    product_page_attribute.save(update_fields=["type"])

    variant_attributes = product_type.variant_attributes.all()
    variant_page_attribute = variant_attributes.last()
    variant_page_attribute.type = AttributeType.PAGE_TYPE
    variant_page_attribute.save(update_fields=["type"])

    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in product_attributes
    ]
    variant_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in variant_attributes
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "kind": ProductTypeKindEnum.NORMAL.name,
        "hasVariants": has_variants,
        "taxCode": "wine",
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
        "variantAttributes": variant_attributes_ids,
    }
    initial_count = ProductType.objects.count()

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    errors = data["errors"]

    assert len(errors) == 2
    expected_errors = [
        {
            "code": ProductErrorCode.INVALID.name,
            "field": "productAttributes",
            "message": ANY,
            "attributes": [
                graphene.Node.to_global_id("Attribute", product_page_attribute.pk)
            ],
        },
        {
            "code": ProductErrorCode.INVALID.name,
            "field": "variantAttributes",
            "message": ANY,
            "attributes": [
                graphene.Node.to_global_id("Attribute", variant_page_attribute.pk)
            ],
        },
    ]
    for error in errors:
        assert error in expected_errors

    assert initial_count == ProductType.objects.count()


PRODUCT_TYPE_UPDATE_MUTATION = """
mutation updateProductType(
    $id: ID!,
    $name: String!,
    $hasVariants: Boolean!,
    $isShippingRequired: Boolean!,
    $productAttributes: [ID!],
    ) {
        productTypeUpdate(
        id: $id,
        input: {
            name: $name,
            hasVariants: $hasVariants,
            isShippingRequired: $isShippingRequired,
            productAttributes: $productAttributes
        }) {
            productType {
                name
                slug
                isShippingRequired
                hasVariants
                variantAttributes {
                    id
                }
                productAttributes {
                    id
                }
            }
            errors {
                code
                field
                attributes
            }
            }
        }
"""


def test_product_type_update_mutation(
    staff_api_client,
    product_type,
    product,
    permission_manage_product_types_and_attributes,
):
    query = PRODUCT_TYPE_UPDATE_MUTATION
    product_type_name = "test type updated"
    slug = product_type.slug
    has_variants = True
    require_shipping = False
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)

    # Test scenario: remove all product attributes using [] as input
    # but do not change variant attributes
    product_attributes = []
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in product_attributes
    ]
    variant_attributes = product_type.variant_attributes.all()

    variables = {
        "id": product_type_id,
        "name": product_type_name,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]["productType"]
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["hasVariants"] == has_variants
    assert data["isShippingRequired"] == require_shipping
    assert not data["productAttributes"]
    assert len(data["variantAttributes"]) == (variant_attributes.count())


def test_product_type_update_mutation_not_valid_attributes(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    size_page_attribute,
):
    # given
    query = PRODUCT_TYPE_UPDATE_MUTATION
    product_type_name = "test type updated"
    has_variants = True
    require_shipping = False
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)

    # Test scenario: adding page attribute raise error

    page_attribute_id = graphene.Node.to_global_id("Attribute", size_page_attribute.id)
    product_attributes_ids = [
        page_attribute_id,
        graphene.Node.to_global_id(
            "Attribute", product_type.product_attributes.first().pk
        ),
    ]

    variables = {
        "id": product_type_id,
        "name": product_type_name,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "productAttributes"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name
    assert errors[0]["attributes"] == [page_attribute_id]


UPDATE_PRODUCT_TYPE_SLUG_MUTATION = """
    mutation($id: ID!, $slug: String) {
        productTypeUpdate(
            id: $id
            input: {
                slug: $slug
            }
        ) {
            productType{
                name
                slug
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
@patch("saleor.product.search.update_products_search_vector")
def test_update_product_type_slug(
    update_products_search_vector_mock,
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    input_slug,
    expected_slug,
    error_message,
):
    query = UPDATE_PRODUCT_TYPE_SLUG_MUTATION
    old_slug = product_type.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]
    if not error_message:
        assert not errors
        assert data["productType"]["slug"] == expected_slug
        update_products_search_vector_mock.assert_not_called()
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_product_type_slug_exists(
    staff_api_client, product_type, permission_manage_product_types_and_attributes
):
    query = UPDATE_PRODUCT_TYPE_SLUG_MUTATION
    input_slug = "test-slug"

    second_product_type = ProductType.objects.get(pk=product_type.pk)
    second_product_type.pk = None
    second_product_type.slug = input_slug
    second_product_type.save()

    assert input_slug != product_type.slug

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", None, None),
        ("", "", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", "This field cannot be blank.", "name"),
        (None, None, None, "Slug value cannot be blank.", "slug"),
    ],
)
def test_update_product_type_slug_and_name(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
    input_slug,
    expected_slug,
    input_name,
    error_message,
    error_field,
):
    query = """
            mutation($id: ID!, $name: String, $slug: String) {
            productTypeUpdate(
                id: $id
                input: {
                    name: $name
                    slug: $slug
                }
            ) {
                productType{
                    name
                    slug
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """

    old_name = product_type.name
    old_slug = product_type.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"slug": input_slug, "name": input_name, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    product_type.refresh_from_db()
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]
    if not error_message:
        assert data["productType"]["name"] == input_name == product_type.name
        assert data["productType"]["slug"] == input_slug == product_type.slug
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_product_type_with_negative_weight(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
):
    query = """
        mutation($id: ID!, $weight: WeightScalar) {
            productTypeUpdate(
                id: $id
                input: {
                    weight: $weight
                }
            ) {
                productType{
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

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"id": node_id, "weight": "-1"}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    product_type.refresh_from_db()
    data = content["data"]["productTypeUpdate"]
    error = data["errors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_update_product_type_kind(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
):
    query = """
        mutation($id: ID!, $kind: ProductTypeKindEnum) {
            productTypeUpdate(id: $id, input: { kind: $kind }) {
                productType{
                    name
                    kind
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    kind = ProductTypeKindEnum.GIFT_CARD.name
    assert product_type.kind != kind

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"kind": kind, "id": node_id}

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["productType"]["kind"] == kind


def test_update_product_type_kind_omitted(
    staff_api_client,
    product_type,
    permission_manage_product_types_and_attributes,
):
    query = """
        mutation($id: ID!, $name: String) {
            productTypeUpdate(id: $id, input: { name: $name }) {
                productType{
                    name
                    kind
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """
    assert product_type.kind == ProductTypeKindEnum.NORMAL.value
    name = "New name"
    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"id": node_id, "name": name}

    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["errors"]
    assert not errors
    assert data["productType"]["kind"] == ProductTypeKindEnum.NORMAL.name
    assert data["productType"]["name"] == name


PRODUCT_TYPE_DELETE_MUTATION = """
    mutation deleteProductType($id: ID!) {
        productTypeDelete(id: $id) {
            productType {
                name
            }
        }
    }
"""


def test_product_type_delete_mutation(
    staff_api_client, product_type, permission_manage_product_types_and_attributes
):
    query = PRODUCT_TYPE_DELETE_MUTATION
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeDelete"]
    assert data["productType"]["name"] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()


@patch("saleor.product.signals.delete_product_media_task.delay")
def test_product_type_delete_mutation_deletes_also_images(
    delete_product_media_task_mock,
    staff_api_client,
    product_type,
    product_with_image,
    permission_manage_product_types_and_attributes,
):
    query = PRODUCT_TYPE_DELETE_MUTATION
    product_type.products.add(product_with_image)
    media_obj = product_with_image.media.first()
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeDelete"]
    assert data["productType"]["name"] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()
    delete_product_media_task_mock.assert_called_once_with(media_obj.id)
    with pytest.raises(product_with_image._meta.model.DoesNotExist):
        product_with_image.refresh_from_db()


def test_product_type_delete_with_file_attributes(
    staff_api_client,
    product_with_variant_with_file_attribute,
    file_attribute,
    permission_manage_product_types_and_attributes,
):
    query = PRODUCT_TYPE_DELETE_MUTATION
    product_type = product_with_variant_with_file_attribute.product_type

    product_type.product_attributes.add(file_attribute)
    associate_attribute_values_to_instance(
        product_with_variant_with_file_attribute,
        file_attribute,
        file_attribute.values.last(),
    )
    values = list(file_attribute.values.all())

    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeDelete"]
    assert data["productType"]["name"] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()
    for value in values:
        with pytest.raises(value._meta.model.DoesNotExist):
            value.refresh_from_db()
    with pytest.raises(
        product_with_variant_with_file_attribute._meta.model.DoesNotExist
    ):
        product_with_variant_with_file_attribute.refresh_from_db()


def test_product_type_delete_mutation_variants_in_draft_order(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product,
    order_list,
    channel_USD,
):
    query = PRODUCT_TYPE_DELETE_MUTATION
    product_type = product.product_type

    variant = product.variants.first()

    order_not_draft = order_list[-1]
    draft_order = order_list[1]
    draft_order.status = OrderStatus.DRAFT
    draft_order.save(update_fields=["status"])

    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    net = variant.get_price(product, [], channel_USD, variant_channel_listing, None)
    gross = Money(amount=net.amount, currency=net.currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    total_price = unit_price * quantity

    order_line_not_in_draft = OrderLine.objects.create(
        variant=variant,
        order=order_not_draft,
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        unit_price=TaxedMoney(net=net, gross=gross),
        total_price=total_price,
        quantity=3,
    )

    order_line_in_draft = OrderLine.objects.create(
        variant=variant,
        order=draft_order,
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        unit_price=TaxedMoney(net=net, gross=gross),
        total_price=total_price,
        quantity=3,
    )

    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeDelete"]
    assert data["productType"]["name"] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()

    with pytest.raises(order_line_in_draft._meta.model.DoesNotExist):
        order_line_in_draft.refresh_from_db()

    assert OrderLine.objects.filter(pk=order_line_not_in_draft.pk).exists()


PRODUCT_MEDIA_CREATE_QUERY = """
    mutation createProductMedia(
        $product: ID!,
        $image: Upload,
        $mediaUrl: String,
        $alt: String
    ) {
        productMediaCreate(input: {
            product: $product,
            mediaUrl: $mediaUrl,
            alt: $alt,
            image: $image
        }) {
            product {
                media {
                    url
                    alt
                    type
                    oembedData
                }
            }
            errors {
                code
                field
            }
        }
    }
    """


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_product_media_create_mutation(
    product_updated_mock,
    monkeypatch,
    staff_api_client,
    product,
    permission_manage_products,
    media_root,
):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        (
            "saleor.graphql.product.mutations.products."
            "create_product_thumbnails.delay"
        ),
        mock_create_thumbnails,
    )

    image_file, image_name = create_image()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "alt": "",
        "image": image_name,
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, image_file, image_name
    )
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    product.refresh_from_db()
    product_image = product.media.last()
    assert product_image.image.file
    img_name, format = os.path.splitext(image_file._name)
    file_name = product_image.image.name
    assert file_name != image_file._name
    assert file_name.startswith(f"products/{img_name}")
    assert file_name.endswith(format)

    # The image creation should have triggered a warm-up
    mock_create_thumbnails.assert_called_once_with(product_image.pk)
    product_updated_mock.assert_called_once_with(product)


def test_product_media_create_mutation_without_file(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "image": "image name",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    errors = content["data"]["productMediaCreate"]["errors"]
    assert errors[0]["field"] == "image"
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


@pytest.mark.vcr
def test_product_media_create_mutation_with_media_url(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "alt": "",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    media = content["data"]["productMediaCreate"]["product"]["media"]
    assert len(media) == 1
    assert media[0]["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert media[0]["alt"] == "Rick Astley - Never Gonna Give You Up (Video)"
    assert media[0]["type"] == ProductMediaTypes.VIDEO

    oembed_data = json.loads(media[0]["oembedData"])
    assert oembed_data["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert oembed_data["type"] == "video"
    assert oembed_data["html"] is not None
    assert oembed_data["thumbnail_url"] == (
        "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
    )


def test_product_media_create_mutation_without_url_or_image(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "alt": "Test Alt Text",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )

    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name
    assert errors[0]["field"] == "input"


def test_product_media_create_mutation_with_both_url_and_image(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    image_file, image_name = create_image()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://www.youtube.com/watch?v=SomeVideoID&ab_channel=Test",
        "image": image_name,
        "alt": "Test Alt Text",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, image_file, image_name
    )

    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["field"] == "input"


def test_product_media_create_mutation_with_unknown_url(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "mediaUrl": "https://www.videohosting.com/SomeVideoID",
        "alt": "Test Alt Text",
    }
    body = get_multipart_request_body(
        PRODUCT_MEDIA_CREATE_QUERY, variables, file="", file_name="name"
    )

    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    errors = content["data"]["productMediaCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.UNSUPPORTED_MEDIA_PROVIDER.name
    assert errors[0]["field"] == "mediaUrl"


def test_invalid_product_media_create_mutation(
    staff_api_client, product, permission_manage_products
):
    query = """
    mutation createProductMedia($image: Upload!, $product: ID!) {
        productMediaCreate(input: {image: $image, product: $product}) {
            media {
                id
                url
                sortOrder
            }
            errors {
                field
                message
            }
        }
    }
    """
    image_file, image_name = create_pdf_file_with_image_ext()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "image": image_name,
    }
    body = get_multipart_request_body(query, variables, image_file, image_name)

    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    assert content["data"]["productMediaCreate"]["errors"] == [
        {"field": "image", "message": "Invalid file type."}
    ]
    product.refresh_from_db()
    assert product.media.count() == 0


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_product_image_update_mutation(
    product_updated_mock,
    monkeypatch,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    query = """
    mutation updateProductMedia($mediaId: ID!, $alt: String) {
        productMediaUpdate(id: $mediaId, input: {alt: $alt}) {
            media {
                alt
            }
        }
    }
    """

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        (
            "saleor.graphql.product.mutations.products."
            "create_product_thumbnails.delay"
        ),
        mock_create_thumbnails,
    )

    media_obj = product_with_image.media.first()
    alt = "damage alt"
    variables = {
        "alt": alt,
        "mediaId": graphene.Node.to_global_id("ProductMedia", media_obj.id),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productMediaUpdate"]["media"]["alt"] == alt

    # We did not update the image field,
    # the image should not have triggered a warm-up
    assert mock_create_thumbnails.call_count == 0
    product_updated_mock.assert_called_once_with(product_with_image)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.product.signals.delete_product_media_task.delay")
def test_product_media_delete(
    delete_product_media_task_mock,
    product_updated_mock,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    product = product_with_image
    query = """
            mutation deleteProductMedia($id: ID!) {
                productMediaDelete(id: $id) {
                    media {
                        id
                        url
                    }
                }
            }
        """
    media_obj = product.media.first()
    node_id = graphene.Node.to_global_id("ProductMedia", media_obj.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productMediaDelete"]
    assert media_obj.image.url in data["media"]["url"]
    media_obj.refresh_from_db()
    assert media_obj.to_remove
    assert node_id == data["media"]["id"]
    product_updated_mock.assert_called_once_with(product)
    delete_product_media_task_mock.assert_called_once_with(media_obj.id)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_reorder_media(
    product_updated_mock,
    staff_api_client,
    product_with_images,
    permission_manage_products,
):
    query = """
    mutation reorderMedia($product_id: ID!, $media_ids: [ID!]!) {
        productMediaReorder(productId: $product_id, mediaIds: $media_ids) {
            product {
                id
            }
        }
    }
    """
    product = product_with_images
    media = product.media.all()
    media_0 = media[0]
    media_1 = media[1]
    media_0_id = graphene.Node.to_global_id("ProductMedia", media_0.id)
    media_1_id = graphene.Node.to_global_id("ProductMedia", media_1.id)
    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {"product_id": product_id, "media_ids": [media_1_id, media_0_id]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)

    # Check if order has been changed
    product.refresh_from_db()
    reordered_media = product.media.all()
    reordered_media_0 = reordered_media[0]
    reordered_media_1 = reordered_media[1]

    assert media_0.id == reordered_media_1.id
    assert media_1.id == reordered_media_0.id
    product_updated_mock.assert_called_once_with(product)


@pytest.mark.django_db(transaction=True)
def test_reorder_not_existing_media(
    staff_api_client,
    product_with_images,
    permission_manage_products,
):
    query = """
    mutation reorderMedia($product_id: ID!, $media_ids: [ID!]!) {
        productMediaReorder(productId: $product_id, mediaIds: $media_ids) {
            product {
                id
            }
            errors{
            field
            code
            message
        }
        }
    }
    """
    product = product_with_images
    media = product.media.all()
    media_0 = media[0]
    media_1 = media[1]
    media_0_id = graphene.Node.to_global_id("ProductMedia", media_0.id)
    media_1_id = graphene.Node.to_global_id("ProductMedia", media_1.id)
    product_id = graphene.Node.to_global_id("Product", product.id)

    def delete_media(*args, **kwargs):
        with transaction.atomic():
            media.delete()

    with before_after.before(
        "saleor.graphql.product.mutations.products.update_ordered_media", delete_media
    ):
        variables = {"product_id": product_id, "media_ids": [media_1_id, media_0_id]}
        response = staff_api_client.post_graphql(
            query, variables, permissions=[permission_manage_products]
        )
    response = get_graphql_content(response, ignore_errors=True)
    assert (
        response["data"]["productMediaReorder"]["errors"][0]["code"]
        == ProductErrorCode.NOT_FOUND.name
    )


ASSIGN_VARIANT_QUERY = """
    mutation assignVariantMediaMutation($variantId: ID!, $mediaId: ID!) {
        variantMediaAssign(variantId: $variantId, mediaId: $mediaId) {
            errors {
                field
                message
                code
            }
            productVariant {
                id
            }
        }
    }
"""


def test_assign_variant_media(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    media_obj = product_with_image.media.first()

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "mediaId": to_global_id("ProductMedia", media_obj.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.media.first() == media_obj


def test_assign_variant_media_second_time(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    # given
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    media_obj = product_with_image.media.first()
    media_obj.variant_media.create(variant=variant)

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "mediaId": to_global_id("ProductMedia", media_obj.pk),
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content_from_response(response)["data"]["variantMediaAssign"]
    assert "errors" in content
    errors = content["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == ProductErrorCode.MEDIA_ALREADY_ASSIGNED.name


def test_assign_variant_media_from_different_product(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    product_with_image.pk = None
    product_with_image.slug = "product-with-image"
    product_with_image.save()

    media_obj_2 = ProductMedia.objects.create(product=product_with_image)
    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "mediaId": to_global_id("ProductMedia", media_obj_2.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["variantMediaAssign"]["errors"][0]["field"] == "mediaId"

    # check permissions
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


UNASSIGN_VARIANT_IMAGE_QUERY = """
    mutation unassignVariantMediaMutation($variantId: ID!, $mediaId: ID!) {
        variantMediaUnassign(variantId: $variantId, mediaId: $mediaId) {
            errors {
                field
                message
            }
            productVariant {
                id
            }
        }
    }
"""


def test_unassign_variant_media_image(
    staff_api_client, product_with_image, permission_manage_products
):
    query = UNASSIGN_VARIANT_IMAGE_QUERY

    media = product_with_image.media.first()
    variant = product_with_image.variants.first()
    variant.variant_media.create(media=media)

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "mediaId": to_global_id("ProductMedia", media.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.media.count() == 0


def test_unassign_not_assigned_variant_media_image(
    staff_api_client, product_with_image, permission_manage_products
):
    query = UNASSIGN_VARIANT_IMAGE_QUERY
    variant = product_with_image.variants.first()
    media = ProductMedia.objects.create(product=product_with_image)
    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "mediaId": to_global_id("ProductMedia", media.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["variantMediaUnassign"]["errors"][0]["field"] == ("mediaId")


@patch("saleor.product.tasks.update_variants_names.delay")
def test_product_type_update_changes_variant_name(
    mock_update_variants_names,
    staff_api_client,
    product_type,
    product,
    permission_manage_product_types_and_attributes,
):
    query = """
    mutation updateProductType(
        $id: ID!,
        $hasVariants: Boolean!,
        $isShippingRequired: Boolean!,
        $variantAttributes: [ID!],
        ) {
            productTypeUpdate(
            id: $id,
            input: {
                hasVariants: $hasVariants,
                isShippingRequired: $isShippingRequired,
                variantAttributes: $variantAttributes}) {
                productType {
                    id
                }
              }
            }
    """
    variant = product.variants.first()
    variant.name = "test name"
    variant.save()
    has_variants = True
    require_shipping = False
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)

    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in variant_attributes
    ]
    variables = {
        "id": product_type_id,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "variantAttributes": variant_attributes_ids,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    get_graphql_content(response)
    variant_attributes = set(variant_attributes)
    variant_attributes_ids = [attr.pk for attr in variant_attributes]
    mock_update_variants_names.assert_called_once_with(
        product_type.pk, variant_attributes_ids
    )


@patch("saleor.product.tasks._update_variants_names")
def test_product_update_variants_names(mock__update_variants_names, product_type):
    variant_attributes = [product_type.variant_attributes.first()]
    variant_attr_ids = [attr.pk for attr in variant_attributes]
    update_variants_names(product_type.pk, variant_attr_ids)
    assert mock__update_variants_names.call_count == 1


QUERY_PRODUCT_VARAINT_BY_ID = """
    query getProductVariant($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            id
            name
            sku
        }
    }
"""


def test_product_variant_without_price_by_id_as_staff_with_permission(
    staff_api_client, variant, channel_USD, permission_manage_products
):
    query = QUERY_PRODUCT_VARAINT_BY_ID
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": variant_id, "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["id"] == variant_id


def test_product_variant_without_price_by_id_as_staff_without_permission(
    staff_api_client, variant, channel_USD
):
    query = QUERY_PRODUCT_VARAINT_BY_ID
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": variant_id, "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_product_variant_without_price_by_id_as_app_without_permission(
    app_api_client, variant, channel_USD
):
    query = QUERY_PRODUCT_VARAINT_BY_ID
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": variant_id, "channel": channel_USD.slug}
    response = app_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_product_variant_without_price_by_id_as_app_with_permission(
    app_api_client, variant, channel_USD, permission_manage_products
):
    query = QUERY_PRODUCT_VARAINT_BY_ID
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": variant_id, "channel": channel_USD.slug}
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["id"] == variant_id


def test_product_variant_without_price_by_id_as_user(
    user_api_client, variant, channel_USD
):
    query = QUERY_PRODUCT_VARAINT_BY_ID
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"id": variant_id, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data is None


def test_variant_query_invalid_id(user_api_client, variant, channel_USD):
    variant_id = "'"
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_VARAINT_BY_ID, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {variant_id}."
    assert content["data"]["productVariant"] is None


def test_variant_query_object_with_given_id_does_not_exist(
    user_api_client, variant, channel_USD
):
    variant_id = graphene.Node.to_global_id("ProductVariant", -1)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_VARAINT_BY_ID, variables)
    content = get_graphql_content(response)
    assert content["data"]["productVariant"] is None


def test_variant_query_with_invalid_object_type(user_api_client, variant, channel_USD):
    variant_id = graphene.Node.to_global_id("Product", variant.pk)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_PRODUCT_VARAINT_BY_ID, variables)
    content = get_graphql_content(response)
    assert content["data"]["productVariant"] is None


def test_product_variant_without_price_by_sku_as_staff_with_permission(
    staff_api_client, variant, channel_USD, permission_manage_products
):
    query = """
        query getProductVariant($sku: String!, $channel: String) {
            productVariant(sku: $sku, channel: $channel) {
                id
                name
                sku
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"sku": variant.sku, "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["id"] == variant_id


def test_product_variant_without_price_by_sku_as_staff_without_permission(
    staff_api_client, variant, channel_USD
):
    query = """
        query getProductVariant($sku: String!, $channel: String) {
            productVariant(sku: $sku, channel: $channel) {
                id
                name
                sku
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)

    variables = {"sku": variant.sku, "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_product_variant_without_price_by_sku_as_app_with_permission(
    app_api_client, variant, channel_USD, permission_manage_products
):
    query = """
        query getProductVariant($sku: String!, $channel: String) {
            productVariant(sku: $sku, channel: $channel) {
                id
                name
                sku
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"sku": variant.sku, "channel": channel_USD.slug}
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["id"] == variant_id


def test_product_variant_without_price_by_sku_as_app_without_permission(
    app_api_client,
    variant,
    channel_USD,
):
    query = """
        query getProductVariant($sku: String!, $channel: String) {
            productVariant(sku: $sku, channel: $channel) {
                id
                name
                sku
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)

    variables = {"sku": variant.sku, "channel": channel_USD.slug}
    response = app_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]


def test_product_variant_without_price_by_sku_as_user(
    user_api_client, variant, channel_USD
):
    query = """
        query getProductVariant($sku: String!, $channel: String) {
            productVariant(sku: $sku, channel: $channel) {
                id
                name
                sku
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)

    variables = {"sku": variant.sku, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data is None


def test_product_variants_by_ids(staff_api_client, variant, channel_USD):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["edges"][0]["node"]["id"] == variant_id
    assert len(data["edges"]) == 1


def test_product_variants_without_price_by_ids_as_staff_without_permission(
    staff_api_client, variant, channel_USD
):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert len(data["edges"]) == 0


def test_product_variants_without_price_by_ids_as_staff_with_permission(
    staff_api_client, variant, channel_USD, permission_manage_products
):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["edges"][0]["node"]["id"] == variant_id
    assert len(data["edges"]) == 1


def test_product_variants_without_price_by_ids_as_user(
    user_api_client, variant, channel_USD
):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                    }
                }
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert len(data["edges"]) == 0


def test_product_variants_without_price_by_ids_as_app_without_permission(
    app_api_client, variant, channel_USD
):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = app_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert len(content["data"]["productVariants"]["edges"]) == 0


def test_product_variants_without_price_by_ids_as_app_with_permission(
    app_api_client, variant, channel_USD, permission_manage_products
):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant.channel_listings.all().delete()
    variant.channel_listings.create(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["edges"][0]["node"]["id"] == variant_id
    assert len(data["edges"]) == 1


def test_product_variants_by_customer(user_api_client, variant, channel_USD):
    query = """
        query getProductVariants($ids: [ID!], $channel: String) {
            productVariants(ids: $ids, first: 1, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        sku
                        channelListings {
                            channel {
                                id
                                isActive
                                name
                                currencyCode
                            }
                            price {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id], "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_product_variants_no_ids_list(user_api_client, variant, channel_USD):
    query = """
        query getProductVariants($channel: String) {
            productVariants(first: 10, channel: $channel) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    variables = {"channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert len(data["edges"]) == ProductVariant.objects.count()


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
    "variant_price_amount, api_variant_price",
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


QUERY_GET_PRODUCT_VARIANTS_PRICING_NO_ADDRESS = """
    query getProductVariants($id: ID!, $channel: String) {
        product(id: $id, channel: $channel) {
            variants {
                id
                pricing {
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


@mock.patch(
    "saleor.graphql.product.types.products.get_variant_availability",
    wraps=get_variant_availability,
)
def test_product_variant_price_no_address(
    mock_get_variant_availability, user_api_client, variant, stock, channel_USD
):
    channel_USD.default_country = "FR"
    channel_USD.save()
    product_id = graphene.Node.to_global_id("Product", variant.product.id)
    variables = {"id": product_id, "channel": channel_USD.slug}
    user_api_client.post_graphql(
        QUERY_GET_PRODUCT_VARIANTS_PRICING_NO_ADDRESS, variables
    )
    assert (
        mock_get_variant_availability.call_args[1]["country"]
        == channel_USD.default_country
    )


QUERY_REPORT_PRODUCT_SALES = """
query TopProducts($period: ReportingPeriod!, $channel: String!) {
    reportProductSales(period: $period, first: 20, channel: $channel) {
        edges {
            node {
                revenue(period: $period) {
                    gross {
                        amount
                    }
                }
                quantityOrdered
                sku
            }
        }
    }
}
"""


def test_report_product_sales(
    staff_api_client,
    order_with_lines,
    order_with_lines_channel_PLN,
    permission_manage_products,
    permission_manage_orders,
    channel_USD,
):
    order = order_with_lines
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_USD.slug}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(
        QUERY_REPORT_PRODUCT_SALES, variables, permissions
    )
    content = get_graphql_content(response)
    edges = content["data"]["reportProductSales"]["edges"]

    node_a = edges[0]["node"]
    line_a = order.lines.get(product_sku=node_a["sku"])
    assert node_a["quantityOrdered"] == line_a.quantity
    amount = str(node_a["revenue"]["gross"]["amount"])
    assert Decimal(amount) == line_a.quantity * line_a.unit_price_gross_amount

    node_b = edges[1]["node"]
    line_b = order.lines.get(product_sku=node_b["sku"])
    assert node_b["quantityOrdered"] == line_b.quantity
    amount = str(node_b["revenue"]["gross"]["amount"])
    assert Decimal(amount) == line_b.quantity * line_b.unit_price_gross_amount


def test_report_product_sales_channel_pln(
    staff_api_client,
    order_with_lines,
    order_with_lines_channel_PLN,
    permission_manage_products,
    permission_manage_orders,
    channel_PLN,
):
    order = order_with_lines_channel_PLN
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_PLN.slug}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(
        QUERY_REPORT_PRODUCT_SALES, variables, permissions
    )
    content = get_graphql_content(response)
    edges = content["data"]["reportProductSales"]["edges"]

    node_a = edges[0]["node"]
    line_a = order.lines.get(product_sku=node_a["sku"])
    assert node_a["quantityOrdered"] == line_a.quantity
    amount = str(node_a["revenue"]["gross"]["amount"])
    assert Decimal(amount) == line_a.quantity * line_a.unit_price_gross_amount

    node_b = edges[1]["node"]
    line_b = order.lines.get(product_sku=node_b["sku"])
    assert node_b["quantityOrdered"] == line_b.quantity
    amount = str(node_b["revenue"]["gross"]["amount"])
    assert Decimal(amount) == line_b.quantity * line_b.unit_price_gross_amount


def test_report_product_sales_not_existing_channel(
    staff_api_client,
    order_with_lines,
    order_with_lines_channel_PLN,
    permission_manage_products,
    permission_manage_orders,
):
    variables = {"period": ReportingPeriod.TODAY.name, "channel": "not-existing"}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(
        QUERY_REPORT_PRODUCT_SALES, variables, permissions
    )
    content = get_graphql_content(response)
    assert not content["data"]["reportProductSales"]["edges"]


def test_product_restricted_fields_permissions(
    staff_api_client,
    permission_manage_products,
    permission_manage_orders,
    product,
    channel_USD,
):
    """Ensure non-public (restricted) fields are correctly requiring
    the 'manage_products' permission.
    """
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


@pytest.mark.parametrize(
    "field, is_nested",
    (("digitalContent", True), ("quantityOrdered", False)),
)
def test_variant_restricted_fields_permissions(
    staff_api_client,
    permission_manage_products,
    permission_manage_orders,
    product,
    field,
    is_nested,
    channel_USD,
):
    """Ensure non-public (restricted) fields are correctly requiring
    the 'manage_products' permission.
    """
    query = """
    query ProductVariant($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            %(field)s
        }
    }
    """ % {
        "field": field if not is_nested else "%s { __typename }" % field
    }
    variant = product.variants.first()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert field in content["data"]["productVariant"]


def test_variant_digital_content(
    staff_api_client, permission_manage_products, digital_content, channel_USD
):
    query = """
    query Margin($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            digitalContent{
                id
            }
        }
    }
    """
    variant = digital_content.product_variant
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }
    permissions = [permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert "digitalContent" in content["data"]["productVariant"]
    assert "id" in content["data"]["productVariant"]["digitalContent"]


@pytest.mark.parametrize(
    "collection_filter, count",
    [
        ({"published": "PUBLISHED"}, 2),
        ({"published": "HIDDEN"}, 1),
        ({"search": "-published1"}, 1),
        ({"search": "Collection3"}, 1),
        ({"ids": [to_global_id("Collection", 2), to_global_id("Collection", 3)]}, 2),
    ],
)
def test_collections_query_with_filter(
    collection_filter,
    count,
    query_collections_with_filter,
    channel_USD,
    staff_api_client,
    permission_manage_products,
):
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
    variables = {
        "filter": collection_filter,
        "channel": channel_USD.slug,
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_collections_with_filter, variables)
    content = get_graphql_content(response)
    collections = content["data"]["collections"]["edges"]

    assert len(collections) == count


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
    "collection_sort, result_order",
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


@pytest.mark.parametrize(
    "category_filter, count",
    [
        ({"search": "slug_"}, 4),
        ({"search": "Category1"}, 1),
        ({"search": "cat1"}, 3),
        ({"search": "Description cat1."}, 2),
        ({"search": "Subcategory_description"}, 1),
        ({"ids": [to_global_id("Category", 2), to_global_id("Category", 3)]}, 2),
    ],
)
def test_categories_query_with_filter(
    category_filter,
    count,
    query_categories_with_filter,
    staff_api_client,
    permission_manage_products,
):
    Category.objects.create(
        id=1,
        name="Category1",
        slug="slug_category1",
        description=dummy_editorjs("Description cat1."),
        description_plaintext="Description cat1.",
    )
    Category.objects.create(
        id=2,
        name="Category2",
        slug="slug_category2",
        description=dummy_editorjs("Description cat2."),
        description_plaintext="Description cat2.",
    )

    Category.objects.create(
        id=3,
        name="SubCategory",
        slug="slug_subcategory",
        parent=Category.objects.get(name="Category1"),
        description=dummy_editorjs("Subcategory_description of cat1."),
        description_plaintext="Subcategory_description of cat1.",
    )
    Category.objects.create(
        id=4,
        name="DoubleSubCategory",
        slug="slug_subcategory4",
        description=dummy_editorjs("Super important Description cat1."),
        description_plaintext="Super important Description cat1.",
    )
    variables = {"filter": category_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_categories_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["categories"]["totalCount"] == count


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
    """Ensure that using the cursor in sorting collections by published at date works
    properly."""
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


QUERY_CATEGORIES_WITH_SORT = """
    query ($sort_by: CategorySortingInput!) {
        categories(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "category_sort, result_order",
    [
        (
            {"field": "NAME", "direction": "ASC"},
            ["Cat1", "Cat2", "SubCat", "SubSubCat"],
        ),
        (
            {"field": "NAME", "direction": "DESC"},
            ["SubSubCat", "SubCat", "Cat2", "Cat1"],
        ),
        (
            {"field": "SUBCATEGORY_COUNT", "direction": "ASC"},
            ["Cat2", "SubSubCat", "Cat1", "SubCat"],
        ),
        (
            {"field": "SUBCATEGORY_COUNT", "direction": "DESC"},
            ["SubCat", "Cat1", "SubSubCat", "Cat2"],
        ),
        (
            {"field": "PRODUCT_COUNT", "direction": "ASC"},
            ["Cat2", "SubCat", "SubSubCat", "Cat1"],
        ),
        (
            {"field": "PRODUCT_COUNT", "direction": "DESC"},
            ["Cat1", "SubSubCat", "SubCat", "Cat2"],
        ),
    ],
)
def test_categories_query_with_sort(
    category_sort,
    result_order,
    staff_api_client,
    permission_manage_products,
    product_type,
):
    cat1 = Category.objects.create(
        name="Cat1",
        slug="slug_category1",
        description=dummy_editorjs("Description cat1."),
    )
    Product.objects.create(
        name="Test",
        slug="test",
        product_type=product_type,
        category=cat1,
    )
    Category.objects.create(
        name="Cat2",
        slug="slug_category2",
        description=dummy_editorjs("Description cat2."),
    )
    Category.objects.create(
        name="SubCat",
        slug="slug_subcategory1",
        parent=Category.objects.get(name="Cat1"),
        description=dummy_editorjs("Subcategory_description of cat1."),
    )
    subsubcat = Category.objects.create(
        name="SubSubCat",
        slug="slug_subcategory2",
        parent=Category.objects.get(name="SubCat"),
        description=dummy_editorjs("Subcategory_description of cat1."),
    )
    Product.objects.create(
        name="Test2",
        slug="test2",
        product_type=product_type,
        category=subsubcat,
    )
    variables = {"sort_by": category_sort}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_CATEGORIES_WITH_SORT, variables)
    content = get_graphql_content(response)
    categories = content["data"]["categories"]["edges"]

    for order, category_name in enumerate(result_order):
        assert categories[order]["node"]["name"] == category_name


@pytest.mark.parametrize(
    "product_type_filter, count",
    [
        ({"configurable": "CONFIGURABLE"}, 2),  # has_variants
        ({"configurable": "SIMPLE"}, 1),  # !has_variants
        ({"productType": "DIGITAL"}, 1),
        ({"productType": "SHIPPABLE"}, 2),  # is_shipping_required
        ({"kind": "NORMAL"}, 2),
        ({"kind": "GIFT_CARD"}, 1),
    ],
)
def test_product_type_query_with_filter(
    product_type_filter, count, staff_api_client, permission_manage_products
):
    query = """
        query ($filter: ProductTypeFilterInput!, ) {
          productTypes(first:5, filter: $filter) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
        """
    ProductType.objects.bulk_create(
        [
            ProductType(
                name="Digital Type",
                slug="digital-type",
                has_variants=True,
                is_shipping_required=False,
                is_digital=True,
                kind=ProductTypeKind.NORMAL,
            ),
            ProductType(
                name="Tools",
                slug="tools",
                has_variants=True,
                is_shipping_required=True,
                is_digital=False,
                kind=ProductTypeKind.NORMAL,
            ),
            ProductType(
                name="Books",
                slug="books",
                has_variants=False,
                is_shipping_required=True,
                is_digital=False,
                kind=ProductTypeKind.GIFT_CARD,
            ),
        ]
    )

    variables = {"filter": product_type_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    product_types = content["data"]["productTypes"]["edges"]

    assert len(product_types) == count


QUERY_PRODUCT_TYPE_WITH_SORT = """
    query ($sort_by: ProductTypeSortingInput!) {
        productTypes(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "product_type_sort, result_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["Digital", "Subscription", "Tools"]),
        ({"field": "NAME", "direction": "DESC"}, ["Tools", "Subscription", "Digital"]),
        # is_digital
        (
            {"field": "DIGITAL", "direction": "ASC"},
            ["Subscription", "Tools", "Digital"],
        ),
        (
            {"field": "DIGITAL", "direction": "DESC"},
            ["Digital", "Tools", "Subscription"],
        ),
        # is_shipping_required
        (
            {"field": "SHIPPING_REQUIRED", "direction": "ASC"},
            ["Digital", "Subscription", "Tools"],
        ),
        (
            {"field": "SHIPPING_REQUIRED", "direction": "DESC"},
            ["Tools", "Subscription", "Digital"],
        ),
    ],
)
def test_product_type_query_with_sort(
    product_type_sort, result_order, staff_api_client, permission_manage_products
):
    ProductType.objects.bulk_create(
        [
            ProductType(
                name="Digital",
                slug="digital",
                has_variants=True,
                is_shipping_required=False,
                is_digital=True,
            ),
            ProductType(
                name="Tools",
                slug="tools",
                has_variants=True,
                is_shipping_required=True,
                is_digital=False,
            ),
            ProductType(
                name="Subscription",
                slug="subscription",
                has_variants=False,
                is_shipping_required=False,
                is_digital=False,
            ),
        ]
    )

    variables = {"sort_by": product_type_sort}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_PRODUCT_TYPE_WITH_SORT, variables)
    content = get_graphql_content(response)
    product_types = content["data"]["productTypes"]["edges"]

    for order, product_type_name in enumerate(result_order):
        assert product_types[order]["node"]["name"] == product_type_name


NOT_EXISTS_IDS_COLLECTIONS_QUERY = """
    query ($filter: ProductTypeFilterInput!) {
        productTypes(first: 5, filter: $filter) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""


def test_product_types_query_ids_not_exists(user_api_client, category):
    query = NOT_EXISTS_IDS_COLLECTIONS_QUERY
    variables = {"filter": {"ids": ["fTEJRuFHU6fd2RU=", "2XwnQNNhwCdEjhP="]}}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    message_error = '{"ids": [{"message": "Invalid ID specified.", "code": ""}]}'

    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["productTypes"] is None


QUERY_AVAILABLE_ATTRIBUTES = """
    query($productTypeId:ID!, $filters: AttributeFilterInput) {
      productType(id: $productTypeId) {
        availableAttributes(first: 10, filter: $filters) {
          edges {
            node {
              id
              slug
            }
          }
        }
      }
    }
"""


def test_product_type_get_unassigned_product_type_attributes(
    staff_api_client, permission_manage_products
):
    query = QUERY_AVAILABLE_ATTRIBUTES
    target_product_type, ignored_product_type = ProductType.objects.bulk_create(
        [
            ProductType(name="Type 1", slug="type-1"),
            ProductType(name="Type 2", slug="type-2"),
        ]
    )

    unassigned_attributes = list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="size", name="Size", type=AttributeType.PRODUCT_TYPE),
                Attribute(
                    slug="weight", name="Weight", type=AttributeType.PRODUCT_TYPE
                ),
                Attribute(
                    slug="thickness", name="Thickness", type=AttributeType.PRODUCT_TYPE
                ),
            ]
        )
    )

    unassigned_page_attributes = list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="length", name="Length", type=AttributeType.PAGE_TYPE),
                Attribute(slug="width", name="Width", type=AttributeType.PAGE_TYPE),
            ]
        )
    )

    assigned_attributes = list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="color", name="Color", type=AttributeType.PRODUCT_TYPE),
                Attribute(slug="type", name="Type", type=AttributeType.PRODUCT_TYPE),
            ]
        )
    )

    # Ensure that assigning them to another product type
    # doesn't return an invalid response
    ignored_product_type.product_attributes.add(*unassigned_attributes)
    ignored_product_type.product_attributes.add(*unassigned_page_attributes)

    # Assign the other attributes to the target product type
    target_product_type.product_attributes.add(*assigned_attributes)

    gql_unassigned_attributes = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            {
                "productTypeId": graphene.Node.to_global_id(
                    "ProductType", target_product_type.pk
                )
            },
            permissions=[permission_manage_products],
        )
    )["data"]["productType"]["availableAttributes"]["edges"]

    assert len(gql_unassigned_attributes) == len(
        unassigned_attributes
    ), gql_unassigned_attributes

    received_ids = sorted((attr["node"]["id"] for attr in gql_unassigned_attributes))
    expected_ids = sorted(
        (
            graphene.Node.to_global_id("Attribute", attr.pk)
            for attr in unassigned_attributes
        )
    )

    assert received_ids == expected_ids


def test_product_type_filter_unassigned_attributes(
    staff_api_client, permission_manage_products, product_type_attribute_list
):
    expected_attribute = product_type_attribute_list[0]
    query = QUERY_AVAILABLE_ATTRIBUTES
    product_type = ProductType.objects.create(
        name="Empty Type", kind=ProductTypeKind.NORMAL
    )
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    filters = {"search": expected_attribute.name}

    found_attributes = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            {"productTypeId": product_type_id, "filters": filters},
            permissions=[permission_manage_products],
        )
    )["data"]["productType"]["availableAttributes"]["edges"]

    assert len(found_attributes) == 1

    _, attribute_id = graphene.Node.from_global_id(found_attributes[0]["node"]["id"])
    assert attribute_id == str(expected_attribute.pk)


QUERY_FILTER_PRODUCT_TYPES = """
    query($filters: ProductTypeFilterInput) {
      productTypes(first: 10, filter: $filters) {
        edges {
          node {
            name
          }
        }
      }
    }
"""


@pytest.mark.parametrize(
    "search, expected_names",
    (
        ("", ["The best juices", "The best beers", "The worst beers"]),
        ("best", ["The best juices", "The best beers"]),
        ("worst", ["The worst beers"]),
        ("average", []),
    ),
)
def test_filter_product_types_by_custom_search_value(
    api_client, search, expected_names
):
    query = QUERY_FILTER_PRODUCT_TYPES

    ProductType.objects.bulk_create(
        [
            ProductType(name="The best juices", slug="best-juices"),
            ProductType(name="The best beers", slug="best-beers"),
            ProductType(name="The worst beers", slug="worst-beers"),
        ]
    )

    variables = {"filters": {"search": search}}

    results = get_graphql_content(api_client.post_graphql(query, variables))["data"][
        "productTypes"
    ]["edges"]

    assert len(results) == len(expected_names)
    matched_names = sorted([result["node"]["name"] for result in results])

    assert matched_names == sorted(expected_names)


def test_product_filter_by_attribute_values(
    user_api_client,
    permission_manage_products,
    color_attribute,
    pink_attribute_value,
    product_with_variant_with_two_attributes,
    channel_USD,
):
    query = """
    query Products($filters: ProductFilterInput, $channel: String) {
      products(first: 5, filter: $filters, channel: $channel) {
        edges {
        node {
          id
          name
          attributes {
            attribute {
              name
              slug
            }
            values {
              name
              slug
            }
          }
        }
        }
      }
    }
    """
    variables = {
        "attributes": [
            {"slug": color_attribute.slug, "values": [pink_attribute_value.slug]}
        ],
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["products"]["edges"] == [
        {
            "node": {
                "attributes": [],
                "name": product_with_variant_with_two_attributes.name,
            }
        }
    ]


MUTATION_CREATE_PRODUCT_WITH_STOCKS = """
mutation createProduct(
        $productType: ID!,
        $category: ID!
        $name: String!,
        $sku: String,
        $stocks: [StockInput!],
        $basePrice: PositiveDecimal!,
        $trackInventory: Boolean,
        $country: CountryCode
        )
    {
        productCreate(
            input: {
                category: $category,
                productType: $productType,
                name: $name,
                sku: $sku,
                stocks: $stocks,
                trackInventory: $trackInventory,
                basePrice: $basePrice,
            })
        {
            product {
                id
                name
                variants{
                    id
                    sku
                    trackInventory
                    quantityAvailable(countryCode: $country)
                }
            }
            errors {
                message
                field
                code
            }
        }
    }
    """


def test_create_stocks_failed(product_with_single_variant, warehouse):
    variant = product_with_single_variant.variants.first()

    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
        {"quantity": 10, "warehouse": "321"},
    ]
    warehouses = [warehouse, second_warehouse]
    with pytest.raises(ValidationError):
        create_stocks(variant, stocks_data, warehouses)


def test_create_stocks(variant, warehouse):
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    assert variant.stocks.count() == 0

    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
        {"quantity": 10, "warehouse": "321"},
    ]
    warehouses = [warehouse, second_warehouse]
    create_stocks(variant, stocks_data, warehouses)

    assert variant.stocks.count() == len(stocks_data)
    assert {stock.warehouse.pk for stock in variant.stocks.all()} == {
        warehouse.pk for warehouse in warehouses
    }
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }


def test_update_or_create_variant_stocks(variant, warehouses):
    Stock.objects.create(
        product_variant=variant,
        warehouse=warehouses[0],
        quantity=5,
    )
    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
        {"quantity": 10, "warehouse": "321"},
    ]

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses, get_plugins_manager()
    )

    variant.refresh_from_db()
    assert variant.stocks.count() == 2
    assert {stock.warehouse.pk for stock in variant.stocks.all()} == {
        warehouse.pk for warehouse in warehouses
    }
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_update_or_create_variant_stocks_when_stock_out_of_quantity(
    back_in_stock_webhook_trigger, variant, warehouses
):
    stock = Stock.objects.create(
        product_variant=variant,
        warehouse=warehouses[0],
        quantity=-5,
    )
    stocks_data = [{"quantity": 10, "warehouse": "321"}]

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses, get_plugins_manager()
    )

    variant.refresh_from_db()
    flush_post_commit_hooks()
    assert variant.stocks.count() == 1
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }
    back_in_stock_webhook_trigger.assert_called_once_with(stock)
    assert variant.stocks.all()[0].quantity == 10


def test_update_or_create_variant_stocks_empty_stocks_data(variant, warehouses):
    Stock.objects.create(
        product_variant=variant,
        warehouse=warehouses[0],
        quantity=5,
    )

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, [], warehouses, get_plugins_manager()
    )

    variant.refresh_from_db()
    assert variant.stocks.count() == 1
    stock = variant.stocks.first()
    assert stock.warehouse == warehouses[0]
    assert stock.quantity == 5


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_update_or_create_variant_with_back_in_stock_webhooks_only_success(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    settings,
    variant,
    warehouses,
    info,
):

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse)
            for warehouse in warehouses
        ]
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    info.context.plugins = get_plugins_manager()
    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
    ]
    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 0

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses, info.context.plugins
    )

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 10

    flush_post_commit_hooks()
    product_variant_back_in_stock_webhook.assert_called_once_with(
        Stock.objects.all()[1]
    )
    product_variant_stock_out_of_stock_webhook.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_update_or_create_variant_with_back_in_stock_webhooks_only_failed(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    settings,
    variant,
    warehouses,
    info,
):

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse)
            for warehouse in warehouses
        ]
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    info.context.plugins = get_plugins_manager()
    stocks_data = [
        {"quantity": 0, "warehouse": "123"},
    ]
    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 0

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses, info.context.plugins
    )

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 0

    flush_post_commit_hooks()
    product_variant_back_in_stock_webhook.assert_not_called()
    product_variant_stock_out_of_stock_webhook.assert_called_once_with(
        Stock.objects.all()[1]
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_update_or_create_variant_stocks_with_out_of_stock_webhook_only(
    product_variant_stock_out_of_stock_webhook,
    product_variant_back_in_stock_webhook,
    settings,
    variant,
    warehouses,
    info,
):

    Stock.objects.bulk_create(
        [
            Stock(product_variant=variant, warehouse=warehouse, quantity=5)
            for warehouse in warehouses
        ]
    )

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    info.context.plugins = get_plugins_manager()

    stocks_data = [
        {"quantity": 0, "warehouse": "123"},
        {"quantity": 2, "warehouse": "321"},
    ]

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 10

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses, info.context.plugins
    )

    assert variant.stocks.aggregate(Sum("quantity"))["quantity__sum"] == 2

    flush_post_commit_hooks()

    product_variant_stock_out_of_stock_webhook.assert_called_once_with(
        Stock.objects.last()
    )
    product_variant_back_in_stock_webhook.assert_not_called()


# Because we use Scalars for Weight this test query tests only a scenario when weight
# value is passed by a variable
MUTATION_CREATE_PRODUCT_WITH_WEIGHT_GQL_VARIABLE = """
mutation createProduct(
        $productType: ID!,
        $category: ID!
        $name: String!,
        $weight: WeightScalar)
    {
        productCreate(
            input: {
                category: $category,
                productType: $productType,
                name: $name,
                weight: $weight
            })
        {
            product {
                id
                weight{
                    value
                    unit
                }
            }
            errors {
                message
                field
                code
            }
        }
    }
    """


@pytest.mark.parametrize(
    "weight, expected_weight_value",
    (
        ("0", 0),
        (0, 0),
        (11.11, 11.11),
        (11, 11.0),
        ("11.11", 11.11),
        ({"value": 11.11, "unit": "kg"}, 11.11),
        ({"value": 11, "unit": "g"}, 0.011),
        ({"value": "1", "unit": "ounce"}, 0.028),
    ),
)
def test_create_product_with_weight_variable(
    weight,
    expected_weight_value,
    staff_api_client,
    category,
    permission_manage_products,
    product_type_without_variant,
    site_settings,
):
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_type_id = graphene.Node.to_global_id(
        "ProductType", product_type_without_variant.pk
    )
    variables = {
        "category": category_id,
        "productType": product_type_id,
        "name": "Test",
        "weight": weight,
    }
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PRODUCT_WITH_WEIGHT_GQL_VARIABLE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    result_weight = content["data"]["productCreate"]["product"]["weight"]
    assert result_weight["value"] == expected_weight_value
    assert result_weight["unit"] == site_settings.default_weight_unit.upper()


@pytest.mark.parametrize(
    "weight, expected_weight_value",
    (
        ("0", 0),
        (0, 0),
        ("11.11", 11.11),
        ("11", 11.0),
        ('"11.11"', 11.11),
        ('{value: 11.11, unit: "kg"}', 11.11),
        ('{value: 11, unit: "g"}', 0.011),
        ('{value: "1", unit: "ounce"}', 0.028),
    ),
)
def test_create_product_with_weight_input(
    weight,
    expected_weight_value,
    staff_api_client,
    category,
    permission_manage_products,
    product_type_without_variant,
    site_settings,
):
    # Because we use Scalars for Weight this test query tests only a scenario when
    # weight value is passed by directly in input
    query = f"""
    mutation createProduct(
            $productType: ID!,
            $category: ID!,
            $name: String!)
        {{
            productCreate(
                input: {{
                    category: $category,
                    productType: $productType,
                    name: $name,
                    weight: {weight}
                }})
            {{
                product {{
                    id
                    weight{{
                        value
                        unit
                    }}
                }}
                errors {{
                    message
                    field
                    code
                }}
            }}
        }}
    """
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_type_id = graphene.Node.to_global_id(
        "ProductType", product_type_without_variant.pk
    )
    variables = {
        "category": category_id,
        "productType": product_type_id,
        "name": "Test",
    }
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    result_weight = content["data"]["productCreate"]["product"]["weight"]
    assert result_weight["value"] == expected_weight_value
    assert result_weight["unit"] == site_settings.default_weight_unit.upper()


def test_hidden_product_access_with_proper_permissions(
    staff_api_client,
    product_list,
    channel_USD,
    permission_manage_products,
):
    hidden_product = product_list[0]
    hidden_product.channel_listings.all().update(is_published=False)

    variables = {
        "channel": channel_USD.slug,
    }

    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables=variables,
        permissions=(permission_manage_products,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    total_count = content["data"]["products"]["totalCount"]
    assert total_count == 3


def test_hidden_product_access_with_permission_manage_orders(
    staff_api_client,
    product_list,
    channel_USD,
    permission_manage_orders,
):
    hidden_product = product_list[0]
    hidden_product.channel_listings.all().update(is_published=False)

    variables = {
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables=variables,
        permissions=(permission_manage_orders,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    total_count = content["data"]["products"]["totalCount"]
    assert total_count == 3


def test_hidden_product_access_with_permission_manage_discounts(
    staff_api_client,
    product_list,
    channel_USD,
    permission_manage_discounts,
):
    hidden_product = product_list[0]
    hidden_product.channel_listings.all().update(is_published=False)

    variables = {
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables=variables,
        permissions=(permission_manage_discounts,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    total_count = content["data"]["products"]["totalCount"]
    assert total_count == 3


def test_hidden_product_access_with_permission_manage_channels(
    staff_api_client,
    product_list,
    channel_USD,
    permission_manage_channels,
):
    hidden_product = product_list[0]
    hidden_product.channel_listings.all().update(is_published=False)

    variables = {
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        variables=variables,
        permissions=(permission_manage_channels,),
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    total_count = content["data"]["products"]["totalCount"]
    assert total_count == 2


def test_query_product_for_federation(api_client, product, channel_USD):
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
    query = """
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

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Product",
            "id": product_id,
            "name": product.name,
        }
    ]


def test_query_product_media_for_federation(
    api_client, product_with_image, channel_USD
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
            url
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
            "url": "http://testserver/media/products/product.jpg",
        }
    ]


def test_query_product_type_for_federation(api_client, product, channel_USD):
    product_type = product.product_type
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductType",
                "id": product_type_id,
            },
        ],
    }
    query = """
      query GetProductTypeInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on ProductType {
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
            "__typename": "ProductType",
            "id": product_type_id,
            "name": product_type.name,
        }
    ]
