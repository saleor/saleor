from unittest.mock import patch

import graphene

from .....app.error_codes import AppErrorCode
from ....tests.utils import get_graphql_content

REENABLE_BREAKER_MUTATION = """
    mutation AppReenableSyncWebhooks($appId: ID!) {
        appReenableSyncWebhooks(appId: $appId) {
            app {
                name
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@patch("saleor.graphql.app.mutations.app_reenable_sync_webhooks.breaker_board")
def test_reenable_sync_webhooks(
    breaker_board_mock,
    app,
    permission_manage_apps,
    staff_api_client,
    staff_user,
    caplog,
):
    # given
    breaker_board_mock.storage.clear_state_for_app.side_effect = lambda id: None
    staff_user.user_permissions.set([permission_manage_apps])
    variables = {
        "appId": graphene.Node.to_global_id("App", app.id),
    }

    # when
    response = staff_api_client.post_graphql(REENABLE_BREAKER_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    breaker_board_mock.storage.clear_state_for_app.assert_called_once_with(app.id)
    data = content["data"]["appReenableSyncWebhooks"]
    assert not data["errors"]
    assert caplog.messages == [
        f"[App ID: {app.id!r}] Circuit breaker manually reset by {staff_user!r}."
    ]


@patch("saleor.graphql.app.mutations.app_reenable_sync_webhooks.breaker_board")
def test_reenable_sync_webhooks_id_not_in_storage(
    breaker_board_mock,
    app,
    permission_manage_apps,
    staff_api_client,
    staff_user,
):
    # given
    breaker_board_mock.storage.clear_state_for_app.side_effect = lambda id: 1
    staff_user.user_permissions.set([permission_manage_apps])
    variables = {
        "appId": graphene.Node.to_global_id("App", app.id),
    }

    # when
    response = staff_api_client.post_graphql(REENABLE_BREAKER_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    breaker_board_mock.storage.clear_state_for_app.assert_called_once_with(app.id)
    error = content["data"]["appReenableSyncWebhooks"]["errors"][0]
    assert error["field"] == "appId"
    assert error["code"] == AppErrorCode.INVALID.name


@patch("saleor.graphql.app.mutations.app_reenable_sync_webhooks.breaker_board")
def test_reenable_sync_webhooks_non_existing_app_id(
    breaker_board_mock,
    permission_manage_apps,
    staff_api_client,
    staff_user,
):
    # given
    breaker_board_mock.storage.clear_state_for_app.side_effect = lambda id: 1
    staff_user.user_permissions.set([permission_manage_apps])
    variables = {
        "appId": graphene.Node.to_global_id("App", 9999),
    }

    # when
    response = staff_api_client.post_graphql(REENABLE_BREAKER_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    breaker_board_mock.storage.clear_state_for_app.assert_not_called()
    error = content["data"]["appReenableSyncWebhooks"]["errors"][0]
    assert error["field"] == "appId"
    assert error["code"] == AppErrorCode.NOT_FOUND.name
