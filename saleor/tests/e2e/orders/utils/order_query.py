from saleor.graphql.tests.utils import get_graphql_content

ORDER_QUERY = """
query OrderDetails($id:ID!) {
  order(id:$id) {
    availableShippingMethods {
      id
      active
    }
    channel {
        id
        name
    }
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
      country {
        code
      }
      countryArea
      firstName
      cityArea
      city
      phone
      postalCode
      streetAddress1
      streetAddress2
    }
    statusDisplay
  }
}
"""


def order_query(
    api_client,
    order_id,
):
    variables = {"id": order_id}

    response = api_client.post_graphql(ORDER_QUERY, variables)
    content = get_graphql_content(response)

    return content["data"]["order"]
