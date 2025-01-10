from saleor.graphql.tests.utils import get_graphql_content

ORDER_LINE_DELETE_MUTATION = """
mutation orderLineDelete($lineId: ID!) {
  orderLineDelete(id: $lineId) {
    order {
      id
      shippingMethods {
        id
        price {
          amount
        }
      }
      total {
        ...BaseTaxedMoney
      }
      subtotal {
        ...BaseTaxedMoney
      }
      undiscountedTotal {
        ...BaseTaxedMoney
      }
      isShippingRequired
      lines {
        id
        quantity
        variant {
          id
        }
        totalPrice {
          ...BaseTaxedMoney
        }
        unitPrice {
          ...BaseTaxedMoney
        }
        unitDiscountReason
        unitDiscountType
        unitDiscountValue
        unitDiscount {
          amount
        }
        undiscountedUnitPrice {
          gross {
            amount
          }
        }
      }
    }
    errors {
      code
      field
      message
    }
  }
}

fragment BaseTaxedMoney on TaxedMoney {
  gross {
    amount
  }
  net {
    amount
  }
  tax {
    amount
  }
  currency
}
"""


def order_line_delete(
    api_client,
    order_line_id,
):
    variables = {"lineId": order_line_id}

    response = api_client.post_graphql(ORDER_LINE_DELETE_MUTATION, variables)
    content = get_graphql_content(response)

    return content["data"]["orderLineDelete"]
