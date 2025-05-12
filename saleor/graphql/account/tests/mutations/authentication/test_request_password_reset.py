import datetime
from unittest.mock import patch
from urllib.parse import urlencode

from django.utils import timezone
from freezegun import freeze_time

from ......account.notifications import get_default_user_payload
from ......core.notify import NotifyEventType
from ......core.tests.utils import get_site_context_payload
from ......core.tokens import token_generator
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
    api_client,
    customer_user,
    channel_PLN,
    channel_USD,
    site_settings,
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    token = token_generator.make_token(customer_user)
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

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_PASSWORD_RESET
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug

    customer_user.refresh_from_db()
    assert customer_user.last_password_reset_request == timezone.now()

    mocked_account_set_password_requested.assert_called_once_with(
        customer_user, channel_PLN.slug, token, reset_url
    )


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_on_cooldown(
    mocked_notify, api_client, customer_user, channel_PLN
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    user = customer_user
    user.last_password_reset_request = timezone.now()
    user.save(update_fields=["last_password_reset_request"])

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["requestPasswordReset"]["errors"]
    assert not errors
    mocked_notify.assert_not_called()


@freeze_time("2018-05-31 12:00:01")
def test_account_reset_password_after_cooldown(
    api_client, customer_user, channel_PLN, settings
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }
    user = customer_user
    user.last_password_reset_request = timezone.now() - datetime.timedelta(
        seconds=settings.RESET_PASSWORD_LOCK_TIME
    )
    user.save(update_fields=["last_password_reset_request"])

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["requestPasswordReset"]["errors"] == []


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_with_upper_case_email(
    mocked_notify,
    api_client,
    customer_user,
    channel_PLN,
    channel_USD,
    site_settings,
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email.upper(),
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    token = token_generator.make_token(customer_user)
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

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_PASSWORD_RESET
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_request_password_reset_email_for_staff(
    mocked_notify,
    api_client,
    channel_USD,
    site_settings,
    staff_user,
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "email": staff_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_USD.slug,
    }
    user = staff_user

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    token = token_generator.make_token(user)
    params = urlencode({"email": user.email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(user),
        "reset_url": reset_url,
        "token": token,
        "recipient_email": user.email,
        "channel_slug": channel_USD.slug,
        **get_site_context_payload(site_settings.site),
    }

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_STAFF_RESET_PASSWORD
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_USD.slug


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_invalid_email(mocked_notify, api_client, channel_USD):
    # given
    variables = {
        "email": "non-existing-email@email.com",
        "redirectUrl": "https://www.example.com",
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    mocked_notify.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_user_is_inactive(
    mocked_notify, api_client, customer_user, channel_USD
):
    # given
    user = customer_user
    user.is_active = False
    user.save()

    variables = {
        "email": customer_user.email,
        "redirectUrl": "https://www.example.com",
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    mocked_notify.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_storefront_hosts_not_allowed(
    mocked_notify, api_client, customer_user, channel_USD
):
    # given
    variables = {
        "email": customer_user.email,
        "redirectUrl": "https://www.fake.com",
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestPasswordReset"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "redirectUrl"
    mocked_notify.assert_not_called()


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_all_storefront_hosts_allowed(
    mocked_notify,
    api_client,
    customer_user,
    settings,
    channel_PLN,
    channel_USD,
    site_settings,
):
    # given
    settings.ALLOWED_CLIENT_HOSTS = ["*"]
    redirect_url = "https://www.test.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]

    token = token_generator.make_token(customer_user)
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
    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_PASSWORD_RESET
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_account_reset_password_subdomain(
    mocked_notify, api_client, customer_user, settings, channel_PLN, site_settings
):
    # given
    settings.ALLOWED_CLIENT_HOSTS = [".example.com"]
    redirect_url = "https://sub.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]

    token = token_generator.make_token(customer_user)
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

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_PASSWORD_RESET
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug


@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_account_reset_password_event_triggered(
    mocked_trigger_webhooks_async,
    settings,
    api_client,
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
    api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)

    # then
    mocked_trigger_webhooks_async.assert_called()


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.plugins.manager.PluginsManager.account_set_password_requested")
def test_account_reset_password_for_not_confirmed_user(
    mocked_account_set_password_requested,
    mocked_notify,
    api_client,
    customer_user,
    channel_PLN,
    channel_USD,
    site_settings,
):
    # given
    customer_user.is_confirmed = False
    customer_user.save(update_fields=["is_confirmed"])

    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
        "channel": channel_PLN.slug,
    }

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    token = token_generator.make_token(customer_user)
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

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_PASSWORD_RESET
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug

    user = customer_user
    user.refresh_from_db()
    assert user.last_password_reset_request == timezone.now()

    mocked_account_set_password_requested.assert_called_once_with(
        user, channel_PLN.slug, token, reset_url
    )


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.plugins.manager.PluginsManager.account_set_password_requested")
@patch("saleor.account.tasks.logger.warning")
def test_account_reset_password_no_channel_provided_multiple_channels(
    mocked_logger_warning,
    mocked_account_set_password_requested,
    mocked_notify,
    api_client,
    customer_user,
    channel_PLN,
    channel_USD,
    site_settings,
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
    }

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    token = token_generator.make_token(customer_user)
    params = urlencode({"email": customer_user.email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "reset_url": reset_url,
        "token": token,
        "recipient_email": customer_user.email,
        "channel_slug": None,
        **get_site_context_payload(site_settings.site),
    }

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_PASSWORD_RESET
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] is None

    customer_user.refresh_from_db()
    assert customer_user.last_password_reset_request == timezone.now()

    mocked_account_set_password_requested.assert_called_once_with(
        customer_user, None, token, reset_url
    )

    mocked_logger_warning.assert_called_once_with(
        "Channel slug was not provided for user %s in request password reset.",
        customer_user.pk,
    )


@freeze_time("2018-05-31 12:00:01")
@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.plugins.manager.PluginsManager.account_set_password_requested")
@patch("saleor.account.tasks.logger.warning")
def test_account_reset_password_no_channel_provided_one_channel(
    mocked_logger_warning,
    mocked_account_set_password_requested,
    mocked_notify,
    api_client,
    customer_user,
    channel_USD,
    site_settings,
):
    # given
    redirect_url = "https://www.example.com"
    variables = {
        "email": customer_user.email,
        "redirectUrl": redirect_url,
    }

    # when
    response = api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    token = token_generator.make_token(customer_user)
    params = urlencode({"email": customer_user.email, "token": token})
    reset_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(customer_user),
        "reset_url": reset_url,
        "token": token,
        "recipient_email": customer_user.email,
        "channel_slug": channel_USD.slug,
        **get_site_context_payload(site_settings.site),
    }

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_PASSWORD_RESET
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_USD.slug

    customer_user.refresh_from_db()
    assert customer_user.last_password_reset_request == timezone.now()

    mocked_account_set_password_requested.assert_called_once_with(
        customer_user, channel_USD.slug, token, reset_url
    )

    mocked_logger_warning.assert_not_called()
