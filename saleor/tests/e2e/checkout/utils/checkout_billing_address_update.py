from ... import DEFAULT_ADDRESS
from ...utils import assert_address_data, get_graphql_content

CHECKOUT_BILLING_ADDRESS_UPDATE_MUTATION = """
mutation CheckoutBillingAddressUpdate(
  $billingAddress: AddressInput!, $checkoutId: ID!
) {
  checkoutBillingAddressUpdate(billingAddress: $billingAddress, id: $checkoutId) {
    errors {
      field
      code
      message
    }
    checkout {
      billingAddress {
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
    }
  }
}
"""


def checkout_billing_address_update(api_client, checkout_id, address=DEFAULT_ADDRESS):
    variables = {
        "checkoutId": checkout_id,
        "billingAddress": address,
    }
    response = api_client.post_graphql(
        CHECKOUT_BILLING_ADDRESS_UPDATE_MUTATION,
        variables=variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["checkoutBillingAddressUpdate"]["errors"] == []

    data = content["data"]["checkoutBillingAddressUpdate"]["checkout"]
    assert_address_data(data["billingAddress"], address)

    return data
