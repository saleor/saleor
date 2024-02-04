from ...utils import get_graphql_content

CHECKOUT_EMAIL_UPDATE_MUTATION = """
mutation checkoutEmailUpdate($checkoutId: ID!, $email: String!){
  checkoutEmailUpdate(
    id: $checkoutId
    email: $email
  ) {
    checkout {
      email
    }
    errors {
      field
      message
    }
  }
}
"""


def checkout_update_email(
    staff_api_client,
    checkout_id,
    email,
):
    variables = {
        "checkoutId": checkout_id,
        "email": email,
    }

    response = staff_api_client.post_graphql(CHECKOUT_EMAIL_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["checkoutEmailUpdate"]["errors"] == []
    data = content["data"]["checkoutEmailUpdate"]["checkout"]
    return data
