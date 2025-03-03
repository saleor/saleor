from ... import DEFAULT_ADDRESS
from ...account.utils.fragments import ADDRESS_FRAGMENT
from ...utils import get_graphql_content

CHECKOUT_CREATE_MUTATION = (
    """
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
      discountName
      discount {
        amount
      }
      shippingPrice {
        gross {
          amount
        }
      }
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
      subtotalPrice {
        gross {
          amount
        }
      }
      created
      isShippingRequired
      billingAddress {
        ...Address
      }
      shippingAddress {
        ...Address
      }
      shippingMethods {
        id
        name
        price {
          amount
          currency
        }
        maximumDeliveryDays
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
        quantity
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
          tax {
            amount
          }
        }
        undiscountedUnitPrice {
          amount
        }
        variant {
          id
        }
      }
    }
  }
}
"""
    + ADDRESS_FRAGMENT
)


def raw_checkout_create(
    api_client,
    lines,
    channel_slug,
    email=None,
    billing_address=DEFAULT_ADDRESS,
    shipping_address=DEFAULT_ADDRESS,
    save_billing_address=None,
    save_shipping_address=None,
):
    variables = {
        "input": {
            "channel": channel_slug,
            "email": email,
            "lines": lines,
        }
    }

    if billing_address:
        variables["input"]["billingAddress"] = billing_address

    if shipping_address:
        variables["input"]["shippingAddress"] = shipping_address

    if save_billing_address is not None:
        variables["input"]["saveBillingAddress"] = save_billing_address

    if save_shipping_address is not None:
        variables["input"]["saveShippingAddress"] = save_shipping_address

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
    billing_address=DEFAULT_ADDRESS,
    shipping_address=DEFAULT_ADDRESS,
    save_billing_address=None,
    save_shipping_address=None,
):
    checkout_response = raw_checkout_create(
        api_client,
        lines,
        channel_slug,
        email,
        billing_address,
        shipping_address,
        save_billing_address,
        save_shipping_address,
    )
    assert checkout_response["errors"] == []

    data = checkout_response["checkout"]
    assert data["id"] is not None
    assert data["channel"]["slug"] == channel_slug

    return data
