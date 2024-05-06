from ...utils import get_graphql_content

CHECKOUT_ADD_PROMO_CODE_MUTATION = """
mutation AddCheckoutPromoCode($checkoutId: ID!, $promoCode: String!) {
  checkoutAddPromoCode(id: $checkoutId, promoCode: $promoCode) {
    checkout {
      id
      totalPrice {
        gross {
          amount
        }
      }
      subtotalPrice {
        gross {
          amount
        }
      }
      shippingPrice {
        gross {
          amount
        }
      }
      shippingMethods {
        id
        name
      }
      deliveryMethod {
        ... on ShippingMethod {
          id
          name
        }
      }
      voucherCode
      discount {
        amount
      }
      discountName
      lines {
        totalPrice {
          gross {
            amount
          }
        }
        undiscountedTotalPrice {
          amount
        }
        unitPrice {
          gross {
            amount
          }
        }
        undiscountedUnitPrice {
          amount
        }
      }
      giftCards {
        id
        last4CodeChars
      }
    }
    errors {
      code
      field
      message
    }
  }
}
"""


def raw_checkout_add_promo_code(
    staff_api_client,
    checkout_id,
    code,
):
    variables = {
        "checkoutId": checkout_id,
        "promoCode": code,
    }
    response = staff_api_client.post_graphql(
        CHECKOUT_ADD_PROMO_CODE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    raw_data = content["data"]["checkoutAddPromoCode"]

    return raw_data


def checkout_add_promo_code(
    staff_api_client,
    checkout_id,
    code,
):
    checkout_response = raw_checkout_add_promo_code(
        staff_api_client,
        checkout_id,
        code,
    )

    assert checkout_response["errors"] == []

    return checkout_response["checkout"]
