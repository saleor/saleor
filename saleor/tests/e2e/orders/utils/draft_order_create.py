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
      discounts {
        amount {
          amount
        }
      }
      voucher {
        code
        id
      }
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
      lines {
        productVariantId
        quantity
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
        totalPrice {
          gross {
            amount
          }
        }
      }
    }
  }
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
