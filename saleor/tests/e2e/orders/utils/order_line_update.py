from saleor.graphql.tests.utils import get_graphql_content

ORDER_LINE_UPDATE_MUTATION = """
mutation orderLineUpdate($id: ID!, $input: OrderLineInput!) {
  orderLineUpdate(id: $id, input: $input) {
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
      discounts {
        id
        type
        name
        valueType
        value
        reason
        amount {
          amount
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


def order_line_update(
    api_client,
    order_line_id,
    input,
):
    variables = {"id": order_line_id, "input": input}

    response = api_client.post_graphql(ORDER_LINE_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    return content["data"]["orderLineUpdate"]
