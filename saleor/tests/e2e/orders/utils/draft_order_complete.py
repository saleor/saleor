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
      undiscountedTotal {
        gross {
          amount
        }
      }
      totalBalance {
        amount
      }
      total {
        gross {
          amount
        }
      }
      subtotal {
        gross {
          amount
        }
      }
      shippingPrice {
        gross {
          amount
        }
      }
      displayGrossPrices
      status
      paymentStatus
      isPaid
      channel {
        orderSettings{
            markAsPaidStrategy
        }
     }
      lines {
        productVariantId
        quantity
        unitDiscount {
          amount
        }
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
        unitDiscountReason
        unitDiscountType
        unitDiscountValue
      }
    }
  }
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
