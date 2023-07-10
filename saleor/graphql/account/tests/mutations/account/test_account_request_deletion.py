from unittest.mock import ANY, patch
from urllib.parse import urlencode

from django.utils import timezone
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......account.notifications import get_default_user_payload
from ......core.notify_events import NotifyEventType
from ......core.tests.utils import get_site_context_payload
from ......core.tokens import account_delete_token_generator
from ......core.utils.url import prepare_url
from .....tests.utils import assert_no_permission, get_graphql_content

ACCOUNT_REQUEST_DELETION_MUTATION = """
    mutation accountRequestDeletion($redirectUrl: String!, $channel: String) {
        accountRequestDeletion(redirectUrl: $redirectUrl, channel: $channel) {
            errors {
                field
                code
                message
            }
        }
    }
"""


@patch("saleor.account.notifications.account_delete_token_generator.make_token")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_request_deletion(
    mocked_notify, mocked_token, user_api_client, channel_PLN, site_settings
):
    mocked_token.return_value = "token"
    user = user_api_client.user
    redirect_url = "https://www.example.com"
    variables = {"redirectUrl": redirect_url, "channel": channel_PLN.slug}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert not data["errors"]
    params = urlencode({"token": "token"})
    delete_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(user),
        "delete_url": delete_url,
        "token": "token",
        "recipient_email": user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_DELETE,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )


@patch("saleor.account.notifications.account_delete_token_generator.make_token")
@patch("saleor.plugins.manager.PluginsManager.account_delete_requested")
def test_account_request_deletion_send_account_delete_requested_event(
    account_delete_requested_mock,
    mocked_token,
    user_api_client,
    channel_PLN,
    site_settings,
):
    mocked_token.return_value = "token"
    user = user_api_client.user
    redirect_url = "https://www.example.com"
    variables = {"redirectUrl": redirect_url, "channel": channel_PLN.slug}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert not data["errors"]
    params = urlencode({"token": "token"})
    delete_url = prepare_url(params, redirect_url)

    account_delete_requested_mock.assert_called_once_with(
        user,
        channel_PLN.slug,
        "token",
        delete_url,
    )


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_request_deletion_token_validation(
    mocked_notify, user_api_client, channel_PLN, site_settings
):
    user = user_api_client.user
    token = account_delete_token_generator.make_token(user)
    redirect_url = "https://www.example.com"
    variables = {"redirectUrl": redirect_url, "channel": channel_PLN.slug}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert not data["errors"]
    params = urlencode({"token": token})
    delete_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(user),
        "delete_url": delete_url,
        "token": token,
        "recipient_email": user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_DELETE,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_request_deletion_anonymous_user(mocked_notify, api_client):
    variables = {"redirectUrl": "https://www.example.com"}
    response = api_client.post_graphql(ACCOUNT_REQUEST_DELETION_MUTATION, variables)
    assert_no_permission(response)
    mocked_notify.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_request_deletion_storefront_hosts_not_allowed(
    mocked_notify, user_api_client
):
    variables = {"redirectUrl": "https://www.fake.com"}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": "redirectUrl",
        "code": AccountErrorCode.INVALID.name,
        "message": ANY,
    }
    mocked_notify.assert_not_called()


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_request_deletion_all_storefront_hosts_allowed(
    mocked_notify, user_api_client, settings, channel_PLN, site_settings
):
    user = user_api_client.user
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    token = account_delete_token_generator.make_token(user)
    settings.ALLOWED_CLIENT_HOSTS = ["*"]
    redirect_url = "https://www.test.com"
    variables = {"redirectUrl": redirect_url, "channel": channel_PLN.slug}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert not data["errors"]

    params = urlencode({"token": token})
    delete_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(user),
        "delete_url": delete_url,
        "token": token,
        "recipient_email": user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_DELETE,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_request_deletion_subdomain(
    mocked_notify, user_api_client, settings, channel_PLN, site_settings
):
    user = user_api_client.user
    token = account_delete_token_generator.make_token(user)
    settings.ALLOWED_CLIENT_HOSTS = [".example.com"]
    redirect_url = "https://sub.example.com"
    variables = {"redirectUrl": redirect_url, "channel": channel_PLN.slug}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert not data["errors"]
    params = urlencode({"token": token})
    delete_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(user),
        "delete_url": delete_url,
        "token": token,
        "recipient_email": user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_DELETE,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )
