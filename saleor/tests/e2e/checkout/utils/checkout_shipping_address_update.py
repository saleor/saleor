from ... import DEFAULT_ADDRESS
from ...utils import get_graphql_content

CHECKOUT_SHIPPING_ADDRESS_UPDATE_MUTATION = """
mutation CheckoutShippingAddressUpdate(
  $shippingAddress: AddressInput!, $checkoutId: ID!
) {
  checkoutShippingAddressUpdate(
    shippingAddress: $shippingAddress
    id: $checkoutId
  ) {
    errors {
      field
      code
      message
    }
    checkout {
      shippingAddress {
        firstName
        lastName
        companyName
        streetAddress1
        postalCode
        country {
          code
        }
        city
        countryArea
        phone
      }
      shippingMethods {
        id
        name
      }
    }
  }
}
"""


def checkout_shipping_address_update(api_client, checkout_id, address=DEFAULT_ADDRESS):
    variables = {
        "checkoutId": checkout_id,
        "shippingAddress": address,
    }
    response = api_client.post_graphql(
        CHECKOUT_SHIPPING_ADDRESS_UPDATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["checkoutShippingAddressUpdate"]["errors"] == []

    data = content["data"]["checkoutShippingAddressUpdate"]["checkout"]
    assert data["shippingAddress"]["firstName"] == address["firstName"]
    assert data["shippingAddress"]["lastName"] == address["lastName"]
    assert data["shippingAddress"]["companyName"] == address["companyName"]
    assert data["shippingAddress"]["streetAddress1"] == address["streetAddress1"]
    assert data["shippingAddress"]["postalCode"] == address["postalCode"]
    assert data["shippingAddress"]["country"]["code"] == address["country"]
    assert data["shippingAddress"]["city"] == address["city"].upper()
    assert data["shippingAddress"]["countryArea"] == address["countryArea"]
    assert data["shippingAddress"]["phone"] == address["phone"]

    return data
