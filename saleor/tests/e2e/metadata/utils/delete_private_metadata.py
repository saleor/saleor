from ...utils import get_graphql_content

PRIVATE_METADATA_DELETE_MUTATION = """
mutation DeletePrivateMetadata(
    $id: ID!,
    $keys:[String!]!,
   ) {
  deletePrivateMetadata(id: $id, keys: $keys) {
    errors {
        message
        field
    }
    item {
      privateMetadata {
        key
        value
      }
    }
  }
}
"""


def delete_private_metadata(
    staff_api_client,
    id,
    keys,
):
    variables = {"id": id, "keys": keys}
    response = staff_api_client.post_graphql(
        PRIVATE_METADATA_DELETE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    assert content["data"]["deletePrivateMetadata"]["errors"] == []

    data = content["data"]["deletePrivateMetadata"]["item"]["privateMetadata"]
    assert data is not None
    return data
