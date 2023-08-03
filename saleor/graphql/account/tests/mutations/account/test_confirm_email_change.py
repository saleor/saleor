from datetime import timedelta
from unittest.mock import patch

from ......core.jwt import create_token
from .....tests.utils import get_graphql_content

EMAIL_UPDATE_QUERY = """
mutation emailUpdate($token: String!, $channel: String) {
    confirmEmailChange(token: $token, channel: $channel){
        user {
            email
        }
        errors {
            code
            message
            field
        }
  }
}
"""


@patch(
    "saleor.graphql.account.mutations.account.confirm_email_change.match_orders_with_new_user"
)
@patch(
    "saleor.graphql.account.mutations.account.confirm_email_change.assign_user_gift_cards"
)
@patch("saleor.plugins.manager.PluginsManager.account_email_changed")
def test_email_update(
    mocked_account_email_changed,
    assign_gift_cards_mock,
    assign_orders_mock,
    user_api_client,
    customer_user,
    channel_PLN,
):
    new_email = "new_email@example.com"
    payload = {
        "old_email": customer_user.email,
        "new_email": new_email,
        "user_pk": customer_user.pk,
    }
    user = user_api_client.user

    token = create_token(payload, timedelta(hours=1))
    variables = {"token": token, "channel": channel_PLN.slug}
    response = user_api_client.post_graphql(EMAIL_UPDATE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["confirmEmailChange"]
    assert data["user"]["email"] == new_email
    user.refresh_from_db()
    assert new_email in user.search_document
    assign_gift_cards_mock.assert_called_once_with(customer_user)
    assign_orders_mock.assert_called_once_with(customer_user)
    mocked_account_email_changed.assert_called_once_with(user)


def test_email_update_to_existing_email(user_api_client, customer_user, staff_user):
    payload = {
        "old_email": customer_user.email,
        "new_email": staff_user.email,
        "user_pk": customer_user.pk,
    }
    token = create_token(payload, timedelta(hours=1))
    variables = {"token": token}

    response = user_api_client.post_graphql(EMAIL_UPDATE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["confirmEmailChange"]
    assert not data["user"]
    assert data["errors"] == [
        {
            "code": "UNIQUE",
            "message": "Email is used by other user.",
            "field": "newEmail",
        }
    ]


@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_account_email_changed_webhook_event_triggered(
    mocked_trigger_webhooks_async,
    settings,
    customer_user,
    user_api_client,
    subscription_account_email_changed_webhook,
    channel_PLN,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    new_email = "new_email@example.com"
    payload = {
        "old_email": customer_user.email,
        "new_email": new_email,
        "user_pk": customer_user.pk,
    }
    user = user_api_client.user

    token = create_token(payload, timedelta(hours=1))
    variables = {"token": token, "channel": channel_PLN.slug}

    # when
    user_api_client.post_graphql(EMAIL_UPDATE_QUERY, variables)

    # then
    user.refresh_from_db()
    assert new_email in user.search_document

    mocked_trigger_webhooks_async.assert_called()
