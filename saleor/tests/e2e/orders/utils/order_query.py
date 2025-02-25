from ...account.utils.fragments import ADDRESS_FRAGMENT
from ...utils import get_graphql_content

ORDER_QUERY = (
    """
query OrderDetails($id: ID!) {
  order(id: $id) {
    availableShippingMethods {
      id
      active
    }
    paymentStatus
    isPaid
    payments {
      id
      gateway
      paymentMethodType
      chargeStatus
      token
    }
    events {
      type
    }
    channel {
      id
      name
    }
    updatedAt
    fulfillments {
      created
      id
    }
    deliveryMethod {
      ... on ShippingMethod {
        id
        name
        active
      }
    }
    shippingMethods {
      id
    }
    shippingAddress {
      ...Address
    }
    billingAddress {
      ...Address
    }
    statusDisplay
    status
    transactions {
      id
    }
    metadata {
      key
      value
    }
    privateMetadata {
      key
      value
    }
  }
}
"""
    + ADDRESS_FRAGMENT
)


def order_query(
    api_client,
    order_id,
):
    variables = {"id": order_id}

    response = api_client.post_graphql(ORDER_QUERY, variables)
    content = get_graphql_content(response)

    return content["data"]["order"]
