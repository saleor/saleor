import graphene
import pytest
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .....attribute.error_codes import AttributeErrorCode
from .....attribute.models import AttributeValue
from ....tests.utils import get_graphql_content
from ...mutations import validate_value_is_unique


def test_validate_value_is_unique(color_attribute):
    value = color_attribute.values.first()

    # a new value but with existing slug should raise an error
    with pytest.raises(ValidationError):
        validate_value_is_unique(color_attribute, AttributeValue(slug=value.slug))

    # a new value with a new slug should pass
    validate_value_is_unique(
        color_attribute, AttributeValue(slug="spanish-inquisition")
    )

    # value that already belongs to the attribute shouldn't be taken into account
    validate_value_is_unique(color_attribute, value)


CREATE_ATTRIBUTE_VALUE_MUTATION = """
    mutation createAttributeValue(
        $attributeId: ID!, $name: String!,
        $value: String, $fileUrl: String, $contentType: String
    ) {
    attributeValueCreate(
        attribute: $attributeId, input: {
            name: $name, value: $value, fileUrl: $fileUrl, contentType: $contentType
        }) {
        errors {
            field
            message
            code
        }
        attribute {
            choices(first: 10) {
                edges {
                    node {
                        name
                        value
                        file {
                            url
                            contentType
                        }
                    }
                }
            }
        }
        attributeValue {
            name
            slug
        }
    }
}
"""


def test_create_attribute_value(
    staff_api_client, color_attribute, permission_manage_products
):
    # given
    attribute = color_attribute
    query = CREATE_ATTRIBUTE_VALUE_MUTATION
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    name = "test name"
    variables = {"name": name, "attributeId": attribute_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueCreate"]
    assert not data["errors"]

    attr_data = data["attributeValue"]
    assert attr_data["name"] == name
    assert attr_data["slug"] == slugify(name)
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


def test_create_swatch_attribute_value_with_value(
    staff_api_client, swatch_attribute, permission_manage_products
):
    # given
    attribute = swatch_attribute
    query = CREATE_ATTRIBUTE_VALUE_MUTATION
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    name = "test name"
    value = "#ffffff"
    variables = {"name": name, "value": value, "attributeId": attribute_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueCreate"]
    assert not data["errors"]

    attr_data = data["attributeValue"]
    assert attr_data["name"] == name
    assert attr_data["slug"] == slugify(name)
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]
    assert value in [
        value["node"]["value"] for value in data["attribute"]["choices"]["edges"]
    ]


def test_create_swatch_attribute_value_with_file(
    staff_api_client, swatch_attribute, permission_manage_products
):
    # given
    attribute = swatch_attribute
    query = CREATE_ATTRIBUTE_VALUE_MUTATION
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    name = "test name"
    file = "http://mirumee.com/test_media/test_file.jpeg"
    content_type = "image/jpeg"
    variables = {
        "name": name,
        "fileUrl": file,
        "contentType": content_type,
        "attributeId": attribute_id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueCreate"]
    assert not data["errors"]

    attr_data = data["attributeValue"]
    assert attr_data["name"] == name
    assert attr_data["slug"] == slugify(name)
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]
    assert {"url": file, "contentType": content_type} in [
        value["node"]["file"] for value in data["attribute"]["choices"]["edges"]
    ]


def test_create_swatch_attribute_value_with_value_and_file(
    staff_api_client, swatch_attribute, permission_manage_products
):
    # given
    attribute = swatch_attribute
    query = CREATE_ATTRIBUTE_VALUE_MUTATION
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    name = "test name"
    value = "#ffffff"
    file_url = "http://mirumee.com/test_media/test_file.jpeg"
    variables = {
        "name": name,
        "value": value,
        "fileUrl": file_url,
        "attributeId": attribute_id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueCreate"]

    assert not data["attributeValue"]
    assert len(data["errors"]) == 2
    assert {error["code"] for error in data["errors"]} == {
        AttributeErrorCode.INVALID.name,
        AttributeErrorCode.INVALID.name,
    }
    assert {error["field"] for error in data["errors"]} == {"fileUrl", "value"}


@pytest.mark.parametrize(
    "field, value",
    [
        ("fileUrl", "http://mirumee.com/test_media/test_file.jpeg"),
        ("contentType", "jpeg"),
    ],
)
def test_create_attribute_value_provide_not_allowed_input_data(
    field, value, staff_api_client, color_attribute, permission_manage_products
):
    # given
    attribute = color_attribute
    query = CREATE_ATTRIBUTE_VALUE_MUTATION
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    name = "test name"
    variables = {"name": name, field: value, "attributeId": attribute_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueCreate"]

    assert not data["attributeValue"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == AttributeErrorCode.INVALID.name
    assert data["errors"][0]["field"] == field


def test_create_attribute_value_not_unique_name(
    staff_api_client, color_attribute, permission_manage_products
):
    # given
    attribute = color_attribute
    query = CREATE_ATTRIBUTE_VALUE_MUTATION
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    value_name = attribute.values.first().name
    variables = {"name": value_name, "attributeId": attribute_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueCreate"]
    assert not data["errors"]
    assert data["attributeValue"]["slug"] == "red-2"


def test_create_attribute_value_capitalized_name(
    staff_api_client, color_attribute, permission_manage_products
):
    # given
    attribute = color_attribute
    query = CREATE_ATTRIBUTE_VALUE_MUTATION
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    value_name = attribute.values.first().name
    variables = {"name": value_name.upper(), "attributeId": attribute_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueCreate"]
    assert not data["errors"]
    assert data["attributeValue"]["slug"] == "red-2"
