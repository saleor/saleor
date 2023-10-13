from ...utils import get_graphql_content

PRIVATE_METADATA_UPDATE_MUTATION = """
mutation UpdatePrivateMetadata(
    $id: ID!,
    $input:[MetadataInput!]!,
   ) {
  updatePrivateMetadata(id: $id, input: $input) {
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


def update_private_metadata(
    staff_api_client,
    id,
    input,
):
    variables = {"id": id, "input": input}
    response = staff_api_client.post_graphql(
        PRIVATE_METADATA_UPDATE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    assert content["data"]["updatePrivateMetadata"]["errors"] == []

    data = content["data"]["updatePrivateMetadata"]["item"]["privateMetadata"]
    assert data is not None
    return data
