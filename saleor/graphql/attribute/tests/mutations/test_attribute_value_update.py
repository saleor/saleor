import json
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....attribute.error_codes import AttributeErrorCode
from .....attribute.tests.model_helpers import (
    get_product_attribute_values,
    get_product_attributes,
)
from .....attribute.utils import associate_attribute_values_to_instance
from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

UPDATE_ATTRIBUTE_VALUE_MUTATION = """
mutation AttributeValueUpdate($id: ID!, $input: AttributeValueUpdateInput!) {
    attributeValueUpdate(id: $id, input: $input) {
        errors {
            field
            message
            code
        }
        attributeValue {
            name
            slug
            value
            externalReference
            file {
                url
                contentType
            }
        }
        attribute {
            choices(first: 10) {
                edges {
                    node {
                        name
                    }
                }
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
    external_reference = "test-ext-ref"
    variables = {
        "id": node_id,
        "input": {
            "name": name,
            "externalReference": external_reference,
        },
    }

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
    assert (
        data["attributeValue"]["externalReference"]
        == external_reference
        == value.external_reference
    )
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


def test_update_attribute_value_update_search_index_dirty_in_product(
    staff_api_client,
    product,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION

    first_attribute = get_product_attributes(product).first()
    value = get_product_attribute_values(product, first_attribute).first()

    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"input": {"name": name}, "id": node_id}

    # when
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    product.refresh_from_db(fields=["search_index_dirty"])

    # then
    assert product.search_index_dirty is True


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_update_attribute_value_trigger_webhooks(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    value = pink_attribute_value
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"input": {"name": name}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        UPDATE_ATTRIBUTE_VALUE_MUTATION,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    attribute = value.attribute
    meta = generate_meta(
        requestor_data=generate_requestor(
            SimpleLazyObject(lambda: staff_api_client.user)
        )
    )

    attribute_updated_call = mock.call(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Attribute", attribute.id),
                "name": attribute.name,
                "slug": attribute.slug,
                "meta": meta,
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.ATTRIBUTE_UPDATED,
        [any_webhook],
        attribute,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )

    attribute_value_created_call = mock.call(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("AttributeValue", value.id),
                "name": value.name,
                "slug": value.slug,
                "value": value.value,
                "meta": meta,
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.ATTRIBUTE_VALUE_UPDATED,
        [any_webhook],
        value,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )

    # then
    assert not data["errors"]
    assert data["attributeValue"]["name"] == name == value.name
    assert len(mocked_webhook_trigger.call_args_list) == 2
    assert attribute_updated_call in mocked_webhook_trigger.call_args_list
    assert attribute_value_created_call in mocked_webhook_trigger.call_args_list


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
    variables = {"input": {"name": pink_attribute_value.name}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    assert not data["errors"]
    assert data["attributeValue"]["slug"] == "pink-2"


def test_update_attribute_value_the_same_name_as_different_attribute_value(
    staff_api_client,
    size_attribute,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION

    value = size_attribute.values.first()
    based_value = color_attribute.values.first()

    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = based_value.name
    variables = {"input": {"name": name}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == name == value.name
    assert data["attributeValue"]["slug"] == based_value.slug
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


def test_update_attribute_value_product_search_document_updated(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
    product,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    attribute = pink_attribute_value.attribute
    value = pink_attribute_value

    product_type = product.product_type
    product_type.product_attributes.add(attribute)

    associate_attribute_values_to_instance(product, {attribute.pk: [value]})

    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"input": {"name": name}, "id": node_id}

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
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


def test_update_attribute_value_product_search_document_updated_variant_attribute(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
    variant,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    attribute = pink_attribute_value.attribute
    value = pink_attribute_value

    product = variant.product
    product_type = product.product_type
    product_type.variant_attributes.add(attribute)

    associate_attribute_values_to_instance(variant, {attribute.pk: [value]})

    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"input": {"name": name}, "id": node_id}

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
    assert name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


def test_update_swatch_attribute_value(
    staff_api_client,
    swatch_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = swatch_attribute.values.filter(value__isnull=False).first()
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "New name"
    variables = {"input": {"name": name, "value": "", "fileUrl": ""}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == value.name
    assert data["attributeValue"]["slug"] == value.slug
    assert data["attributeValue"]["value"] == ""
    assert data["attributeValue"]["file"] is None
    assert value.name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


@pytest.mark.parametrize("additional_field", [{"value": ""}, {"value": None}, {}])
def test_update_swatch_attribute_value_clear_value(
    additional_field,
    staff_api_client,
    swatch_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = swatch_attribute.values.filter(value__isnull=False).first()
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    file_url = "https://example.com/test_media/test_file.jpeg"
    variables = {"input": {"fileUrl": file_url, **additional_field}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == value.name
    assert data["attributeValue"]["slug"] == value.slug
    assert data["attributeValue"]["value"] == ""
    assert data["attributeValue"]["file"]["url"] == file_url
    assert value.name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


@pytest.mark.parametrize("additional_field", [{"fileUrl": ""}, {"fileUrl": None}, {}])
def test_update_swatch_attribute_value_clear_file_value(
    additional_field,
    staff_api_client,
    swatch_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = swatch_attribute.values.filter(file_url__isnull=False).first()
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    input_value = "#ffffff"
    variables = {"input": {"value": input_value, **additional_field}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == value.name
    assert data["attributeValue"]["slug"] == value.slug
    assert data["attributeValue"]["value"] == input_value
    assert data["attributeValue"]["file"] is None
    assert value.name in [
        value["node"]["name"] for value in data["attribute"]["choices"]["edges"]
    ]


@pytest.mark.parametrize(
    ("field", "input_value"),
    [
        ("fileUrl", "https://example.com/test_media/test_file.jpeg"),
        ("contentType", "jpeg"),
    ],
)
def test_update_attribute_value_invalid_input_data(
    field,
    input_value,
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = pink_attribute_value
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    name = "Crimson name"
    variables = {"input": {"name": name, field: input_value}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert not data["attributeValue"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == AttributeErrorCode.INVALID.name
    assert data["errors"][0]["field"] == field


def test_update_attribute_value_swatch_attr_value(
    staff_api_client,
    swatch_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_MUTATION
    value = swatch_attribute.values.first()
    node_id = graphene.Node.to_global_id("AttributeValue", value.id)
    new_value = "#FFFFF"
    variables = {"input": {"value": new_value}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeValueUpdate"]
    value.refresh_from_db()
    assert data["attributeValue"]["name"] == value.name
    assert data["attributeValue"]["slug"] == value.slug
    assert data["attributeValue"]["value"] == new_value


UPDATE_ATTRIBUTE_VALUE_BY_EXTERNAL_REFERENCE_MUTATION = """
mutation AttributeValueUpdate(
        $id: ID, $externalReference: String, $input: AttributeValueUpdateInput!
) {
    attributeValueUpdate(
        id: $id, externalReference: $externalReference, input: $input
    ) {
        errors {
            field
            message
            code
        }
        attributeValue {
            name
            id
            externalReference
        }
    }
}
"""


def test_update_attribute_value_by_external_reference(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_BY_EXTERNAL_REFERENCE_MUTATION
    value = pink_attribute_value
    new_name = "updated name"
    ext_ref = "test-ext-ref"
    value.external_reference = ext_ref
    value.save(update_fields=["external_reference"])

    variables = {
        "input": {"name": new_name},
        "externalReference": ext_ref,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    value.refresh_from_db()
    data = content["data"]["attributeValueUpdate"]
    assert not data["errors"]
    assert data["attributeValue"]["name"] == new_name == value.name
    assert data["attributeValue"]["id"] == graphene.Node.to_global_id(
        "AttributeValue", value.id
    )
    assert data["attributeValue"]["externalReference"] == ext_ref


def test_update_attribute_value_by_both_id_and_external_reference(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_BY_EXTERNAL_REFERENCE_MUTATION
    variables = {"input": {}, "externalReference": "whatever", "id": "whatever"}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["attributeValueUpdate"]
    assert not data["attributeValue"]
    assert (
        data["errors"][0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_update_attribute_value_by_external_reference_not_existing(
    staff_api_client,
    pink_attribute_value,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_BY_EXTERNAL_REFERENCE_MUTATION
    ext_ref = "non-existing-ext-ref"
    variables = {
        "input": {},
        "externalReference": ext_ref,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["attributeValueUpdate"]
    assert not data["attributeValue"]
    assert data["errors"][0]["message"] == f"Couldn't resolve to a node: {ext_ref}"
    assert data["errors"][0]["field"] == "externalReference"


def test_update_attribute_value_with_non_unique_external_reference(
    staff_api_client,
    color_attribute,
    numeric_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    query = UPDATE_ATTRIBUTE_VALUE_BY_EXTERNAL_REFERENCE_MUTATION
    value_1 = color_attribute.values.first()
    ext_ref = "test-ext-ref"
    value_1.external_reference = ext_ref
    value_1.save(update_fields=["external_reference"])
    value_2 = numeric_attribute.values.first()
    value_2_id = graphene.Node.to_global_id("AttributeValue", value_2.id)

    variables = {
        "input": {"externalReference": ext_ref},
        "id": value_2_id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["attributeValueUpdate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == AttributeErrorCode.UNIQUE.name
    assert (
        error["message"]
        == "Attribute value with this External reference already exists."
    )
