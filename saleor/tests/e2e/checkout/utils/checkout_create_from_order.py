from saleor.graphql.tests.utils import get_graphql_content

CHECKOUT_CREATE_FROM_ORDER_MUTATION = """
mutation CheckoutCreateFromOrder( $id: ID!){
  checkoutCreateFromOrder(id: $id){
    errors{
      field
      message
      code
    }
    unavailableVariants{
      lineId
      variantId
      code
      message
    }
    checkout{
      id
      email
      totalPrice{
          gross{
            amount
            currency
          }
          net{
            amount
            currency
          }
          tax{
            amount
            currency
          }
        }
      user{
        id
      }
      lines{
        variant{
          id
          name
          product{
            id
            name
          }
        }
        quantity
        totalPrice{
          gross{
            amount
            currency
          }
          net{
            amount
            currency
          }
          tax{
            amount
            currency
          }
        }
      }
      metadata{
        key
        value
      }
      shippingPrice{
          gross{
            amount
            currency
          }
          net{
            amount
            currency
          }
          tax{
            amount
            currency
          }
        }
      shippingAddress{
        country{
          code
        }
        countryArea
        streetAddress1
        streetAddress2
        postalCode
        city
        firstName
        lastName
      }
      billingAddress{
        country{
          code
        }
        countryArea
        streetAddress1
        streetAddress2
        postalCode
        city
        firstName
        lastName
      }
      shippingMethods{
        id
        name
      }
    }
  }
}
"""


def checkout_create_from_order(api_client, order_id):
    variables = {"id": order_id}

    response = api_client.post_graphql(
        CHECKOUT_CREATE_FROM_ORDER_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    checkout_data = content["data"]["checkoutCreateFromOrder"]

    return checkout_data
