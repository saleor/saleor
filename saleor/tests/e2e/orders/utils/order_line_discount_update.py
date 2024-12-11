from .....graphql.tests.utils import get_graphql_content

ORDER_LINE_DISCOUNT_UPDATE = """
mutation OrderLineDiscountUpdate($input: OrderDiscountCommonInput!, $orderLineId: ID!){
  orderLineDiscountUpdate(orderLineId: $orderLineId, input: $input){
    order {
      id
      voucherCode
      voucher {
        id
      }
      total {
        ...BaseTaxedMoney
      }
      undiscountedTotal {
        ...BaseTaxedMoney
      }
      subtotal {
        ...BaseTaxedMoney
      }
      shippingPrice {
        ...BaseTaxedMoney
      }
      undiscountedShippingPrice {
        amount
      }
      lines {
            id
            undiscountedUnitPrice {
            ...BaseTaxedMoney
            }
            unitPrice {
            ...BaseTaxedMoney
            }
            totalPrice {
             ...BaseTaxedMoney
            }
            undiscountedTotalPrice {
            ...BaseTaxedMoney
            }
            quantity
            unitDiscount {
            amount
            }
            unitDiscountValue
            unitDiscountReason
            voucherCode
        }
    }
    errors{
      field
      message
      code
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
}
"""


def order_line_discount_update(api_client, id, input):
    variables = {"orderLineId": id, "input": input}

    response = api_client.post_graphql(
        ORDER_LINE_DISCOUNT_UPDATE,
        variables=variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["orderLineDiscountUpdate"]
    assert not data["errors"]

    return data
