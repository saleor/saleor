from datetime import timedelta

import graphene
import pytest
from django.utils import timezone

from saleor.attribute.models import Attribute, AttributeValue
from saleor.attribute.utils import associate_attribute_values_to_instance
from saleor.product import ProductTypeKind
from saleor.product.models import Product, ProductChannelListing, ProductType

from ....tests.utils import get_graphql_content

PRODUCTS_WHERE_QUERY = """
    query($where: ProductWhereInput!, $channel: String) {
      products(first: 10, where: $where, channel: $channel) {
        edges {
          node {
            id
            name
            slug
          }
        }
      }
    }
"""


def test_product_filter_by_ids(api_client, product_list, channel_USD):
    # given
    ids = [
        graphene.Node.to_global_id("Product", product.pk)
        for product in product_list[:2]
    ]
    variables = {"channel": channel_USD.slug, "where": {"id": ids}}

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    products = data["data"]["products"]["edges"]
    assert len(products) == 2
    returned_slugs = {node["node"]["slug"] for node in products}
    assert returned_slugs == {
        product_list[0].slug,
        product_list[1].slug,
    }


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"eq": "Test product 1"}, [0]),
        ({"eq": "Non-existing"}, []),
        ({"oneOf": ["Test product 1", "Test product 2"]}, [0, 1]),
        ({"oneOf": ["Test product 1", "Non-existing"]}, [0]),
        ({"oneOf": ["Non-existing 1", "Non-existing 2"]}, []),
    ],
)
def test_product_filter_by_name(where, indexes, api_client, product_list, channel_USD):
    # given
    variables = {"channel": channel_USD.slug, "where": {"name": where}}

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"eq": "test-product-a"}, [0]),
        ({"eq": "non-existing"}, []),
        ({"oneOf": ["test-product-a", "test-product-b"]}, [0, 1]),
        ({"oneOf": ["test-product-a", "non-existing"]}, [0]),
        ({"oneOf": ["non-existing-1", "non-existing-2"]}, []),
    ],
)
def test_product_filter_by_slug(where, indexes, api_client, product_list, channel_USD):
    # given
    variables = {"channel": channel_USD.slug, "where": {"slug": where}}

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}


def test_product_filter_by_product_types(
    api_client, product_list, channel_USD, product_type_list
):
    # given
    product_list[0].product_type = product_type_list[0]
    product_list[1].product_type = product_type_list[1]
    product_list[2].product_type = product_type_list[2]
    Product.objects.bulk_update(product_list, ["product_type"])

    type_ids = [
        graphene.Node.to_global_id("ProductType", type.pk)
        for type in product_type_list[:2]
    ]
    variables = {
        "channel": channel_USD.slug,
        "where": {"productType": {"oneOf": type_ids}},
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    products = data["data"]["products"]["edges"]
    assert len(products) == 2
    returned_slugs = {node["node"]["slug"] for node in products}
    assert returned_slugs == {
        product_list[0].slug,
        product_list[1].slug,
    }


def test_product_filter_by_product_type(
    api_client, product_list, channel_USD, product_type_list
):
    # given
    product_list[0].product_type = product_type_list[0]
    Product.objects.bulk_update(product_list, ["product_type"])

    type_id = graphene.Node.to_global_id("ProductType", product_type_list[0].pk)

    variables = {
        "channel": channel_USD.slug,
        "where": {"productType": {"eq": type_id}},
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    products = data["data"]["products"]["edges"]
    assert len(products) == 1
    assert product_list[0].slug == products[0]["node"]["slug"]


def test_product_filter_by_categories(
    api_client, product_list, channel_USD, category_list
):
    # given
    product_list[0].category = category_list[0]
    product_list[1].category = category_list[1]
    product_list[2].category = category_list[2]
    Product.objects.bulk_update(product_list, ["category"])

    category_ids = [
        graphene.Node.to_global_id("Category", category.pk)
        for category in category_list[:2]
    ]
    variables = {
        "channel": channel_USD.slug,
        "where": {"category": {"oneOf": category_ids}},
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    products = data["data"]["products"]["edges"]
    assert len(products) == 2
    returned_slugs = {node["node"]["slug"] for node in products}
    assert returned_slugs == {
        product_list[0].slug,
        product_list[1].slug,
    }


def test_product_filter_by_category(
    api_client, product_list, channel_USD, category_list
):
    # given
    product_list[1].category = category_list[1]
    Product.objects.bulk_update(product_list, ["category"])

    category_id = graphene.Node.to_global_id("Category", category_list[1].pk)

    variables = {
        "channel": channel_USD.slug,
        "where": {"category": {"eq": category_id}},
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    products = data["data"]["products"]["edges"]
    assert len(products) == 1
    assert product_list[1].slug == products[0]["node"]["slug"]


def test_product_filter_by_collections(
    api_client, product_list, channel_USD, collection_list
):
    # given
    collection_list[0].products.add(product_list[0])
    collection_list[1].products.add(product_list[1])
    collection_list[2].products.add(product_list[2])

    collection_ids = [
        graphene.Node.to_global_id("Collection", collection.pk)
        for collection in collection_list[:2]
    ]
    variables = {
        "channel": channel_USD.slug,
        "where": {"collection": {"oneOf": collection_ids}},
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    products = data["data"]["products"]["edges"]
    assert len(products) == 2
    returned_slugs = {node["node"]["slug"] for node in products}
    assert returned_slugs == {product_list[0].slug, product_list[1].slug}


def test_product_filter_by_collection(
    api_client, product_list, channel_USD, collection_list
):
    # given
    collection_list[1].products.add(product_list[1])
    collection_id = graphene.Node.to_global_id("Collection", collection_list[1].pk)

    variables = {
        "channel": channel_USD.slug,
        "where": {"collection": {"eq": collection_id}},
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    products = data["data"]["products"]["edges"]
    assert len(products) == 1
    assert product_list[1].slug == products[0]["node"]["slug"]


@pytest.mark.parametrize(
    "where, indexes",
    [({"isAvailable": True}, [0, 2]), ({"isAvailable": False}, [1])],
)
def test_product_filter_by_is_available(
    where, indexes, api_client, product_list, channel_USD
):
    # given
    ProductChannelListing.objects.filter(
        product=product_list[1], channel=channel_USD
    ).update(available_for_purchase_at=timezone.now() + timedelta(days=1))
    variables = {
        "channel": channel_USD.slug,
        "where": where,
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}


@pytest.mark.parametrize(
    "where, indexes",
    [({"isPublished": True}, [0, 2]), ({"isPublished": False}, [])],
)
def test_product_filter_by_is_published(
    where, indexes, api_client, product_list, channel_USD
):
    # given
    ProductChannelListing.objects.filter(
        product=product_list[1], channel=channel_USD
    ).update(is_published=False)
    variables = {
        "channel": channel_USD.slug,
        "where": where,
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}


@pytest.mark.parametrize(
    "where, indexes",
    [({"isVisibleInListing": True}, [0, 2]), ({"isVisibleInListing": False}, [])],
)
def test_product_filter_by_is_visible_in_listing(
    where, indexes, api_client, product_list, channel_USD
):
    # given
    ProductChannelListing.objects.filter(
        product=product_list[1], channel=channel_USD
    ).update(visible_in_listings=False)
    variables = {
        "channel": channel_USD.slug,
        "where": where,
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}


@pytest.mark.parametrize(
    "where, indexes",
    [({"hasCategory": True}, [0, 2]), ({"hasCategory": False}, [1])],
)
def test_product_filter_by_has_category(
    where, indexes, api_client, product_list, channel_USD
):
    # given
    product_list[1].category = None
    product_list[1].save(update_fields=["category"])
    variables = {
        "channel": channel_USD.slug,
        "where": where,
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}


def test_product_filter_by_published_from(api_client, product_list, channel_USD):
    # given
    timestamp = timezone.now()
    ProductChannelListing.objects.filter(
        product__in=product_list, channel=channel_USD
    ).update(published_at=timestamp + timedelta(days=1))
    ProductChannelListing.objects.filter(
        product=product_list[0], channel=channel_USD
    ).update(published_at=timestamp - timedelta(days=1))
    variables = {
        "channel": channel_USD.slug,
        "where": {"publishedFrom": timestamp},
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    products = data["data"]["products"]["edges"]
    assert len(products) == 1
    assert product_list[0].slug == products[0]["node"]["slug"]


def test_product_filter_by_available_from(api_client, product_list, channel_USD):
    # given
    timestamp = timezone.now()
    ProductChannelListing.objects.filter(
        product__in=product_list, channel=channel_USD
    ).update(available_for_purchase_at=timestamp - timedelta(days=1))
    ProductChannelListing.objects.filter(
        product=product_list[0], channel=channel_USD
    ).update(available_for_purchase_at=timestamp + timedelta(days=1))
    variables = {
        "channel": channel_USD.slug,
        "where": {"availableFrom": timestamp},
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    products = data["data"]["products"]["edges"]
    assert len(products) == 2
    assert product_list[1].slug == products[0]["node"]["slug"]
    assert product_list[2].slug == products[1]["node"]["slug"]


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"price": {"range": {"gte": 0, "lte": 50}}}, [0, 1, 2]),
        ({"price": {"range": {"gte": 10, "lte": 20}}}, [0, 1]),
        ({"price": {"range": {"gte": 15}}}, [1, 2]),
        ({"price": {"range": {"lte": 15}}}, [0]),
        ({"price": {"range": {"gte": 9.9999, "lte": 19.9999}}}, [0]),
        ({"price": {"eq": 20}}, [1]),
        ({"price": {"oneOf": [20, 30, 50]}}, [1, 2]),
    ],
)
def test_product_filter_by_variant_price(
    where, indexes, api_client, product_list, channel_USD
):
    # given
    variables = {
        "channel": channel_USD.slug,
        "where": where,
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"minimalPrice": {"range": {"gte": 0, "lte": 50}}}, [0, 1, 2]),
        ({"minimalPrice": {"range": {"gte": 10, "lte": 20}}}, [0, 1]),
        ({"minimalPrice": {"range": {"gte": 15}}}, [1, 2]),
        ({"minimalPrice": {"range": {"lte": 15}}}, [0]),
        ({"minimalPrice": {"range": {"gte": 9.9999, "lte": 19.9999}}}, [0]),
        ({"minimalPrice": {"eq": 20}}, [1]),
        ({"minimalPrice": {"oneOf": [20, 30, 50]}}, [1, 2]),
    ],
)
def test_product_filter_by_minimal_price(
    where, indexes, api_client, product_list, channel_USD
):
    # given
    variables = {
        "channel": channel_USD.slug,
        "where": where,
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}


def test_products_filter_by_attributes(
    api_client,
    product_list,
    channel_USD,
):
    # given
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
    product = product_list[0]
    product.product_type = product_type
    product.save()
    associate_attribute_values_to_instance(product, attribute, attr_value)

    variables = {
        "channel": channel_USD.slug,
        "where": {
            "attributes": [{"slug": attribute.slug, "values": [attr_value.slug]}],
        },
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    product_id = graphene.Node.to_global_id("Product", product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product.name


@pytest.mark.parametrize(
    "values_range, indexes",
    [
        ({"lte": 8}, [1, 2]),
        ({"gte": 0, "lte": 8}, [1, 2]),
        ({"gte": 7, "lte": 8}, []),
        ({"gte": 5}, [0, 1, 2]),
        ({"gte": 8, "lte": 10}, [0]),
        ({"gte": 12}, [0]),
        ({"gte": 20}, []),
        ({"gte": 20, "lte": 8}, []),
        ({"gte": 5, "lte": 5}, [1, 2]),
    ],
)
def test_products_filter_by_numeric_attributes(
    values_range,
    indexes,
    api_client,
    product_list,
    numeric_attribute,
    channel_USD,
):
    # given
    product_list[0].product_type.product_attributes.add(numeric_attribute)
    associate_attribute_values_to_instance(
        product_list[0], numeric_attribute, *numeric_attribute.values.all()
    )

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    numeric_attribute.product_types.add(product_type)

    product_list[1].product_type = product_type
    attr_value = AttributeValue.objects.create(
        attribute=numeric_attribute, name="5", slug="5"
    )
    associate_attribute_values_to_instance(
        product_list[1], numeric_attribute, attr_value
    )

    attr_value = AttributeValue.objects.create(
        attribute=numeric_attribute, name="5", slug="5_X"
    )
    product_list[2].product_type = product_type
    associate_attribute_values_to_instance(
        product_list[2], numeric_attribute, attr_value
    )

    variables = {
        "channel": channel_USD.slug,
        "where": {
            "attributes": [
                {"slug": numeric_attribute.slug, "valuesRange": values_range}
            ]
        },
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}


@pytest.mark.parametrize("filter_value, indexes", [(False, [0, 1]), (True, [0])])
def test_products_filter_by_boolean_attributes(
    filter_value,
    indexes,
    api_client,
    product_list,
    boolean_attribute,
    channel_USD,
):
    # given
    product_list[0].product_type.product_attributes.add(boolean_attribute)
    associate_attribute_values_to_instance(
        product_list[0],
        boolean_attribute,
        boolean_attribute.values.get(boolean=filter_value),
    )

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    boolean_attribute.product_types.add(product_type)

    product_list[1].product_type = product_type
    associate_attribute_values_to_instance(
        product_list[1], boolean_attribute, boolean_attribute.values.get(boolean=False)
    )

    variables = {
        "channel": channel_USD.slug,
        "where": {
            "attributes": [{"slug": boolean_attribute.slug, "boolean": filter_value}]
        },
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["products"]["edges"]
    assert len(nodes) == len(indexes)
    returned_slugs = {node["node"]["slug"] for node in nodes}
    assert returned_slugs == {product_list[index].slug for index in indexes}


def test_products_filter_by_attributes_values_and_range(
    api_client,
    product_list,
    category,
    numeric_attribute,
    channel_USD,
):
    # given
    product_attr = product_list[0].attributes.first()
    attr_value_1 = product_attr.values.first()
    product_list[0].product_type.product_attributes.add(numeric_attribute)
    associate_attribute_values_to_instance(
        product_list[0], numeric_attribute, *numeric_attribute.values.all()
    )

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    numeric_attribute.product_types.add(product_type)

    product_list[1].product_type = product_type
    attr_value_2 = AttributeValue.objects.create(
        attribute=numeric_attribute, name="1.2", slug="1_2"
    )
    associate_attribute_values_to_instance(
        product_list[1], numeric_attribute, attr_value_2
    )
    variables = {
        "channel": channel_USD.slug,
        "where": {
            "attributes": [
                {"slug": numeric_attribute.slug, "valuesRange": {"gte": 2}},
                {"slug": attr_value_1.attribute.slug, "values": [attr_value_1.slug]},
            ]
        },
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    products = content["data"]["products"]["edges"]
    assert len(products) == 1
    assert products[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_list[0].pk
    )
    assert products[0]["node"]["slug"] == product_list[0].slug


def test_products_filter_by_swatch_attributes(
    api_client,
    product_list,
    swatch_attribute,
    channel_USD,
):
    # given
    product_list[0].product_type.product_attributes.add(swatch_attribute)
    associate_attribute_values_to_instance(
        product_list[0], swatch_attribute, *swatch_attribute.values.all()
    )

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        has_variants=True,
        is_shipping_required=True,
    )
    swatch_attribute.product_types.add(product_type)

    product_list[1].product_type = product_type
    attr_value = AttributeValue.objects.create(
        attribute=swatch_attribute, name="Dark", slug="dark"
    )
    associate_attribute_values_to_instance(
        product_list[1], swatch_attribute, attr_value
    )

    variables = {
        "channel": channel_USD.slug,
        "where": {
            "attributes": [{"slug": swatch_attribute.slug, "values": [attr_value.slug]}]
        },
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    products = content["data"]["products"]["edges"]
    assert len(products) == 1
    assert products[0]["node"]["slug"] == product_list[1].slug


def test_products_filter_by_date_range_date_attributes(
    api_client,
    product_list,
    date_attribute,
    channel_USD,
):
    """Ensure both products will be returned when filtering attributes by date range,
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
        "channel": channel_USD.slug,
        "where": {
            "attributes": [
                {
                    "slug": date_attribute.slug,
                    "date": {"gte": date_value.date(), "lte": date_value.date()},
                }
            ],
        },
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    assert {node["node"]["id"] for node in products} == {
        graphene.Node.to_global_id("Product", instance.id)
        for instance in product_list[:2]
    }


def test_products_filter_by_date_range_date_variant_attributes(
    api_client,
    product_list,
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
        "channel": channel_USD.slug,
        "where": {
            "attributes": [
                {
                    "slug": date_attribute.slug,
                    "date": {"gte": date_value.date(), "lte": date_value.date()},
                }
            ],
        },
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)

    # then
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    assert {node["node"]["id"] for node in products} == {
        graphene.Node.to_global_id("Product", instance.id)
        for instance in product_list[1:]
    }


def test_products_filter_by_date_range_date_time_attributes(
    api_client,
    product_list,
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
        "channel": channel_USD.slug,
        "where": {
            "attributes": [
                {
                    "slug": date_time_attribute.slug,
                    "date": {"gte": date_value.date(), "lte": date_value.date()},
                }
            ],
        },
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    assert {node["node"]["id"] for node in products} == {
        graphene.Node.to_global_id("Product", instance.id)
        for instance in product_list[:2]
    }


def test_products_filter_by_date_range_date_time_variant_attributes(
    api_client,
    product_list,
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
        "channel": channel_USD.slug,
        "where": {
            "attributes": [
                {
                    "slug": date_time_attribute.slug,
                    "date": {"gte": date_value.date(), "lte": date_value.date()},
                }
            ],
        },
    }

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    assert {node["node"]["id"] for node in products} == {
        graphene.Node.to_global_id("Product", instance.id)
        for instance in product_list[1:]
    }


def test_products_filter_by_date_time_range_date_time_attributes(
    api_client,
    product_list,
    date_time_attribute,
    channel_USD,
):
    """Ensure both products will be returned when filtering by attributes by date range
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
        "channel": channel_USD.slug,
        "where": {
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

    # when
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 2
    assert {node["node"]["id"] for node in products} == {
        graphene.Node.to_global_id("Product", instance.id)
        for instance in product_list[:2]
    }


def test_products_filter_by_non_existing_attribute(
    api_client, product_list, channel_USD
):
    variables = {
        "channel": channel_USD.slug,
        "where": {"attributes": [{"slug": "i-do-not-exist", "values": ["red"]}]},
    }
    response = api_client.post_graphql(PRODUCTS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]
    assert len(products) == 0
