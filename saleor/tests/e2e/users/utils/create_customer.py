from ...utils import get_graphql_content

CUSTOMER_CREATE_MUTATION = """
mutation CreateCustomer ($input: UserCreateInput!) {
  customerCreate(
    input: $input
  ) {
    errors {
      field
      message
      code
    }
    user {
      id
      email
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


def create_customer(
    staff_api_client,
    input_data,
):
    variables = {"input": input_data}

    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["customerCreate"]["errors"] == []

    data = content["data"]["customerCreate"]["user"]
    assert data["id"] is not None

    return data
