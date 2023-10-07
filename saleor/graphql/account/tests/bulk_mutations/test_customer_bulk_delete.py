from unittest.mock import patch

import graphene

from .....account.models import User
from ....tests.utils import get_graphql_content

CUSTOMER_BULK_DELETE_MUTATION = """
    mutation customerBulkDelete($ids: [ID!]!) {
        customerBulkDelete(ids: $ids) {
            count
        }
    }
"""


@patch("saleor.graphql.account.mutations.base.account_events.customer_deleted_event")
def test_delete_customers(
    mocked_deletion_event,
    staff_api_client,
    staff_user,
    user_list,
    permission_manage_users,
):
    user_1, user_2, *users = user_list

    query = CUSTOMER_BULK_DELETE_MUTATION

    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in user_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    assert content["data"]["customerBulkDelete"]["count"] == 2

    deleted_customers = [user_1, user_2]
    saved_customers = users

    # Ensure given customers were properly deleted and others properly saved
    # and any related event was properly triggered

    # Ensure the customers were properly deleted and others were preserved
    assert not User.objects.filter(
        id__in=[user.id for user in deleted_customers]
    ).exists()
    assert User.objects.filter(
        id__in=[user.id for user in saved_customers]
    ).count() == len(saved_customers)

    mocked_deletion_event.assert_called_once_with(
        staff_user=staff_user, app=None, deleted_count=len(deleted_customers)
    )


@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_customers_trigger_webhooks(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    staff_user,
    user_list,
    permission_manage_users,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in user_list]
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["customerBulkDelete"]["count"] == 2
    assert mocked_webhook_trigger.call_count == 2


@patch("saleor.graphql.account.mutations.base.account_events.customer_deleted_event")
def test_delete_customers_by_app(
    mocked_deletion_event,
    app_api_client,
    staff_user,
    user_list,
    permission_manage_users,
):
    user_1, user_2, *users = user_list

    query = CUSTOMER_BULK_DELETE_MUTATION

    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in user_list]
    }
    response = app_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    assert content["data"]["customerBulkDelete"]["count"] == 2

    deleted_customers = [user_1, user_2]
    saved_customers = users

    # Ensure given customers were properly deleted and others properly saved
    # and any related event was properly triggered

    # Ensure the customers were properly deleted and others were preserved
    assert not User.objects.filter(
        id__in=[user.id for user in deleted_customers]
    ).exists()
    assert User.objects.filter(
        id__in=[user.id for user in saved_customers]
    ).count() == len(saved_customers)

    mocked_deletion_event.assert_called_once_with(
        staff_user=None,
        app=app_api_client.app,
        deleted_count=len(deleted_customers),
    )
