from ...utils import get_graphql_content

CHECKOUT_LINES_UPDATE_MUTATION = """
mutation checkoutLinesUpdate($checkoutId: ID!, $lines: [CheckoutLineUpdateInput!]! ){
  checkoutLinesUpdate(lines: $lines, checkoutId: $checkoutId) {
    checkout {
      lines {
        quantity
        variant {
          id
          quantityLimitPerCustomer
        }
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


def checkout_lines_update(
    staff_api_client,
    checkout_id,
    lines,
):
    variables = {
        "checkoutId": checkout_id,
        "lines": lines,
    }

    response = staff_api_client.post_graphql(CHECKOUT_LINES_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    return content["data"]["checkoutLinesUpdate"]
