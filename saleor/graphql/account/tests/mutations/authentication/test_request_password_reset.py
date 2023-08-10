import datetime
from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from freezegun import freeze_time

from ......account.error_codes import AccountErrorCode
from ......account.notifications import get_default_user_payload
from ......core.notify_events import NotifyEventType
from ......core.tests.utils import get_site_context_payload
from ......core.utils.url import prepare_url
from .....tests.utils import get_graphql_content

REQUEST_PASSWORD_RESET_MUTATION = """
    mutation RequestPasswordReset(
        $email: String!, $redirectUrl: String!, $channel: String) {
        requestPasswordReset(
            email: $email, redirectUrl: $redirectUrl, channel: $channel) {
            errors {
                field
                message
                code
            }
        }
    }
"""


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.plugins.manager.PluginsManager.account_set_password_requested")
def test_account_reset_password(
    mocked_account_set_password_requested,
    mocked_notify,
    user_api_client,
    customer_user,
    channel_PLN,
    channel_USD,
    site_settings,
):
    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    token = default_token_generator.make_token(customer_user)
    params = urlencode({"email": customer_user.email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "reset_url": reset_url,
        "token": token,
        "recipient_email": customer_user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_PASSWORD_RESET,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )
    user = user_api_client.user
    user.refresh_from_db()
    assert user.last_password_reset_request == timezone.now()

    mocked_account_set_password_requested.assert_called_once_with(
        user, channel_PLN.slug, token, reset_url
    )


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_on_cooldown(
    mocked_notify, user_api_client, customer_user, channel_PLN
):
    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    user = user_api_client.user
    user.last_password_reset_request = timezone.now()
    user.save(update_fields=["last_password_reset_request"])
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    errors = content["data"]["requestPasswordReset"]["errors"]
    assert errors == [
        {
            "field": "email",
            "message": "Password reset already requested",
            "code": AccountErrorCode.PASSWORD_RESET_ALREADY_REQUESTED.name,
        }
    ]
    mocked_notify.assert_not_called()


@freeze_time("2018-05-31 12:00:01")
def test_account_reset_password_after_cooldown(
    user_api_client, customer_user, channel_PLN, settings
):
    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    user = user_api_client.user
    user.last_password_reset_request = timezone.now() - datetime.timedelta(
        seconds=settings.RESET_PASSWORD_LOCK_TIME
    )
    user.save(update_fields=["last_password_reset_request"])
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["requestPasswordReset"]["errors"] == []


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_with_upper_case_email(
    mocked_notify,
    user_api_client,
    customer_user,
    channel_PLN,
    channel_USD,
    site_settings,
):
    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email.upper(),
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    token = default_token_generator.make_token(customer_user)
    params = urlencode({"email": customer_user.email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "reset_url": reset_url,
        "token": token,
        "recipient_email": customer_user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_PASSWORD_RESET,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_request_password_reset_email_for_staff(
    mocked_notify, staff_api_client, channel_USD, site_settings
):
    redirect_url = "https://www.example.com"
    variables = {"email": staff_api_client.user.email, "redirectUrl": redirect_url}
    response = staff_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    token = default_token_generator.make_token(staff_api_client.user)
    params = urlencode({"email": staff_api_client.user.email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(staff_api_client.user),
        "reset_url": reset_url,
        "token": token,
        "recipient_email": staff_api_client.user.email,
        "channel_slug": None,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_STAFF_RESET_PASSWORD,
        payload=expected_payload,
        channel_slug=None,
    )


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_invalid_email(
    mocked_notify, user_api_client, channel_USD
):
    variables = {
        "email": "non-existing-email@email.com",
        "redirectUrl": "https://www.example.com",
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert len(data["errors"]) == 1
    mocked_notify.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_user_is_inactive(
    mocked_notify, user_api_client, customer_user, channel_USD
):
    user = customer_user
    user.is_active = False
    user.save()

    variables = {
        "email": customer_user.email,
        "redirectUrl": "https://www.example.com",
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    results = response.json()
    assert "errors" in results
    assert (
        results["errors"][0]["message"]
        == "Invalid token. User does not exist or is inactive."
    )
    assert not mocked_notify.called


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_storefront_hosts_not_allowed(
    mocked_notify, user_api_client, customer_user, channel_USD
):
    variables = {
        "email": customer_user.email,
        "redirectUrl": "https://www.fake.com",
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "redirectUrl"
    mocked_notify.assert_not_called()


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_all_storefront_hosts_allowed(
    mocked_notify,
    user_api_client,
    customer_user,
    settings,
    channel_PLN,
    channel_USD,
    site_settings,
):
    settings.ALLOWED_CLIENT_HOSTS = ["*"]
    redirect_url = "https://www.test.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]

    token = default_token_generator.make_token(customer_user)
    params = urlencode({"email": customer_user.email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "reset_url": reset_url,
        "token": token,
        "recipient_email": customer_user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_PASSWORD_RESET,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_subdomain(
    mocked_notify, user_api_client, customer_user, settings, channel_PLN, site_settings
):
    settings.ALLOWED_CLIENT_HOSTS = [".example.com"]
    redirect_url = "https://sub.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]

    token = default_token_generator.make_token(customer_user)
    params = urlencode({"email": customer_user.email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "reset_url": reset_url,
        "token": token,
        "recipient_email": customer_user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    mocked_notify.assert_called_once_with(
        NotifyEventType.ACCOUNT_PASSWORD_RESET,
        payload=expected_payload,
        channel_slug=channel_PLN.slug,
    )


@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_account_reset_password_event_triggered(
    mocked_trigger_webhooks_async,
    settings,
    user_api_client,
    customer_user,
    channel_PLN,
    subscription_account_set_password_requested_webhook,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    redirect_url = "https://www.example.com"

    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }

    # when
    user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)

    # then
    mocked_trigger_webhooks_async.assert_called()
