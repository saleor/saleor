import pytest
from django.utils.text import slugify

from .....attribute.error_codes import AttributeErrorCode
from ....tests.utils import get_graphql_content
from ...enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum

CREATE_ATTRIBUTE_MUTATION = """
    mutation createAttribute(
        $input: AttributeCreateInput!
    ){
        attributeCreate(input: $input) {
            attributeErrors {
                field
                message
                code
            }
            attribute {
                name
                slug
                type
                inputType
                entityType
                filterableInStorefront
                filterableInDashboard
                availableInGrid
                storefrontSearchPosition
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
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    name = "Value name"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name}],
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
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


def test_create_attribute_with_file_input_type(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.FILE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
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
    assert len(data["attribute"]["values"]) == 0
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.FILE.name


@pytest.mark.parametrize(
    "entity_type",
    [AttributeEntityTypeEnum.PAGE.name, AttributeEntityTypeEnum.PRODUCT.name],
)
def test_create_attribute_with_reference_input_type(
    entity_type,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
            "entityType": entity_type,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
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
    assert len(data["attribute"]["values"]) == 0
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.REFERENCE.name
    assert data["attribute"]["entityType"] == entity_type


def test_create_attribute_with_reference_input_type_entity_type_not_given(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["attributeErrors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == "entityType"
    assert errors[0]["code"] == AttributeErrorCode.REQUIRED.name


def test_create_page_attribute_and_attribute_values(
    staff_api_client,
    permission_manage_page_types_and_attributes,
    permission_manage_pages,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    name = "Value name"
    variables = {
        "input": {
            "name": attribute_name,
            "values": [{"name": name}],
            "type": AttributeTypeEnum.PAGE_TYPE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_page_types_and_attributes,
            permission_manage_pages,
        ],
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
    assert data["attribute"]["filterableInStorefront"] is False
    assert data["attribute"]["filterableInDashboard"] is False
    assert data["attribute"]["availableInGrid"] is False
    assert data["attribute"]["storefrontSearchPosition"] == 0

    # Check if the attribute values were correctly created
    assert len(data["attribute"]["values"]) == 1
    assert data["attribute"]["type"] == AttributeTypeEnum.PAGE_TYPE.name
    assert data["attribute"]["values"][0]["name"] == name
    assert data["attribute"]["values"][0]["slug"] == slugify(name)


def test_create_attribute_with_file_input_type_and_values(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    name = "Value name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "values": [{"name": name}],
            "inputType": AttributeInputTypeEnum.FILE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["attributeErrors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == "values"
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


def test_create_attribute_with_file_input_type_correct_attribute_settings(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.FILE.name,
            "filterableInStorefront": False,
            "filterableInDashboard": False,
            "availableInGrid": False,
            "storefrontSearchPosition": 0,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
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
    assert len(data["attribute"]["values"]) == 0
    assert data["attribute"]["type"] == AttributeTypeEnum.PRODUCT_TYPE.name
    assert data["attribute"]["inputType"] == AttributeInputTypeEnum.FILE.name


def test_create_attribute_with_file_input_type_and_invalid_settings(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.FILE.name,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
            "storefrontSearchPosition": 1,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["attributeErrors"]

    assert not data["attribute"]
    assert len(errors) == 4
    assert {error["field"] for error in errors} == {
        "filterableInStorefront",
        "filterableInDashboard",
        "availableInGrid",
        "storefrontSearchPosition",
    }
    assert {error["code"] for error in errors} == {AttributeErrorCode.INVALID.name}


@pytest.mark.parametrize(
    "entity_type",
    [AttributeEntityTypeEnum.PAGE.name, AttributeEntityTypeEnum.PRODUCT.name],
)
def test_create_attribute_with_reference_input_type_invalid_settings(
    entity_type,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
            "entityType": entity_type,
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
            "storefrontSearchPosition": 1,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["attributeErrors"]

    assert not data["attribute"]
    assert len(errors) == 4
    assert {error["field"] for error in errors} == {
        "filterableInStorefront",
        "filterableInDashboard",
        "availableInGrid",
        "storefrontSearchPosition",
    }
    assert {error["code"] for error in errors} == {AttributeErrorCode.INVALID.name}


@pytest.mark.parametrize(
    "field, value",
    [
        ("filterableInStorefront", True),
        ("filterableInDashboard", True),
        ("availableInGrid", True),
        ("storefrontSearchPosition", 4),
    ],
)
def test_create_attribute_with_file_input_type_and_invalid_one_settings_value(
    field,
    value,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.FILE.name,
            field: value,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["attributeErrors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == field
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


@pytest.mark.parametrize(
    "field, value",
    [
        ("filterableInStorefront", True),
        ("filterableInDashboard", True),
        ("availableInGrid", True),
        ("storefrontSearchPosition", 4),
    ],
)
def test_create_attribute_with_reference_input_type_invalid_one_settings_value(
    field,
    value,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
            "entityType": AttributeEntityTypeEnum.PAGE.name,
            field: value,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["attributeErrors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == field
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


@pytest.mark.parametrize(
    "entity_type",
    [AttributeEntityTypeEnum.PAGE.name, AttributeEntityTypeEnum.PRODUCT.name],
)
def test_create_attribute_with_reference_input_type_values_given(
    entity_type,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION

    attribute_name = "Example name"
    variables = {
        "input": {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
            "entityType": entity_type,
            "values": [{"name": "test-value"}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeCreate"]
    errors = data["attributeErrors"]

    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == "values"
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


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
    permission_manage_products,
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
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION
    name = "わたし わ にっぽん です"
    slug = "わたし-わ-にっぽん-で"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
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
    permission_manage_products,
    product_type,
):
    # given
    query = CREATE_ATTRIBUTE_MUTATION
    variables = {
        "input": {
            "name": "Example name",
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "values": [{"name": name_1}, {"name": name_2}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_product_types_and_attributes,
            permission_manage_products,
        ],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["attributeCreate"]["attributeErrors"]
    assert errors
    assert errors[0]["field"] == "values"
    assert errors[0]["message"] == error_msg
    assert errors[0]["code"] == error_code.name
