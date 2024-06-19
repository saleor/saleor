from datetime import datetime, timedelta
from decimal import Decimal

import graphene
import pytest
import pytz
from django.utils import timezone

from .....attribute import AttributeInputType, AttributeType
from .....attribute.models import Attribute, AttributeValue
from .....attribute.tests.model_helpers import (
    get_product_attribute_values,
    get_product_attributes,
)
from .....attribute.utils import associate_attribute_values_to_instance
from .....core.postgres import FlatConcatSearchVector
from .....core.units import MeasurementUnits
from .....product import ProductTypeKind
from .....product.models import (
    Category,
    Product,
    ProductChannelListing,
    ProductType,
    ProductVariantChannelListing,
)
from .....product.search import prepare_product_search_vector_value
from .....tests.utils import dummy_editorjs
from .....warehouse.models import Allocation, Reservation, Stock, Warehouse
from ....tests.utils import get_graphql_content


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
    associate_attribute_values_to_instance(
        second_product,
        {attribute.id: [attr_value]},
    )

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
    ("gte", "lte", "expected_products_index"),
    [
        (None, 8, [1, 2]),
        (0, 8, [1, 2]),
        (7, 8, []),
        (5, None, [0, 1, 2]),
        (8, 10, [0]),
        (12, None, [0]),
        (20, None, []),
        (20, 8, []),
        (5, 5, [1, 2]),
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
        product,
        {numeric_attribute.id: list(numeric_attribute.values.all())},
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
        attribute=numeric_attribute, name="5", slug="5"
    )

    associate_attribute_values_to_instance(
        second_product,
        {numeric_attribute.id: [attr_value]},
    )

    third_product = Product.objects.create(
        name="Third product",
        slug="third-product",
        product_type=product_type,
        category=category,
    )
    attr_value = AttributeValue.objects.create(
        attribute=numeric_attribute, name="5", slug="5_X"
    )

    associate_attribute_values_to_instance(
        third_product,
        {numeric_attribute.id: [attr_value]},
    )

    second_product.refresh_from_db()
    third_product.refresh_from_db()
    products_instances = [product, second_product, third_product]
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
    ("filter_value", "expected_products_index"),
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
        product,
        {boolean_attribute.id: [boolean_attribute.values.get(boolean=filter_value)]},
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
        second_product,
        {boolean_attribute.id: [boolean_attribute.values.get(boolean=False)]},
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


@pytest.mark.parametrize(
    "filter_value",
    [
        False,
        True,
    ],
)
def test_products_query_with_filter_non_existing_boolean_attributes(
    filter_value,
    query_products_with_filter,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given

    variables = {
        "filter": {
            "attributes": [{"slug": "non-existing-atr", "boolean": filter_value}]
        }
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 0


@pytest.mark.parametrize(
    "filter_value",
    [
        False,
        True,
    ],
)
def test_products_query_with_filter_boolean_attributes_not_assigned_to_product(
    filter_value,
    query_products_with_filter,
    staff_api_client,
    product,
    category,
    boolean_attribute,
    permission_manage_products,
):
    # given
    boolean_attribute.values.all().delete()
    product.product_type.product_attributes.add(boolean_attribute)

    variables = {
        "filter": {
            "attributes": [{"slug": boolean_attribute.slug, "boolean": filter_value}]
        }
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 0


def test_products_query_with_filter_by_attributes_values_and_range(
    query_products_with_filter,
    staff_api_client,
    product,
    category,
    numeric_attribute,
    permission_manage_products,
):
    product_attr = get_product_attributes(product).first()
    attr_value_1 = get_product_attribute_values(product, product_attr).first()
    product.product_type.product_attributes.add(numeric_attribute)
    associate_attribute_values_to_instance(
        product,
        {numeric_attribute.id: list(numeric_attribute.values.all())},
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
        second_product,
        {numeric_attribute.id: [attr_value_2]},
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
        product,
        {swatch_attribute.id: list(swatch_attribute.values.all())},
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

    associate_attribute_values_to_instance(
        second_product,
        {swatch_attribute.id: [attr_value]},
    )

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
        product_list[0],
        {date_attribute.id: [attr_value_1]},
    )
    associate_attribute_values_to_instance(
        product_list[1],
        {date_attribute.id: [attr_value_2]},
    )
    associate_attribute_values_to_instance(
        product_list[2],
        {date_attribute.id: [attr_value_3]},
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
        product_list[0].variants.first(),
        {date_attribute.id: [attr_value_1]},
    )
    associate_attribute_values_to_instance(
        product_list[1].variants.first(),
        {date_attribute.id: [attr_value_2]},
    )
    associate_attribute_values_to_instance(
        product_list[2].variants.first(),
        {date_attribute.id: [attr_value_3]},
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
        product_list[0],
        {date_time_attribute.id: [attr_value_1]},
    )
    associate_attribute_values_to_instance(
        product_list[1],
        {date_time_attribute.id: [attr_value_2]},
    )
    associate_attribute_values_to_instance(
        product_list[2],
        {date_time_attribute.id: [attr_value_3]},
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
        product_list[0].variants.first(),
        {date_time_attribute.id: [attr_value_1]},
    )
    associate_attribute_values_to_instance(
        product_list[1].variants.first(),
        {date_time_attribute.id: [attr_value_2]},
    )
    associate_attribute_values_to_instance(
        product_list[2].variants.first(),
        {date_time_attribute.id: [attr_value_3]},
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
    # given
    product_type = product_list[0].product_type
    date_value = datetime.now(tz=pytz.utc)
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
        product_list[0],
        {date_time_attribute.id: [attr_value_1]},
    )
    associate_attribute_values_to_instance(
        product_list[1].variants.first(),
        {date_time_attribute.id: [attr_value_2]},
    )
    associate_attribute_values_to_instance(
        product_list[2].variants.first(),
        {date_time_attribute.id: [attr_value_3]},
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
        pr.search_vector = FlatConcatSearchVector(
            *prepare_product_search_vector_value(pr)
        )
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
    second_product.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(second_product)
    )
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
        product_with_dropdown_attr,
        {color_attribute.id: [dropdown_attr_value]},
    )

    product_with_dropdown_attr.refresh_from_db()

    product_with_dropdown_attr.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product_with_dropdown_attr)
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
    "search_value",
    ["eco mode", "ECO Performance", "performance", "eco performance mode"],
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
        {multiselect_attribute.id: [multiselect_attr_val_1, multiselect_attr_val_2]},
    )

    product_with_multiselect_attr.refresh_from_db()

    product_with_multiselect_attr.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product_with_multiselect_attr)
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
        product_with_rich_text_attr,
        {rich_text_attribute.id: [rich_text_value]},
    )

    product_with_rich_text_attr.refresh_from_db()

    product_with_rich_text_attr.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product_with_rich_text_attr)
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


@pytest.mark.parametrize("search_value", ["plain", "test plain", "PLAIN text"])
def test_products_query_with_filter_search_by_plain_text_attribute(
    search_value,
    query_products_with_filter,
    staff_api_client,
    product_list,
    permission_manage_products,
    channel_USD,
    plain_text_attribute,
):
    # given
    product_with_plain_text_attr = product_list[1]

    product_type = product_with_plain_text_attr.product_type
    product_type.product_attributes.add(plain_text_attribute)

    plain_text_value = plain_text_attribute.values.first()
    plain_text_value.plain_text = "Test plain text."
    plain_text_value.save(update_fields=["plain_text"])

    associate_attribute_values_to_instance(
        product_with_plain_text_attr,
        {plain_text_attribute.id: [plain_text_value]},
    )

    product_with_plain_text_attr.refresh_from_db()

    product_with_plain_text_attr.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product_with_plain_text_attr)
    )
    product_with_plain_text_attr.save(update_fields=["search_vector"])

    variables = {"filter": {"search": search_value}, "channel": channel_USD.slug}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # then
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_with_plain_text_attr.id
    )
    assert products[0]["node"]["name"] == product_with_plain_text_attr.name


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
        product_with_numeric_attr,
        {numeric_attribute.id: [numeric_attr_value]},
    )

    product_with_numeric_attr.refresh_from_db()

    product_with_numeric_attr.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product_with_numeric_attr)
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
        product_with_numeric_attr,
        {numeric_attribute.id: [numeric_attr_value]},
    )

    product_with_numeric_attr.refresh_from_db()

    product_with_numeric_attr.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product_with_numeric_attr)
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
        product_with_date_attr,
        {date_attribute.id: [date_attr_value]},
    )

    product_with_date_attr.refresh_from_db()

    product_with_date_attr.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product_with_date_attr)
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
        product_with_date_time_attr,
        {date_time_attribute.id: [date_time_attr_value]},
    )

    product_with_date_time_attr.refresh_from_db()

    product_with_date_time_attr.search_vector = FlatConcatSearchVector(
        *prepare_product_search_vector_value(product_with_date_time_attr)
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


def test_products_query_with_filter_stock_availability_including_reservations(
    query_products_with_filter,
    staff_api_client,
    product_list,
    order_line,
    checkout_line,
    permission_manage_products,
    channel_USD,
    warehouse_JPY,
    stock,
):
    # given
    stocks = [product.variants.first().stocks.first() for product in product_list]
    stock.quantity = 50
    stock.product_variant = stocks[2].product_variant
    stock.warehouse_id = warehouse_JPY.id
    stocks[2].quantity = 50

    Allocation.objects.create(
        order_line=order_line, stock=stocks[0], quantity_allocated=50
    )
    Reservation.objects.bulk_create(
        [
            Reservation(
                checkout_line=checkout_line,
                stock=stocks[0],
                quantity_reserved=50,
                reserved_until=timezone.now() + timedelta(minutes=5),
            ),
            Reservation(
                checkout_line=checkout_line,
                stock=stocks[1],
                quantity_reserved=100,
                reserved_until=timezone.now() - timedelta(minutes=5),
            ),
            Reservation(
                checkout_line=checkout_line,
                stock=stocks[2],
                quantity_reserved=50,
                reserved_until=timezone.now() + timedelta(minutes=5),
            ),
        ]
    )
    variables = {
        "filter": {"stockAvailability": "OUT_OF_STOCK"},
        "channel": channel_USD.slug,
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_list[0].id
    )


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


def test_products_query_with_filter_stock_availability_only_stock_in_cc_warehouse(
    query_products_with_filter,
    user_api_client,
    product,
    order_line,
    channel_USD,
    warehouse_for_cc,
):
    # given
    variant = product.variants.first()
    variant.stocks.all().delete()

    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=10
    )

    variables = {
        "filter": {"stockAvailability": "IN_STOCK"},
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(query_products_with_filter, variables)

    # then
    content = get_graphql_content(response)

    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product.id
    )


@pytest.mark.parametrize(
    ("quantity_input", "warehouse_indexes", "count", "indexes_of_products_in_result"),
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
