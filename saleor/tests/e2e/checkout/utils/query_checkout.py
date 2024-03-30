from ...utils import get_graphql_content

CHECKOUT_QUERY = """
query Checkout($checkoutId: ID!){
  checkout(id: $checkoutId){
    id
    voucherCode
    discount {
        amount
      }
    totalPrice{
      gross{
        amount
      }
      net{
        amount
      }
      tax{
        amount
      }
    }
    subtotalPrice {
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
    availablePaymentGateways{
      id
      name
    }
    shippingMethods{
      id
      name
      price{
        amount
      }
    }
    shippingPrice {
      tax {
        amount
      }
      net {
        amount
      }
      gross {
        amount
      }
    }
  }
}
"""


def get_checkout(
    api_client,
    checkout_id,
):
    variables = {"checkoutId": checkout_id}

    response = api_client.post_graphql(CHECKOUT_QUERY, variables)
    content = get_graphql_content(response)

    return content["data"]["checkout"]
