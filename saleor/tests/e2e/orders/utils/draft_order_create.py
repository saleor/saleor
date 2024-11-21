from saleor.graphql.tests.utils import get_graphql_content

DRAFT_ORDER_CREATE_MUTATION = """
mutation OrderDraftCreate($input: DraftOrderCreateInput!) {
  draftOrderCreate(input: $input) {
    errors {
      message
      field
      code
    }
    order {
      id
      created
      status
      user {
        id
        email
      }
      discounts {
        amount {
          amount
        }
      }
      voucher {
        code
        id
      }
      voucherCode
      billingAddress {
        streetAddress1
      }
      shippingAddress {
        streetAddress1
      }
      isShippingRequired
      shippingMethods {
        id
      }
      undiscountedTotal {
        ... BaseTaxedMoney
      }
      total {
        ... BaseTaxedMoney
      }
      shippingPrice {
        ... BaseTaxedMoney
      }
      lines {
        productVariantId
        quantity
        undiscountedUnitPrice {
          ... BaseTaxedMoney
        }
        unitPrice {
          ... BaseTaxedMoney
        }
        undiscountedTotalPrice {
          ... BaseTaxedMoney
        }
        totalPrice {
          ... BaseTaxedMoney
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


def draft_order_create(api_client, input):
    variables = {"input": input}

    response = api_client.post_graphql(
        DRAFT_ORDER_CREATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["draftOrderCreate"]

    order_id = data["order"]["id"]
    errors = data["errors"]

    assert errors == []
    assert order_id is not None

    return data
