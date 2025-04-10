from ...account.utils.fragments import ADDRESS_FRAGMENT
from ...utils import get_graphql_content

CHECKOUT_COMPLETE_MUTATION = (
    """
mutation CheckoutComplete($checkoutId: ID!) {
  checkoutComplete(id: $checkoutId) {
    errors {
      message
      field
      code
    }
    order {
      id
      userEmail
      status
      paymentStatus
      isPaid
      isShippingRequired
      total {
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
      paymentStatus
      statusDisplay
      status
      isPaid
      subtotal {
        gross {
          amount
        }
      }
      checkoutId
      deliveryMethod {
        ... on ShippingMethod {
          id
          name
          price {
            amount
          }
        }
        ... on Warehouse {
          id
        }
      }
      shippingPrice {
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
      lines {
        id
        quantity
        totalPrice {
          gross {
            amount
          }
        }
        unitPrice {
          gross {
            amount
          }
        }
        undiscountedTotalPrice {
          gross {
            amount
          }
        }
        undiscountedUnitPrice {
          gross {
            amount
          }
        }
        unitDiscount {
          amount
        }
        unitDiscountType
        unitDiscountReason
        unitDiscountValue
        discounts{
          id
          type
          value
          total{
            amount
          }
          unit{
            amount
          }
        }
      }
      discounts {
        id
        name
        type
        value
        amount {
          amount
        }
      }
      voucher {
        code
      }
      giftCards {
        id
        last4CodeChars
      }
      billingAddress {
        ...Address
      }
      shippingAddress {
        ...Address
      }
    }
  }
}
"""
    + ADDRESS_FRAGMENT
)


def raw_checkout_complete(api_client, checkout_id):
    variables = {
        "checkoutId": checkout_id,
    }
    response = api_client.post_graphql(
        CHECKOUT_COMPLETE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    raw_data = content["data"]["checkoutComplete"]

    return raw_data


def checkout_complete(api_client, checkout_id):
    checkout_response = raw_checkout_complete(api_client, checkout_id)

    assert checkout_response["errors"] == []

    data = checkout_response["order"]
    assert data["id"] is not None
    assert data["checkoutId"] == checkout_id

    return data
