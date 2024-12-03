from saleor.graphql.tests.utils import get_graphql_content

ORDER_DISCOUNT_DELETE_MUTATION = """
mutation OrderDiscountDelete($discountId: ID!){
  orderDiscountDelete(discountId: $discountId){
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
      }
      voucherCode
      voucher {
        id
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


def order_discount_delete(api_client, id):
    response = api_client.post_graphql(
        ORDER_DISCOUNT_DELETE_MUTATION,
        variables={"discountId": id},
    )
    content = get_graphql_content(response)
    data = content["data"]["orderDiscountDelete"]
    assert not data["errors"]

    return data
