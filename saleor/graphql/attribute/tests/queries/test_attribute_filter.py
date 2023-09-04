from unittest import mock

import graphene
import pytest

from .....attribute.models import Attribute
from .....attribute.utils import associate_attribute_values_to_instance
from .....product import ProductTypeKind
from .....product.models import ProductType
from ....tests.utils import get_graphql_content, get_graphql_content_from_response
from ...filters import filter_attributes_by_product_types

ATTRIBUTES_FILTER_QUERY = """
    query($filters: AttributeFilterInput!, $channel: String) {
      attributes(first: 10, filter: $filters, channel: $channel) {
        edges {
          node {
            name
            slug
          }
        }
      }
    }
"""

ATTRIBUTES_VALUE_FILTER_QUERY = """
query($filters: AttributeValueFilterInput!) {
    attributes(first: 10) {
        edges {
            node {
                name
                slug
                choices(first: 10, filter: $filters) {
                    edges {
                        node {
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


def test_search_attributes(api_client, color_attribute, size_attribute):
    variables = {"filters": {"search": "color"}}

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 1
    assert attributes[0]["node"]["slug"] == "color"


@pytest.mark.parametrize(
    "filter_value",
    ["red", "blue"],
)
def test_search_attributes_value(
    filter_value, api_client, color_attribute, size_attribute
):
    variables = {"filters": {"search": filter_value}}

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_VALUE_FILTER_QUERY, variables)
    )
    values = attributes["data"]["attributes"]["edges"][0]["node"]["choices"]["edges"]
    assert len(values) == 1
    assert values[0]["node"]["slug"] == filter_value


@pytest.mark.parametrize(
    "filter_by, attributes_count",
    [({"slugs": ["red", "blue"]}, 2), ({"slugs": ["red"]}, 1), ({"slugs": []}, 2)],
)
def test_atribute_values_with_filtering_slugs(
    filter_by, api_client, attributes_count, color_attribute, size_attribute
):
    variables = {"filters": filter_by}

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_VALUE_FILTER_QUERY, variables)
    )["data"]["attributes"]

    slugs = attributes["edges"][0]["node"]["choices"]["edges"]
    assert len(slugs) == attributes_count


def test_filter_attributes_if_filterable_in_dashboard(
    api_client, color_attribute, size_attribute
):
    color_attribute.filterable_in_dashboard = False
    color_attribute.save(update_fields=["filterable_in_dashboard"])

    variables = {"filters": {"filterableInDashboard": True}}

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 1
    assert attributes[0]["node"]["slug"] == "size"


def test_filter_attributes_if_available_in_grid(
    api_client, color_attribute, size_attribute
):
    color_attribute.available_in_grid = False
    color_attribute.save(update_fields=["available_in_grid"])

    variables = {"filters": {"availableInGrid": True}}

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 1
    assert attributes[0]["node"]["slug"] == "size"


def test_filter_attributes_by_global_id_list(api_client, product_type_attribute_list):
    global_ids = [
        graphene.Node.to_global_id("Attribute", attribute.pk)
        for attribute in product_type_attribute_list[:2]
    ]
    variables = {"filters": {"ids": global_ids}}

    expected_slugs = sorted(
        [product_type_attribute_list[0].slug, product_type_attribute_list[1].slug]
    )

    attributes = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    assert len(attributes) == 2
    received_slugs = sorted(
        [attributes[0]["node"]["slug"], attributes[1]["node"]["slug"]]
    )

    assert received_slugs == expected_slugs


def test_filter_attribute_values_by_global_id_list(
    api_client, attribute_choices_for_sorting
):
    # given
    values = attribute_choices_for_sorting.values.all()
    global_ids = [
        graphene.Node.to_global_id("AttributeValue", value.pk) for value in values[:2]
    ]
    variables = {"filters": {"ids": global_ids}}

    # when
    content = get_graphql_content(
        api_client.post_graphql(ATTRIBUTES_VALUE_FILTER_QUERY, variables)
    )

    # then
    expected_slugs = sorted([values[0].slug, values[1].slug])
    values = content["data"]["attributes"]["edges"][0]["node"]["choices"]["edges"]
    assert len(values) == 2
    received_slugs = sorted([value["node"]["slug"] for value in values])
    assert received_slugs == expected_slugs


def test_filter_attributes_in_category_invalid_category_id(
    user_api_client, product_list, weight_attribute, channel_USD
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(visible_in_listings=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    variables = {
        "filters": {
            "inCategory": "xyz",
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)

    # then
    content = get_graphql_content_from_response(response)
    message_error = (
        '{"in_category": [{"message": "Invalid ID specified.", "code": ""}]}'
    )
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["attributes"] is None


def test_filter_attributes_in_category_object_with_given_id_does_not_exist(
    user_api_client, product_list, weight_attribute, channel_USD
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(visible_in_listings=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Product", -1),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["attributes"]["edges"] == []


def test_filter_attributes_in_category_not_visible_in_listings_by_customer(
    user_api_client, product_list, weight_attribute, channel_USD
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(visible_in_listings=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    category = last_product.category
    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        user_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count - 1
    assert weight_attribute.slug not in {
        attribute["node"]["slug"] for attribute in attributes
    }


def test_filter_attributes_in_category_not_visible_in_listings_by_staff_with_perm(
    staff_api_client,
    product_list,
    weight_attribute,
    permission_manage_products,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(visible_in_listings=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    category = last_product.category
    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count


def test_filter_attributes_in_category_not_in_listings_by_staff_without_manage_products(
    staff_api_client,
    product_list,
    weight_attribute,
    channel_USD,
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(visible_in_listings=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    category = last_product.category
    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count - 1  # product not listed will not count


def test_filter_attributes_in_category_not_visible_in_listings_by_app_with_perm(
    app_api_client,
    product_list,
    weight_attribute,
    permission_manage_products,
    channel_USD,
):
    # given
    app_api_client.app.permissions.add(permission_manage_products)

    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(visible_in_listings=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    category = last_product.category
    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        app_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count


def test_filter_attributes_in_category_not_in_listings_by_app_without_manage_products(
    app_api_client,
    product_list,
    weight_attribute,
    channel_USD,
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(visible_in_listings=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    category = last_product.category
    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        app_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count - 1  # product not visible will not count


def test_filter_attributes_in_category_not_published_by_customer(
    user_api_client, product_list, weight_attribute, channel_USD
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(is_published=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    category = last_product.category
    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        user_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count - 1
    assert weight_attribute.slug not in {
        attribute["node"]["slug"] for attribute in attributes
    }


def test_filter_attributes_in_category_not_published_by_staff_with_perm(
    staff_api_client,
    product_list,
    weight_attribute,
    permission_manage_products,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(is_published=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    category = last_product.category
    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count


def test_filter_attributes_in_category_not_published_by_staff_without_manage_products(
    staff_api_client,
    product_list,
    weight_attribute,
    channel_USD,
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(is_published=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    category = last_product.category
    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count - 1


def test_filter_attributes_in_category_not_published_by_app_with_perm(
    app_api_client,
    product_list,
    weight_attribute,
    permission_manage_products,
    channel_USD,
):
    # given
    app_api_client.app.permissions.add(permission_manage_products)

    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(is_published=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    category = last_product.category
    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        app_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count


def test_filter_attributes_in_category_not_published_by_app_without_manage_products(
    app_api_client,
    product_list,
    weight_attribute,
    channel_USD,
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(is_published=False)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    category = last_product.category
    variables = {
        "filters": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        app_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count - 1


def test_filter_attributes_in_collection_invalid_category_id(
    user_api_client, product_list, weight_attribute, collection, channel_USD
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(visible_in_listings=False)

    for product in product_list:
        collection.products.add(product)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    variables = {
        "filters": {
            "inCollection": "xnd",
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)

    # then
    content = get_graphql_content_from_response(response)
    message_error = (
        '{"in_collection": [{"message": "Invalid ID specified.", "code": ""}]}'
    )
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["attributes"] is None


def test_filter_attributes_in_collection_object_with_given_id_does_not_exist(
    user_api_client, product_list, weight_attribute, collection, channel_USD
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(visible_in_listings=False)

    for product in product_list:
        collection.products.add(product)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    variables = {
        "filters": {
            "inCollection": graphene.Node.to_global_id("Product", -1),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["attributes"]["edges"] == []


def test_filter_attributes_in_collection_not_visible_in_listings_by_customer(
    user_api_client, product_list, weight_attribute, collection, channel_USD
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(visible_in_listings=False)

    for product in product_list:
        collection.products.add(product)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    variables = {
        "filters": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        user_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count


def test_filter_in_collection_not_published_by_customer(
    user_api_client, product_list, weight_attribute, collection, channel_USD
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(is_published=False)

    for product in product_list:
        collection.products.add(product)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    variables = {
        "filters": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        user_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count - 1
    assert weight_attribute.slug not in {
        attribute["node"]["slug"] for attribute in attributes
    }


def test_filter_in_collection_not_published_by_staff_with_perm(
    staff_api_client,
    product_list,
    weight_attribute,
    permission_manage_products,
    collection,
    channel_USD,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(is_published=False)

    for product in product_list:
        collection.products.add(product)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    variables = {
        "filters": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count


def test_filter_in_collection_not_published_by_staff_without_manage_products(
    staff_api_client,
    product_list,
    weight_attribute,
    collection,
    channel_USD,
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(is_published=False)

    for product in product_list:
        collection.products.add(product)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    variables = {
        "filters": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count - 1


def test_filter_in_collection_not_published_by_app_with_perm(
    app_api_client,
    product_list,
    weight_attribute,
    permission_manage_products,
    collection,
    channel_USD,
):
    # given
    app_api_client.app.permissions.add(permission_manage_products)

    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(is_published=False)

    for product in product_list:
        collection.products.add(product)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    variables = {
        "filters": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        app_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count


def test_filter_in_collection_not_published_by_app_without_manage_products(
    app_api_client,
    product_list,
    weight_attribute,
    collection,
    channel_USD,
):
    # given
    product_type = ProductType.objects.create(
        name="Default Type 2",
        slug="default-type-2",
        kind=ProductTypeKind.NORMAL,
        has_variants=True,
        is_shipping_required=True,
    )
    product_type.product_attributes.add(weight_attribute)

    last_product = product_list[-1]
    last_product.product_type = product_type
    last_product.save(update_fields=["product_type"])
    last_product.channel_listings.all().update(is_published=False)

    for product in product_list:
        collection.products.add(product)

    associate_attribute_values_to_instance(
        product_list[-1], weight_attribute, weight_attribute.values.first()
    )

    attribute_count = Attribute.objects.count()

    variables = {
        "filters": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    attributes = get_graphql_content(
        app_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == attribute_count - 1


def test_filter_attributes_by_page_type(
    staff_api_client,
    size_page_attribute,
    product_type_attribute_list,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    variables = {"filters": {"type": "PAGE_TYPE"}}

    # when
    attributes = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == 1
    assert attributes[0]["node"]["slug"] == size_page_attribute.slug


def test_filter_attributes_by_product_type(
    staff_api_client,
    size_page_attribute,
    product_type_attribute_list,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    variables = {"filters": {"type": "PRODUCT_TYPE"}}

    # when
    attributes = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTES_FILTER_QUERY, variables)
    )["data"]["attributes"]["edges"]

    # then
    assert len(attributes) == len(product_type_attribute_list)
    assert size_page_attribute.slug not in {
        attribute["node"]["slug"] for attribute in attributes
    }


def test_attributes_filter_by_product_type_with_empty_value():
    """Ensure passing an empty or null value is ignored and the queryset is simply
    returned without any modification.
    """

    qs = Attribute.objects.all()

    assert filter_attributes_by_product_types(qs, "...", "", None, None) is qs
    assert filter_attributes_by_product_types(qs, "...", None, None, None) is qs


def test_attributes_filter_by_product_type_with_unsupported_field(
    customer_user, channel_USD
):
    """Ensure using an unknown field to filter attributes by raises a NotImplemented
    exception.
    """

    qs = Attribute.objects.all()

    with pytest.raises(NotImplementedError) as exc:
        filter_attributes_by_product_types(
            qs, "in_space", "a-value", customer_user, channel_USD.slug
        )

    assert exc.value.args == ("Filtering by in_space is unsupported",)


def test_attributes_filter_by_non_existing_category_id(customer_user, channel_USD):
    """Ensure using a non-existing category ID returns an empty query set."""

    category_id = graphene.Node.to_global_id("Category", -1)
    mocked_qs = mock.MagicMock()
    qs = filter_attributes_by_product_types(
        mocked_qs, "in_category", category_id, customer_user, channel_USD.slug
    )
    assert qs == mocked_qs.none.return_value
