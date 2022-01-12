import graphene
import pytest

from .....attribute.models import Attribute, AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from ....tests.utils import get_graphql_content

ATTRIBUTE_BULK_DELETE_MUTATION = """
    mutation attributeBulkDelete($ids: [ID]!) {
        attributeBulkDelete(ids: $ids) {
            count
        }
    }
"""


@pytest.fixture
def attribute_value_list(color_attribute):
    value_1 = AttributeValue.objects.create(
        slug="pink", name="Pink", attribute=color_attribute, value="#FF69B4"
    )
    value_2 = AttributeValue.objects.create(
        slug="white", name="White", attribute=color_attribute, value="#FFFFFF"
    )
    value_3 = AttributeValue.objects.create(
        slug="black", name="Black", attribute=color_attribute, value="#000000"
    )
    return value_1, value_2, value_3


def test_delete_attributes(
    staff_api_client,
    product_type_attribute_list,
    permission_manage_page_types_and_attributes,
):
    query = ATTRIBUTE_BULK_DELETE_MUTATION

    variables = {
        "ids": [
            graphene.Node.to_global_id("Attribute", attr.id)
            for attr in product_type_attribute_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_page_types_and_attributes]
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeBulkDelete"]["count"] == 3
    assert not Attribute.objects.filter(
        id__in=[attr.id for attr in product_type_attribute_list]
    ).exists()


def test_delete_attributes_products_search_document_updated(
    staff_api_client,
    product_type_attribute_list,
    permission_manage_page_types_and_attributes,
    product_list,
    color_attribute,
):
    query = ATTRIBUTE_BULK_DELETE_MUTATION
    product_1 = product_list[0]
    product_2 = product_list[1]
    variant_1 = product_1.variants.first()

    product_type = product_1.product_type

    attr_1, attr_2, attr_3 = product_type_attribute_list
    product_type.product_attributes.add(attr_1, attr_2, color_attribute)
    product_type.variant_attributes.add(attr_1, attr_3)

    attr_1_name = "attr 1 value"
    attr_1_value = AttributeValue.objects.create(name=attr_1_name, attribute=attr_1)

    color_attribute_value = color_attribute.values.first()

    attr_2_name = "attr 2 value"
    attr_2_value = AttributeValue.objects.create(name=attr_2_name, attribute=attr_2)

    attr_3_name = "attr 3 value"
    attr_3_value = AttributeValue.objects.create(name=attr_3_name, attribute=attr_3)

    associate_attribute_values_to_instance(product_1, attr_1, attr_1_value)
    associate_attribute_values_to_instance(
        product_1, color_attribute, color_attribute_value
    )
    associate_attribute_values_to_instance(product_2, attr_2, attr_2_value)
    associate_attribute_values_to_instance(variant_1, attr_3, attr_3_value)

    variables = {
        "ids": [
            graphene.Node.to_global_id("Attribute", attr.id)
            for attr in product_type_attribute_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_page_types_and_attributes]
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeBulkDelete"]["count"] == 3
    assert not Attribute.objects.filter(
        id__in=[attr.id for attr in product_type_attribute_list]
    ).exists()

    product_1.refresh_from_db()
    product_2.refresh_from_db()
    assert product_1.search_document
    assert attr_1_name not in product_1.search_document
    assert color_attribute_value.name.lower() in product_1.search_document
    assert attr_3_name not in product_1.search_document

    assert product_2.search_document
    assert attr_2_name not in product_2.search_document


ATTRIBUTE_VALUE_BULK_DELETE_MUTATION = """
    mutation attributeValueBulkDelete($ids: [ID]!) {
        attributeValueBulkDelete(ids: $ids) {
            count
        }
    }
"""


def test_delete_attribute_values(
    staff_api_client, attribute_value_list, permission_manage_page_types_and_attributes
):
    query = ATTRIBUTE_VALUE_BULK_DELETE_MUTATION

    variables = {
        "ids": [
            graphene.Node.to_global_id("AttributeValue", val.id)
            for val in attribute_value_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_page_types_and_attributes]
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeValueBulkDelete"]["count"] == 3
    assert not AttributeValue.objects.filter(
        id__in=[val.id for val in attribute_value_list]
    ).exists()


def test_delete_attribute_values_search_document_updated(
    staff_api_client,
    product_list,
    attribute_value_list,
    permission_manage_page_types_and_attributes,
):
    query = ATTRIBUTE_VALUE_BULK_DELETE_MUTATION
    value_1, value_2, value_3 = attribute_value_list

    attribute = value_1.attribute
    value_4 = AttributeValue.objects.create(
        slug="orange", name="Orange", attribute=attribute, value="#ABCD"
    )

    val_1_name = value_1.name
    val_2_name = value_2.name
    val_3_name = value_3.name
    val_4_name = value_4.name

    product_1 = product_list[0]
    product_2 = product_list[1]
    variant_1 = product_1.variants.first()
    product_type = product_1.product_type

    product_type.product_attributes.add(attribute)
    product_type.variant_attributes.add(attribute)

    associate_attribute_values_to_instance(product_1, attribute, value_1, value_4)
    associate_attribute_values_to_instance(product_2, attribute, value_2)
    associate_attribute_values_to_instance(variant_1, attribute, value_3)

    variables = {
        "ids": [
            graphene.Node.to_global_id("AttributeValue", val.id)
            for val in attribute_value_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_page_types_and_attributes]
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeValueBulkDelete"]["count"] == 3
    assert not AttributeValue.objects.filter(
        id__in=[val.id for val in attribute_value_list]
    ).exists()

    product_1.refresh_from_db()
    product_2.refresh_from_db()
    assert product_1.search_document
    assert val_1_name not in product_1.search_document
    assert val_4_name.lower() in product_1.search_document
    assert val_3_name not in product_1.search_document

    assert product_2.search_document
    assert val_2_name not in product_2.search_document
