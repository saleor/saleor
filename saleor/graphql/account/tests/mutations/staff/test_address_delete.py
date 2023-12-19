from unittest.mock import patch

import graphene
import pytest
from freezegun import freeze_time

from ......account.search import generate_address_search_document_value
from ......webhook.event_types import WebhookEventAsyncType
from .....tests.utils import assert_no_permission, get_graphql_content
from ..utils import generate_address_webhook_call_args

ADDRESS_DELETE_MUTATION = """
    mutation deleteUserAddress($id: ID!) {
        addressDelete(id: $id) {
            address {
                city
            }
            user {
                id
            }
        }
    }
"""


def test_address_delete_mutation(
    staff_api_client, customer_user, permission_manage_users
):
    query = ADDRESS_DELETE_MUTATION
    address_obj = customer_user.addresses.first()
    variables = {"id": graphene.Node.to_global_id("Address", address_obj.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["addressDelete"]
    assert data["address"]["city"] == address_obj.city
    assert data["user"]["id"] == graphene.Node.to_global_id("User", customer_user.pk)
    with pytest.raises(address_obj._meta.model.DoesNotExist):
        address_obj.refresh_from_db()

    customer_user.refresh_from_db()
    assert (
        generate_address_search_document_value(address_obj)
        not in customer_user.search_document
    )


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_address_delete_mutation_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    customer_user,
    permission_manage_users,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    address = customer_user.addresses.first()
    variables = {"id": graphene.Node.to_global_id("Address", address.id)}

    # when
    response = staff_api_client.post_graphql(
        ADDRESS_DELETE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["addressDelete"]
    mocked_webhook_trigger.assert_called_once_with(
        *generate_address_webhook_call_args(
            address,
            WebhookEventAsyncType.ADDRESS_DELETED,
            staff_api_client.user,
            any_webhook,
        ),
        allow_replica=False,
    )


def test_address_delete_mutation_as_app(
    app_api_client, customer_user, permission_manage_users
):
    query = ADDRESS_DELETE_MUTATION
    address_obj = customer_user.addresses.first()
    variables = {"id": graphene.Node.to_global_id("Address", address_obj.id)}
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["addressDelete"]
    assert data["address"]["city"] == address_obj.city
    assert data["user"]["id"] == graphene.Node.to_global_id("User", customer_user.pk)
    with pytest.raises(address_obj._meta.model.DoesNotExist):
        address_obj.refresh_from_db()


def test_customer_delete_address_for_other(
    user_api_client, customer_user, address_other_country
):
    address_obj = address_other_country
    assert customer_user not in address_obj.user_addresses.all()
    variables = {"id": graphene.Node.to_global_id("Address", address_obj.id)}
    response = user_api_client.post_graphql(ADDRESS_DELETE_MUTATION, variables)
    assert_no_permission(response)
    address_obj.refresh_from_db()
