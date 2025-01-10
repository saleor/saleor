from ...utils import get_graphql_content

METADATA_DELETE_MUTATION = """
mutation DeleteMetadata(
    $id: ID!,
    $keys:[String!]!,
   ) {
  deleteMetadata(id: $id, keys: $keys) {
    errors {
        message
        field
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


def delete_metadata(
    staff_api_client,
    id,
    keys,
):
    variables = {"id": id, "keys": keys}
    response = staff_api_client.post_graphql(
        METADATA_DELETE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    assert content["data"]["deleteMetadata"]["errors"] == []

    metadata = content["data"]["deleteMetadata"]["item"]["metadata"]
    assert metadata is not None
    return metadata
