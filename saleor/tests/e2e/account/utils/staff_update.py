from ...utils import get_graphql_content

STAFF_UPDATE_MUTATION = """
mutation StaffUpdate($id: ID!, $input: StaffUpdateInput!){
  staffUpdate(id: $id,
    input: $input) {
    user {
      id
      metadata {
        key
        value
      }
      privateMetadata {
        key
        value
      }
    }
    errors {
      field
      message
    }
  }
}
"""


def update_staff(
    staff_api_client,
    staff_id,
    input_data,
):
    variables = {
        "id": staff_id,
        "input": input_data,
    }

    response = staff_api_client.post_graphql(
        STAFF_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)
    assert content["data"]["staffUpdate"]["errors"] == []
    data = content["data"]["staffUpdate"]["user"]

    return data
