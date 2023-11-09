from ...utils import get_graphql_content

STAFF_CREATE_MUTATION = """
mutation CreateStaff($input: StaffCreateInput!){
  staffCreate(input:$input) {
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


def create_staff(
    staff_api_client,
    input_data,
):
    variables = {"input": input_data}

    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["staffCreate"]["errors"] == []

    data = content["data"]["staffCreate"]["user"]

    return data
