from ...utils import get_graphql_content

METADATA_UPDATE_MUTATION = """
mutation UpdateMetadata(
    $id: ID!,
    $input:[MetadataInput!]!,
   ) {
  updateMetadata(id: $id, input: $input) {
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


def update_metadata(
    staff_api_client,
    id,
    input,
):
    variables = {"id": id, "input": input}
    response = staff_api_client.post_graphql(
        METADATA_UPDATE_MUTATION,
        variables,
    )

    content = get_graphql_content(response)

    assert content["data"]["updateMetadata"]["errors"] == []

    metadata = content["data"]["updateMetadata"]["item"]["metadata"]
    assert metadata is not None
    return metadata
