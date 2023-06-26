import graphene

from ......checkout import AddressType
from .....tests.utils import get_graphql_content

SET_DEFAULT_ADDRESS_MUTATION = """
mutation($address_id: ID!, $user_id: ID!, $type: AddressTypeEnum!) {
  addressSetDefault(addressId: $address_id, userId: $user_id, type: $type) {
    errors {
      field
      message
    }
    user {
      defaultBillingAddress {
        id
      }
      defaultShippingAddress {
        id
      }
    }
  }
}
"""


def test_set_default_address(
    staff_api_client, address_other_country, customer_user, permission_manage_users
):
    customer_user.default_billing_address = None
    customer_user.default_shipping_address = None
    customer_user.save()

    # try to set an address that doesn't belong to that user
    address = address_other_country

    variables = {
        "address_id": graphene.Node.to_global_id("Address", address.id),
        "user_id": graphene.Node.to_global_id("User", customer_user.id),
        "type": AddressType.SHIPPING.upper(),
    }

    response = staff_api_client.post_graphql(
        SET_DEFAULT_ADDRESS_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["addressSetDefault"]
    assert data["errors"][0]["field"] == "addressId"

    # try to set a new billing address using one of user's addresses
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.id)

    variables["address_id"] = address_id
    response = staff_api_client.post_graphql(SET_DEFAULT_ADDRESS_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["addressSetDefault"]
    assert data["user"]["defaultShippingAddress"]["id"] == address_id
