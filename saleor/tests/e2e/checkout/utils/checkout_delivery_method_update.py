from ...utils import get_graphql_content

CHECKOUT_DELIVERY_METHOD_UPDATE_MUTATION = """
mutation checkoutDeliveryMethodUpdate($checkoutId: ID!, $deliveryMethodId: ID) {
  checkoutDeliveryMethodUpdate(
    id: $checkoutId
    deliveryMethodId: $deliveryMethodId
  ) {
    errors {
      field
      code
      message
    }
    checkout {
      id
      totalPrice {
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
      subtotalPrice {
        gross {
          amount
        }
        tax {
          amount
        }
      }
      shippingMethods {
        id
      }
      shippingPrice {
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
      deliveryMethod {
        ... on ShippingMethod {
          id
          price {
            amount
          }
        }
        ... on Warehouse {
          id
        }
      }
    }
  }
}
"""


def checkout_delivery_method_update(
    staff_api_client,
    checkout_id,
    delivery_method_id=None,
):
    variables = {
        "checkoutId": checkout_id,
        "deliveryMethodId": delivery_method_id,
    }

    response = staff_api_client.post_graphql(
        CHECKOUT_DELIVERY_METHOD_UPDATE_MUTATION, variables
    )
    content = get_graphql_content(response)

    assert content["data"]["checkoutDeliveryMethodUpdate"]["errors"] == []

    data = content["data"]["checkoutDeliveryMethodUpdate"]["checkout"]
    assert data["id"] is not None

    return data
