from saleor.graphql.tests.utils import get_graphql_content

ORDER_CREATE_FROM_CHECKOUT_MUTATION = """
mutation orderCreateFromCheckout($id: ID!) {
  orderCreateFromCheckout(id: $id) {
    errors {
      message
      field
      code
    }
    order {
        id
        created
        status
        paymentStatus
        channel { id }
        discounts {
            amount {
                amount
            }
        }
        channel {
            orderSettings {
                expireOrdersAfter
                deleteExpiredOrdersAfter
            }
        }
        billingAddress {
        streetAddress1
        }
        shippingAddress {
            streetAddress1
        }
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


def order_create_from_checkout(api_client, id):
    variables = {"id": id}

    response = api_client.post_graphql(
        ORDER_CREATE_FROM_CHECKOUT_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    data = content["data"]["orderCreateFromCheckout"]

    order_id = data["order"]["id"]
    errors = data["errors"]

    assert errors == []
    assert order_id is not None

    return data
