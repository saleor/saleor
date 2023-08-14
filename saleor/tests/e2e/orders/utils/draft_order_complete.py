from saleor.graphql.tests.utils import get_graphql_content

DRAFT_ORDER_COMPLETE_MUTATION = """
mutation DraftOrderComplete($id: ID!) {
  draftOrderComplete(id: $id) {
    errors {
      message
      field
      code
    }
    order {
      id
      undiscountedTotal {
        gross {
          amount
        }
      }
      totalBalance {
        amount
      }
      total {
        gross {
          amount
        }
      }
      subtotal {
        gross {
          amount
        }
      }
      shippingPrice {
        gross {
          amount
        }
      }
      displayGrossPrices
      status
      lines {
        productVariantId
        quantity
        unitDiscount {
          amount
        }
        undiscountedUnitPrice {
          gross {
            amount
          }
        }
        unitPrice {
          gross {
            amount
          }
        }
        unitDiscountReason
        unitDiscountType
        unitDiscountValue
      }
    }
  }
}
"""


def draft_order_complete(api_client, id):
    variables = {"id": id}

    response = api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["draftOrderComplete"]

    errors = data["errors"]

    assert errors == []

    return data
