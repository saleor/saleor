import json
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

ATTRIBUTE_DELETE_MUTATION = """
    mutation deleteAttribute($id: ID!) {
        attributeDelete(id: $id) {
            errors {
                field
                message
            }
            attribute {
                id
            }
        }
    }
"""


def test_delete_attribute(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
    product_type,
):
    # given
    attribute = color_attribute
    query = ATTRIBUTE_DELETE_MUTATION
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeDelete"]
    assert data["attribute"]["id"] == variables["id"]
    with pytest.raises(attribute._meta.model.DoesNotExist):
        attribute.refresh_from_db()


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_attribute_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
    product_type,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    node_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    variables = {"id": node_id}

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_product_types_and_attributes],
    )
    content = get_graphql_content(response)
    data = content["data"]["attributeDelete"]

    # then
    assert not data["errors"]
    assert data["attribute"]["id"] == variables["id"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
                "name": color_attribute.name,
                "slug": color_attribute.slug,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.ATTRIBUTE_DELETED,
        [any_webhook],
        color_attribute,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )


def test_delete_file_attribute(
    staff_api_client,
    file_attribute,
    permission_manage_product_types_and_attributes,
    product_type,
):
    # given
    attribute = file_attribute
    query = ATTRIBUTE_DELETE_MUTATION
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeDelete"]
    assert data["attribute"]["id"] == variables["id"]
    with pytest.raises(attribute._meta.model.DoesNotExist):
        attribute.refresh_from_db()


ATTRIBUTE_DELETE_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation deleteAttribute($id: ID, $externalReference: String) {
        attributeDelete(id: $id, externalReference: $externalReference) {
            attribute {
                id
                externalReference
            }
            errors {
                field
                message
            }
        }
    }
"""


def test_delete_attribute_by_external_reference(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
):
    # given
    attribute = color_attribute
    query = ATTRIBUTE_DELETE_BY_EXTERNAL_REFERENCE_MUTATION
    ext_ref = "test-ext-ref"
    attribute.external_reference = ext_ref
    attribute.save(update_fields=["external_reference"])
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["attributeDelete"]
    with pytest.raises(attribute._meta.model.DoesNotExist):
        attribute.refresh_from_db()
    assert data["attribute"]["externalReference"] == ext_ref
    assert (
        graphene.Node.to_global_id("Attribute", attribute.id) == data["attribute"]["id"]
    )


def test_delete_attribute_by_both_id_and_external_reference(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    query = ATTRIBUTE_DELETE_BY_EXTERNAL_REFERENCE_MUTATION
    variables = {"externalReference": "whatever", "id": "whatever"}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["attributeDelete"]["errors"]
    assert (
        errors[0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_delete_attribute_by_external_reference_not_existing(
    staff_api_client, permission_manage_product_types_and_attributes
):
    # given
    query = ATTRIBUTE_DELETE_BY_EXTERNAL_REFERENCE_MUTATION
    ext_ref = "non-existing-ext-ref"
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["attributeDelete"]["errors"]
    assert errors[0]["message"] == f"Couldn't resolve to a node: {ext_ref}"
