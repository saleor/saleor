from unittest import mock

import graphene

from ....tests.utils import get_graphql_content

UPDATE_METADATA = """
    mutation UpdateMetadata($id: ID!, $input: [MetadataInput!]!) {
        updateMetadata(id: $id, input: $input) {
            errors {
                code
                field
                message
            }
            item {
                metadata {
                    key
                    value
                }
            }
        }
    }
"""


def test_handling_invalid_graphene_type(api_client):
    # given

    # This ID is invalid and represents "Che3kout:42953eb4-fa86-4e02-943f-403f47fbebe7"
    # with a typo in the type name.
    checkout_id = "Q2hlM2tvdXQ6NDI5NTNlYjQtZmE4Ni00ZTAyLTk0M2YtNDAzZjQ3ZmJlYmU3"

    # when
    response = api_client.post_graphql(
        UPDATE_METADATA, {"id": checkout_id, "input": [{"key": "foo", "value": "bar"}]}
    )
    response = get_graphql_content(response)

    # then
    errors = response["data"]["updateMetadata"]["errors"]
    assert errors
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == "GRAPHQL_ERROR"
    assert errors[0]["message"] == "Invalid type: Che3kout"


@mock.patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_call_extra_action_only_when_metadata_change(
    mocked_product_metadata_webhook,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    product.metadata = {"foo": "bar"}
    product.save(update_fields=["metadata"])

    # when
    staff_api_client.post_graphql(
        UPDATE_METADATA,
        {"id": product_id, "input": [{"key": "foo", "value": "bar"}]},
        permissions=[permission_manage_products],
    )

    # then
    mocked_product_metadata_webhook.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_call_extra_action_when_metadata_changed(
    mocked_product_metadata_webhook,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    product.metadata = {}
    product.save(update_fields=["metadata"])

    # when
    staff_api_client.post_graphql(
        UPDATE_METADATA,
        {"id": product_id, "input": [{"key": "foo", "value": "bar"}]},
        permissions=[permission_manage_products],
    )

    # then
    mocked_product_metadata_webhook.assert_called_once()
