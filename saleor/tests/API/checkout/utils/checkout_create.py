from .....graphql.tests.utils import get_graphql_content

CHECKOUT_CREATE_MUTATION = """
mutation CreateCheckout($input: CheckoutCreateInput!) {
  checkoutCreate(input: $input) {
    errors {
      field
      code
      message
    }
    checkout {
      id
      channel {
        slug
      }
      totalPrice {
        gross {
          amount
        }
      }
    }
  }
}
"""


def checkout_create(api_client, lines, channel_slug):
    variables = {
        "input": {
            "channel": channel_slug,
            "email": "testEmail@example.com",
            "lines": lines,
        }
    }
    response = api_client.post_graphql(
        CHECKOUT_CREATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["checkoutCreate"]["errors"] == []

    data = content["data"]["checkoutCreate"]["checkout"]
    assert data["channel"]["slug"] == channel_slug

    return data
