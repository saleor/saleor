from unittest.mock import patch

import graphene
import pytest
from django.test import override_settings
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......account.models import Address
from ......account.search import generate_address_search_document_value
from ......checkout import AddressType
from ......webhook.event_types import WebhookEventAsyncType
from .....tests.utils import assert_no_permission, get_graphql_content
from ..utils import generate_address_webhook_call_args

ACCOUNT_ADDRESS_CREATE_MUTATION = """
mutation($addressInput: AddressInput!, $addressType: AddressTypeEnum) {
  accountAddressCreate(input: $addressInput, type: $addressType) {
    address {
        id,
        city
        metadata {
            key
            value
        }
    }
    user {
        email
    }
    errors {
        code
        field
        addressType
    }
  }
}
"""


def test_customer_create_address(user_api_client, graphql_address_data):
    user = user_api_client.user
    user_addresses_count = user.addresses.count()
    user_addresses_ids = list(user.addresses.values_list("id", flat=True))

    query = ACCOUNT_ADDRESS_CREATE_MUTATION
    mutation_name = "accountAddressCreate"
    variables = {"addressInput": graphql_address_data}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]

    assert data["address"]["metadata"] == [{"key": "public", "value": "public_value"}]
    assert data["address"]["city"] == graphql_address_data["city"].upper()

    user.refresh_from_db()

    assert user.addresses.exclude(id__in=user_addresses_ids).first().metadata == {
        "public": "public_value"
    }
    assert user.addresses.count() == user_addresses_count + 1
    assert (
        generate_address_search_document_value(user.addresses.last())
        in user.search_document
    )


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_customer_create_address_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    user_api_client,
    graphql_address_data,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {"addressInput": graphql_address_data}

    # when
    response = user_api_client.post_graphql(ACCOUNT_ADDRESS_CREATE_MUTATION, variables)
    content = get_graphql_content(response)
    address = Address.objects.last()

    # then
    assert content["data"]["accountAddressCreate"]
    mocked_webhook_trigger.assert_called_with(
        *generate_address_webhook_call_args(
            address,
            WebhookEventAsyncType.ADDRESS_CREATED,
            user_api_client.user,
            any_webhook,
        )
    )


def test_account_address_create_return_user(user_api_client, graphql_address_data):
    user = user_api_client.user
    variables = {"addressInput": graphql_address_data}
    response = user_api_client.post_graphql(ACCOUNT_ADDRESS_CREATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountAddressCreate"]["user"]
    assert data["email"] == user.email


def test_customer_create_default_address(user_api_client, graphql_address_data):
    user = user_api_client.user
    user_addresses_count = user.addresses.count()

    query = ACCOUNT_ADDRESS_CREATE_MUTATION
    mutation_name = "accountAddressCreate"

    address_type = AddressType.SHIPPING.upper()
    variables = {"addressInput": graphql_address_data, "addressType": address_type}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert data["address"]["city"] == graphql_address_data["city"].upper()

    user.refresh_from_db()
    assert user.addresses.count() == user_addresses_count + 1
    assert user.default_shipping_address.id == int(
        graphene.Node.from_global_id(data["address"]["id"])[1]
    )

    address_type = AddressType.BILLING.upper()
    variables = {"addressInput": graphql_address_data, "addressType": address_type}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert data["address"]["city"] == graphql_address_data["city"].upper()

    user.refresh_from_db()
    assert user.addresses.count() == user_addresses_count + 2
    assert user.default_billing_address.id == int(
        graphene.Node.from_global_id(data["address"]["id"])[1]
    )


@override_settings(MAX_USER_ADDRESSES=2)
def test_customer_create_address_the_oldest_address_is_deleted(
    user_api_client, graphql_address_data, address
):
    """Ensure that when mew address it added to user with max amount of addressess,
    the oldest address will be removed."""
    user = user_api_client.user
    same_address = Address.objects.create(**address.as_data())
    user.addresses.set([address, same_address])

    user_addresses_count = user.addresses.count()

    query = ACCOUNT_ADDRESS_CREATE_MUTATION
    mutation_name = "accountAddressCreate"

    variables = {"addressInput": graphql_address_data}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]

    assert data["address"]["city"] == graphql_address_data["city"].upper()

    user.refresh_from_db()
    assert user.addresses.count() == user_addresses_count

    with pytest.raises(address._meta.model.DoesNotExist):
        address.refresh_from_db()


def test_anonymous_user_create_address(api_client, graphql_address_data):
    query = ACCOUNT_ADDRESS_CREATE_MUTATION
    variables = {"addressInput": graphql_address_data}
    response = api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_address_not_created_after_validation_fails(
    user_api_client, graphql_address_data
):
    user = user_api_client.user
    user_addresses_count = user.addresses.count()

    query = ACCOUNT_ADDRESS_CREATE_MUTATION

    graphql_address_data["postalCode"] = "wrong postal code"

    address_type = AddressType.SHIPPING.upper()
    variables = {"addressInput": graphql_address_data, "addressType": address_type}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)

    data = content["data"]["accountAddressCreate"]
    assert not data["address"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == AccountErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "postalCode"
    assert data["errors"][0]["addressType"] == address_type
    user.refresh_from_db()
    assert user.addresses.count() == user_addresses_count
