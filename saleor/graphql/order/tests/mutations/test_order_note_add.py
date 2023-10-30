from unittest.mock import patch

import graphene
import pytest

from .....account.models import CustomerEvent
from .....order import OrderStatus
from .....order import events as order_events
from .....order.error_codes import OrderNoteAddErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

ORDER_NOTE_ADD_MUTATION = """
    mutation addNote($id: ID!, $message: String!) {
        orderNoteAdd(order: $id, input: {message: $message}) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
            event {
                user {
                    email
                }
                app {
                    name
                }
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_note_add_as_staff_user(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    staff_user,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    assert not order.events.all()
    order_id = graphene.Node.to_global_id("Order", order.id)
    message = "nuclear note"
    variables = {"id": order_id, "message": message}

    # when
    response = staff_api_client.post_graphql(ORDER_NOTE_ADD_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderNoteAdd"]

    assert data["order"]["id"] == order_id
    assert data["event"]["user"]["email"] == staff_user.email
    assert data["event"]["message"] == message
    order_updated_webhook_mock.assert_called_once_with(order)

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED

    # Ensure the correct order event was created
    event = order.events.get()
    assert event.type == order_events.OrderEvents.NOTE_ADDED
    assert event.user == staff_user
    assert event.parameters == {"message": message}

    # Ensure no customer events were created as it was a staff action
    assert not CustomerEvent.objects.exists()


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
    ],
)
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_note_add_fail_on_empty_message(
    order_updated_webhook_mock,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    message,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    variables = {"id": order_id, "message": message}

    # when
    response = staff_api_client.post_graphql(ORDER_NOTE_ADD_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderNoteAdd"]
    assert data["errors"][0]["field"] == "message"
    assert data["errors"][0]["code"] == OrderNoteAddErrorCode.REQUIRED.name
    order_updated_webhook_mock.assert_not_called()


def test_order_add_note_as_user_no_channel_access(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    order_with_lines,
    channel_PLN,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    order = order_with_lines
    order.channel = channel_PLN
    order.save(update_fields=["channel"])

    order_id = graphene.Node.to_global_id("Order", order.id)
    message = "nuclear note"
    variables = {"id": order_id, "message": message}

    # when
    response = staff_api_client.post_graphql(ORDER_NOTE_ADD_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_add_note_by_app(
    order_updated_webhook_mock,
    app_api_client,
    permission_manage_orders,
    order_with_lines,
):
    # given
    order = order_with_lines
    assert not order.events.all()
    order_id = graphene.Node.to_global_id("Order", order.id)
    message = "nuclear note"
    variables = {"id": order_id, "message": message}

    # when
    response = app_api_client.post_graphql(
        ORDER_NOTE_ADD_MUTATION, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderNoteAdd"]

    assert data["order"]["id"] == order_id
    assert data["event"]["user"] is None
    assert data["event"]["app"]["name"] == app_api_client.app.name
    assert data["event"]["message"] == message
    order_updated_webhook_mock.assert_called_once_with(order)


def test_order_note_add_fail_on_missing_permission(staff_api_client, order):
    # given
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id, "message": "a note"}

    # when
    response = staff_api_client.post_graphql(ORDER_NOTE_ADD_MUTATION, variables)

    # then
    assert_no_permission(response)
