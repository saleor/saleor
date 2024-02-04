from ...utils import get_graphql_content

CUSTOMER_UPDATE_MUTATION = """
mutation CustomerUpdate($id: ID!, $input: CustomerInput!) {
  customerUpdate(id: $id, input: $input) {
    errors {
      field
      message
      code
    }
    user {
      id
      email
      isActive
      isConfirmed
      isStaff
      metadata {
        key
        value
      }
      privateMetadata {
        key
        value
      }
    }
  }
}
"""


def customer_update(
    api_client,
    user_id,
    input_data,
):
    variables = {
        "id": user_id,
        "input": input_data,
    }

    response = api_client.post_graphql(
        CUSTOMER_UPDATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["customerUpdate"]
    assert data["errors"] == []
    user_data = data["user"]

    return user_data
