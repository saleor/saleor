import json

import graphene
import pytest

from .....attribute import AttributeInputType, AttributeType
from .....attribute.models import Attribute
from .....attribute.utils import associate_attribute_values_to_instance
from .....core.units import MeasurementUnits
from .....product import ProductTypeKind
from .....product.models import ProductType
from ....core.enums import MeasurementUnitsEnum
from ....tests.utils import get_graphql_content, get_graphql_content_from_response
from ...enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum

ATTRIBUTES_WHERE_QUERY = """
    query($where: AttributeWhereInput!, $channel: String) {
      attributes(first: 10, where: $where, channel: $channel) {
        edges {
          node {
            name
            slug
          }
        }
      }
    }
"""


def test_attributes_filter_by_ids(api_client, product_type_attribute_list):
    # given
    ids = [
        graphene.Node.to_global_id("Attribute", attribute.pk)
        for attribute in product_type_attribute_list[:2]
    ]
    variables = {"where": {"ids": ids}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    attributes = data["data"]["attributes"]["edges"]
    assert len(attributes) == 2
    received_slugs = {node["node"]["slug"] for node in attributes}
    assert received_slugs == {
        product_type_attribute_list[0].slug,
        product_type_attribute_list[1].slug,
    }


def test_attributes_filter_by_none_as_ids(api_client, product_type_attribute_list):
    # given
    variables = {"where": {"ids": None}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    attributes = data["data"]["attributes"]["edges"]
    assert len(attributes) == 0


def test_attributes_filter_by_ids_empty_list(api_client, product_type_attribute_list):
    # given
    variables = {"where": {"ids": []}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    attributes = data["data"]["attributes"]["edges"]
    assert len(attributes) == 0


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"eq": "Color"}, [0]),
        ({"eq": "test"}, []),
        ({"oneOf": ["Color", "Text"]}, [0, 2]),
        ({"oneOf": ["a", "acd"]}, []),
        ({"oneOf": []}, []),
        ({"oneOf": None}, []),
        ({"eq": ""}, []),
        ({"eq": None}, []),
        (None, []),
    ],
)
def test_attributes_filter_by_name(
    where, indexes, api_client, color_attribute, date_attribute, rich_text_attribute
):
    # given
    attributes = [color_attribute, date_attribute, rich_text_attribute]
    variables = {"where": {"name": where}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"eq": "color"}, [0]),
        ({"eq": "test"}, []),
        ({"oneOf": ["color", "text"]}, [0, 2]),
        ({"oneOf": ["a", "acd"]}, []),
        ({"oneOf": []}, []),
        ({"oneOf": None}, []),
        ({"eq": ""}, []),
        ({"eq": None}, []),
        (None, []),
    ],
)
def test_attributes_filter_by_slug(
    where, indexes, api_client, color_attribute, date_attribute, rich_text_attribute
):
    # given
    attributes = [color_attribute, date_attribute, rich_text_attribute]
    variables = {"where": {"slug": where}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}


@pytest.mark.parametrize("value, indexes", [(True, [0]), (False, [1, 2]), (None, [])])
def test_attributes_filter_by_with_choices(
    value, indexes, api_client, color_attribute, date_attribute, rich_text_attribute
):
    # given
    attributes = [color_attribute, date_attribute, rich_text_attribute]
    variables = {"where": {"withChoices": value}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"eq": AttributeInputTypeEnum.DROPDOWN.name}, [0]),
        ({"eq": AttributeInputTypeEnum.FILE.name}, []),
        (
            {
                "oneOf": [
                    AttributeInputTypeEnum.RICH_TEXT.name,
                    AttributeInputTypeEnum.DATE.name,
                ]
            },
            [1, 2],
        ),
        (
            {
                "oneOf": [
                    AttributeInputTypeEnum.DATE_TIME.name,
                    AttributeInputTypeEnum.FILE.name,
                ]
            },
            [],
        ),
        ({"oneOf": []}, []),
        ({"oneOf": None}, []),
        ({"eq": None}, []),
        (None, []),
    ],
)
def test_attributes_filter_by_input_type(
    where, indexes, api_client, color_attribute, date_attribute, rich_text_attribute
):
    # given
    attributes = [color_attribute, date_attribute, rich_text_attribute]
    variables = {"where": {"inputType": where}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"eq": AttributeEntityTypeEnum.PRODUCT_VARIANT.name}, [2]),
        ({"eq": AttributeEntityTypeEnum.PRODUCT.name}, []),
        (
            {
                "oneOf": [
                    AttributeEntityTypeEnum.PAGE.name,
                    AttributeEntityTypeEnum.PRODUCT_VARIANT.name,
                ]
            },
            [1, 2],
        ),
        (
            {
                "oneOf": [
                    AttributeEntityTypeEnum.PRODUCT.name,
                ]
            },
            [],
        ),
        ({"oneOf": []}, []),
        ({"oneOf": None}, []),
        ({"eq": None}, [0]),
        (None, []),
    ],
)
def test_attributes_filter_by_entity_type(
    where,
    indexes,
    api_client,
    color_attribute,
    product_type_page_reference_attribute,
    page_type_variant_reference_attribute,
):
    # given
    attributes = [
        color_attribute,
        product_type_page_reference_attribute,
        page_type_variant_reference_attribute,
    ]
    color_attribute.entity_type = None
    color_attribute.save(update_fields=["entity_type"])

    variables = {"where": {"entityType": where}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"eq": AttributeTypeEnum.PRODUCT_TYPE.name}, [0, 1]),
        ({"eq": AttributeTypeEnum.PAGE_TYPE.name}, []),
        (
            {
                "oneOf": [
                    AttributeTypeEnum.PRODUCT_TYPE.name,
                    AttributeTypeEnum.PAGE_TYPE.name,
                ]
            },
            [0, 1],
        ),
        (
            {
                "oneOf": [
                    AttributeTypeEnum.PAGE_TYPE.name,
                ]
            },
            [],
        ),
        ({"oneOf": []}, []),
        ({"oneOf": None}, []),
        ({"eq": None}, []),
    ],
)
def test_attributes_filter_by_type(
    where,
    indexes,
    api_client,
    color_attribute,
    product_type_page_reference_attribute,
):
    # given
    attributes = [
        color_attribute,
        product_type_page_reference_attribute,
    ]
    variables = {"where": {"type": where}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}


@pytest.mark.parametrize(
    "where, indexes",
    [
        ({"eq": MeasurementUnitsEnum.CM.name}, [1]),
        ({"eq": MeasurementUnitsEnum.SQ_CM.name}, []),
        (
            {
                "oneOf": [
                    MeasurementUnitsEnum.CM.name,
                    MeasurementUnitsEnum.M.name,
                ]
            },
            [1, 2],
        ),
        (
            {
                "oneOf": [
                    MeasurementUnitsEnum.SQ_CM.name,
                ]
            },
            [],
        ),
        ({"oneOf": []}, []),
        ({"oneOf": None}, []),
        ({"eq": None}, [0, 3]),
    ],
)
def test_attributes_filter_by_unit(
    where,
    indexes,
    api_client,
    color_attribute,
    numeric_attribute,
    date_attribute,
):
    # given
    numeric_attribute_2 = Attribute.objects.create(
        slug="length-2",
        name="Length 2",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.NUMERIC,
        unit=MeasurementUnits.M,
        filterable_in_dashboard=True,
    )
    attributes = [
        color_attribute,
        numeric_attribute,
        numeric_attribute_2,
        date_attribute,
    ]
    variables = {"where": {"unit": where}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}


@pytest.mark.parametrize("value, indexes", [(True, [0, 1]), (False, [2]), (None, [])])
def test_attributes_filter_by_value_required(
    value, indexes, api_client, color_attribute, date_attribute, rich_text_attribute
):
    # given
    attributes = [color_attribute, date_attribute, rich_text_attribute]

    color_attribute.value_required = True
    date_attribute.value_required = True
    rich_text_attribute.value_required = False

    Attribute.objects.bulk_update(attributes, ["value_required"])

    variables = {"where": {"valueRequired": value}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}


@pytest.mark.parametrize("value, indexes", [(True, [0, 1]), (False, [2]), (None, [])])
def test_attributes_filter_by_visible_in_storefront(
    value,
    indexes,
    staff_api_client,
    color_attribute,
    date_attribute,
    rich_text_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    attributes = [color_attribute, date_attribute, rich_text_attribute]

    color_attribute.visible_in_storefront = True
    date_attribute.visible_in_storefront = True
    rich_text_attribute.visible_in_storefront = False

    Attribute.objects.bulk_update(attributes, ["visible_in_storefront"])

    variables = {"where": {"visibleInStorefront": value}}

    # when
    response = staff_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}


@pytest.mark.parametrize("value, indexes", [(True, [0]), (False, [1, 2]), (None, [])])
def test_attributes_filter_by_filterable_in_dashboard(
    value, indexes, api_client, color_attribute, date_attribute, rich_text_attribute
):
    # given
    attributes = [color_attribute, date_attribute, rich_text_attribute]

    color_attribute.filterable_in_dashboard = True
    date_attribute.filterable_in_dashboard = False
    rich_text_attribute.filterable_in_dashboard = False

    Attribute.objects.bulk_update(attributes, ["filterable_in_dashboard"])

    variables = {"where": {"filterableInDashboard": value}}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}


def test_attributes_filter_attributes_in_collection_not_visible_in_listings_by_customer(
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
        "where": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count


def test_attributes_filter_in_collection_not_published_by_customer(
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
        "where": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count - 1
    assert weight_attribute.slug not in {
        attribute["node"]["slug"] for attribute in attributes
    }


def test_attributes_filter_in_collection_not_published_by_staff_with_perm(
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
        "where": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count


def test_attributes_filter_in_collection_not_published_by_staff_without_manage_products(
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
        "where": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count - 1


def test_attributes_filter_in_collection_not_published_by_app_with_perm(
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
        "where": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count


def test_attributes_filter_in_collection_not_published_by_app_without_manage_products(
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
        "where": {
            "inCollection": graphene.Node.to_global_id("Collection", collection.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count - 1


def test_attributes_filter_attributes_in_collection_invalid_collection_id(
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
        "where": {
            "inCollection": "xnd",
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content_from_response(response)
    message_error = (
        '{"in_collection": [{"message": "Invalid ID specified.", "code": ""}]}'
    )
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["attributes"] is None


def test_attributes_filter_attributes_in_collection_object_with_given_id_does_not_exist(
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
        "where": {
            "inCollection": graphene.Node.to_global_id("Product", -1),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["attributes"]["edges"] == []


def test_attributes_filter_in_collection_empty_value(
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

    variables = {
        "where": {
            "inCollection": None,
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == 0


def test_attributes_filter_in_category_not_visible_in_listings_by_customer(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count - 1
    assert weight_attribute.slug not in {
        attribute["node"]["slug"] for attribute in attributes
    }


def test_attributes_filter_in_category_not_visible_in_listings_by_staff_with_perm(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count


def test_attributes_filter_in_category_not_in_listings_by_staff_without_manage_products(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count - 1  # product not listed will not count


def test_attributes_filter_in_category_not_visible_in_listings_by_app_with_perm(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count


def test_attributes_filter_in_category_not_in_listings_by_app_without_manage_products(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count - 1  # product not visible will not count


def test_attributes_filter_in_category_not_published_by_customer(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count - 1
    assert weight_attribute.slug not in {
        attribute["node"]["slug"] for attribute in attributes
    }


def test_attributes_filter_in_category_not_published_by_staff_with_perm(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count


def test_attributes_filter_in_category_not_published_by_staff_without_manage_products(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count - 1


def test_attributes_filter_in_category_not_published_by_app_with_perm(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count


def test_attributes_filter_in_category_not_published_by_app_without_manage_products(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Category", category.pk),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == attribute_count - 1


def test_attributes_filter_in_category_invalid_category_id(
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
        "where": {
            "inCategory": "xyz",
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content_from_response(response)
    message_error = (
        '{"in_category": [{"message": "Invalid ID specified.", "code": ""}]}'
    )
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["attributes"] is None


def test_attributes_filter_in_category_object_with_given_id_does_not_exist(
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
        "where": {
            "inCategory": graphene.Node.to_global_id("Product", -1),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["attributes"]["edges"] == []


def test_attributes_filter_in_category_empty_value(
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

    variables = {
        "where": {
            "inCategory": None,
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    attributes = content["data"]["attributes"]["edges"]
    assert len(attributes) == 0


def test_attributes_filter_and_where_both_used(api_client, product_type_attribute_list):
    # given
    query = """
        query($where: AttributeWhereInput!, $filter: AttributeFilterInput!) {
            attributes(first: 10, where: $where, filter: $filter) {
                edges {
                    node {
                        name
                        slug
                    }
                }
            }
        }
    """
    ids = [
        graphene.Node.to_global_id("Attribute", attribute.pk)
        for attribute in product_type_attribute_list[:2]
    ]
    variables = {
        "where": {"AND": [{"ids": ids}]},
        "filter": {"filterableInDashboard": True},
    }

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content_from_response(response)
    message_error = "Only one filtering argument (filter or where) can be specified."
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["attributes"] is None


@pytest.mark.parametrize(
    "where, field_name",
    [
        ({"name": {"eq": "Text", "oneOf": ["Color", "Text"]}}, "name"),
        ({"slug": {"eq": "text", "oneOf": ["color", "text"]}}, "slug"),
        (
            {
                "inputType": {
                    "eq": AttributeInputTypeEnum.DATE.name,
                    "oneOf": [
                        AttributeInputTypeEnum.RICH_TEXT.name,
                        AttributeInputTypeEnum.DATE_TIME.name,
                    ],
                }
            },
            "input_type",
        ),
        (
            {
                "entityType": {
                    "eq": AttributeEntityTypeEnum.PAGE.name,
                    "oneOf": [
                        AttributeEntityTypeEnum.PAGE.name,
                        AttributeEntityTypeEnum.PRODUCT_VARIANT.name,
                    ],
                }
            },
            "entity_type",
        ),
        (
            {
                "type": {
                    "eq": AttributeTypeEnum.PRODUCT_TYPE.name,
                    "oneOf": [
                        AttributeTypeEnum.PAGE_TYPE.name,
                        AttributeTypeEnum.PRODUCT_TYPE.name,
                    ],
                }
            },
            "type",
        ),
        (
            {
                "unit": {
                    "eq": MeasurementUnitsEnum.M.name,
                    "oneOf": [
                        MeasurementUnitsEnum.CM.name,
                        MeasurementUnitsEnum.SQ_CM.name,
                    ],
                }
            },
            "unit",
        ),
    ],
)
def test_attributes_filter_invalid_input(
    where,
    field_name,
    api_client,
    color_attribute,
    numeric_attribute,
    date_attribute,
):
    # given
    variables = {"where": where}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content_from_response(response)
    message_error = "Only one option can be specified."
    assert len(content["errors"]) == 1
    message = json.loads(content["errors"][0]["message"])
    assert message[field_name][0]["message"] == message_error
    assert content["data"]["attributes"] is None


@pytest.mark.parametrize(
    "where",
    [
        # {"name": {"eq": "Text"}, "NOT": {"slug": {"eq": "test"}}},
        {"name": {"eq": "Text"}, "AND": [{"slug": {"eq": "test"}}]},
        {"name": {"eq": "Text"}, "OR": [{"slug": {"eq": "test"}}]},
        {"AND": [{"name": {"eq": "Text"}}], "OR": [{"slug": {"eq": "test"}}]},
        # {"AND": [{"name": {"eq": "Text"}}], "NOT": {"slug": {"eq": "test"}}},
        # {"OR": [{"name": {"eq": "Text"}}], "NOT": {"slug": {"eq": "test"}}},
        # {"NOT": {"slug": {"eq": "test"}, "AND": [{"name": {"eq": "Text"}}]}},
        {"OR": [{"slug": {"eq": "test"}, "AND": [{"name": {"eq": "Text"}}]}]},
        {"AND": [{"slug": {"eq": "test"}, "OR": [{"name": {"eq": "Text"}}]}]},
    ],
)
def test_attributes_where_operator_invalid_input_data(where, api_client):
    # given
    variables = {"where": where}

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    content = get_graphql_content_from_response(response)
    message_error = "Cannot mix operators with other filter inputs."
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["attributes"] is None


def test_attributes_where_with_and_operator(
    api_client, color_attribute, date_attribute, rich_text_attribute
):
    # given
    variables = {
        "where": {
            "AND": [
                {"type": {"eq": AttributeTypeEnum.PRODUCT_TYPE.name}},
                {"inputType": {"eq": AttributeInputTypeEnum.DATE.name}},
            ]
        }
    }

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == 1
    assert nodes[0]["node"]["slug"] == date_attribute.slug


# def test_attributes_where_with_not_operator(
#     api_client, color_attribute, date_attribute, rich_text_attribute
# ):
#     # given
#     variables = {
#         "where": {
#             "NOT": {
#                 "inputType": {"eq": AttributeInputTypeEnum.RICH_TEXT.name},
#             }
#         }
#     }

#     # when
#     response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

#     # then
#     data = get_graphql_content(response)
#     nodes = data["data"]["attributes"]["edges"]
#     assert len(nodes) == 2
#     assert {node["node"]["slug"] for node in nodes} == {
#         color_attribute.slug,
#         date_attribute.slug,
#     }


# def test_attributes_where_with_not_operator_nested_query(
#     api_client, color_attribute, date_attribute, rich_text_attribute
# ):
#     # given
#     variables = {
#         "where": {
#             "NOT": {
#                 "OR": [
#                     {"inputType": {"eq": AttributeInputTypeEnum.DATE.name}},
#                     {"name": {"eq": "Color"}},
#                 ]
#             }
#         }
#     }

#     # when
#     response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

#     # then
#     data = get_graphql_content(response)
#     nodes = data["data"]["attributes"]["edges"]
#     assert len(nodes) == 1
#     assert nodes[0]["node"]["slug"] == rich_text_attribute.slug


def test_attributes_where_with_or_operator(
    api_client, color_attribute, date_attribute, rich_text_attribute
):
    # given
    variables = {
        "where": {
            "OR": [
                {"inputType": {"eq": AttributeInputTypeEnum.DATE.name}},
                {"name": {"eq": "Color"}},
            ]
        }
    }

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == 2
    assert {node["node"]["slug"] for node in nodes} == {
        color_attribute.slug,
        date_attribute.slug,
    }


def test_attributes_where_with_multiple_nested_operators(
    api_client, color_attribute, date_attribute, rich_text_attribute
):
    # given
    variables = {
        "where": {
            "AND": [
                {
                    "OR": [
                        {
                            "AND": [
                                {
                                    "AND": [
                                        {
                                            "AND": [
                                                {
                                                    "AND": [
                                                        {
                                                            "AND": [
                                                                {
                                                                    "slug": {
                                                                        "oneOf": [
                                                                            "color",
                                                                            "text",
                                                                        ]
                                                                    }
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "OR": [
                        {"inputType": {"eq": AttributeInputTypeEnum.DATE.name}},
                        {"name": {"eq": "Color"}},
                    ]
                },
            ]
        }
    }

    # when
    response = api_client.post_graphql(ATTRIBUTES_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == 1
    assert nodes[0]["node"]["slug"] == color_attribute.slug


ATTRIBUTES_SEARCH_QUERY = """
    query($search: String, $channel: String) {
      attributes(first: 10, search: $search, channel: $channel) {
        edges {
          node {
            name
            slug
          }
        }
      }
    }
"""


@pytest.mark.parametrize(
    "search, indexes",
    [
        ("color", [0]),
        ("size", [1]),
        ("date", [2, 3]),
        ("ABCD", []),
        (None, [0, 1, 2, 3]),
        ("", [0, 1, 2, 3]),
    ],
)
def test_search_attributes_on_root_level(
    search,
    indexes,
    api_client,
    color_attribute,
    size_attribute,
    date_attribute,
    date_time_attribute,
):
    # given
    attributes = [color_attribute, size_attribute, date_attribute, date_time_attribute]
    variables = {"search": search}

    # when
    response = api_client.post_graphql(ATTRIBUTES_SEARCH_QUERY, variables)

    # then
    data = get_graphql_content(response)
    nodes = data["data"]["attributes"]["edges"]
    assert len(nodes) == len(indexes)
    returned_attrs = {node["node"]["slug"] for node in nodes}
    assert returned_attrs == {attributes[index].slug for index in indexes}
