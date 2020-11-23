import graphene
import pytest

from .....attribute.models import Attribute, AttributeValue
from ....tests.utils import get_graphql_content


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
    query = """
    mutation attributeBulkDelete($ids: [ID]!) {
        attributeBulkDelete(ids: $ids) {
            count
        }
    }
    """

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


def test_delete_attribute_values(
    staff_api_client, attribute_value_list, permission_manage_page_types_and_attributes
):
    query = """
    mutation attributeValueBulkDelete($ids: [ID]!) {
        attributeValueBulkDelete(ids: $ids) {
            count
        }
    }
    """

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
