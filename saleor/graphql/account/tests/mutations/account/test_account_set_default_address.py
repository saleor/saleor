import graphene

from ......checkout import AddressType
from .....tests.utils import get_graphql_content

ACCOUNT_SET_DEFAULT_ADDRESS_MUTATION = """
mutation($id: ID!, $type: AddressTypeEnum!) {
  accountSetDefaultAddress(id: $id, type: $type) {
    errors {
      field,
      message
    }
  }
}
"""


def test_customer_set_address_as_default(user_api_client):
    user = user_api_client.user
    user.default_billing_address = None
    user.default_shipping_address = None
    user.save()
    assert not user.default_billing_address
    assert not user.default_shipping_address
    assert user.addresses.exists()

    address = user.addresses.first()
    query = ACCOUNT_SET_DEFAULT_ADDRESS_MUTATION
    mutation_name = "accountSetDefaultAddress"

    variables = {
        "id": graphene.Node.to_global_id("Address", address.id),
        "type": AddressType.SHIPPING.upper(),
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert not data["errors"]

    user.refresh_from_db()
    assert user.default_shipping_address == address

    variables["type"] = AddressType.BILLING.upper()
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert not data["errors"]

    user.refresh_from_db()
    assert user.default_billing_address == address


def test_customer_change_default_address(user_api_client, address_other_country):
    user = user_api_client.user
    assert user.default_billing_address
    assert user.default_billing_address
    address = user.default_shipping_address
    assert address in user.addresses.all()
    assert address_other_country not in user.addresses.all()

    user.default_shipping_address = address_other_country
    user.save()
    user.refresh_from_db()
    assert address_other_country not in user.addresses.all()

    query = ACCOUNT_SET_DEFAULT_ADDRESS_MUTATION
    mutation_name = "accountSetDefaultAddress"

    variables = {
        "id": graphene.Node.to_global_id("Address", address.id),
        "type": AddressType.SHIPPING.upper(),
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert not data["errors"]

    user.refresh_from_db()
    assert user.default_shipping_address == address
    assert address_other_country in user.addresses.all()


def test_customer_change_default_address_invalid_address(
    user_api_client, address_other_country
):
    user = user_api_client.user
    assert address_other_country not in user.addresses.all()

    query = ACCOUNT_SET_DEFAULT_ADDRESS_MUTATION
    mutation_name = "accountSetDefaultAddress"

    variables = {
        "id": graphene.Node.to_global_id("Address", address_other_country.id),
        "type": AddressType.SHIPPING.upper(),
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"][mutation_name]["errors"][0]["field"] == "id"
