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


def raw_checkout_shipping_address_update(
    api_client, checkout_id, address=DEFAULT_ADDRESS, save_address=None
):
    variables = {
        "checkoutId": checkout_id,
        "shippingAddress": address,
    }
    if save_address is not None:
        variables["saveAddress"] = save_address

    response = api_client.post_graphql(
        CHECKOUT_SHIPPING_ADDRESS_UPDATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)
    return content["data"]["checkoutShippingAddressUpdate"]


def checkout_shipping_address_update(
    api_client, checkout_id, address=DEFAULT_ADDRESS, save_address=None
):
    response = raw_checkout_shipping_address_update(
        api_client, checkout_id, address=address, save_address=None
    )

    assert response["errors"] == []

    data = response["checkout"]
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
