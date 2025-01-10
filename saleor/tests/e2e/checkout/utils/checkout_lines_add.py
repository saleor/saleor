from ...utils import get_graphql_content

CHECKOUT_LINES_ADD_MUTATION = """
mutation checkoutLinesAdd($checkoutId: ID!, $lines: [CheckoutLineInput!]!) {
  checkoutLinesAdd(id: $checkoutId, lines: $lines) {
    checkout {
      lines {
        id
        quantity
        variant {
          id
        }
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
        undiscountedUnitPrice {
          amount
        }
        undiscountedTotalPrice {
          amount
        }
      }
      availablePaymentGateways {
        id
      }
      subtotalPrice {
        gross {
          amount
        }
      }
      totalPrice {
        gross {
          amount
        }
      }
      isShippingRequired
      availableCollectionPoints {
        id
        name
      }
      shippingMethods {
        id
        name
      }
    }
    errors {
      field
      lines
      message
      variants
      code
    }
  }
}
"""


def checkout_lines_add(
    staff_api_client,
    checkout_id,
    lines,
):
    variables = {
        "checkoutId": checkout_id,
        "lines": lines,
    }

    response = staff_api_client.post_graphql(CHECKOUT_LINES_ADD_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["checkoutLinesAdd"]["errors"] == []

    return content["data"]["checkoutLinesAdd"]["checkout"]
