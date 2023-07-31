from unittest.mock import ANY, patch
from urllib.parse import urlencode

from ......account import events as account_events
from ......account.error_codes import AccountErrorCode
from ......account.models import User
from ......account.notifications import get_default_user_payload
from ......account.search import (
    generate_address_search_document_value,
    generate_user_fields_search_document_value,
)
from ......core.notify_events import NotifyEventType
from ......core.tests.utils import get_site_context_payload
from ......core.utils.url import prepare_url
from .....tests.utils import get_graphql_content
from ....tests.utils import convert_dict_keys_to_camel_case

CUSTOMER_CREATE_MUTATION = """
    mutation CreateCustomer(
        $email: String, $firstName: String, $lastName: String, $channel: String
        $note: String, $billing: AddressInput, $shipping: AddressInput,
        $redirect_url: String, $languageCode: LanguageCodeEnum,
        $externalReference: String, $metadata: [MetadataInput!],
        $privateMetadata: [MetadataInput!],
    ) {
        customerCreate(input: {
            email: $email,
            firstName: $firstName,
            lastName: $lastName,
            note: $note,
            defaultShippingAddress: $shipping,
            defaultBillingAddress: $billing,
            redirectUrl: $redirect_url,
            languageCode: $languageCode,
            channel: $channel,
            externalReference: $externalReference
            metadata: $metadata, privateMetadata: $privateMetadata
        }) {
            errors {
                field
                code
                message
            }
            user {
                id
                defaultBillingAddress {
                    id
                    metadata {
                        key
                        value
                    }
                }
                defaultShippingAddress {
                    id
                    metadata {
                        key
                        value
                    }
                }
                languageCode
                email
                firstName
                lastName
                isActive
                isStaff
                note
                externalReference
                metadata {
                    key
                    value
                }
                privateMetadata {
                    key
                    value
                }
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.customer_metadata_updated")
@patch("saleor.account.notifications.default_token_generator.make_token")
@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.plugins.manager.PluginsManager.account_set_password_requested")
def test_customer_create(
    mocked_account_set_password_requested,
    mocked_notify,
    mocked_generator,
    mocked_customer_metadata_updated,
    staff_api_client,
    address,
    permission_manage_users,
    channel_PLN,
    site_settings,
):
    # given
    mocked_generator.return_value = "token"
    email = "api_user@example.com"
    first_name = "api_first_name"
    last_name = "api_last_name"
    note = "Test user"
    address_data = convert_dict_keys_to_camel_case(address.as_data())
    metadata = [{"key": "test key", "value": "test value"}]
    stored_metadata = {"test key": "test value"}
    address_data["metadata"] = metadata
    address_data.pop("privateMetadata")

    redirect_url = "https://www.example.com"
    external_reference = "test-ext-ref"
    private_metadata = [{"key": "private test key", "value": "private test value"}]
    variables = {
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "note": note,
        "shipping": address_data,
        "billing": address_data,
        "redirect_url": redirect_url,
        "languageCode": "PL",
        "channel": channel_PLN.slug,
        "externalReference": external_reference,
        "metadata": metadata,
        "privateMetadata": private_metadata,
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then
    content = get_graphql_content(response)

    new_customer = User.objects.get(email=email)

    shipping_address, billing_address = (
        new_customer.default_shipping_address,
        new_customer.default_billing_address,
    )
    assert shipping_address == billing_address
    assert billing_address.metadata == stored_metadata
    assert shipping_address.metadata == stored_metadata
    assert shipping_address.pk != billing_address.pk

    data = content["data"]["customerCreate"]
    assert data["errors"] == []
    assert data["user"]["email"] == email
    assert data["user"]["firstName"] == first_name
    assert data["user"]["lastName"] == last_name
    assert data["user"]["note"] == note
    assert data["user"]["languageCode"] == "PL"
    assert data["user"]["externalReference"] == external_reference
    assert not data["user"]["isStaff"]
    assert data["user"]["isActive"]
    assert data["user"]["metadata"] == metadata
    assert data["user"]["privateMetadata"] == private_metadata
    assert data["user"]["defaultShippingAddress"]["metadata"] == metadata
    assert data["user"]["defaultBillingAddress"]["metadata"] == metadata

    new_user = User.objects.get(email=email)
    assert (
        generate_user_fields_search_document_value(new_user) in new_user.search_document
    )
    assert generate_address_search_document_value(address) in new_user.search_document
    params = urlencode({"email": new_user.email, "token": "token"})
    password_set_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(new_user),
        "token": "token",
        "password_set_url": password_set_url,
        "recipient_email": new_user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_SET_CUSTOMER_PASSWORD,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )
    mocked_customer_metadata_updated.assert_called_once_with(new_user)

    assert set([shipping_address, billing_address]) == set(new_user.addresses.all())
    customer_creation_event = account_events.CustomerEvent.objects.get()
    assert customer_creation_event.type == account_events.CustomerEvents.ACCOUNT_CREATED
    assert customer_creation_event.user == new_customer

    mocked_account_set_password_requested.assert_called_once_with(
        new_user, channel_PLN.slug, "token", password_set_url
    )


@patch("saleor.account.notifications.default_token_generator.make_token")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_customer_create_send_password_with_url(
    mocked_notify,
    mocked_generator,
    staff_api_client,
    permission_manage_users,
    channel_PLN,
    site_settings,
):
    mocked_generator.return_value = "token"
    email = "api_user@example.com"
    variables = {
        "email": email,
        "redirect_url": "https://www.example.com",
        "channel": channel_PLN.slug,
    }

    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert not data["errors"]

    new_customer = User.objects.get(email=email)
    assert new_customer
    redirect_url = "https://www.example.com"
    params = urlencode({"email": email, "token": "token"})
    password_set_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(new_customer),
        "password_set_url": password_set_url,
        "token": "token",
        "recipient_email": new_customer.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }
    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_SET_CUSTOMER_PASSWORD,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )


def test_customer_create_empty_metadata_key(
    staff_api_client,
    address,
    permission_manage_users,
    channel_PLN,
    site_settings,
):
    # then
    email = "api_user@example.com"
    first_name = "api_first_name"
    last_name = "api_last_name"
    note = "Test user"
    address_data = convert_dict_keys_to_camel_case(address.as_data())
    address_data.pop("metadata")
    address_data.pop("privateMetadata")

    redirect_url = "https://www.example.com"
    external_reference = "test-ext-ref"
    metadata = [{"key": "", "value": "test value"}]
    variables = {
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "note": note,
        "shipping": address_data,
        "billing": address_data,
        "redirect_url": redirect_url,
        "languageCode": "PL",
        "channel": channel_PLN.slug,
        "externalReference": external_reference,
        "metadata": metadata,
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["customerCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == AccountErrorCode.REQUIRED.name


def test_customer_create_without_send_password(
    staff_api_client, permission_manage_users
):
    email = "api_user@example.com"
    variables = {"email": email}
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert not data["errors"]
    User.objects.get(email=email)


def test_customer_create_with_invalid_url(staff_api_client, permission_manage_users):
    email = "api_user@example.com"
    variables = {"email": email, "redirect_url": "invalid"}
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert data["errors"][0] == {
        "field": "redirectUrl",
        "code": AccountErrorCode.INVALID.name,
        "message": ANY,
    }
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_customer_create_with_not_allowed_url(
    staff_api_client, permission_manage_users
):
    email = "api_user@example.com"
    variables = {"email": email, "redirect_url": "https://www.fake.com"}
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert data["errors"][0] == {
        "field": "redirectUrl",
        "code": AccountErrorCode.INVALID.name,
        "message": ANY,
    }
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_customer_create_with_upper_case_email(
    staff_api_client, permission_manage_users
):
    # given
    email = "UPPERCASE@example.com"
    variables = {"email": email}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["customerCreate"]
    assert not data["errors"]
    assert data["user"]["email"] == email.lower()


def test_customer_create_with_non_unique_external_reference(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    ext_ref = "test-ext-ref"
    customer_user.external_reference = ext_ref
    customer_user.save(update_fields=["external_reference"])

    variables = {"email": "mail.test@exampale.com", "externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["customerCreate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == AccountErrorCode.UNIQUE.name
    assert error["message"] == "User with this External reference already exists."


@patch("saleor.account.notifications.default_token_generator.make_token")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_customer_create_webhook_event_triggered(
    mocked_trigger_webhooks_async,
    mocked_generator,
    settings,
    user_api_client,
    subscription_account_set_password_requested_webhook,
    staff_api_client,
    address,
    channel_PLN,
    permission_manage_users,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mocked_generator.return_value = "token"
    email = "api_user@example.com"
    address_data = convert_dict_keys_to_camel_case(address.as_data())
    address_data.pop("privateMetadata")

    variables = {
        "email": email,
        "firstName": "api_first_name",
        "lastName": "api_last_name",
        "note": "Test user",
        "shipping": address_data,
        "billing": address_data,
        "redirect_url": "https://www.example.com",
        "languageCode": "PL",
        "channel": channel_PLN.slug,
        "externalReference": "test-ext-ref",
    }

    # when
    staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then
    User.objects.get(email=email)
    mocked_trigger_webhooks_async.assert_called()
