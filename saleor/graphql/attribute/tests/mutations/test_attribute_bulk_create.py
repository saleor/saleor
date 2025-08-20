from unittest.mock import patch

import graphene

from .....attribute.error_codes import AttributeBulkCreateErrorCode
from .....attribute.models import Attribute, AttributeValue
from ....core.enums import ErrorPolicyEnum
from ....tests.utils import get_graphql_content
from ...enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum

ATTRIBUTE_BULK_CREATE_MUTATION = """
    mutation AttributeBulkCreate(
        $attributes: [AttributeCreateInput!]!,
        $errorPolicy: ErrorPolicyEnum
    ) {
        attributeBulkCreate(attributes: $attributes, errorPolicy: $errorPolicy) {
            results {
                errors {
                    path
                    message
                    code
                }
                attribute{
                    id
                    name
                    slug
                    entityType
                    referenceTypes {
                        ... on ProductType {
                            id
                            slug
                        }
                        ... on PageType {
                            id
                            slug
                        }
                    }
                    choices(first: 10) {
                        edges {
                            node {
                                name
                                slug
                                value
                                file {
                                    url
                                    contentType
                                }
                            }
                        }
                    }
                }
            }
            count
        }
    }
"""


def test_attribute_bulk_create_with_base_data(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    attribute_1_name = "Example name 1"
    attribute_2_name = "Example name 2"
    external_reference_1 = "test-ext-ref-1"
    external_reference_2 = "test-ext-ref-2"

    attributes = [
        {
            "name": attribute_1_name,
            "externalReference": external_reference_1,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        },
        {
            "name": attribute_2_name,
            "externalReference": external_reference_2,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()

    assert len(attributes) == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["attribute"]["name"] == attribute_1_name
    assert data["results"][1]["attribute"]["name"] == attribute_2_name


@patch("saleor.plugins.manager.PluginsManager.attribute_created")
def test_attribute_bulk_create_trigger_webhook(
    created_webhook_mock,
    staff_api_client,
    permission_manage_product_types_and_attributes,
):
    # given

    attribute_1_name = "Example name 1"
    attribute_2_name = "Example name 2"
    external_reference_1 = "test-ext-ref-1"
    external_reference_2 = "test-ext-ref-2"

    attributes = [
        {
            "name": attribute_1_name,
            "externalReference": external_reference_1,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        },
        {
            "name": attribute_2_name,
            "externalReference": external_reference_2,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()

    assert len(attributes) == 2
    assert data["count"] == 2
    assert created_webhook_mock.call_count == 2


def test_attribute_bulk_create_without_permission(staff_api_client):
    # given
    attribute_1_name = "Example name 1"
    attribute_2_name = "Example name 2"
    external_reference_1 = "test-ext-ref-1"
    external_reference_2 = "test-ext-ref-2"

    attributes = [
        {
            "name": attribute_1_name,
            "externalReference": external_reference_1,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        },
        {
            "name": attribute_2_name,
            "externalReference": external_reference_2,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        },
    ]

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()

    assert len(attributes) == 0
    assert data["results"][0]["errors"]
    assert data["results"][1]["errors"]
    assert data["count"] == 0


def test_attribute_bulk_create_with_deprecated_field(staff_api_client):
    # given
    attribute_1_name = "Example name 1"
    external_reference_1 = "test-ext-ref-1"

    attributes = [
        {
            "name": attribute_1_name,
            "externalReference": external_reference_1,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "filterableInStorefront": True,
        }
    ]

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()
    errors = data["results"][0]["errors"]
    message = (
        "Deprecated fields 'storefront_search_position', "
        "'filterable_in_storefront', 'available_in_grid' and are not "
        "allowed in bulk mutation."
    )

    assert len(attributes) == 0
    assert data["count"] == 0
    assert errors
    assert errors[0]["code"] == AttributeBulkCreateErrorCode.INVALID.name
    assert errors[0]["message"] == message


def test_attribute_bulk_create_with_file_input_type_and_invalid_settings(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_products,
):
    # given
    attribute_1_name = "Example name 1"
    attribute_2_name = "Example name 2"
    external_reference_1 = "test-ext-ref-1"
    external_reference_2 = "test-ext-ref-2"

    attributes = [
        {
            "name": attribute_1_name,
            "externalReference": external_reference_1,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.FILE.name,
            "filterableInDashboard": True,
        },
        {
            "name": attribute_2_name,
            "externalReference": external_reference_2,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.FILE.name,
            "filterableInDashboard": True,
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION, {"attributes": attributes}
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()

    errors_1 = data["results"][0]["errors"]
    errors_2 = data["results"][1]["errors"]

    assert len(attributes) == 0
    assert errors_1
    assert errors_2
    assert data["count"] == 0

    assert {error["path"] for error in errors_1 + errors_2} == {
        "filterableInDashboard",
    }
    assert {error["code"] for error in errors_1 + errors_2} == {
        AttributeBulkCreateErrorCode.INVALID.name
    }


def test_attribute_bulk_create_with_duplicated_external_ref(
    staff_api_client,
    permission_manage_product_types_and_attributes,
):
    # given
    attribute_1_name = "Example name 1"
    attribute_2_name = "Example name 2"
    external_reference = "test-ext-ref"

    attributes = [
        {
            "name": attribute_1_name,
            "externalReference": external_reference,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        },
        {
            "name": attribute_2_name,
            "externalReference": external_reference,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION, {"attributes": attributes}
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()

    errors_1 = data["results"][0]["errors"]
    errors_2 = data["results"][1]["errors"]

    assert len(attributes) == 0
    assert errors_1
    assert errors_2
    assert errors_1[0]["path"] == "externalReference"
    assert (
        errors_1[0]["code"] == AttributeBulkCreateErrorCode.DUPLICATED_INPUT_ITEM.name
    )
    assert errors_2[0]["path"] == "externalReference"
    assert (
        errors_2[0]["code"] == AttributeBulkCreateErrorCode.DUPLICATED_INPUT_ITEM.name
    )
    assert data["count"] == 0


def test_attribute_bulk_create_with_to_long_name(
    staff_api_client,
    permission_manage_product_types_and_attributes,
):
    # given
    attribute_name = 30 * "1234567890"

    attributes = [
        {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION, {"attributes": attributes}
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()

    errors = data["results"][0]["errors"]

    assert len(attributes) == 0
    assert data["count"] == 0

    assert errors
    assert errors[0]["path"] == "slug"
    assert errors[0]["code"] == AttributeBulkCreateErrorCode.MAX_LENGTH.name
    assert errors[1]["path"] == "name"
    assert errors[1]["code"] == AttributeBulkCreateErrorCode.MAX_LENGTH.name


def test_attribute_bulk_create_with_existing_external_ref(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    attribute_name = "Example name"

    attributes = [
        {
            "name": attribute_name,
            "externalReference": color_attribute.external_reference,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION, {"attributes": attributes}
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    errors = data["results"][0]["errors"]

    assert data["count"] == 0
    assert errors[0]["path"] == "externalReference"
    assert errors[0]["code"] == AttributeBulkCreateErrorCode.UNIQUE.name


def test_attribute_bulk_create_dropdown_with_values(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    attribute_1_name = "Example name 1"
    external_reference_1 = "test-ext-ref-1"
    value_1 = "RED"
    value_2 = "BLUE"

    attributes = [
        {
            "name": attribute_1_name,
            "externalReference": external_reference_1,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.DROPDOWN.name,
            "values": [
                {"name": value_1},
                {"name": value_2},
            ],
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()
    values = AttributeValue.objects.all()

    assert len(attributes) == 1
    assert len(values) == 2
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    choices = data["results"][0]["attribute"]["choices"]["edges"]
    assert choices[0]["node"]["name"] == value_1
    assert choices[1]["node"]["name"] == value_2
    assert choices[0]["node"]["value"] == ""
    assert choices[1]["node"]["value"] == ""


def test_attribute_bulk_create_with_duplicated_external_reference_in_values(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    attribute_1_name = "Example name 1"
    attribute_2_name = "Example name 2"
    external_reference_1 = "test-ext-ref-1"
    value_1 = "RED"
    value_2 = "BLUE"
    value_external_reference = "test-value-ext-ref"

    attributes = [
        {
            "name": attribute_1_name,
            "externalReference": external_reference_1,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.DROPDOWN.name,
            "values": [
                {"name": value_1, "externalReference": value_external_reference},
                {"name": value_2, "externalReference": value_external_reference},
            ],
        },
        {
            "name": attribute_2_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.DROPDOWN.name,
            "values": [
                {"name": value_1, "externalReference": value_external_reference},
            ],
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()
    values = AttributeValue.objects.all()

    assert len(attributes) == 0
    assert len(values) == 0
    assert data["count"] == 0

    errors_1 = data["results"][0]["errors"]
    errors_2 = data["results"][1]["errors"]
    assert errors_1[0]["path"] == "values.0.externalReference"
    assert (
        errors_1[0]["code"] == AttributeBulkCreateErrorCode.DUPLICATED_INPUT_ITEM.name
    )
    assert errors_1[1]["path"] == "values.1.externalReference"
    assert (
        errors_1[1]["code"] == AttributeBulkCreateErrorCode.DUPLICATED_INPUT_ITEM.name
    )
    assert errors_2[0]["path"] == "values.0.externalReference"
    assert (
        errors_2[0]["code"] == AttributeBulkCreateErrorCode.DUPLICATED_INPUT_ITEM.name
    )


def test_attribute_bulk_create_with_existing_external_reference_in_values(
    staff_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    attribute_1_name = "Example name 1"
    value_1 = "RED"
    value_external_reference = color_attribute.values.first().external_reference

    attributes = [
        {
            "name": attribute_1_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.DROPDOWN.name,
            "values": [
                {"name": value_1, "externalReference": value_external_reference},
            ],
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    assert data["count"] == 0

    errors = data["results"][0]["errors"]
    assert errors
    assert errors[0]["path"] == "values.0.externalReference"
    assert errors[0]["code"] == AttributeBulkCreateErrorCode.UNIQUE.name


def test_attribute_bulk_create_dropdown_with_one_invalid_value_and_ignore_failed(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    attribute_name = "Example name 1"
    value_1 = "RED"
    invalid_value_2 = 30 * "1234567890"

    attributes = [
        {
            "name": attribute_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.DROPDOWN.name,
            "values": [
                {"name": value_1},
                {"name": invalid_value_2},
            ],
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {"attributes": attributes, "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()
    values = AttributeValue.objects.all()

    errors = data["results"][0]["errors"]
    assert len(attributes) == 1
    assert len(values) == 1
    assert errors
    assert data["count"] == 1
    choices = data["results"][0]["attribute"]["choices"]["edges"]
    assert choices[0]["node"]["name"] == value_1
    assert choices[0]["node"]["value"] == ""
    assert len(errors) == 1
    assert errors[0]["path"] == "values.1.name"
    assert errors[0]["code"] == AttributeBulkCreateErrorCode.MAX_LENGTH.name


def test_attribute_bulk_create_dropdown_with_invalid_row_and_reject_failed_rows(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    attribute_1_name = "Example name 1"
    attribute_2_name = "Example name 2"
    value_1 = "RED"
    invalid_value_2 = 30 * "1234567890"

    attributes = [
        {
            "name": attribute_1_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.DROPDOWN.name,
            "values": [
                {"name": value_1},
            ],
        },
        {
            "name": attribute_2_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.DROPDOWN.name,
            "values": [
                {"name": invalid_value_2},
            ],
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {
            "attributes": attributes,
            "errorPolicy": ErrorPolicyEnum.REJECT_FAILED_ROWS.name,
        },
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()
    values = AttributeValue.objects.all()

    assert len(attributes) == 1
    assert len(values) == 1
    assert not data["results"][0]["errors"]
    assert data["results"][1]["errors"]
    assert data["results"][1]["errors"][0]["path"] == "values.0.name"
    assert data["count"] == 1
    choices = data["results"][0]["attribute"]["choices"]["edges"]
    assert choices[0]["node"]["name"] == value_1
    assert choices[0]["node"]["value"] == ""


def test_attribute_bulk_create_with_reference_types(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product_type,
    page_type,
):
    # given
    attribute_1_name = "Example name 1"
    attribute_2_name = "Example name 2"
    ref_product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)
    ref_page_type_id = graphene.Node.to_global_id("PageType", page_type.id)
    entity_type_1 = AttributeEntityTypeEnum.PRODUCT.name
    entity_type_2 = AttributeEntityTypeEnum.PAGE.name

    attributes = [
        {
            "name": attribute_1_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
            "entityType": entity_type_1,
            "referenceTypes": [ref_product_type_id],
        },
        {
            "name": attribute_2_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.SINGLE_REFERENCE.name,
            "entityType": entity_type_2,
            "referenceTypes": [ref_page_type_id],
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()

    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["attribute"]["name"] == attribute_1_name
    assert data["results"][1]["attribute"]["name"] == attribute_2_name
    assert data["results"][0]["attribute"]["entityType"] == entity_type_1
    assert data["results"][1]["attribute"]["entityType"] == entity_type_2
    assert len(data["results"][0]["attribute"]["referenceTypes"]) == 1
    assert len(data["results"][1]["attribute"]["referenceTypes"]) == 1

    assert (
        data["results"][0]["attribute"]["referenceTypes"][0]["id"]
        == ref_product_type_id
    )
    assert (
        data["results"][1]["attribute"]["referenceTypes"][0]["id"] == ref_page_type_id
    )


@patch("saleor.graphql.attribute.mutations.mixins.REFERENCE_TYPES_LIMIT", 1)
def test_attribute_bulk_create_with_invalid_reference_types(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product_type,
    page_type,
    page_type_list,
):
    # given
    attribute_1_name = "Example name 1"
    attribute_2_name = "Example name 2"
    ref_product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)
    ref_page_type_id = graphene.Node.to_global_id("PageType", page_type.id)

    attributes = [
        {
            "name": attribute_1_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.REFERENCE.name,
            "entityType": AttributeEntityTypeEnum.PRODUCT.name,
            # should be a list of product types
            "referenceTypes": [ref_page_type_id],
        },
        {
            "name": attribute_2_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.SINGLE_REFERENCE.name,
            "entityType": AttributeEntityTypeEnum.PAGE.name,
            # should be a list of page types
            "referenceTypes": [ref_product_type_id],
        },
        {
            "name": attribute_2_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.SINGLE_REFERENCE.name,
            "entityType": AttributeEntityTypeEnum.PAGE.name,
            # limit exceeded
            "referenceTypes": [
                graphene.Node.to_global_id("PageType", p_type.id)
                for p_type in page_type_list
            ],
        },
        {
            "name": attribute_2_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            "inputType": AttributeInputTypeEnum.SINGLE_REFERENCE.name,
            # invalid entity type
            "entityType": AttributeEntityTypeEnum.COLLECTION.name,
            "referenceTypes": [ref_product_type_id],
        },
        {
            "name": attribute_2_name,
            "type": AttributeTypeEnum.PRODUCT_TYPE.name,
            # invalid input type
            "inputType": AttributeInputTypeEnum.DROPDOWN.name,
            "referenceTypes": [ref_product_type_id],
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_CREATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkCreate"]

    # then
    attributes = Attribute.objects.all()

    assert data["count"] == 0
    assert data["results"][0]["errors"]
    assert data["results"][1]["errors"]
    assert data["results"][2]["errors"]
    assert data["results"][3]["errors"]
    assert data["results"][4]["errors"]

    for result in data["results"]:
        assert len(result["errors"]) == 1
        assert result["errors"][0]["code"] == AttributeBulkCreateErrorCode.INVALID.name
        assert result["errors"][0]["path"] == "referenceTypes"
