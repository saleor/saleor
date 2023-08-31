from ...utils import get_graphql_content

CHECKOUT_LINES_ADD_MUTATION = """
mutation checkoutLinesAdd($checkoutId: ID!, $lines: [CheckoutLineInput!]!) {
  checkoutLinesAdd(id: $checkoutId, lines: $lines) {
    checkout {
      lines {
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
        undiscountedUnitPrice {
          amount
        }
      }
      availablePaymentGateways {
        id
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
