import graphene

from .....core.error_codes import MetadataErrorCode
from ....tests.utils import get_graphql_content

UPDATE_METADATA_MUTATION = """
mutation UpdatePublicMetadata($id: ID!, $input: [MetadataInput!]!) {
    updateMetadata(id: $id, input: $input) {
        errors {
            field
            code
            message
        }
        item {
            ... on Checkout {
                id
            }
        }
    }
}
"""

DELETE_METADATA_MUTATION = """
mutation DeletePublicMetadata($id: ID!, $keys: [String!]!) {
    deleteMetadata(id: $id, keys: $keys) {
        errors {
            field
            code
            message
        }
        item {
            ... on Checkout {
                id
            }
        }
    }
}
"""


def test_update_metadata_rejects_oversized_input(api_client, checkout):
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    checkout.metadata_storage.store_value_in_metadata({"existing": "value"})
    checkout.metadata_storage.save(update_fields=["metadata"])
    input_items = [{"key": f"key-{index}", "value": "value"} for index in range(101)]

    response = api_client.post_graphql(
        UPDATE_METADATA_MUTATION,
        {"id": checkout_id, "input": input_items},
    )

    content = get_graphql_content(response)
    errors = content["data"]["updateMetadata"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == MetadataErrorCode.INVALID.name
    assert "100" in errors[0]["message"]
    checkout.metadata_storage.refresh_from_db()
    assert checkout.metadata_storage.metadata == {"existing": "value"}


def test_delete_metadata_rejects_oversized_keys(api_client, checkout):
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    checkout.metadata_storage.store_value_in_metadata({"existing": "value"})
    checkout.metadata_storage.save(update_fields=["metadata"])
    keys = [f"key-{index}" for index in range(101)]

    response = api_client.post_graphql(
        DELETE_METADATA_MUTATION,
        {"id": checkout_id, "keys": keys},
    )

    content = get_graphql_content(response)
    errors = content["data"]["deleteMetadata"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "keys"
    assert errors[0]["code"] == MetadataErrorCode.INVALID.name
    assert "100" in errors[0]["message"]
    checkout.metadata_storage.refresh_from_db()
    assert checkout.metadata_storage.metadata == {"existing": "value"}
