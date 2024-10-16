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
      user {
        id
        email
      }
      undiscountedTotal {
        ...BaseTaxedMoney
      }
      totalBalance {
        amount
      }
      total {
        ...BaseTaxedMoney
      }
      subtotal {
        ...BaseTaxedMoney
      }
      undiscountedShippingPrice {
        amount
      }
      shippingPrice {
        ...BaseTaxedMoney
      }
      status
      voucher {
        id
        code
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
      paymentStatus
      isPaid
      channel {
        orderSettings {
          markAsPaidStrategy
        }
      }
      lines {
        id
        productVariantId
        quantity
        unitDiscount {
          amount
        }
        undiscountedUnitPrice {
          ...BaseTaxedMoney
        }
        unitPrice {
          ...BaseTaxedMoney
        }
        undiscountedTotalPrice {
          ...BaseTaxedMoney
        }
        totalPrice {
          ...BaseTaxedMoney
        }
        unitDiscountReason
        unitDiscountType
        unitDiscountValue
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


def raw_draft_order_complete(api_client, id):
    variables = {"id": id}

    response = api_client.post_graphql(
        DRAFT_ORDER_COMPLETE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["draftOrderComplete"]

    return data


def draft_order_complete(api_client, id):
    response = raw_draft_order_complete(api_client, id)

    assert response["order"] is not None

    errors = response["errors"]

    assert errors == []

    return response
