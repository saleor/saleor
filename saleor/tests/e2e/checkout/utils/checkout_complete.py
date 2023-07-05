from ...utils import get_graphql_content

CHECKOUT_COMPLETE_MUTATION = """
mutation CheckoutComplete($checkoutId: ID!) {
  checkoutComplete(id: $checkoutId) {
    errors {
      message
      field
      code
    }
    order {
      id
      status
      user {
        email
      }
      isShippingRequired
      total {
        gross {
          amount
        }
      }
      checkoutId
      deliveryMethod {
        ... on ShippingMethod {
          id
        }
        ... on Warehouse {
          id
        }
      }
    }
  }
}
"""


def checkout_complete(api_client, checkout_id):
    variables = {
        "checkoutId": checkout_id,
    }
    response = api_client.post_graphql(
        CHECKOUT_COMPLETE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["checkoutComplete"]["errors"] == []

    data = content["data"]["checkoutComplete"]["order"]
    assert data["id"] is not None
    assert data["checkoutId"] == checkout_id

    return data
