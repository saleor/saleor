import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import ANY, Mock, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify
from freezegun import freeze_time
from graphql_relay import to_global_id
from measurement.measures import Weight
from prices import Money, TaxedMoney

from ....attribute import AttributeInputType, AttributeType
from ....attribute.models import Attribute, AttributeValue
from ....attribute.utils import associate_attribute_values_to_instance
from ....core.taxes import TaxType
from ....core.weight import WeightUnits
from ....order import OrderStatus
from ....order.models import OrderLine
from ....plugins.manager import PluginsManager
from ....product.error_codes import ProductErrorCode
from ....product.models import (
    Category,
    Collection,
    CollectionChannelListing,
    Product,
    ProductChannelListing,
    ProductImage,
    ProductType,
    ProductVariant,
    ProductVariantChannelListing,
)
from ....product.tasks import update_variants_names
from ....product.tests.utils import create_image, create_pdf_file_with_image_ext
from ....product.utils.costs import get_product_costs_data
from ....warehouse.models import Allocation, Stock, Warehouse
from ...core.enums import AttributeErrorCode, ReportingPeriod
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
    get_multipart_request_body,
)
from ..bulk_mutations.products import ProductVariantStocksUpdate
from ..enums import VariantAttributeScope
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
            isAvailableForPurchase
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

    site_settings.default_weight_unit = WeightUnits.POUND
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
    assert product_data["weight"]["unit"] == WeightUnits.POUND.upper()


def test_product_query_by_id_weight_is_rounded(
    user_api_client, product, site_settings, channel_USD
):
    # given
    product.weight = Weight(kg=1.83456)
    product.save(update_fields=["weight"])

    site_settings.default_weight_unit = WeightUnits.KILOGRAM
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
    assert product_data["weight"]["unit"] == WeightUnits.KILOGRAM.upper()


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
    available_for_purchase = datetime.today() - timedelta(days=1)
    product.channel_listings.update(available_for_purchase=available_for_purchase)

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
    assert product_data["isAvailableForPurchase"] is True


def test_product_query_is_available_for_purchase_false(
    user_api_client, product, channel_USD
):
    # given
    available_for_purchase = datetime.today() + timedelta(days=1)
    product.channel_listings.update(available_for_purchase=available_for_purchase)

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
    assert product_data["isAvailableForPurchase"] is False


def test_product_query_is_available_for_purchase_false_no_available_for_purchase_date(
    user_api_client, product, channel_USD
):
    # given
    product.channel_listings.update(available_for_purchase=None)

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
    assert product_data["isAvailableForPurchase"] is False


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
    assert len(product_data) == product_count


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
    assert len(product_data) == product_count


def test_fetch_product_from_category_query(
    staff_api_client, product, permission_manage_products, stock, channel_USD
):
    category = Category.objects.first()
    product = category.products.first()
    query = """
    query {
        category(id: "%(category_id)s") {
            products(first: 20, channel: "%(channel_slug)s") {
                edges {
                    node {
                        id
                        name
                        url
                        slug
                        thumbnail{
                            url
                            alt
                        }
                        images {
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
                        isAvailable
                        pricing {
                            priceRange {
                                start {
                                    gross {
                                        amount
                                        currency
                                        localized
                                    }
                                    net {
                                        amount
                                        currency
                                        localized
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
    """ % {
        "category_id": graphene.Node.to_global_id("Category", category.id),
        "channel_slug": channel_USD.slug,
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["category"] is not None
    product_edges_data = content["data"]["category"]["products"]["edges"]
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]["node"]
    assert product_data["name"] == product.name
    assert product_data["url"] == ""
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


def test_products_query_with_filter_attributes(
    query_products_with_filter, staff_api_client, product, permission_manage_products
):

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        has_variants=True,
        is_shipping_required=True,
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
        "filter": {"attributes": [{"slug": attribute.slug, "value": attr_value.slug}]}
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_product_type(
    query_products_with_filter, staff_api_client, product, permission_manage_products
):
    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        has_variants=True,
        is_shipping_required=True,
    )
    second_product = product
    second_product.id = None
    second_product.product_type = product_type
    second_product.slug = "second-product"
    second_product.save()

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"filter": {"productType": product_type_id}}

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


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
        {"price": {"gte": 1.0, "lte": 2.0}},
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
        channel=channel_USD,
        is_published=True,
    )
    variables = {"filter": {"search": "Juice1"}, "channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


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


def test_products_query_with_filter_stock_availability(
    query_products_with_filter,
    staff_api_client,
    product,
    order_line,
    permission_manage_products,
):
    stock = product.variants.first().stocks.first()
    Allocation.objects.create(
        order_line=order_line, stock=stock, quantity_allocated=stock.quantity
    )
    variables = {"filter": {"stockAvailability": "OUT_OF_STOCK"}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    product_id = graphene.Node.to_global_id("Product", product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product.name


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


def test_query_product_image_by_id(user_api_client, product_with_image, channel_USD):
    image = product_with_image.images.first()
    query = """
    query productImageById($imageId: ID!, $productId: ID!, $channel: String) {
        product(id: $productId, channel: $channel) {
            imageById(id: $imageId) {
                id
                url
            }
        }
    }
    """
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "imageId": graphene.Node.to_global_id("ProductImage", image.pk),
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(query, variables)
    data = get_graphql_content(response)
    assert data["data"]["product"]["imageById"]["id"]
    assert data["data"]["product"]["imageById"]["url"]


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
    attr_value = (
        product.product_type.variant_attributes.get(slug="size").values.first().id
    )
    query = """
    query ($channel: String){
        products(
            filter: {attributes: {slug: "%(slug)s", value: "%(value)s"}},
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
    """ % {
        "slug": product_attr.slug,
        "value": attr_value,
    }

    variables = {"channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert products == []


SORT_PRODUCTS_QUERY = """
    query ($channel:String) {
        products (
            sortBy: %(sort_by_product_order)s, first: 2, channel: $channel
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

    variables = {"channel": channel_USD.slug}
    query = SORT_PRODUCTS_QUERY

    # Test sorting by PRICE, ascending
    sort_by = f'{{field: PRICE, direction: ASC, channel: "{channel_USD.slug}"}}'
    asc_price_query = query % {"sort_by_product_order": sort_by}
    response = user_api_client.post_graphql(asc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert price1 < price2

    # Test sorting by PRICE, descending
    sort_by = f'{{field: PRICE, direction:DESC, channel: "{channel_USD.slug}"}}'
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
    sort_by = f'{{field: MINIMAL_PRICE, direction:ASC, channel: "{channel_USD.slug}"}}'
    asc_price_query = query % {"sort_by_product_order": sort_by}
    response = user_api_client.post_graphql(asc_price_query, variables)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    price2 = edges[1]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    assert price1 < price2

    # Test sorting by MINIMAL_PRICE, descending
    sort_by = f'{{field: MINIMAL_PRICE, direction:DESC, channel: "{channel_USD.slug}"}}'
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

    site_settings.default_weight_unit = WeightUnits.OUNCE
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
    assert product_data["weight"]["unit"] == WeightUnits.OUNCE.upper()


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
                            descriptionJson
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
                                    file {
                                        url
                                        contentType
                                    }
                                }
                            }
                          }
                          productErrors {
                            field
                            code
                            message
                            attributes
                          }
                        }
                      }
"""


def test_create_product(
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
            "descriptionJson": description_json,
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
    assert data["productErrors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["descriptionJson"] == description_json
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
    assert data["productErrors"] == []
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
    assert data["productErrors"] == []
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
                    "file": {"url": existing_value.file_url, "contentType": None},
                    "reference": None,
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
    assert data["productErrors"] == []
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
    assert data["productErrors"] == []
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
    assert data["productErrors"] == []
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
    assert data["productErrors"] == []
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
    assert data["productErrors"] == []
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
    errors = data["productErrors"]
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
    errors = data["productErrors"]
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
    errors = data["productErrors"]
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
    assert data["productErrors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert len(data["product"]["attributes"]) == 1
    assert data["product"]["attributes"][0]["values"] == []


PRODUCT_VARIANT_SET_DEFAULT_MUTATION = """
    mutation Prod($productId: ID!, $variantId: ID!) {
        productVariantSetDefault(productId: $productId, variantId: $variantId) {
            product {
                defaultVariant {
                    id
                }
            }
            productErrors {
                code
                field
            }
        }
    }
"""


REORDER_PRODUCT_VARIANTS_MUTATION = """
    mutation ProductVariantReorder($product: ID!, $moves: [ReorderInput]!) {
        productVariantReorder(productId: $product, moves: $moves) {
            productErrors {
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
    assert not data["productErrors"]
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
    assert data["productErrors"][0]["code"] == ProductErrorCode.INVALID.name
    assert data["productErrors"][0]["field"] == "variantId"


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
    assert (
        data["productErrors"][0]["code"] == ProductErrorCode.NOT_PRODUCTS_VARIANT.name
    )
    assert data["productErrors"][0]["field"] == "variantId"


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
    assert not data["productErrors"]
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
    assert data["productErrors"][0]["field"] == "moves"
    assert data["productErrors"][0]["code"] == ProductErrorCode.NOT_FOUND.name


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
    assert data["productErrors"] == []
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
    assert data["productErrors"] == []
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
    error = data["productErrors"][0]
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
    error = data["productErrors"]
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
            "descriptionJson": description_json,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
            "attributes": [
                {"id": color_attr_id, "values": [" "]},
                {"id": weight_attr_id, "values": [None]},
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
    errors = data["productErrors"]

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


MUTATION_UPDATE_PRODUCT = """
    mutation updateProduct($productId: ID!, $input: ProductInput!) {
        productUpdate(id: $productId, input: $input) {
                product {
                    category {
                        name
                    }
                    rating
                    descriptionJson
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
                            reference
                            file {
                                url
                                contentType
                            }
                        }
                    }
                }
                productErrors {
                    message
                    field
                    code
                }
            }
        }
"""


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_update_product(
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

    variables = {
        "productId": product_id,
        "input": {
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "descriptionJson": other_description_json,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
            "attributes": [{"id": attribute_id, "values": ["Rainbow"]}],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["productErrors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["descriptionJson"] == other_description_json
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
    assert data["productErrors"] == []

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
    assert data["productErrors"] == []

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
                    "url": existing_value.file_url,
                    "contentType": existing_value.content_type,
                },
            }
        ],
    }
    assert expected_file_att_data in attributes

    file_attribute.refresh_from_db()
    assert file_attribute.values.count() == values_count

    updated_webhook_mock.assert_called_once_with(product)


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
    assert data["productErrors"] == []
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
    assert data["productErrors"] == []

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
            }
        ],
    }
    assert expected_file_att_data in attributes

    updated_webhook_mock.assert_called_once_with(product)

    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.values.count() == values_count + 1


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
    assert data["productErrors"] == []

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
    errors = data["productErrors"]

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
    assert data["productErrors"] == []

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
    assert data["productErrors"] == []

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
    errors = data["productErrors"]

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
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page_list[1].title,
        slug=f"{product.pk}_{page_list[1].pk}",
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
    assert data["productErrors"] == []

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
            productErrors {
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
    errors = data["productErrors"]
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
    errors = data["productErrors"]
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
                productErrors {
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
    errors = data["productErrors"]
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
        productErrors {
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
    assert data["productErrors"] == [
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
    assert not data["productErrors"]


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
    assert not data["productErrors"]

    assert (
        color_attribute.values.count() == expected_attribute_values_count
    ), "A new attribute value shouldn't have been created"


def test_update_product_without_supplying_required_product_attribute(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensure assigning an existing value to a product doesn't create a new
    attribute value."""

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

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": color_attribute_id, "values": ["Blue"]}],
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert data["productErrors"] == [
        {
            "field": "attributes",
            "code": ProductErrorCode.REQUIRED.name,
            "message": ANY,
            "attributes": [required_attribute_id],
        }
    ]


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
    assert data["productErrors"] == [
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
    assert data["productErrors"] == [
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
                productErrors {
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
    error = data["productErrors"][0]
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
            }
            errors {
                field
                message
            }
            }
        }
"""


def test_delete_product(staff_api_client, product, permission_manage_products):
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


def test_delete_product_variant_in_draft_order(
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
            is_shipping_required=variant.is_shipping_required(),
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
            is_shipping_required=variant.is_shipping_required(),
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
            taxRate
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


PRODUCT_TYPE_CREATE_MUTATION = """
    mutation createProductType(
        $name: String,
        $slug: String,
        $taxCode: String,
        $hasVariants: Boolean,
        $isShippingRequired: Boolean,
        $productAttributes: [ID],
        $variantAttributes: [ID],
        $weight: WeightScalar) {
        productTypeCreate(
            input: {
                name: $name,
                slug: $slug,
                taxCode: $taxCode,
                hasVariants: $hasVariants,
                isShippingRequired: $isShippingRequired,
                productAttributes: $productAttributes,
                variantAttributes: $variantAttributes,
                weight: $weight}) {
            productType {
                name
                slug
                taxRate
                isShippingRequired
                hasVariants
                variantAttributes {
                    name
                    values {
                        name
                    }
                }
                productAttributes {
                    name
                    values {
                        name
                    }
                }
            }
            productErrors {
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
    assert data["hasVariants"] == has_variants
    assert data["isShippingRequired"] == require_shipping

    pa = product_attributes[0]
    assert data["productAttributes"][0]["name"] == pa.name
    pa_values = data["productAttributes"][0]["values"]
    assert sorted([value["name"] for value in pa_values]) == sorted(
        [value.name for value in pa.values.all()]
    )

    va = variant_attributes[0]
    assert data["variantAttributes"][0]["name"] == va.name
    va_values = data["variantAttributes"][0]["values"]
    assert sorted([value["name"] for value in va_values]) == sorted(
        [value.name for value in va.values.all()]
    )

    new_instance = ProductType.objects.latest("pk")
    tax_code = manager.get_tax_code_from_object_meta(new_instance).code
    assert tax_code == "wine"


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
    variables = {"name": name, "slug": input_slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    assert not data["productErrors"]
    assert data["productType"]["slug"] == expected_slug


def test_create_product_type_with_unicode_in_name(
    staff_api_client, permission_manage_product_types_and_attributes
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    name = "わたし わ にっぽん です"
    variables = {"name": name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    assert not data["productErrors"]
    assert data["productType"]["name"] == name
    assert data["productType"]["slug"] == "わたし-わ-にっぽん-です"


def test_create_product_type_create_with_negative_weight(
    staff_api_client, permission_manage_product_types_and_attributes
):
    query = PRODUCT_TYPE_CREATE_MUTATION
    name = "Test product type"
    variables = {"name": name, "weight": -1.1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    error = data["productErrors"][0]
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
    errors = data["productErrors"]

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
    $productAttributes: [ID],
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
            productErrors {
                code
                field
                attributes
            }
            }
        }
"""


def test_product_type_update_mutation(
    staff_api_client, product_type, permission_manage_product_types_and_attributes
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
    errors = data["productErrors"]

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
            productErrors {
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
def test_update_product_type_slug(
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
    errors = data["productErrors"]
    if not error_message:
        assert not errors
        assert data["productType"]["slug"] == expected_slug
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
    errors = data["productErrors"]
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
                productErrors {
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
    errors = data["productErrors"]
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
                productErrors {
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
    error = data["productErrors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


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
        is_shipping_required=variant.is_shipping_required(),
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
        is_shipping_required=variant.is_shipping_required(),
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


def test_product_image_create_mutation(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    query = """
    mutation createProductImage($image: Upload!, $product: ID!) {
        productImageCreate(input: {image: $image, product: $product}) {
            image {
                id
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

    image_file, image_name = create_image()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "image": image_name,
    }
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    product.refresh_from_db()
    product_image = product.images.last()
    assert product_image.image.file

    # The image creation should have triggered a warm-up
    mock_create_thumbnails.assert_called_once_with(product_image.pk)


def test_product_image_create_mutation_without_file(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    query = """
    mutation createProductImage($image: Upload!, $product: ID!) {
        productImageCreate(input: {image: $image, product: $product}) {
            productErrors {
                code
                field
            }
        }
    }
    """
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "image": "image name",
    }
    body = get_multipart_request_body(query, variables, file="", file_name="name")
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    errors = content["data"]["productImageCreate"]["productErrors"]
    assert errors[0]["field"] == "image"
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_invalid_product_image_create_mutation(
    staff_api_client, product, permission_manage_products
):
    query = """
    mutation createProductImage($image: Upload!, $product: ID!) {
        productImageCreate(input: {image: $image, product: $product}) {
            image {
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
    assert content["data"]["productImageCreate"]["errors"] == [
        {"field": "image", "message": "Invalid file type"}
    ]
    product.refresh_from_db()
    assert product.images.count() == 0


def test_product_image_update_mutation(
    monkeypatch, staff_api_client, product_with_image, permission_manage_products
):
    query = """
    mutation updateProductImage($imageId: ID!, $alt: String) {
        productImageUpdate(id: $imageId, input: {alt: $alt}) {
            image {
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

    image_obj = product_with_image.images.first()
    alt = "damage alt"
    variables = {
        "alt": alt,
        "imageId": graphene.Node.to_global_id("ProductImage", image_obj.id),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productImageUpdate"]["image"]["alt"] == alt

    # We did not update the image field,
    # the image should not have triggered a warm-up
    assert mock_create_thumbnails.call_count == 0


def test_product_image_delete(
    staff_api_client, product_with_image, permission_manage_products
):
    product = product_with_image
    query = """
            mutation deleteProductImage($id: ID!) {
                productImageDelete(id: $id) {
                    image {
                        id
                        url
                    }
                }
            }
        """
    image_obj = product.images.first()
    node_id = graphene.Node.to_global_id("ProductImage", image_obj.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productImageDelete"]
    assert image_obj.image.url in data["image"]["url"]
    with pytest.raises(image_obj._meta.model.DoesNotExist):
        image_obj.refresh_from_db()
    assert node_id == data["image"]["id"]


def test_reorder_images(
    staff_api_client, product_with_images, permission_manage_products
):
    query = """
    mutation reorderImages($product_id: ID!, $images_ids: [ID]!) {
        productImageReorder(productId: $product_id, imagesIds: $images_ids) {
            product {
                id
            }
        }
    }
    """
    product = product_with_images
    images = product.images.all()
    image_0 = images[0]
    image_1 = images[1]
    image_0_id = graphene.Node.to_global_id("ProductImage", image_0.id)
    image_1_id = graphene.Node.to_global_id("ProductImage", image_1.id)
    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {"product_id": product_id, "images_ids": [image_1_id, image_0_id]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)

    # Check if order has been changed
    product.refresh_from_db()
    reordered_images = product.images.all()
    reordered_image_0 = reordered_images[0]
    reordered_image_1 = reordered_images[1]
    assert image_0.id == reordered_image_1.id
    assert image_1.id == reordered_image_0.id


ASSIGN_VARIANT_QUERY = """
    mutation assignVariantImageMutation($variantId: ID!, $imageId: ID!) {
        variantImageAssign(variantId: $variantId, imageId: $imageId) {
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


def test_assign_variant_image(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    image = product_with_image.images.first()

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "imageId": to_global_id("ProductImage", image.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.images.first() == image


def test_assign_variant_image_second_time(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    # given
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    image = product_with_image.images.first()

    image.variant_images.create(variant=variant)

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "imageId": to_global_id("ProductImage", image.pk),
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content_from_response(response)
    assert "errors" in content
    assert (
        "duplicate key value violates unique constraint"
        in content["errors"][0]["message"]
    )


def test_assign_variant_image_from_different_product(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    product_with_image.pk = None
    product_with_image.slug = "product-with-image"
    product_with_image.save()

    image_2 = ProductImage.objects.create(product=product_with_image)
    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "imageId": to_global_id("ProductImage", image_2.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["variantImageAssign"]["errors"][0]["field"] == "imageId"

    # check permissions
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


UNASSIGN_VARIANT_IMAGE_QUERY = """
    mutation unassignVariantImageMutation($variantId: ID!, $imageId: ID!) {
        variantImageUnassign(variantId: $variantId, imageId: $imageId) {
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


def test_unassign_variant_image(
    staff_api_client, product_with_image, permission_manage_products
):
    query = UNASSIGN_VARIANT_IMAGE_QUERY

    image = product_with_image.images.first()
    variant = product_with_image.variants.first()
    variant.variant_images.create(image=image)

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "imageId": to_global_id("ProductImage", image.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.images.count() == 0


def test_unassign_not_assigned_variant_image(
    staff_api_client, product_with_image, permission_manage_products
):
    query = UNASSIGN_VARIANT_IMAGE_QUERY
    variant = product_with_image.variants.first()
    image_2 = ProductImage.objects.create(product=product_with_image)
    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "imageId": to_global_id("ProductImage", image_2.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["variantImageUnassign"]["errors"][0]["field"] == ("imageId")


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
        $variantAttributes: [ID],
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


def test_product_variants_by_ids(staff_api_client, variant, channel_USD):
    query = """
        query getProduct($ids: [ID!], $channel: String) {
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


def test_product_variants_by_customer(user_api_client, variant, channel_USD):
    query = """
        query getProduct($ids: [ID!], $channel: String) {
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

    query = """
        query getProductVariants($id: ID!, $channel: String) {
            product(id: $id, channel: $channel) {
                variants {
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
    product_id = graphene.Node.to_global_id("Product", variant.product.id)
    variables = {"id": product_id, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["product"]
    variant_price = data["variants"][0]["pricing"]["priceUndiscounted"]["gross"]
    assert variant_price["amount"] == api_variant_price


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
                description="Test description",
            ),
            Collection(
                id=2,
                name="Collection2",
                slug="collection-published2",
                description="Test description",
            ),
            Collection(
                id=3,
                name="Collection3",
                slug="collection-unpublished",
                description="Test description",
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
    collection_filter["channel"] = channel_USD.slug
    variables = {
        "filter": collection_filter,
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_collections_with_filter, variables)
    content = get_graphql_content(response)
    collections = content["data"]["collections"]["edges"]

    assert len(collections) == count


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
    collection_sort["channel"] = channel_USD.slug
    variables = {"sort_by": collection_sort}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_COLLECTIONS_WITH_SORT, variables)
    content = get_graphql_content(response)
    collections = content["data"]["collections"]["edges"]
    for order, collection_name in enumerate(result_order):
        assert collections[order]["node"]["name"] == collection_name


@pytest.mark.parametrize(
    "category_filter, count",
    [
        ({"search": "slug_"}, 3),
        ({"search": "Category1"}, 1),
        ({"search": "cat1"}, 2),
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
        id=1, name="Category1", slug="slug_category1", description="Description cat1"
    )
    Category.objects.create(
        id=2, name="Category2", slug="slug_category2", description="Description cat2"
    )
    Category.objects.create(
        id=3,
        name="SubCategory",
        slug="slug_subcategory",
        parent=Category.objects.get(name="Category1"),
        description="Subcategory_description of cat1",
    )
    variables = {"filter": category_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_categories_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["categories"]["totalCount"] == count


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
        name="Cat1", slug="slug_category1", description="Description cat1"
    )
    Product.objects.create(
        name="Test",
        slug="test",
        product_type=product_type,
        category=cat1,
    )
    Category.objects.create(
        name="Cat2", slug="slug_category2", description="Description cat2"
    )
    Category.objects.create(
        name="SubCat",
        slug="slug_subcategory1",
        parent=Category.objects.get(name="Cat1"),
        description="Subcategory_description of cat1",
    )
    subsubcat = Category.objects.create(
        name="SubSubCat",
        slug="slug_subcategory2",
        parent=Category.objects.get(name="SubCat"),
        description="Subcategory_description of cat1",
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
            ),
            ProductType(
                name="Tools",
                slug="tools",
                has_variants=True,
                is_shipping_required=True,
                is_digital=False,
            ),
            ProductType(
                name="Books",
                slug="books",
                has_variants=False,
                is_shipping_required=True,
                is_digital=False,
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
    product_type = ProductType.objects.create(name="Empty Type")
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
            productErrors {
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
        variant, stocks_data, warehouses
    )

    variant.refresh_from_db()
    assert variant.stocks.count() == 2
    assert {stock.warehouse.pk for stock in variant.stocks.all()} == {
        warehouse.pk for warehouse in warehouses
    }
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }


def test_update_or_create_variant_stocks_empty_stocks_data(variant, warehouses):
    Stock.objects.create(
        product_variant=variant,
        warehouse=warehouses[0],
        quantity=5,
    )

    ProductVariantStocksUpdate.update_or_create_variant_stocks(variant, [], warehouses)

    variant.refresh_from_db()
    assert variant.stocks.count() == 1
    stock = variant.stocks.first()
    assert stock.warehouse == warehouses[0]
    assert stock.quantity == 5


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
            productErrors {
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
                productErrors {{
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
