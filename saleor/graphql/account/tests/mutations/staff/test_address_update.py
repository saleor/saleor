from unittest.mock import patch

import graphene
from freezegun import freeze_time

from ......account.search import generate_address_search_document_value
from ......webhook.event_types import WebhookEventAsyncType
from .....tests.utils import assert_no_permission, get_graphql_content
from ..utils import generate_address_webhook_call_args

ADDRESS_UPDATE_MUTATION = """
    mutation updateUserAddress($addressId: ID!, $address: AddressInput!) {
        addressUpdate(id: $addressId, input: $address) {
            address {
                city
            }
            user {
                id
            }
        }
    }
"""


def test_address_update_mutation(
    staff_api_client, customer_user, permission_manage_users, graphql_address_data
):
    query = ADDRESS_UPDATE_MUTATION
    address_obj = customer_user.addresses.first()
    assert staff_api_client.user not in address_obj.user_addresses.all()
    variables = {
        "addressId": graphene.Node.to_global_id("Address", address_obj.id),
        "address": graphql_address_data,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["addressUpdate"]
    assert data["address"]["city"] == graphql_address_data["city"].upper()
    address_obj.refresh_from_db()
    assert address_obj.city == graphql_address_data["city"].upper()
    customer_user.refresh_from_db()
    assert (
        generate_address_search_document_value(address_obj)
        in customer_user.search_document
    )


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_address_update_mutation_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    customer_user,
    permission_manage_users,
    graphql_address_data,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    address = customer_user.addresses.first()
    assert staff_api_client.user not in address.user_addresses.all()
    variables = {
        "addressId": graphene.Node.to_global_id("Address", address.id),
        "address": graphql_address_data,
    }

    # when
    response = staff_api_client.post_graphql(
        ADDRESS_UPDATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    address.refresh_from_db()

    # then
    assert content["data"]["addressUpdate"]
    mocked_webhook_trigger.assert_called_with(
        *generate_address_webhook_call_args(
            address,
            WebhookEventAsyncType.ADDRESS_UPDATED,
            staff_api_client.user,
            any_webhook,
        )
    )


@patch("saleor.graphql.account.mutations.base.prepare_user_search_document_value")
def test_address_update_mutation_no_user_assigned(
    prepare_user_search_document_value_mock,
    staff_api_client,
    address,
    permission_manage_users,
    graphql_address_data,
):
    # given
    query = ADDRESS_UPDATE_MUTATION

    variables = {
        "addressId": graphene.Node.to_global_id("Address", address.id),
        "address": graphql_address_data,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["addressUpdate"]
    assert data["address"]["city"] == graphql_address_data["city"].upper()
    prepare_user_search_document_value_mock.assert_not_called()


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
    response = user_api_client.post_graphql(ADDRESS_UPDATE_MUTATION, variables)
    assert_no_permission(response)
