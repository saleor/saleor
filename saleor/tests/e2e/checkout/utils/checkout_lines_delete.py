from ...utils import get_graphql_content

CHECKOUT_LINES_DELETE_MUTATION = """
mutation CheckoutLinesDelete($checkoutId: ID!, $linesIds: [ID!]!) {
  checkoutLinesDelete(id: $checkoutId, linesIds: $linesIds) {
    checkout {
      discountName
      discount {
        amount
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
      lines {
        id
        quantity
        undiscountedTotalPrice {
          amount
        }
        variant {
          id
          quantityLimitPerCustomer
        }
        unitPrice {
          gross {
            amount
          }
        }
        undiscountedUnitPrice {
          amount
        }
        totalPrice {
          gross {
            amount
          }
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


def checkout_lines_delete(
    staff_api_client,
    checkout_id,
    linesIds,
):
    variables = {
        "checkoutId": checkout_id,
        "linesIds": linesIds,
    }

    response = staff_api_client.post_graphql(CHECKOUT_LINES_DELETE_MUTATION, variables)
    content = get_graphql_content(response)

    assert content["data"]["checkoutLinesDelete"]["errors"] == []
    return content["data"]["checkoutLinesDelete"]["checkout"]
