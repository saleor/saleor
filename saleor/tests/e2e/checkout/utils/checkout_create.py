from ... import DEFAULT_ADDRESS
from ...utils import get_graphql_content

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
      email
      user {
        id
        email
      }
      channel {
        slug
      }
      isShippingRequired
      totalPrice {
        gross {
          amount
        }
      }
      isShippingRequired
      shippingMethods {
        id
      }
      deliveryMethod {
        ... on ShippingMethod {
          id
        }
        ... on Warehouse {
          id
        }
      }
      shippingMethod {
        id
      }
      availableCollectionPoints {
        id
        isPrivate
        clickAndCollectOption
      }
      lines {
        id
        totalPrice {
          gross {
            amount
          }
          net {
            amount
          }
          tax {
            amount
          }
        }
        undiscountedTotalPrice {
          amount
        }
        unitPrice {
          gross {
            amount
          }
        }
        undiscountedUnitPrice {
          amount
        }
      }
    }
  }
}
"""


def raw_checkout_create(
    api_client,
    lines,
    channel_slug,
    email=None,
    set_default_billing_address=False,
    set_default_shipping_address=False,
):
    variables = {
        "input": {
            "channel": channel_slug,
            "email": email,
            "lines": lines,
        }
    }

    if set_default_billing_address:
        variables["input"]["billingAddress"] = DEFAULT_ADDRESS

    if set_default_shipping_address:
        variables["input"]["shippingAddress"] = DEFAULT_ADDRESS

    response = api_client.post_graphql(
        CHECKOUT_CREATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    checkout_data = content["data"]["checkoutCreate"]

    return checkout_data


def checkout_create(
    api_client,
    lines,
    channel_slug,
    email=None,
    set_default_billing_address=False,
    set_default_shipping_address=False,
):
    checkout_response = raw_checkout_create(
        api_client,
        lines,
        channel_slug,
        email,
        set_default_billing_address,
        set_default_shipping_address,
    )
    assert checkout_response["errors"] == []

    data = checkout_response["checkout"]
    assert data["id"] is not None
    assert data["channel"]["slug"] == channel_slug

    return data
