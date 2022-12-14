import json
from unittest import mock

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....attribute.error_codes import AttributeErrorCode
from .....attribute.models import AttributeValue
from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content
from ...mutations.validators import validate_value_is_unique


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
        $attributeId: ID!, $name: String!, $externalReference: String,
        $value: String, $fileUrl: String, $contentType: String
    ) {
    attributeValueCreate(
        attribute: $attributeId, input: {
            name: $name, value: $value, fileUrl: $fileUrl,
            contentType: $contentType, externalReference: $externalReference
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
            externalReference
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
    external_reference = "test-ext-ref"
    variables = {
        "name": name,
        "attributeId": attribute_id,
        "externalReference": external_reference,
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
    assert attr_data["externalReference"] == external_reference
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_attribute_value_trigger_webhooks(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    color_attribute,
    permission_manage_products,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    name = "test name"
    variables = {"name": name, "attributeId": attribute_id}

    # when
    response = staff_api_client.post_graphql(
        CREATE_ATTRIBUTE_VALUE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueCreate"]
    attribute_value = AttributeValue.objects.get(attribute=color_attribute, name=name)
    meta = generate_meta(
        requestor_data=generate_requestor(
            SimpleLazyObject(lambda: staff_api_client.user)
        )
    )

    attribute_updated_call = mock.call(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
                "name": color_attribute.name,
                "slug": color_attribute.slug,
                "meta": meta,
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.ATTRIBUTE_UPDATED,
        [any_webhook],
        color_attribute,
        SimpleLazyObject(lambda: staff_api_client.user),
    )

    attribute_value_created_call = mock.call(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("AttributeValue", attribute_value.id),
                "name": attribute_value.name,
                "slug": attribute_value.slug,
                "value": attribute_value.value,
                "meta": meta,
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.ATTRIBUTE_VALUE_CREATED,
        [any_webhook],
        attribute_value,
        SimpleLazyObject(lambda: staff_api_client.user),
    )

    # then
    assert not data["errors"]
    assert data["attributeValue"]
    assert len(mocked_webhook_trigger.call_args_list) == 2
    assert attribute_updated_call in mocked_webhook_trigger.call_args_list
    assert attribute_value_created_call in mocked_webhook_trigger.call_args_list


def test_create_attribute_value_with_the_same_name_as_different_attribute_value(
    staff_api_client,
    attribute_without_values,
    color_attribute,
    permission_manage_products,
):
    """Ensure the attribute value with the same slug as value of different attribute
    can be created."""
    # given
    attribute = attribute_without_values
    query = CREATE_ATTRIBUTE_VALUE_MUTATION
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)

    existing_value = color_attribute.values.first()

    name = existing_value.name
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
    assert attr_data["slug"] == existing_value.slug
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


def test_create_attribute_value_with_non_unique_external_reference(
    staff_api_client, color_attribute, permission_manage_products
):
    # given
    query = CREATE_ATTRIBUTE_VALUE_MUTATION

    ext_ref = "test-ext-ref"
    value = color_attribute.values.first()
    value.external_reference = ext_ref
    value.save(update_fields=["external_reference"])
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    variables = {
        "name": "some value name",
        "attributeId": attribute_id,
        "externalReference": ext_ref,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["attributeValueCreate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == AttributeErrorCode.UNIQUE.name
    assert (
        error["message"]
        == "Attribute value with this External reference already exists."
    )
