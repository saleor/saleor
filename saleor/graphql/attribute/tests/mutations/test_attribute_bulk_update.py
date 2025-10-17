from unittest.mock import patch

import graphene

from .....attribute.error_codes import AttributeBulkUpdateErrorCode
from .....attribute.models import Attribute
from .....attribute.tests.model_helpers import (
    get_product_attribute_values,
    get_product_attributes,
)
from ....core.enums import ErrorPolicyEnum
from ....tests.utils import get_graphql_content

ATTRIBUTE_BULK_UPDATE_MUTATION = """
    mutation AttributeBulkUpdate(
        $attributes: [AttributeBulkUpdateInput!]!,
        $errorPolicy: ErrorPolicyEnum
    ) {
        attributeBulkUpdate(attributes: $attributes, errorPolicy: $errorPolicy) {
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


def test_attribute_bulk_update_with_base_data(
    staff_api_client,
    color_attribute,
    size_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    attribute_1_new_name = "ColorAttrNewName"
    attribute_2_new_name = "SizeAttrNewName"

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {"name": attribute_1_new_name},
        },
        {
            "id": graphene.Node.to_global_id("Attribute", size_attribute.id),
            "fields": {"name": attribute_2_new_name},
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    attributes = Attribute.objects.all()

    assert len(attributes) == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert data["results"][0]["attribute"]["name"] == attribute_1_new_name
    assert data["results"][1]["attribute"]["name"] == attribute_2_new_name


@patch("saleor.plugins.manager.PluginsManager.attribute_updated")
def test_attribute_bulk_update_trigger_webhook(
    created_webhook_mock,
    color_attribute,
    size_attribute,
    staff_api_client,
    permission_manage_product_types_and_attributes,
):
    # given
    attribute_1_new_name = "ColorAttrNewName"
    attribute_2_new_name = "SizeAttrNewName"

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {"name": attribute_1_new_name},
        },
        {
            "id": graphene.Node.to_global_id("Attribute", size_attribute.id),
            "fields": {"name": attribute_2_new_name},
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert data["count"] == 2
    assert created_webhook_mock.call_count == 2


def test_attribute_bulk_update_without_permission(
    staff_api_client,
    color_attribute,
):
    # given
    attribute_new_name = "ColorAttrNewName"

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {"name": attribute_new_name},
        }
    ]

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert data["count"] == 0
    errors = data["results"][0]["errors"]
    assert errors


def test_attribute_bulk_update_with_deprecated_fields(
    staff_api_client,
    color_attribute,
):
    # given
    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {"filterableInStorefront": True},
        }
    ]

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    errors = data["results"][0]["errors"]
    message = (
        "Deprecated fields 'storefront_search_position', "
        "'filterable_in_storefront', 'available_in_grid' and are not "
        "allowed in bulk mutation."
    )

    assert data["count"] == 0
    assert errors
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.INVALID.name
    assert errors[0]["message"] == message


def test_attribute_bulk_update_with_duplicated_external_ref(
    staff_api_client,
    color_attribute,
    size_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    duplicated_external_ref = "duplicated_external_ref"

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {"externalReference": duplicated_external_ref},
        },
        {
            "id": graphene.Node.to_global_id("Attribute", size_attribute.id),
            "fields": {"externalReference": duplicated_external_ref},
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    errors_1 = data["results"][0]["errors"]
    errors_2 = data["results"][1]["errors"]

    assert data["count"] == 0
    assert errors_1
    assert errors_2
    assert errors_1[0]["path"] == "fields.externalReference"
    assert (
        errors_1[0]["code"] == AttributeBulkUpdateErrorCode.DUPLICATED_INPUT_ITEM.name
    )
    assert errors_2[0]["path"] == "fields.externalReference"
    assert (
        errors_2[0]["code"] == AttributeBulkUpdateErrorCode.DUPLICATED_INPUT_ITEM.name
    )


def test_attribute_bulk_update_with_existing_external_ref(
    staff_api_client,
    color_attribute,
    size_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    existing_external_ref = size_attribute.external_reference

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {"externalReference": existing_external_ref},
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    errors = data["results"][0]["errors"]

    assert data["count"] == 0
    assert errors
    assert errors[0]["path"] == "fields.externalReference"
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.UNIQUE.name


def test_attribute_bulk_update_with_invalid_type_id(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    invalid_id = graphene.Node.to_global_id("Page", 1)
    attributes = [{"id": invalid_id, "fields": {"name": "ExampleName"}}]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert data["count"] == 0
    errors = data["results"][0]["errors"]
    assert errors
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == f"Invalid ID: {invalid_id}. Expected: Attribute, received: Page."
    )


def test_attribute_bulk_update_without_id_and_external_ref(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    attributes = [{"fields": {"name": "ExampleName"}}]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert data["count"] == 0
    errors = data["results"][0]["errors"]
    assert errors
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == "At least one of arguments is required: 'id', 'externalReference'."
    )


def test_attribute_bulk_update_with_id_and_external_ref(
    staff_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    color_attribute.external_reference = "ColorExternalRef"
    color_attribute.save(update_fields=["external_reference"])

    global_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    attributes = [
        {
            "id": global_id,
            "externalReference": color_attribute.external_reference,
            "fields": {"name": "ExampleName"},
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert data["count"] == 0
    errors = data["results"][0]["errors"]
    assert errors
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == "Argument 'id' cannot be combined with 'externalReference'"
    )


def test_attribute_bulk_update_removes_value(
    staff_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    assert color_attribute.values.count() == 2

    value_global_id = graphene.Node.to_global_id(
        "AttributeValue", color_attribute.values.first().id
    )

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {"removeValues": [value_global_id]},
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    color_attribute.refresh_from_db()

    assert color_attribute.values.count() == 1
    assert data["count"] == 1
    assert not data["results"][0]["errors"]


@patch("saleor.plugins.manager.PluginsManager.attribute_updated")
@patch("saleor.plugins.manager.PluginsManager.attribute_value_deleted")
def test_attribute_bulk_update_removes_value_trigger_webhook(
    attribute_updated_webhook_mock,
    value_deleted_webhook_mock,
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    assert color_attribute.values.count() == 2

    value_global_id = graphene.Node.to_global_id(
        "AttributeValue", color_attribute.values.first().id
    )

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {"removeValues": [value_global_id]},
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert data["count"] == 1
    assert value_deleted_webhook_mock.call_count == 1
    assert attribute_updated_webhook_mock.call_count == 1


def test_attribute_bulk_update_removes_invalid_value(
    staff_api_client,
    color_attribute,
    size_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    assert size_attribute.values.count() == 2

    invalid_value_global_id = graphene.Node.to_global_id(
        "AttributeValue", size_attribute.values.first().id
    )

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {"removeValues": [invalid_value_global_id]},
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    color_attribute.refresh_from_db()
    size_attribute.refresh_from_db()

    assert color_attribute.values.count() == 2
    assert color_attribute.values.count() == 2
    assert data["count"] == 0
    errors = data["results"][0]["errors"]
    assert errors
    assert errors[0]["path"] == "removeValues.0"
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == f"Value {invalid_value_global_id} does not belong to this attribute."
    )


def test_attribute_bulk_update_removes_value_mark_product_search_index_dirty(
    staff_api_client, product, permission_manage_product_types_and_attributes
):
    # given
    attribute = get_product_attributes(product).first()
    value = get_product_attribute_values(product, attribute).first()
    assert product.search_index_dirty is False

    value_global_id = graphene.Node.to_global_id("AttributeValue", value.id)
    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", attribute.id),
            "fields": {"removeValues": [value_global_id]},
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert data["count"] == 1
    assert not data["results"][0]["errors"]
    product.refresh_from_db()
    assert product.search_index_dirty is True


def test_attribute_bulk_update_removes_value_mark_page_search_index_dirty(
    staff_api_client, page, permission_manage_page_types_and_attributes
):
    # given
    value = page.attributevalues.first().value
    attribute = value.attribute
    assert page.search_index_dirty is False

    value_global_id = graphene.Node.to_global_id("AttributeValue", value.id)
    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", attribute.id),
            "fields": {"removeValues": [value_global_id]},
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert data["count"] == 1
    assert not data["results"][0]["errors"]
    page.refresh_from_db()
    assert page.search_index_dirty is True


def test_attribute_bulk_update_add_new_value(
    staff_api_client,
    color_attribute,
    size_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    assert color_attribute.values.count() == 2
    assert size_attribute.values.count() == 2

    color_new_value_name = "BLACK"
    size_new_value_name = "MINI"

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {
                "addValues": [
                    {
                        "name": color_new_value_name,
                    }
                ]
            },
        },
        {
            "id": graphene.Node.to_global_id("Attribute", size_attribute.id),
            "fields": {
                "addValues": [
                    {
                        "name": size_new_value_name,
                    }
                ]
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    color_attribute.refresh_from_db()
    size_attribute.refresh_from_db()

    assert data["count"] == 2
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert color_attribute.values.count() == 3
    assert size_attribute.values.count() == 3


def test_attribute_bulk_update_add_value_with_existing_name(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    assert color_attribute.values.count() == 2

    value = color_attribute.values.first()

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {
                "addValues": [
                    {
                        "name": value.name,
                    }
                ]
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    color_attribute.refresh_from_db()

    assert data["count"] == 1
    assert not data["results"][0]["errors"]
    assert color_attribute.values.count() == 3


def test_attribute_bulk_update_with_duplicated_external_reference_in_values(
    staff_api_client,
    color_attribute,
    size_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    assert color_attribute.values.count() == 2
    assert size_attribute.values.count() == 2

    color_new_value_name = "BLACK"
    size_new_value_name = "MINI"
    value_external_reference = "test-value-ext-ref"

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {
                "addValues": [
                    {
                        "name": color_new_value_name,
                        "externalReference": value_external_reference,
                    }
                ]
            },
        },
        {
            "id": graphene.Node.to_global_id("Attribute", size_attribute.id),
            "fields": {
                "addValues": [
                    {
                        "name": size_new_value_name,
                        "externalReference": value_external_reference,
                    }
                ]
            },
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert data["count"] == 0
    errors_1 = data["results"][0]["errors"]
    errors_2 = data["results"][1]["errors"]
    assert errors_1
    assert errors_2
    assert errors_1[0]["path"] == "addValues.0.externalReference"
    assert (
        errors_1[0]["code"] == AttributeBulkUpdateErrorCode.DUPLICATED_INPUT_ITEM.name
    )

    assert errors_2[0]["path"] == "addValues.0.externalReference"
    assert (
        errors_2[0]["code"] == AttributeBulkUpdateErrorCode.DUPLICATED_INPUT_ITEM.name
    )


def test_attribute_bulk_update_add_value_with_to_long_name_and_reject_failed_rows(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    assert color_attribute.values.count() == 2

    new_value_1_name = 60 * "BLACK"
    new_value_2_name = "BLACK"
    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {
                "addValues": [
                    {
                        "name": new_value_1_name,
                    },
                    {
                        "name": new_value_2_name,
                    },
                ]
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {
            "attributes": attributes,
            "errorPolicy": ErrorPolicyEnum.REJECT_FAILED_ROWS.name,
        },
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    color_attribute.refresh_from_db()

    errors = data["results"][0]["errors"]
    assert data["count"] == 0
    assert errors
    assert errors[0]["path"] == "addValues.0.name"
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.MAX_LENGTH.name
    assert color_attribute.values.count() == 2


def test_attribute_bulk_update_add_value_with_to_long_name_and_ignore_failed(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    assert color_attribute.values.count() == 2

    new_value_1_name = 60 * "BLACK"
    new_value_2_name = "BLACK"
    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {
                "addValues": [
                    {
                        "name": new_value_1_name,
                    },
                    {
                        "name": new_value_2_name,
                    },
                ]
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes, "errorPolicy": ErrorPolicyEnum.IGNORE_FAILED.name},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    color_attribute.refresh_from_db()

    errors = data["results"][0]["errors"]
    assert data["count"] == 1
    assert errors
    assert errors[0]["path"] == "addValues.0.name"
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.MAX_LENGTH.name
    assert color_attribute.values.count() == 3


def test_attribute_bulk_update_add_value_with_existing_external_ref(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    assert color_attribute.values.count() == 2
    external_ref = color_attribute.values.first().external_reference
    new_value = "BLACK"
    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {
                "addValues": [
                    {
                        "name": new_value,
                        "externalReference": external_ref,
                    },
                ]
            },
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    color_attribute.refresh_from_db()

    errors = data["results"][0]["errors"]
    assert data["count"] == 0
    assert errors
    assert errors[0]["path"] == "addValues.0.externalReference"
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.UNIQUE.name
    assert color_attribute.values.count() == 2


def test_attribute_bulk_update_removes_value_with_invalid_id(
    staff_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    assert color_attribute.values.count() == 2

    invalid_value_id = graphene.Node.to_global_id("Product", 1)

    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            "fields": {"removeValues": [invalid_value_id]},
        }
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    errors = data["results"][0]["errors"]
    assert data["count"] == 0
    assert errors
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.INVALID.name
    assert errors[0]["path"] == "removeValues.0"


def test_attribute_bulk_update_add_value_missing_name(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    attr_external_ref = color_attribute.external_reference
    attributes = [
        {
            "externalReference": attr_external_ref,
            "fields": {
                "addValues": [
                    {
                        "externalReference": "new_ext_reference",
                    },
                    {
                        "name": "",
                    },
                ]
            },
        }
    ]
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["attributeBulkUpdate"]
    errors = data["results"][0]["errors"]
    assert data["count"] == 0
    assert errors
    assert len(errors) == 2
    assert errors[0]["path"] == "addValues.0.name"
    assert errors[0]["code"] == AttributeBulkUpdateErrorCode.REQUIRED.name
    assert errors[1]["path"] == "addValues.1.name"
    assert errors[1]["code"] == AttributeBulkUpdateErrorCode.REQUIRED.name


def test_attribute_bulk_update_reference_types(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_page_types_and_attributes,
    product_type_product_single_reference_attribute,
    product_type_variant_single_reference_attribute,
    product_type_page_reference_attribute,
    page_type_page_reference_attribute,
    page_type_list,
    product_type,
):
    # given
    product_type_variant_single_reference_attribute.reference_product_types.add(
        product_type
    )
    product_type_page_reference_attribute.reference_page_types.add(page_type_list[0])
    page_type_page_reference_attribute.reference_page_types.add(page_type_list[1])

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)
    page_type_ids = [
        graphene.Node.to_global_id("PageType", page_type.id)
        for page_type in page_type_list
    ]
    attributes = [
        # set reference types
        {
            "id": graphene.Node.to_global_id(
                "Attribute", product_type_product_single_reference_attribute.id
            ),
            "fields": {"referenceTypes": [product_type_id]},
        },
        # clear product reference types
        {
            "id": graphene.Node.to_global_id(
                "Attribute", product_type_variant_single_reference_attribute.id
            ),
            "fields": {"referenceTypes": []},
        },
        # change reference types
        {
            "id": graphene.Node.to_global_id(
                "Attribute", product_type_page_reference_attribute.id
            ),
            "fields": {"referenceTypes": page_type_ids[1:]},
        },
        # clear page reference types
        {
            "id": graphene.Node.to_global_id(
                "Attribute", page_type_page_reference_attribute.id
            ),
            "fields": {"referenceTypes": []},
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes,
        permission_manage_page_types_and_attributes,
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert len(attributes) == 4
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert not data["results"][2]["errors"]
    assert not data["results"][3]["errors"]
    assert data["count"] == 4
    assert len(data["results"][0]["attribute"]["referenceTypes"]) == 1
    assert len(data["results"][1]["attribute"]["referenceTypes"]) == 0
    assert (
        len(data["results"][2]["attribute"]["referenceTypes"])
        == len(page_type_list) - 1
    )
    assert len(data["results"][3]["attribute"]["referenceTypes"]) == 0

    assert data["results"][0]["attribute"]["referenceTypes"][0]["id"] == product_type_id
    assert {
        ref_type["id"] for ref_type in data["results"][2]["attribute"]["referenceTypes"]
    } == set(page_type_ids[1:])

    product_type_product_single_reference_attribute.refresh_from_db()
    assert (
        product_type_product_single_reference_attribute.reference_product_types.count()
        == 1
    )
    product_type_variant_single_reference_attribute.refresh_from_db()
    assert (
        product_type_variant_single_reference_attribute.reference_product_types.count()
        == 0
    )
    product_type_page_reference_attribute.refresh_from_db()
    assert product_type_page_reference_attribute.reference_page_types.count() == len(
        page_type_ids[1:]
    )
    page_type_page_reference_attribute.refresh_from_db()
    assert page_type_page_reference_attribute.reference_page_types.count() == 0


@patch("saleor.graphql.attribute.mutations.mixins.REFERENCE_TYPES_LIMIT", 1)
def test_attribute_bulk_update_invalid_reference_types(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_page_types_and_attributes,
    product_type_variant_single_reference_attribute,
    product_type_collection_single_reference_attribute,
    product_type_page_reference_attribute,
    color_attribute,
    page_type_page_reference_attribute,
    page_type_list,
    product_type,
):
    # given
    product_type_variant_single_reference_attribute.reference_product_types.add(
        product_type
    )
    product_type_page_reference_attribute.reference_page_types.add(page_type_list[0])
    page_type_page_reference_attribute.reference_page_types.add(page_type_list[1])

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)
    page_type_ids = [
        graphene.Node.to_global_id("PageType", page_type.id)
        for page_type in page_type_list
    ]
    input_attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
            # invalid input type
            "fields": {"referenceTypes": [product_type_id]},
        },
        {
            "id": graphene.Node.to_global_id(
                "Attribute", product_type_collection_single_reference_attribute.id
            ),
            # invalid entity type of attribute
            "fields": {"referenceTypes": [product_type_id]},
        },
        {
            "id": graphene.Node.to_global_id(
                "Attribute", product_type_variant_single_reference_attribute.id
            ),
            # should be a list of product types
            "fields": {"referenceTypes": [page_type_ids[1]]},
        },
        {
            "id": graphene.Node.to_global_id(
                "Attribute", product_type_page_reference_attribute.id
            ),
            # # limit exceeded
            "fields": {"referenceTypes": page_type_ids[1:]},
        },
        {
            "id": graphene.Node.to_global_id(
                "Attribute", page_type_page_reference_attribute.id
            ),
            # should be a list of page types
            "fields": {"referenceTypes": [product_type_id]},
        },
    ]

    # when
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes,
        permission_manage_page_types_and_attributes,
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_BULK_UPDATE_MUTATION,
        {"attributes": input_attributes},
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeBulkUpdate"]

    # then
    assert data["results"][0]["errors"]
    assert data["results"][1]["errors"]
    assert data["results"][2]["errors"]
    assert data["results"][3]["errors"]
    assert data["results"][4]["errors"]
    assert data["count"] == 0
    for result in data["results"]:
        assert len(result["errors"]) == 1
        assert result["errors"][0]["code"] == AttributeBulkUpdateErrorCode.INVALID.name
        assert result["errors"][0]["path"] == "referenceTypes"
