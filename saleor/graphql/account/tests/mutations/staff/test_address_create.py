from unittest.mock import patch

import graphene
import pytest
from django.test import override_settings
from freezegun import freeze_time

from ......account.models import Address
from ......webhook.event_types import WebhookEventAsyncType
from .....tests.utils import get_graphql_content
from ..utils import generate_address_webhook_call_args

ADDRESS_CREATE_MUTATION = """
    mutation CreateUserAddress($user: ID!, $address: AddressInput!) {
        addressCreate(userId: $user, input: $address) {
            errors {
                field
                message
            }
            address {
                id
                city
                country {
                    code
                }
                metadata {
                    key
                    value
                }
            }
            user {
                id
            }
        }
    }
"""


def test_create_address_mutation(
    staff_api_client, customer_user, permission_manage_users, graphql_address_data
):
    # given
    query = ADDRESS_CREATE_MUTATION
    graphql_address_data["city"] = "Dummy"
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"user": user_id, "address": graphql_address_data}
    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    # then
    assert content["data"]["addressCreate"]["errors"] == []
    data = content["data"]["addressCreate"]
    assert data["address"]["city"] == "DUMMY"
    assert data["address"]["country"]["code"] == "PL"
    assert data["address"]["metadata"] == [{"key": "public", "value": "public_value"}]
    address_obj = Address.objects.get(city="DUMMY")

    assert address_obj.metadata == {"public": "public_value"}
    assert address_obj.user_addresses.first() == customer_user
    assert data["user"]["id"] == user_id

    customer_user.refresh_from_db()
    for field in ["city", "country"]:
        assert variables["address"][field].lower() in customer_user.search_document


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_address_mutation_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    customer_user,
    permission_manage_users,
    settings,
    graphql_address_data,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"user": user_id, "address": graphql_address_data}

    # when
    response = staff_api_client.post_graphql(
        ADDRESS_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    address = Address.objects.last()

    # then
    assert not content["data"]["addressCreate"]["errors"]
    assert content["data"]["addressCreate"]

    mocked_webhook_trigger.assert_called_once_with(
        *generate_address_webhook_call_args(
            address,
            WebhookEventAsyncType.ADDRESS_CREATED,
            staff_api_client.user,
            any_webhook,
        )
    )


@override_settings(MAX_USER_ADDRESSES=2)
def test_create_address_mutation_the_oldest_address_is_deleted(
    staff_api_client,
    customer_user,
    address,
    permission_manage_users,
    graphql_address_data,
):
    # given
    same_address = Address.objects.create(**address.as_data())
    customer_user.addresses.set([address, same_address])

    user_addresses_count = customer_user.addresses.count()
    graphql_address_data["city"] = "Dummy"
    query = ADDRESS_CREATE_MUTATION
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"user": user_id, "address": graphql_address_data}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["addressCreate"]["errors"] == []
    data = content["data"]["addressCreate"]
    assert data["address"]["city"] == "DUMMY"
    assert data["address"]["country"]["code"] == "PL"
    address_obj = Address.objects.get(city="DUMMY")
    assert address_obj.user_addresses.first() == customer_user
    assert data["user"]["id"] == user_id

    customer_user.refresh_from_db()
    assert customer_user.addresses.count() == user_addresses_count

    with pytest.raises(address._meta.model.DoesNotExist):
        address.refresh_from_db()


def test_create_address_validation_fails(
    staff_api_client,
    customer_user,
    graphql_address_data,
    permission_manage_users,
    address,
):
    # given
    query = ADDRESS_CREATE_MUTATION
    address_data = graphql_address_data
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data["postalCode"] = "wrong postal code"
    variables = {"user": user_id, "address": graphql_address_data}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["addressCreate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "postalCode"
    assert data["address"] is None
