from unittest.mock import patch

import graphene

from .....core.error_codes import MetadataErrorCode
from ....tests.utils import get_graphql_content

LIMIT_PATCH = "saleor.graphql.meta.mutations.utils.METADATA_LIST_INPUT_LIMIT"

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


@patch(LIMIT_PATCH, 1)
def test_update_metadata_rejects_oversized_input(api_client, checkout):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {
        "id": checkout_id,
        "input": [
            {"key": "key0", "value": "value0"},
            {"key": "key1", "value": "value1"},
        ],
    }

    # when
    response = api_client.post_graphql(UPDATE_METADATA_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["updateMetadata"]["errors"][0]
    assert error["field"] == "input"
    assert error["code"] == MetadataErrorCode.INVALID.name
    assert "1" in error["message"]


@patch(LIMIT_PATCH, 1)
def test_delete_metadata_rejects_oversized_keys(api_client, checkout):
    # given
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {
        "id": checkout_id,
        "keys": ["key0", "key1"],
    }

    # when
    response = api_client.post_graphql(DELETE_METADATA_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    error = content["data"]["deleteMetadata"]["errors"][0]
    assert error["field"] == "keys"
    assert error["code"] == MetadataErrorCode.INVALID.name
    assert "1" in error["message"]
