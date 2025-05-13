from unittest.mock import patch
from urllib.parse import urlencode

from django.db import IntegrityError
from django.test import override_settings

from ......account import events as account_events
from ......account.error_codes import AccountErrorCode
from ......account.models import User
from ......account.notifications import get_default_user_payload
from ......account.search import generate_user_fields_search_document_value
from ......core.notify import NotifyEventType
from ......core.tests.utils import get_site_context_payload
from ......core.tokens import token_generator
from ......core.utils.url import prepare_url
from .....tests.utils import get_graphql_content

ACCOUNT_REGISTER_MUTATION = """
    mutation RegisterAccount(
        $input: AccountRegisterInput!
    ) {
        accountRegister(
            input: $input
        ) {
            errors {
                field
                message
                code
            }
            user {
                id
                email
            }
        }
    }
"""


@override_settings(
    ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL=True, ALLOWED_CLIENT_HOSTS=["localhost"]
)
@patch("saleor.account.notifications.token_generator.make_token")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_customer_register(
    mocked_notify,
    mocked_generator,
    api_client,
    channel_PLN,
    order,
    site_settings,
):
    # given
    mocked_generator.return_value = "token"
    email = "customer@example.com"

    redirect_url = "http://localhost:3000"
    variables = {
        "input": {
            "email": email,
            "password": "Password",
            "redirectUrl": redirect_url,
            "firstName": "saleor",
            "lastName": "rocks",
            "languageCode": "PL",
            "metadata": [{"key": "meta", "value": "data"}],
            "channel": channel_PLN.slug,
        }
    }
    query = ACCOUNT_REGISTER_MUTATION
    mutation_name = "accountRegister"

    # when
    response = api_client.post_graphql(query, variables)

    # then
    new_user = User.objects.get(email=email)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    params = urlencode({"email": email, "token": "token"})
    confirm_url = prepare_url(params, redirect_url)

    expected_payload = {
        "user": get_default_user_payload(new_user),
        "token": "token",
        "confirm_url": confirm_url,
        "recipient_email": new_user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }
    assert new_user.metadata == {"meta": "data"}
    assert new_user.language_code == "pl"
    assert new_user.first_name == variables["input"]["firstName"]
    assert new_user.last_name == variables["input"]["lastName"]
    assert new_user.search_document == generate_user_fields_search_document_value(
        new_user
    )
    assert not data["errors"]
    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_CONFIRMATION
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert data["errors"]
    assert data["errors"][0]["field"] == "email"
    assert data["errors"][0]["code"] == AccountErrorCode.UNIQUE.name

    customer_creation_event = account_events.CustomerEvent.objects.get()
    assert customer_creation_event.type == account_events.CustomerEvents.ACCOUNT_CREATED
    assert customer_creation_event.user == new_user


@override_settings(
    ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL=True, ALLOWED_CLIENT_HOSTS=["localhost"]
)
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_customer_register_generates_valid_token(
    mocked_notify,
    api_client,
    channel_PLN,
    order,
    site_settings,
):
    # given
    email = "customer@example.com"
    redirect_url = "http://localhost:3000"
    variables = {
        "input": {
            "email": email,
            "password": "Password",
            "redirectUrl": redirect_url,
            "firstName": "saleor",
            "lastName": "rocks",
            "languageCode": "PL",
            "metadata": [{"key": "meta", "value": "data"}],
            "channel": channel_PLN.slug,
        }
    }

    # when
    response = api_client.post_graphql(ACCOUNT_REGISTER_MUTATION, variables)
    new_user = User.objects.get(email=email)
    content = get_graphql_content(response)
    data = content["data"]["accountRegister"]

    # then
    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_kwargs = call_args.kwargs
    token = called_kwargs["payload_func"]()["token"]
    assert called_kwargs["channel_slug"] == channel_PLN.slug

    assert not data["errors"]
    assert token_generator.check_token(new_user, token)


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_customer_register_disabled_email_confirmation(
    mocked_notify, api_client, site_settings
):
    # given
    site_settings.enable_account_confirmation_by_email = False
    site_settings.save(update_fields=["enable_account_confirmation_by_email"])

    email = "customer@example.com"
    variables = {"input": {"email": email, "password": "Password"}}

    #   when
    response = api_client.post_graphql(ACCOUNT_REGISTER_MUTATION, variables)
    errors = response.json()["data"]["accountRegister"]["errors"]

    # then
    assert errors == []
    created_user = User.objects.get()
    expected_payload = get_default_user_payload(created_user)
    expected_payload["token"] = "token"
    expected_payload["redirect_url"] = "http://localhost:3000"
    mocked_notify.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_customer_register_no_redirect_url(mocked_notify, api_client, site_settings):
    # given
    site_settings.enable_account_confirmation_by_email = True
    site_settings.save(update_fields=["enable_account_confirmation_by_email"])

    variables = {"input": {"email": "customer@example.com", "password": "Password"}}

    #   when
    response = api_client.post_graphql(ACCOUNT_REGISTER_MUTATION, variables)
    errors = response.json()["data"]["accountRegister"]["errors"]

    # then
    assert "redirectUrl" in map(lambda error: error["field"], errors)
    mocked_notify.assert_not_called()


@override_settings(ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL=False)
def test_customer_register_upper_case_email(api_client, site_settings):
    # given
    site_settings.enable_account_confirmation_by_email = False
    site_settings.save(update_fields=["enable_account_confirmation_by_email"])

    email = "CUSTOMER@example.com"
    variables = {"input": {"email": email, "password": "Password"}}

    # when
    response = api_client.post_graphql(ACCOUNT_REGISTER_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["accountRegister"]
    assert not data["errors"]
    assert data["user"]["email"].lower()


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_customer_register_no_channel_email_confirmation_unset(
    mocked_notify, api_client, channel_PLN, site_settings
):
    # given
    site_settings.enable_account_confirmation_by_email = False
    site_settings.save(update_fields=["enable_account_confirmation_by_email"])

    email = "customer@example.com"
    redirect_url = "http://localhost:3000"
    variables = {
        "input": {
            "email": email,
            "password": "Password",
            "redirectUrl": redirect_url,
            "firstName": "saleor",
            "lastName": "rocks",
            "languageCode": "PL",
            "metadata": [{"key": "meta", "value": "data"}],
        }
    }

    # when
    response = api_client.post_graphql(ACCOUNT_REGISTER_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountRegister"]

    # then
    data = content["data"]["accountRegister"]
    assert not data["errors"]
    assert data["user"]["email"].lower()
    mocked_notify.assert_not_called()


@patch("saleor.account.models.User.save")
def test_account_register_race_condition(
    mocked_user_save, api_client, site_settings, customer_user
):
    # given
    site_settings.enable_account_confirmation_by_email = False
    site_settings.save(update_fields=["enable_account_confirmation_by_email"])

    email_to_create = "test-user@example.com"

    variables = {
        "input": {
            "email": email_to_create,
            "password": "Password",
            "firstName": "John",
            "lastName": "Doe",
        }
    }

    # Mock that first save() call raises IntegrityError
    mocked_user_save.side_effect = IntegrityError(
        "User with this Email already exists."
    )

    # Make sure User.objects.get raises DoesNotExist to bypass the race condition check
    with patch("saleor.account.models.User.objects.get") as mocked_user_get:
        mocked_user_get.return_value = customer_user

        # when
        response = api_client.post_graphql(ACCOUNT_REGISTER_MUTATION, variables)

        # then
        content = get_graphql_content(response)
        errors_list = content["data"]["accountRegister"]["errors"]

        # Should reraise IntegrityError
        assert len(errors_list) == 1
        assert errors_list[0]["field"] == "email"
        assert errors_list[0]["code"] == AccountErrorCode.UNIQUE.name
        assert errors_list[0]["message"] == "User with this Email already exists."
