import pytest
from django.utils.text import slugify

from .....attribute.error_codes import AttributeErrorCode
from ....tests.utils import get_graphql_content
from ...enums import AttributeTypeEnum

CREATE_ATTRIBUTE_MUTATION = """
    mutation createAttribute(
        $name: String!, $slug: String, $type: AttributeTypeEnum!,
        $values: [AttributeValueCreateInput]
    ){
        attributeCreate(input: {
            name: $name, values: $values, slug: $slug, type: $type,
        }) {
            attributeErrors {
                field
                message
                code
            }
            attribute {
                name
                slug
                type
                values {
                    name
                    slug
                }
                productTypes(first: 10) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        }
    }
"""


def test_create_attribute_and_attribute_values(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    name = "Value name"
    variables = {
        "name": attribute_name,
        "values": [{"name": name}],
        "type": AttributeTypeEnum.PRODUCT_TYPE.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["attributeErrors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["values"]) == 1
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["values"][0]["name"] == name
    assert data["attribute"]["values"][0]["slug"] == slugify(name)


def test_create_page_attribute_and_attribute_values(
    staff_api_client, permission_manage_page_types_and_attributes
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    name = "Value name"
    variables = {
        "name": attribute_name,
        "values": [{"name": name}],
        "type": AttributeTypeEnum.PAGE_TYPE.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_page_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["attributeCreate"]["attributeErrors"]
    data = content["data"]["attributeCreate"]

    # Check if the attribute was correctly created
    assert data["attribute"]["name"] == attribute_name
    assert data["attribute"]["slug"] == slugify(
        attribute_name
    ), "The default slug should be the slugified name"
    assert (
        data["attribute"]["productTypes"]["edges"] == []
    ), "The attribute should not have been assigned to a product type"

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["values"]) == 1
    assert data["attribute"]["type"] == AttributeTypeEnum.PAGE_TYPE.name
    assert data["attribute"]["values"][0]["name"] == name
    assert data["attribute"]["values"][0]["slug"] == slugify(name)


@pytest.mark.parametrize(
    "input_slug, expected_slug",
    (
        ("my-slug", "my-slug"),
        (None, "my-name"),
        ("", "my-name"),
        ("わたし-わ-にっぽん-です", "わたし-わ-にっぽん-です"),
    ),
)
def test_create_attribute_with_given_slug(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    input_slug,
    expected_slug,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    query = """
        mutation createAttribute(
            $name: String!, $slug: String, $type: AttributeTypeEnum!) {
        attributeCreate(input: {name: $name, slug: $slug, type: $type}) {
            attributeErrors {
                field
                message
                code
            }
            attribute {
                slug
            }
        }
    }
    """

    attribute_name = "My Name"
    variables = {
        "name": attribute_name,
        "slug": input_slug,
        "type": AttributeTypeEnum.PRODUCT_TYPE.name,
    }

    # when
    content = get_graphql_content(staff_api_client.post_graphql(query, variables))

    # then
    assert not content["data"]["attributeCreate"]["attributeErrors"]
    assert content["data"]["attributeCreate"]["attribute"]["slug"] == expected_slug


def test_create_attribute_value_name_and_slug_with_unicode(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION
    name = "わたし わ にっぽん です"
    slug = "わたし-わ-にっぽん-で"
    variables = {
        "name": name,
        "slug": slug,
        "type": AttributeTypeEnum.PRODUCT_TYPE.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    assert not data["attributeErrors"]
    assert data["attribute"]["name"] == name
    assert data["attribute"]["slug"] == slug


@pytest.mark.parametrize(
    "name_1, name_2, error_msg, error_code",
    (
        (
            "Red color",
            "Red color",
            "Provided values are not unique.",
            AttributeErrorCode.UNIQUE,
        ),
        (
            "Red color",
            "red color",
            "Provided values are not unique.",
            AttributeErrorCode.UNIQUE,
        ),
    ),
)
def test_create_attribute_and_attribute_values_errors(
    staff_api_client,
    name_1,
    name_2,
    error_msg,
    error_code,
    permission_manage_product_types_and_attributes,
    product_type,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION
    variables = {
        "name": "Example name",
        "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        "values": [{"name": name_1}, {"name": name_2}],
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["attributeCreate"]["attributeErrors"]
    assert errors
    assert errors[0]["field"] == "values"
    assert errors[0]["message"] == error_msg
    assert errors[0]["code"] == error_code.name
