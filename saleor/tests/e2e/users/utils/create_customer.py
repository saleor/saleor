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
    email,
    metadata=None,
    private_metadata=None,
    is_active=False,
):
    variables = {
        "input": {
            "email": email,
            "metadata": metadata,
            "privateMetadata": private_metadata,
            "isActive": is_active,
        }
    }

    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["customerCreate"]["errors"] == []

    data = content["data"]["customerCreate"]["user"]
    assert data["id"] is not None

    return data
