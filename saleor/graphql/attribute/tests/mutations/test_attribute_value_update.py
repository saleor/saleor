import graphene
from django.utils.text import slugify

from .....attribute.error_codes import AttributeErrorCode
from ....tests.utils import get_graphql_content

UPDATE_ATTRIBUTE_VALUE_MUTATION = """
mutation AttributeValueUpdate(
        $id: ID!, $name: String!) {
    attributeValueUpdate(
    id: $id, input: {name: $name}) {
        attributeErrors {
            field
            message
            code
        }
        attributeValue {
            name
            slug
        }
        attribute {
            values {
                name
            }
        }
    }
}
"""


def test_update_attribute_value(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = pink_attribute_value
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"name": name, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == name == value.name
    assert data["attributeValue"]["slug"] == slugify(name)
    assert name in [value["name"] for value in data["attribute"]["values"]]


def test_update_attribute_value_name_not_unique(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = pink_attribute_value.attribute.values.create(
        name="Example Name", slug="example-name", value="#RED"
    )
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    variables = {"name": pink_attribute_value.name, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    assert data["attributeErrors"]
    assert data["attributeErrors"][0]["message"]
    assert data["attributeErrors"][0]["field"] == "name"
    assert data["attributeErrors"][0]["code"] == AttributeErrorCode.ALREADY_EXISTS.name
