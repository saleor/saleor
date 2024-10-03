from saleor.graphql.tests.utils import get_graphql_content

ORDER_UPDATE_SHIPPING_MUTATION = """
mutation OrderUpdateShipping($input: OrderUpdateShippingInput!, $id: ID!) {
  orderUpdateShipping(input: $input, order: $id) {
    errors {
      message
      field
      code
    }
    order {
      id
      subtotal {
        ...BaseTaxedMoney
      }
      total {
        ...BaseTaxedMoney
      }
      undiscountedTotal {
        ...BaseTaxedMoney
      }
      deliveryMethod {
        __typename
        ... on ShippingMethod {
          id
        }
      }
      shippingPrice {
        ...BaseTaxedMoney
      }
      undiscountedShippingPrice {
        amount
      }
      voucher {
        id
        code
        discountValue
      }
      discounts {
        type
        value
        reason
        valueType
        amount {
          amount
        }
      }
      lines {
        totalPrice {
          ...BaseTaxedMoney
        }
        unitPrice {
          ...BaseTaxedMoney
        }
        unitDiscountReason
        isGift
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


def order_update_shipping(
    api_client,
    id,
    input,
):
    variables = {"id": id, "input": input}

    response = api_client.post_graphql(
        ORDER_UPDATE_SHIPPING_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)
    data = content["data"]["orderUpdateShipping"]
    order_id = data["order"]["id"]
    errors = data["errors"]

    assert errors == []
    assert order_id == id

    return data
