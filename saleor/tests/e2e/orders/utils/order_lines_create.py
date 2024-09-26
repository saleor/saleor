from saleor.graphql.tests.utils import get_graphql_content

ORDER_LINES_CREATE_MUTATION = """
mutation orderLinesCreate($id: ID!, $input: [OrderLineCreateInput!]!) {
  orderLinesCreate(id: $id, input: $input) {
    order {
      id
      shippingMethods {
        id
        price {
          amount
        }
      }
      undiscountedShippingPrice {
        amount
      }
      shippingPrice {
        ...BaseTaxedMoney
      }
      subtotal {
        ...BaseTaxedMoney
      }
      total {
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


def order_lines_create(
    api_client,
    order_id,
    input,
):
    variables = {"id": order_id, "input": input}

    response = api_client.post_graphql(ORDER_LINES_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    return content["data"]["orderLinesCreate"]
