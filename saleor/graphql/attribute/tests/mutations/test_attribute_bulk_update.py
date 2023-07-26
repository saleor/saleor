from unittest.mock import patch

import graphene

from .....attribute.error_codes import AttributeBulkCreateErrorCode
from .....attribute.models import Attribute
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


def test_attribute_bulk_update_with_invalid_type_id(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    attributes = [
        {"id": graphene.Node.to_global_id("Page", 1), "fields": {"name": "ExampleName"}}
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
    assert errors[0]["code"] == AttributeBulkCreateErrorCode.INVALID.name
    assert errors[0]["message"] == "Must receive a Attribute id."


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
    assert errors[0]["code"] == AttributeBulkCreateErrorCode.INVALID.name
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
    assert errors[0]["code"] == AttributeBulkCreateErrorCode.INVALID.name
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
    assert errors[0]["code"] == AttributeBulkCreateErrorCode.INVALID.name
    assert (
        errors[0]["message"]
        == f"Value {invalid_value_global_id} does not belong to this attribute."
    )
