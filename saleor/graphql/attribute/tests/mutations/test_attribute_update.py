import json
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....attribute.error_codes import AttributeErrorCode
from .....attribute.models import Attribute
from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....core.enums import MeasurementUnitsEnum
from ....tests.utils import get_graphql_content

UPDATE_ATTRIBUTE_MUTATION = """
    mutation updateAttribute(
        $id: ID!, $input: AttributeUpdateInput!
    ) {
    attributeUpdate(
            id: $id,
            input: $input) {
        errors {
            field
            message
            code
        }
        attribute {
            name
            slug
            unit
            choices(first: 10) {
                edges {
                    node {
                        name
                        slug
                    }
                }
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


def test_update_attribute_name(
    staff_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = color_attribute
    name = "Wings name"
    slug = attribute.slug
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {
        "input": {"name": name, "addValues": [], "removeValues": []},
        "id": node_id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    assert data["attribute"]["name"] == name == attribute.name
    assert data["attribute"]["slug"] == slug == attribute.slug
    assert data["attribute"]["productTypes"]["edges"] == []


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_update_attribute_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    new_name = "Wings name"
    node_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    variables = {
        "input": {"name": new_name, "addValues": [], "removeValues": []},
        "id": node_id,
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_ATTRIBUTE_MUTATION,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)
    color_attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]

    # then
    assert not data["errors"]
    assert data["attribute"]["name"] == new_name
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
                "name": new_name,
                "slug": color_attribute.slug,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.ATTRIBUTE_UPDATED,
        [any_webhook],
        color_attribute,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_update_attribute_remove_and_add_values(
    staff_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = color_attribute
    name = "Wings name"
    attribute_value_name = "Red Color"
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    attribute_value_id = attribute.values.first().id
    value_id = graphene.Node.to_global_id("AttributeValue", attribute_value_id)
    variables = {
        "id": node_id,
        "input": {
            "name": name,
            "addValues": [{"name": attribute_value_name}],
            "removeValues": [value_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    assert not data["errors"]
    assert data["attribute"]["name"] == name == attribute.name
    assert not attribute.values.filter(pk=attribute_value_id).exists()
    assert attribute.values.filter(name=attribute_value_name).exists()


def test_update_empty_attribute_and_add_values(
    staff_api_client,
    color_attribute_without_values,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = color_attribute_without_values
    name = "Wings name"
    attribute_value_name = "Yellow Color"
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {
        "id": node_id,
        "input": {
            "name": name,
            "addValues": [{"name": attribute_value_name}],
            "removeValues": [],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    get_graphql_content(response)
    attribute.refresh_from_db()
    assert attribute.values.count() == 1
    assert attribute.values.filter(name=attribute_value_name).exists()


def test_update_empty_attribute_and_add_values_name_not_given(
    staff_api_client,
    color_attribute_without_values,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = color_attribute_without_values
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {
        "id": node_id,
        "input": {
            "addValues": [{"value": "abc"}],
            "removeValues": [],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == AttributeErrorCode.REQUIRED.name
    assert data["errors"][0]["field"] == "addValues"


def test_update_attribute_with_file_input_type(
    staff_api_client,
    file_attribute_with_file_input_type_without_values,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = file_attribute_with_file_input_type_without_values
    name = "Wings name"
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)

    variables = {
        "id": node_id,
        "input": {"name": name, "addValues": [], "removeValues": []},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    assert not data["errors"]
    assert data["attribute"]["name"] == name == attribute.name


def test_update_attribute_with_numeric_input_type(
    staff_api_client,
    numeric_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = numeric_attribute
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)

    name = "Weight"
    slug = "weight"
    unit = MeasurementUnitsEnum.G.name
    variables = {
        "id": node_id,
        "input": {"name": name, "slug": slug, "unit": unit},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    assert not data["errors"]
    assert data["attribute"]["name"] == name
    assert data["attribute"]["slug"] == slug
    assert data["attribute"]["unit"] == unit


def test_update_attribute_with_file_input_type_and_values(
    staff_api_client,
    file_attribute_with_file_input_type_without_values,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = file_attribute_with_file_input_type_without_values
    name = "Wings name"
    attribute_value_name = "Test file"
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)

    variables = {
        "id": node_id,
        "input": {
            "name": name,
            "addValues": [{"name": attribute_value_name}],
            "removeValues": [],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    errors = data["errors"]
    assert not data["attribute"]
    assert len(errors) == 1
    assert errors[0]["field"] == "addValues"
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name


def test_update_attribute_with_file_input_type_invalid_settings(
    staff_api_client,
    file_attribute_with_file_input_type_without_values,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = file_attribute_with_file_input_type_without_values
    name = "Wings name"
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)

    variables = {
        "id": node_id,
        "input": {
            "name": name,
            "addValues": [],
            "removeValues": [],
            "filterableInStorefront": True,
            "filterableInDashboard": True,
            "availableInGrid": True,
            "storefrontSearchPosition": 3,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    errors = data["errors"]
    assert not data["attribute"]
    assert len(errors) == 4
    assert {error["field"] for error in errors} == {
        "filterableInStorefront",
        "filterableInDashboard",
        "availableInGrid",
        "storefrontSearchPosition",
    }
    assert {error["code"] for error in errors} == {AttributeErrorCode.INVALID.name}


def test_update_attribute_provide_existing_value_name(
    staff_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = color_attribute
    value = color_attribute.values.first()
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {
        "input": {"addValues": [{"name": value.name}], "removeValues": []},
        "id": node_id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    assert len(data["errors"]) == 1


UPDATE_ATTRIBUTE_SLUG_MUTATION = """
    mutation updateAttribute(
    $id: ID!, $slug: String) {
    attributeUpdate(
            id: $id,
            input: {
                slug: $slug}) {
        errors {
            field
            message
            code
        }
        attribute {
            name
            slug
        }
    }
}
"""


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
def test_update_attribute_slug(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
    input_slug,
    expected_slug,
    error_message,
):
    # given
    query = UPDATE_ATTRIBUTE_SLUG_MUTATION

    attribute = color_attribute
    name = attribute.name
    old_slug = attribute.slug

    assert input_slug != old_slug

    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"slug": input_slug, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    errors = data["errors"]
    if not error_message:
        assert data["attribute"]["name"] == name == attribute.name
        assert data["attribute"]["slug"] == input_slug == attribute.slug
    else:
        assert errors
        assert data["attribute"] is None
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == AttributeErrorCode.REQUIRED.name


def test_update_attribute_slug_exists(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_SLUG_MUTATION

    second_attribute = Attribute.objects.get(pk=color_attribute.pk)
    second_attribute.pk = None
    second_attribute.slug = "second-attribute"
    second_attribute.save()

    attribute = color_attribute
    old_slug = attribute.slug
    new_slug = second_attribute.slug

    assert new_slug != old_slug

    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"slug": new_slug, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    errors = data["errors"]

    assert errors
    assert data["attribute"] is None
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == AttributeErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", None, None),
        ("", "", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", "This field cannot be blank.", "name"),
        (None, None, None, "Slug value cannot be blank.", "slug"),
    ],
)
def test_update_attribute_slug_and_name(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
    input_slug,
    expected_slug,
    input_name,
    error_message,
    error_field,
):
    # given
    query = """
        mutation updateAttribute(
        $id: ID!, $slug: String, $name: String) {
        attributeUpdate(
                id: $id,
                input: {
                    slug: $slug, name: $name}) {
            errors {
                field
                message
                code
            }
            attribute {
                name
                slug
            }
        }
    }
    """

    attribute = color_attribute
    old_name = attribute.name
    old_slug = attribute.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"slug": input_slug, "name": input_name, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    attribute.refresh_from_db()
    data = content["data"]["attributeUpdate"]
    errors = data["errors"]
    if not error_message:
        assert data["attribute"]["name"] == input_name == attribute.name
        assert data["attribute"]["slug"] == input_slug == attribute.slug
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == AttributeErrorCode.REQUIRED.name


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
def test_update_attribute_and_add_attribute_values_errors(
    staff_api_client,
    name_1,
    name_2,
    error_msg,
    error_code,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = color_attribute
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {
        "id": node_id,
        "input": {
            "name": "Example name",
            "removeValues": [],
            "addValues": [{"name": name_1}, {"name": name_2}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["attributeUpdate"]["errors"]
    assert errors
    assert errors[0]["field"] == "addValues"
    assert errors[0]["message"] == error_msg
    assert errors[0]["code"] == error_code.name


def test_update_attribute_and_remove_others_attribute_value(
    staff_api_client,
    color_attribute,
    size_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_MUTATION
    attribute = color_attribute
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    size_attribute = size_attribute.values.first()
    attr_id = graphene.Node.to_global_id("AttributeValue", size_attribute.pk)
    variables = {
        "id": node_id,
        "input": {"name": "Example name", "addValues": [], "removeValues": [attr_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["attributeUpdate"]["errors"]
    assert errors
    assert errors[0]["field"] == "removeValues"
    assert errors[0]["code"] == AttributeErrorCode.INVALID.name
