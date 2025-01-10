from saleor.graphql.tests.utils import get_graphql_content

ORDER_BY_CHECKOUT_ID_QUERY = """
query OrderByCheckoutIdDetails($checkout_id: ID!) {
  orders(first:1, filter: {checkoutIds: [$checkout_id]}) {
    totalCount
    edges {
      node {
        chargeStatus
        authorizeStatus
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
        status
        transactions {
          id
          pspReference
        }
      }
    }
  }
}

"""


def order_by_checkout_id_query(
    api_client,
    checkout_id,
):
    variables = {"checkout_id": checkout_id}

    response = api_client.post_graphql(ORDER_BY_CHECKOUT_ID_QUERY, variables)
    content = get_graphql_content(response)

    return content["data"]["orders"]["edges"][0]["node"]
