from saleor.graphql.tests.utils import get_graphql_content

ORDER_DISCOUNT_ADD_MUTATION = """
mutation OrderDiscountAdd($input: OrderDiscountCommonInput!, $id: ID!) {
  orderDiscountAdd(input: $input, orderId: $id) {
    errors {
      message
      field
    }
    order {
      errors {
        message
        field
      }
      id
      total {
        ...BaseTaxedMoney
      }
      undiscountedTotal {
        ...BaseTaxedMoney
      }
      undiscountedShippingPrice {
        amount
      }
      discounts {
        id
        value
        valueType
        type
        amount {
          amount
        }
        reason
      }
      shippingPrice {
        ...BaseTaxedMoney
      }
      subtotal {
        ...BaseTaxedMoney
      }
      lines {
        id
        totalPrice {
          ...BaseTaxedMoney
        }
        unitPrice {
          ...BaseTaxedMoney
        }
        unitDiscountReason
        undiscountedUnitPrice {
          ...BaseTaxedMoney
        }
        undiscountedTotalPrice {
          ...BaseTaxedMoney
        }
      }
      voucherCode
      voucher {
        id
        code
        discountValue
        codes(first: 10) {
          edges {
            node {
              id
              code
              isActive
              used
            }
          }
          totalCount
        }
      }
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


def order_discount_add(
    api_client,
    id,
    input,
):
    variables = {"id": id, "input": input}

    response = api_client.post_graphql(
        ORDER_DISCOUNT_ADD_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountAdd"]
    order_id = data["order"]["id"]
    errors = data["errors"]

    assert errors == []
    assert order_id is not None

    return data
