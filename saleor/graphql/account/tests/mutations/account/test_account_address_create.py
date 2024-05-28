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
mutation($addressInput: AddressInput!, $addressType: AddressTypeEnum, $customerId: ID) {
  accountAddressCreate(
    input: $addressInput, type: $addressType, customerId: $customerId
  ) {
    address {
        id
        city
        metadata {
            key
            value
        }
        firstName
        postalCode
    }
    user {
        email
    }
    errors {
        code
        field
        addressType
        message
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

    address = user.addresses.exclude(id__in=user_addresses_ids).first()
    assert address.metadata == {"public": "public_value"}
    assert address.validation_skipped is False
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
        ),
        allow_replica=False,
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


def test_customer_create_address_skip_validation(
    user_api_client,
    graphql_address_data_skipped_validation,
):
    # given
    query = ACCOUNT_ADDRESS_CREATE_MUTATION
    address_data = graphql_address_data_skipped_validation
    invalid_postal_code = "invalid_postal_code"
    address_data["postalCode"] = invalid_postal_code
    variables = {"addressInput": address_data}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_account_address_create_by_app(
    app_api_client, graphql_address_data, permission_impersonate_user, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    new_first_name = "Andrew"
    graphql_address_data["firstName"] = new_first_name
    variables = {"addressInput": graphql_address_data, "customerId": customer_id}

    # when
    response = app_api_client.post_graphql(
        ACCOUNT_ADDRESS_CREATE_MUTATION,
        variables,
        permissions=[permission_impersonate_user],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["accountAddressCreate"]
    assert not data["errors"]
    assert data["address"]["firstName"] == new_first_name


def test_account_address_create_by_app_no_permissions(
    app_api_client, graphql_address_data, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"addressInput": graphql_address_data, "customerId": customer_id}

    # when
    response = app_api_client.post_graphql(ACCOUNT_ADDRESS_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_account_address_create_by_user_with_customer_id(
    user_api_client, graphql_address_data, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"addressInput": graphql_address_data, "customerId": customer_id}

    # when
    response = user_api_client.post_graphql(
        ACCOUNT_ADDRESS_CREATE_MUTATION,
        variables,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["accountAddressCreate"]
    assert not data["address"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "customerId"
    assert errors[0]["code"] == AccountErrorCode.INVALID.name


def test_account_address_create_by_app_invalid_customer_id(
    app_api_client, graphql_address_data, permission_impersonate_user, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("Address", customer_user.pk)
    variables = {"addressInput": graphql_address_data, "customerId": customer_id}

    # when
    response = app_api_client.post_graphql(
        ACCOUNT_ADDRESS_CREATE_MUTATION,
        variables,
        permissions=[permission_impersonate_user],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["accountAddressCreate"]
    assert not data["address"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "customerId"
    assert errors[0]["code"] == AccountErrorCode.GRAPHQL_ERROR.name


def test_account_address_create_by_app_no_customer_id(
    app_api_client, graphql_address_data, permission_impersonate_user
):
    # given
    variables = {"addressInput": graphql_address_data}

    # when
    response = app_api_client.post_graphql(
        ACCOUNT_ADDRESS_CREATE_MUTATION,
        variables,
        permissions=[permission_impersonate_user],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["accountAddressCreate"]
    assert not data["address"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "customerId"
    assert errors[0]["code"] == AccountErrorCode.REQUIRED.name


def test_account_address_create_by_app_skip_validation(
    app_api_client,
    permission_impersonate_user,
    customer_user,
    graphql_address_data_skipped_validation,
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    invalid_postal_code = "invalid postal code"
    address_data = graphql_address_data_skipped_validation
    address_data["postalCode"] = invalid_postal_code
    address_type = AddressType.SHIPPING.upper()
    variables = {
        "addressInput": address_data,
        "customerId": customer_id,
        "addressType": address_type,
    }

    # when
    response = app_api_client.post_graphql(
        ACCOUNT_ADDRESS_CREATE_MUTATION,
        variables,
        permissions=[permission_impersonate_user],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["accountAddressCreate"]
    assert not data["errors"]
    assert data["address"]["postalCode"] == invalid_postal_code
    customer_user.refresh_from_db()
    assert customer_user.default_shipping_address.postal_code == invalid_postal_code
    assert customer_user.default_shipping_address.validation_skipped is True


def test_account_address_create_by_app_skip_validation_no_permissions(
    app_api_client, customer_user, graphql_address_data_skipped_validation
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    invalid_postal_code = "invalid postal code"
    address_data = graphql_address_data_skipped_validation
    address_data["postalCode"] = invalid_postal_code
    address_type = AddressType.SHIPPING.upper()
    variables = {
        "addressInput": address_data,
        "customerId": customer_id,
        "addressType": address_type,
    }

    # when
    response = app_api_client.post_graphql(ACCOUNT_ADDRESS_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)
