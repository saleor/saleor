from unittest.mock import patch

import graphene
from freezegun import freeze_time

from ......account.search import generate_address_search_document_value
from ......webhook.event_types import WebhookEventAsyncType
from .....tests.utils import assert_no_permission, get_graphql_content
from ..utils import generate_address_webhook_call_args

ACCOUNT_ADDRESS_UPDATE_MUTATION = """
    mutation updateAccountAddress($addressId: ID!, $address: AddressInput!) {
        accountAddressUpdate(id: $addressId, input: $address) {
            address {
                city
            }
            user {
                id
            }
        }
    }
"""


def test_customer_update_own_address(
    user_api_client, customer_user, graphql_address_data
):
    query = ACCOUNT_ADDRESS_UPDATE_MUTATION
    address_obj = customer_user.addresses.first()
    address_data = graphql_address_data
    address_data["city"] = "Poznań"
    assert address_data["city"] != address_obj.city
    user = user_api_client.user

    variables = {
        "addressId": graphene.Node.to_global_id("Address", address_obj.id),
        "address": address_data,
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountAddressUpdate"]
    assert data["address"]["city"] == address_data["city"].upper()
    address_obj.refresh_from_db()
    assert address_obj.city == address_data["city"].upper()
    user.refresh_from_db()
    assert generate_address_search_document_value(address_obj) in user.search_document


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_customer_address_update_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    user_api_client,
    customer_user,
    graphql_address_data,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    address = customer_user.addresses.first()
    address_data = graphql_address_data
    address_data["city"] = "Poznań"
    assert address_data["city"] != address.city

    variables = {
        "addressId": graphene.Node.to_global_id("Address", address.id),
        "address": graphql_address_data,
    }

    # when
    response = user_api_client.post_graphql(ACCOUNT_ADDRESS_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    address.refresh_from_db()

    # then
    assert content["data"]["accountAddressUpdate"]
    mocked_webhook_trigger.assert_called_once_with(
        *generate_address_webhook_call_args(
            address,
            WebhookEventAsyncType.ADDRESS_UPDATED,
            user_api_client.user,
            any_webhook,
        )
    )


def test_update_address_as_anonymous_user(
    api_client, customer_user, graphql_address_data
):
    query = ACCOUNT_ADDRESS_UPDATE_MUTATION
    address_obj = customer_user.addresses.first()

    variables = {
        "addressId": graphene.Node.to_global_id("Address", address_obj.id),
        "address": graphql_address_data,
    }
    response = api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_customer_update_own_address_not_updated_when_validation_fails(
    user_api_client, customer_user, graphql_address_data
):
    query = ACCOUNT_ADDRESS_UPDATE_MUTATION
    address_obj = customer_user.addresses.first()
    address_data = graphql_address_data
    address_data["city"] = "Poznań"
    address_data["postalCode"] = "wrong postal code"
    assert address_data["city"] != address_obj.city

    variables = {
        "addressId": graphene.Node.to_global_id("Address", address_obj.id),
        "address": address_data,
    }
    user_api_client.post_graphql(query, variables)
    address_obj.refresh_from_db()
    assert address_obj.city != address_data["city"]
    assert address_obj.postal_code != address_data["postalCode"]


def test_customer_update_address_for_other(
    user_api_client, customer_user, address_other_country, graphql_address_data
):
    address_obj = address_other_country
    assert customer_user not in address_obj.user_addresses.all()

    address_data = graphql_address_data
    variables = {
        "addressId": graphene.Node.to_global_id("Address", address_obj.id),
        "address": address_data,
    }
    response = user_api_client.post_graphql(ACCOUNT_ADDRESS_UPDATE_MUTATION, variables)
    assert_no_permission(response)
